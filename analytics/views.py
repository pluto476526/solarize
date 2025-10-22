## visualisation/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from django.contrib import messages
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.pvwatts.simulator import PVWattsSimulator
from data_factory.pvlib.fixed_mount_simulator import FixedMountSimulator
from data_factory.pvlib.analyzer import Analyzer
from data_factory.pvlib import plots
from analytics import utils
import json
import logging

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

        fig = go.Figure(data=[
            go.Candlestick(
                x=df["bucket"],
                open=df["open"],
                high=df["high"],
                low=df["low"],
                close=df["close"],
            )
        ])

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="kWh/m²/day",
            xaxis_rangeslider_visible=False,
            template="plotly_dark"
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

    context = {}
    return render(request, "analytics/pvwatts_modelling.html", context)



def pvwatts_report_view(request):
    reports = request.session.get("pvwatts_report")

    if not reports:
        return redirect("pvwatts_modelling")

    savings_chart = None

    for report in reports:
        monthly_savings = report["financial_analysis"]["monthly_savings_breakdown"]
        savings_chart = utils.monthly_savings_chart(monthly_savings)
        report["savings_chart"] = savings_chart

        scenario_data = report["scenario_analysis"]
        efficiency_chart = utils.scenario_efficiency_chart(scenario_data)
        report["efficiency_chart"] = efficiency_chart

    context = {
        "reports": reports,
    }

    return render(request, "analytics/pvwatts_report.html", context)


def fixed_mount_system_view(request):
    conn = DatabaseConnection()
    db = DataManager(conn)

    if request.method == "POST":
        arrays_file = request.FILES.get('arrays_json')
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
            "name": request.POST.get("name"),
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
            "total_arrays": request.POST.get("arrays"),
            "temp_model": request.POST.get("temp_model"),
            "temp_model_params": request.POST.get("temp_model_params"),
            "description": request.POST.get("description"),
            "arrays_config": arrays_config,
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

        fms = FixedMountSimulator(
            timeframe_params=timeframe_params,
            location_params=location_params,
            system_params=system_params,
            losses_params=losses_params
        )

        report = fms.run_simulation()
        report_id = db.save_modelchain_result(report, array_names)
        db.close()

        messages.success(request, f"Configured system with {len(arrays_config)} arrays")
        request.session["pvlib_report"] = report_id
        return redirect("pvlib_report")

    context = {}
    return render(request, "analytics/fixed_mount_system.html", context)


