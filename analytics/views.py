## visualisation/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from django.core.cache import cache
from django.core.signing import Signer
from data_factory.database.db_manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.pvwatts.simulator import PVWattsSimulator
from data_factory.pvlib import (
    fixed_mount_simulator,
    specs_simulator,
    bifacial_simulation,
    axis_tracking,
)
from data_factory.climate_projection import climate_projector, climate_plots
from data_factory.pvlib import general_analyzer, seasonal_analyzer, financial_analysis
from data_factory.pvlib import plots, timeseries
from data_factory import weather_analyzer, airquality_analyzer
from analytics import utils
import pickle
import json
import logging
import uuid

logger = logging.getLogger(__name__)


def index_view(request):
    locations = utils.load_locations()
    conn = DatabaseConnection()
    dbm = DataManager(conn)
    df = dbm.get_irradiance_ohlc_data(bucket="1 week")

    if df.empty:
        irradiance_chart = "<p>No data available</p>"

    else:
        df.dropna(subset=["open", "high", "low", "close"], how="all", inplace=True)

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df["bucket"],
                    open=df["open"],
                    high=df["high"],
                    low=df["low"],
                    close=df["close"],
                )
            ]
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="kWh/m²/day",
            xaxis_rangeslider_visible=False,
            template="plotly_dark",
        )

        irradiance_chart = plot(fig, output_type="div", include_plotlyjs=False)

    context = {
        "locations": locations,
        "irradiance_chart": irradiance_chart,
    }
    return render(request, "analytics/index.html", context)


def pvwatts_modelling_view(request):
    simulator = PVWattsSimulator()
    reports = []
    location_idx = 0

    if request.method == "POST":
        # Get system config parameters
        system_config = {
            "system_capacity": float(request.POST.get("system_capacity", 5)),
            "azimuth": int(request.POST.get("azimuth", 180)),
            "tilt": int(request.POST.get("tilt", 20)),
            "array_type": int(request.POST.get("array_type", 0)),
            "module_type": int(request.POST.get("module_type", 0)),
            "losses": int(request.POST.get("losses", 14)),
            "timeframe": request.POST.get("timeframe", "hourly"),
        }

        while True:
            loc_name = request.POST.get(f"locations[{location_idx}][name]")
            lat = request.POST.get(f"locations[{location_idx}][lat]")
            lon = request.POST.get(f"locations[{location_idx}][lon]")

            # Stop looping if no more locations in POST data
            if not (loc_name and lat and lon):
                break

            simulator.add_location(name=loc_name, lat=float(lat), lon=float(lon))
            report = simulator.generate_report(loc_name, config=system_config)
            reports.append(report)

            location_idx += 1

        request.session["pvwatts_report"] = reports
        return redirect("pvwatts_report")

    return render(request, "analytics/pvwatts_modelling.html", {})


def pvwatts_report_view(request):
    reports = request.session.get("pvwatts_report")

    if not reports:
        return redirect("pvwatts_modelling")

    for report in reports:
        monthly_savings = report["financial_analysis"]["monthly_savings_breakdown"]
        report["savings_chart"] = utils.monthly_savings_chart(monthly_savings)
        
        scenario_data = report["scenario_analysis"]
        report["efficiency_chart"] = utils.scenario_efficiency_chart(scenario_data)

    context = {"reports": reports}
    return render(request, "analytics/pvwatts_report.html", context)


def fixed_mount_system_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)

    if request.method == "POST":

        required_fields = ["lat", "lon", "alt", "tz"]
        missing = [f for f in required_fields if not request.POST.get(f)]

        if missing:
            messages.error(request, f"Missing required fields: {', '.join(missing)}")
            return redirect("fixed_mount_system")

        simulation_name = request.POST.get("name", "Fixed_Mount")
        description = request.POST.get("description")
        arrays_file = request.FILES.get("arrays_json")
        arrays_config = json.load(arrays_file) if arrays_file else {}

        array_names = {}

        for idx, arr in enumerate(arrays_config):
            name = arr.get("name", f"Array_{idx}")
            array_names[str(idx)] = name

        index = len(array_names)
        array_names[str(index)] = "MainArray"

        location_params = {
            "name": simulation_name,
            "lat": request.POST.get("lat"),
            "lon": request.POST.get("lon"),
            "alt": request.POST.get("alt"),
            "tz": request.POST.get("tz"),
            "albedo": request.POST.get("albedo"),
        }

        system_params = {
            "module": request.POST.get("module"),
            "module_type": request.POST.get("module_type"),
            "inverter": request.POST.get("inverter"),
            "surface_azimuth": request.POST.get("azimuth"),
            "surface_tilt": request.POST.get("tilt"),
            "modules_per_string": request.POST.get("modules_per_string"),
            "strings": request.POST.get("strings"),
            "temp_model": request.POST.get("temp_model"),
            "temp_model_params": request.POST.get("temp_model_params"),
            "arrays_config": arrays_config,
            "description": request.POST.get("description", ""),
            "year": request.POST.get("year"),
        }

        losses_params = {
            "soiling": request.POST.get("soiling"),
            "shading": request.POST.get("shading"),
            "snow": request.POST.get("snow"),
            "mismatch": request.POST.get("mismatch"),
            "wiring": request.POST.get("wiring"),
            "connections": request.POST.get("connections"),
            "lid": request.POST.get("lid"),
            "nameplate": request.POST.get("nameplate"),
            "age": request.POST.get("age"),
            "availability": request.POST.get("availability"),
        }

        try:
            fms = fixed_mount_simulator.FixedMountSimulator(
                location_params=location_params,
                system_params=system_params,
                losses_params=losses_params,
            )

            result, config = fms.run_simulation()
            result_id = db.save_modelchain_result(
                result=result,
                config=config,
                array_names=array_names
            )
            db.close()

        except Exception as e:
            logger.error(e)
            messages.warning(request, "Could not complete simulation. Check parameters and try again.")
            return redirect("fixed_mount_system")

        signer = Signer()
        token = signer.sign(result_id)
        return redirect("modelchain_result", token=token)

    context = {}
    return render(request, "analytics/fixed_mount_system.html", context)