def pvlib_report_view(request):
    report_id = request.session.get("pvlib_report", 1)

    if not report_id:
        return redirect("pvlib_modelling")

    conn = DatabaseConnection()
    db = DataManager(conn)

    simulation_data = db.fetch_modelchain_result(report_id)
    analyzer = Analyzer(simulation_data)
    analysis = analyzer.calculate_score()

    ac_aoi_param = request.GET.get("ac_aoi_parameter", "ac")
    ac_aoi_array = int(request.GET.get("array_idx", "1"))
    ac_aoi_chart = utils.ac_aoi_chart(simulation_data["ac_aoi"], ac_aoi_array, ac_aoi_param)

    n_dc = plots.normalize_pv_tuple(simulation_data["dc"])
    n_ac = plots.normalize_pv_tuple(simulation_data["ac_aoi"])
    n_irr = plots.normalize_pv_tuple(simulation_data["irradiance"])
    n_weather = plots.normalize_pv_tuple(simulation_data["weather"])
    n_cell_temp = plots.normalize_pv_tuple(simulation_data["cell_temperature"])

    charts = {
        "solar": plots.solar_elevation_chart(simulation_data["solar_position"]),
        "sunpath": plots.sunpath_chart(simulation_data["solar_position"]),
        "poa_vs_ghi": plots.poa_vs_ghi_chart(n_irr, n_weather),
        "irr_breakdown": plots.irradiance_breakdown_chart(n_weather),
        "poa_heatmap": plots.poa_heatmap(n_irr),
        "temp_wind": plots.temp_wind_chart(n_weather),
        "temp_vs_irr": plots.temp_vs_irradiance(n_cell_temp, n_irr),
        # "airmass_vs_spec": airmass_vs_spectral(airmass, spectral_modifier),
        "dc_vs_irr": plots.dc_vs_irradiance(n_dc, n_irr),
        "dc_vs_ac": plots.dc_vs_ac(n_dc, n_ac),
        "inverter_eff": plots.inverter_efficiency(n_dc, n_ac),
        "power_ts": plots.power_timeseries(n_dc, n_ac),
        "monthly_yield": plots.monthly_yield(n_ac),
        # "loss_waterfall": loss_waterfall(),
        # "irr_hist": effective_irradiance_hist(weather),
        # "temp_derate": temp_derating(cell_temperature, dc),
        # "ac_box": ac_boxplot(ac_aoi),
        # "power_heatmap": power_heatmap(ac_aoi),
        # "poa_vs_dc": poa_vs_dc(weather, dc),
        # "daily_yield": daily_yield(ac_aoi),
        # "cap_factor": capacity_factor(ac_aoi),
        # "cum_energy": cumulative_energy(ac_aoi),
        # "pr": performance_ratio(ac_aoi, weather)
    }
















    airmass = db.fetch_airmass_data(result_id=report_id)
    cell_temp = db.fetch_cell_temp_data(result_id=report_id)
    dc_output = db.fetch_dc_output_data(result_id=report_id)
    diode_params = db.fetch_diode_params_data(result_id=report_id)
    total_irradiance = db.fetch_total_irradiance_data(result_id=report_id)
    solar_position = db.fetch_solar_position_data(result_id=report_id)
    weather = db.fetch_weather_data(result_id=report_id)
    db.close()

    airmass_chart = utils.airmass_chart(airmass, param="relative_airmass")
    cell_temp_chart = utils.cell_temp_chart(cell_temp)
    dc_output_chart = utils.dc_output_chart(dc_output, param="i_sc")
    diode_params_chart = utils.diode_params_chart(diode_params, param="i_l")
    total_irradiance_chart = utils.total_irradiance_chart(total_irradiance, param="poa_global")
    solar_position_chart = utils.solar_position_chart(solar_position, param="zenith")
    weather_chart = utils.weather_chart(weather, param="ghi")



    context = {
        "analysis": analysis,
        "charts": charts,
        "ac_aoi_cols": ["ac", "aoi", "aoi_modifier"],
        # "ac_aoi_chart": ac_aoi_chart,
        "airmass_chart": airmass_chart,
        "cell_temp_chart": cell_temp_chart,
        "dc_output_chart": dc_output_chart,
        "diode_params_chart": diode_params_chart,
        "total_irradiance_chart": total_irradiance_chart,
        "solar_position_chart": solar_position_chart,
        "weather_chart": weather_chart,
    }

    return render(request, "analytics/pvlib_report.html", context)


def single_axis_tracking_view(request):
    context = {}
    return render(request, "analytics/single_axis_tracking.html", context)

def dual_axis_tracking_view(request):
    context = {}
    return render(request, "analytics/dual_axis_tracking.html", context)

def spec_sheet_modelling_view(request):
    context = {}
    return render(request, "analytics/spec_sheet_modelling.html", context)

def bifacial_system_view(request):
    context = {}
    return render(request, "analytics/bifacial_system.html", context)

def spectral_response_view(request):
    context = {}
    return render(request, "analytics/spectral_response.html", context)

def temperature_effects_view(request):
    context = {}
    return render(request, "analytics/temperature_effects.html", context)

def system_sizing_view(request):
    context = {}
    return render(request, "analytics/system_sizing.html", context)

def climate_modelling_view(request):
    context = {}
    return render(request, "analytics/climate_modelling.html", context)

def astronomy_view(request):
    context = {}
    return render(request, "analytics/astronomy.html", context)

def weather_view(request):
    context = {}
    return render(request, "analytics/weather.html", context)

def air_quality_view(request):
    context = {}
    return render(request, "analytics/air_quality.html", context)

def machine_learning_view(request):
    context = {}
    return render(request, "analytics/machine_learning.html", context)


def module_search(request):
    query = request.GET.get("q", "").lower()
    modules = utils.load_CEC_modules()
    results = [
        {"name": name, "manufacturer": mfg}
        for name, mfg in modules.items()
        if query in name.lower()
    ][:50]  # limit to 50 results
    return JsonResponse(results, safe=False)

def inverter_search(request):
    query = request.GET.get("q", "").lower()
    modules = utils.load_CEC_inverters()
    results = [
        {"name": name, "manufacturer": mfg}
        for name, mfg in modules.items()
        if query in name.lower()
    ][:50]  # limit to 50 results
    return JsonResponse(results, safe=False)