def spec_sheet_modelling_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)

    if request.method == "POST":

        required_fields = ["lat", "lon", "alt", "tz"]
        missing = [f for f in required_fields if not request.POST.get(f)]

        if missing:
            messages.error(request, f"Missing required fields: {', '.join(missing)}")
            return redirect("spec_sheet_modelling")

        simulation_name = request.POST.get("name", "Custom PV System")
        description = request.POST.get("description")
        arrays_file = request.FILES.get("arrays_json")
        arrays_config = json.load(arrays_file) if arrays_file else {}

        array_names = {}

        for idx, arr in enumerate(arrays_config):
            name = arr.get("name", f"Array_{idx}")
            array_names[str(idx)] = name

        index = len(array_names)
        array_names[str(index)] = "MainArray"

        location_params = {
            "name": simulation_name,
            "lat": request.POST.get("lat"),
            "lon": request.POST.get("lon"),
            "alt": request.POST.get("alt"),
            "tz": request.POST.get("tz"),
            "albedo": request.POST.get("albedo"),
        }

        module_params = {
            "pdc0": float(request.POST.get("pdc0")),
            "v_mp": float(request.POST.get("v_mp")),
            "i_mp": float(request.POST.get("i_mp")),
            "v_oc": float(request.POST.get("v_oc")),
            "i_sc": float(request.POST.get("i_sc")),
            "cells_in_series": int(request.POST.get("cells_in_series"))
        }

        temp_coefficients = {
            "alpha_sc": (float(request.POST.get("Isc")) / 100)
            * float(request.POST.get("i_sc")),
            "beta_voc": (float(request.POST.get("voc")) / 100)
            * float(request.POST.get("v_oc")),
            "gamma_pmp": float(request.POST.get("Pmax")),
        }

        inverter_params = {
            "pdc0": float(request.POST.get("pdc")),
            "eta_inv_nom": float(request.POST.get("eta_inv_nom")),
            "eta_inv_ref": float(request.POST.get("eta_inv_ref")),
        }

        system_params = {
            "arrays_config": arrays_config,
            "module_params": module_params,
            "temp_coefficients": temp_coefficients,
            "inverter_params": inverter_params,
            "module_type": request.POST.get("module_type"),
            "celltype": request.POST.get("celltype"),
            "surface_azimuth": request.POST.get("azimuth"),
            "surface_tilt": request.POST.get("tilt"),
            "modules_per_string": request.POST.get("modules_per_string"),
            "strings": request.POST.get("strings"),
            "racking_model": request.POST.get("racking_model"),
            "temp_model": request.POST.get("temp_model"),
            "temp_model_params": request.POST.get("temp_model_params"),
            "description": request.POST.get("description"),
            "year": request.POST.get("year"),
        }

        losses_params = {
            "soiling": request.POST.get("soiling"),
            "shading": request.POST.get("shading"),
            "snow": request.POST.get("snow"),
            "mismatch": request.POST.get("mismatch"),
            "wiring": request.POST.get("wiring"),
            "connections": request.POST.get("connections"),
            "lid": request.POST.get("lid"),
            "nameplate": request.POST.get("nameplate"),
            "age": request.POST.get("age"),
            "availability": request.POST.get("availability"),
        }

        try:
            sss = specs_simulator.SpecSheetSimulator(
                location_params=location_params,
                system_params=system_params,
                losses_params=losses_params,
            )

            if not sss.validate_inputs(request=request):
                return redirect("spec_sheet_modelling")

            result, config = sss.run_simulation()
            result_id = db.save_modelchain_result(
                result=result,
                config=config,
                array_names=array_names
            )
            db.close()

        except Exception as e:
            logger.debug(e)
            messages.error(request, "Could not complete simulation. Check parameters and try again.")
            return redirect("spec_sheet_modelling")

        signer = Signer()
        token = signer.sign(result_id)
        return redirect("modelchain_result", token=token)

    context = {}
    return render(request, "analytics/spec_sheet_modelling.html", context)


def axis_tracking_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)

    if request.method == "POST":

        required_fields = ["lat", "lon", "alt", "tz"]
        missing = [f for f in required_fields if not request.POST.get(f)]

        if missing:
            messages.error(request, f"Missing required fields: {', '.join(missing)}")
            return redirect("axis_tracking")

        simulation_name = request.POST.get("name", "Single_Dual_Axis_Tracking")
        description = request.POST.get("description")
        arrays_file = request.FILES.get("arrays_json")
        arrays_config = json.load(arrays_file) if arrays_file else {}

        array_names = {}

        for idx, arr in enumerate(arrays_config):
            name = arr.get("name", f"Array_{idx}")
            array_names[str(idx)] = name

        index = len(array_names)
        array_names[str(index)] = "MainArray"

        timeframe_params = {
            "start_date": request.POST.get("start_date"),
            "end_date": request.POST.get("end_date"),
            "timeframe": request.POST.get("timeframe", "hourly"),
        }

        location_params = {
            "name": simulation_name,
            "lat": request.POST.get("lat"),
            "lon": request.POST.get("lon"),
            "alt": request.POST.get("alt"),
            "tz": request.POST.get("tz"),
            "albedo": request.POST.get("albedo"),
        }

        system_params = {
            "arrays_config": arrays_config,
            "module": request.POST.get("module"),
            "module_type": request.POST.get("module_type"),
            "inverter": request.POST.get("inverter"),
            "modules_per_string": request.POST.get("modules_per_string"),
            "strings": request.POST.get("strings"),
            "temp_model": request.POST.get("temp_model"),
            "temp_model_params": request.POST.get("temp_model_params"),
            "description": request.POST.get("description"),
            "year": request.POST.get("year"),
        }

        tracking_params = {
            "axis_azimuth": request.POST.get("azimuth"),
            "axis_tilt": request.POST.get("tilt"),
            "max_angle": request.POST.get("max_angle"),
            "backtrack": request.POST.get("backtrack"),
            "gcr": request.POST.get("gcr"),
        }

        losses_params = {
            "soiling": request.POST.get("soiling"),
            "shading": request.POST.get("shading"),
            "snow": request.POST.get("snow"),
            "mismatch": request.POST.get("mismatch"),
            "wiring": request.POST.get("wiring"),
            "connections": request.POST.get("connections"),
            "lid": request.POST.get("lid"),
            "nameplate": request.POST.get("nameplate"),
            "age": request.POST.get("age"),
            "availability": request.POST.get("availability"),
        }

        try:
            sdt = axis_tracking.SingleDualAxisTracker(
                location_params=location_params,
                system_params=system_params,
                tracking_params=tracking_params,
                losses_params=losses_params,
            )

            result, config = sdt.run_simulation()
            result_id = db.save_modelchain_result(
                result=result,
                config=config,
                array_names=array_names
            )
            db.close()

        except Exception as e:
            logger.error(e)
            messages.error(request, "Could not complete simulation. Check parameters and try again.")
            return redirect("axis_tracking")

        signer = Signer()
        token = signer.sign(result_id)
        return redirect("modelchain_result", token=token)

    context = {}
    return render(request, "analytics/axis_tracking.html", context)


def bifacial_system_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)

    if request.method == "POST":

        required_fields = ["lat", "lon", "alt", "tz"]
        missing = [f for f in required_fields if not request.POST.get(f)]

        if missing:
            messages.error(request, f"Missing required fields: {', '.join(missing)}")
            return redirect("bifacial_system")


        simulation_name = request.POST.get("name", "Bifacial_System")
        description = request.POST.get("description")
        arrays_file = request.FILES.get("arrays_json")
        
        if arrays_file:
            try:
                arrays_config = json.load(arrays_file)
                if not isinstance(arrays_config, list):
                    messages.error(request, "Invalid arrays file: must be a JSON array.")
                    return redirect("bifacial_system")
            except json.JSONDecodeError:
                messages.error(request, "Invalid JSON in arrays file.")
                return redirect("bifacial_system")


        location_params = {
            "name": simulation_name,
            "lat": request.POST.get("lat"),
            "lon": request.POST.get("lon"),
            "alt": request.POST.get("alt"),
            "tz": request.POST.get("tz"),
            "albedo": request.POST.get("albedo"),
        }

        bifacial_params = {
            "bifaciality": float(request.POST.get("bifaciality")),
            "gcr": float(request.POST.get("gcr")),
            "pvrow_height": float(request.POST.get("pvrow_height")),
            "pvrow_width": float(request.POST.get("pvrow_width")),
            "n_pvrows": int(request.POST.get("n_pvrows")),
            "index_observed_pvrow": int(request.POST.get("index_observed_pvrow")),
            "rho_front_pvrow": float(request.POST.get("rho_front_pvrow")),
            "rho_back_pvrow": float(request.POST.get("rho_back_pvrow")),
            "horizon_band_angle": float(request.POST.get("horizon_band_angle")),
        }

        system_params = {
            "arrays_config": arrays_config,
            "bifaciality": bifacial_params,
            "surface_azimuth": request.POST.get("azimuth"),
            "surface_tilt": request.POST.get("tilt"),
            "module": request.POST.get("module"),
            "module_type": request.POST.get("module_type"),
            "inverter": request.POST.get("inverter"),
            "modules_per_string": request.POST.get("modules_per_string"),
            "strings": request.POST.get("strings"),
            "temp_model": request.POST.get("temp_model"),
            "temp_model_params": request.POST.get("temp_model_params"),
            "description": request.POST.get("description"),
            "year": request.POST.get("year"),
        }

        losses_params = {
            "soiling": request.POST.get("soiling"),
            "shading": request.POST.get("shading"),
            "snow": request.POST.get("snow"),
            "mismatch": request.POST.get("mismatch"),
            "wiring": request.POST.get("wiring"),
            "connections": request.POST.get("connections"),
            "lid": request.POST.get("lid"),
            "nameplate": request.POST.get("nameplate"),
            "age": request.POST.get("age"),
            "availability": request.POST.get("availability"),
        }

        try:
            bpv = bifacial_simulation.BifacialPVSimulator(
                location_params=location_params,
                system_params=system_params,
                losses_params=losses_params,
            )

            result = bpv.run_simulation()
            result_id = db.save_modelchain_result(
                result=result,
                array_names=array_names,
                simulation_name=simulation_name,
                description=description,
            )
        except Exception as e:
            logger.error(e)
            messages.error(request, "Could not complete simulation. Check parameters and try again.")
            return redirect("bifacial_system")

        signer = Signer()
        token = signer.sign(result_id)
        return redirect("modelchain_result", token=token)

    context = {}
    return render(request, "analytics/bifacial_system.html", context)


def modelchain_result_view(request, token):
    signer = Signer()

    try:
        result_id = signer.unsign(token)
    except Exception:
        return redirect(request.META.get("HTTP_REFERER", "/"))

    user_id = request.user.id
    cache_version_key = f"mc_result_version_{user_id}_{result_id}"
    version = cache.get(cache_version_key, 1)  # used for invalidation control

    # Primary cache keys
    data_key = f"mc_data_{user_id}_{result_id}_v{version}"
    norm_key = f"mc_norm_{user_id}_{result_id}_v{version}"
    charts_key = f"mc_charts_{user_id}_{result_id}_v{version}"

    # Fetch or compute simulation data
    # simulation_data = None
    simulation_data = cache.get(data_key)

    if not simulation_data:
        conn = DatabaseConnection()
        db = DataManager(conn)
        simulation_data = db.fetch_modelchain_result(result_id)
        db.close()
        cache.set(data_key, simulation_data, timeout=86400)  # cache for 24h

    # Pre-normalize data for chart generation
    normalized_data = cache.get(norm_key)
    if not normalized_data:
        normalized_data = {
            "dc": plots.normalize_pv_tuple(simulation_data["dc"]),
            "ac": plots.normalize_pv_tuple(simulation_data["ac"]),
            "irr": plots.normalize_pv_tuple(simulation_data["irradiance"]),
            "weather": plots.normalize_pv_tuple(simulation_data["weather"]),
            "cell_temp": plots.normalize_pv_tuple(simulation_data["cell_temperature"]),
        }
        cache.set(norm_key, normalized_data, timeout=86400)

    # Cache heavy chart objects separately for modular control
    charts = cache.get(charts_key)
    if not charts:
        nd = normalized_data
        charts = {
            "temp_wind": plots.temp_wind_chart(nd["weather"]),
            "temp_vs_irr": plots.temp_vs_irradiance(nd["cell_temp"], nd["irr"]),
            "dc_vs_ac": plots.dc_vs_ac(nd["dc"], nd["ac"]),
            "dc_vs_irr": plots.dc_vs_irradiance(nd["dc"], nd["irr"]),
            "inverter_eff": plots.inverter_efficiency(nd["dc"], nd["ac"]),
            "power_ts": plots.power_timeseries(nd["dc"], nd["ac"]),
            "monthly_yield": plots.monthly_yield(nd["ac"]),
            "temp_derate": plots.temp_derating(nd["cell_temp"], nd["dc"]),
            "power_heatmap": plots.power_heatmap(nd["ac"]),
            "daily_yield": plots.daily_yield(nd["ac"]),
            "cap_factor": plots.capacity_factor(nd["ac"]),
            "cum_energy": plots.cumulative_energy(nd["ac"]),
            "solar_elevation": plots.solar_elevation_chart(
                simulation_data["solar_position"]
            ),
            "sunpath": plots.sunpath_chart(simulation_data["solar_position"]),
            "poa_vs_ghi": plots.poa_vs_ghi_chart(nd["irr"], nd["weather"]),
            "poa_heatmap": plots.poa_heatmap(nd["irr"]),
            "irr_breakdown": plots.irradiance_breakdown_chart(nd["weather"]),
            "peak_power_vs_irr": plots.peak_power_vs_irradiance(nd["ac"], nd["irr"]),
            "performance_ratio": plots.performance_ratio(nd["ac"], nd["irr"]),
        }
        cache.set(charts_key, charts, timeout=86400)

    # User-specific visualization parameters
    ac_param = request.GET.get("ac_param", "ac")
    aoi_param = request.GET.get("aoi_param", "aoi")
    dc_output_param = request.GET.get("dc_output_param", "i_sc")
    diode_params_param = request.GET.get("diode_params_param", "i_l")
    irradiance_param = request.GET.get("irradiance_param", "poa_global")
    weather_param = request.GET.get("weather_param", "temp_air")
    solar_position_param = request.GET.get("solar_position_param", "zenith")

    # Build time-series charts
    time_series = {
        "ac": timeseries.ac_chart(
            simulation_data["ac"], ac_param
        ),
        "aoi": timeseries.aoi_chart(
            simulation_data["aoi"], aoi_param
        ),
        "cell_temp": timeseries.cell_temp_chart(
            simulation_data["cell_temperature"]
        ),
        "dc_output": timeseries.dc_output_chart(
            simulation_data["dc"], dc_output_param
        ),
        "diode_params": timeseries.diode_params_chart(
            simulation_data["diode_params"], diode_params_param
        ),
        "irradiance": timeseries.total_irradiance_chart(
            simulation_data["irradiance"], irradiance_param
        ),
        "weather": timeseries.weather_chart(simulation_data["weather"], weather_param),
        "solar_position": timeseries.solar_position_chart(simulation_data["solar_position"], solar_position_param)
    }

    meta_data = {
        "simulation_name": simulation_data["simulation_name"],
        "system_type": simulation_data["system_type"],
        "latitude": simulation_data["latitude"],
        "longitude": simulation_data["longitude"],
        "altitude": simulation_data["altitude"],
        "timezone": simulation_data["timezone"],
        "module_name": simulation_data["module_name"],
        "module_type": simulation_data["module_type"],
        "cell_type": simulation_data["cell_type"],
        "custom_module_params": simulation_data["custom_module_params"],
        "arrays": simulation_data["arrays"],
        "inverter_name": simulation_data["inverter_name"],
        "custom_inverter_params": simulation_data["custom_inverter_params"],
        "temperature_model": simulation_data["temperature_model"],
        "temp_model_params": simulation_data["temp_model_params"],
        "custom_temp_params": simulation_data["custom_temp_params"],
        "description": simulation_data["description"],
        "created_at": simulation_data["created_at"],
    }

    # Analysis modules
    gm = general_analyzer.Analyzer(simulation_data)
    sa = seasonal_analyzer.SeasonalAnalyzer(simulation_data)
    fn = financial_analysis.FinancialAnalyzer(simulation_data)
    general_metrics = gm.calculate_score()
    seasonal_analysis = sa.generate_seasonal_report()
    financial_metrics = fn.calculate_score()

    context = {
        "meta_data": meta_data,
        "general_metrics": general_metrics,
        "seasonal_analysis": seasonal_analysis,
        "financial_data": financial_metrics,
        "charts": charts,
        "timeseries": time_series,
        "ac_cols": ["ac"],
        "aoi_cols": ["aoi", "aoi_modifier"],
        "cell_temp_cols": ["temperature"],
        "dc_output_cols": ["i_sc", "v_oc", "i_mp", "v_mp", "p_mp", "i_x", "i_xx"],
        "diode_params_cols": ["I_L", "I_o", "R_s", "R_sh", "nNsVth"],
        "irradiance_cols": [
            "poa_global",
            "poa_direct",
            "poa_diffuse",
            "poa_sky_diffuse",
            "poa_ground_diffuse",
        ],
        "weather_cols": ["ghi", "dni", "dhi", "temp_air", "wind_speed"],
        "solar_cols": [
            "zenith",
            "azimuth",
            "elevation",
            "apparent_zenith",
            "apparent_elevation",
            "equation_of_time",
        ],
        "arrays": {},
    }

    return render(request, "analytics/modelchain_result.html", context)


def weather_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)
    lat, lon = -1.2921, 36.8219
    location_data, current_df, hourly_df, daily_df = db.fetch_openmeteo_data(lat, lon)
    db.close()
    wa = weather_analyzer.WeatherAnalyzer(
        location_data=location_data,
        current_weather=current_df,
        hourly_weather=hourly_df,
        daily_weather=daily_df,
    )
    analysis = wa.analyze_weather()
    context = {"analysis": analysis}
    return render(request, "analytics/weather.html", context)


def nasa_climate_modelling_view(request):
    if request.method == "POST":
        nasa_params = {
            "name": request.POST.get("name"),
            "lat": request.POST.get("lat"),
            "lon": request.POST.get("lon"),
            "timestandard": request.POST.get("time_standard"),
            "community": request.POST.get("community"),
            "model": request.POST.get("climate_model"),
            "scenario": request.POST.get("scenario"),
            "crops": request.POST.getlist("crops"),
            "start": request.POST.get("start"),
            "end": request.POST.get("end"),
        }
        cm = climate_projector.SolarAgriProjector(nasa_params)
        result = cm.run_simulation()
        plots = climate_plots.generate_all_plots(result)

        data = {"result": result, "plots": plots}
        pickled_data = pickle.dumps(data)
        
        cache_key = uuid.uuid4()
        cache.set(cache_key, pickled_data, timeout=3600)
        return redirect("climate_results", key=cache_key)
    context = {}
    return render(request, "analytics/climate_modelling_nasa.html", context)


def climate_results_view(request, key):
    pickled_data = cache.get(key)
    data = pickle.loads(pickled_data)
    context = {
        "insights": data["result"]["insights"],
        "plots": data["plots"],
    }
    return render(request, "analytics/climate_results.html", context)

def help_view(request):
    context = {}
    return render(request, "analytics/help.html", context)


def repository_view(request):
    context = {}
    return render(request, "analytics/repository.html", context)



def air_quality_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)
    lat, lon = -1.2921, 36.8219
    location_data, current_df, hourly_df = db.fetch_air_quality_data(lat, lon)
    db.close()
    aq = airquality_analyzer.AirQualityAnalyzer(
        location_data=location_data,
        current_weather=current_df,
        hourly_weather=hourly_df,
    )
    analysis = aq.analyze_air_quality()
    context = {"air_quality": analysis}
    return render(request, "analytics/air_quality.html", context)


def module_search(request):
    query = request.GET.get("q", "").lower()
    modules = utils.load_CEC_modules()
    results = [
        {"name": name, "manufacturer": mfg}
        for name, mfg in modules.items()
        if query in name.lower()
    ][
        :50
    ]  # limit to 50 results
    return JsonResponse(results, safe=False)


def inverter_search(request):
    query = request.GET.get("q", "").lower()
    modules = utils.load_CEC_inverters()
    results = [
        {"name": name, "manufacturer": mfg}
        for name, mfg in modules.items()
        if query in name.lower()
    ][
        :50
    ]  # limit to 50 results
    return JsonResponse(results, safe=False)
