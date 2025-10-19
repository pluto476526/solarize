## visualisation/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.pvwatts.simulator import PVWattsSimulator
from data_factory.pvlib.simulator import PvlibSimulator
from data_factory.pvlib.analyzer import Analyzer
from analytics import utils
import logging

logger = logging.getLogger(__name__)




def index_view(request):
    locations = utils.import_locations()
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
        name = request.POST.get("name")
        lat = request.POST.get("lat")
        lon = request.POST.get("lon")
        alt = request.POST.get("alt")
        tz = request.POST.get("tz")

        module = request.POST.get("module")
        module_db = request.POST.get("module_db")
        inverter = request.POST.get("inverter")
        inverter_db = request.POST.get("inverter_db")
        surface_azimuth = request.POST.get("azimuth")
        surface_tilt = request.POST.get("tilt")
        temp_model = request.POST.get("temp_model")
        temp_model_params = request.POST.get("temp_model_params")

        # "timeframe": request.POST.get("timeframe", "hourly"),

        simulator = PvlibSimulator(
            name=name,
            lat=lat,
            lon=lon,
            alt=alt,
            tz=tz,
            module=module,
            inverter=inverter,
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            temp_model=temp_model,
            temp_model_params=temp_model_params
        )

        report = simulator.run_pvlib_simulation()
        report_id = db.save_modelchain_result(report)
        db.close()
        request.session["pvlib_report"] = report_id
        return redirect("pvlib_report")

    context = {}
    return render(request, "analytics/fixed_mount_system.html", context)


def pvlib_report_view(request):
    # report_id = request.session.get("pvlib_report")

    # if not report_id:
    #     return redirect("pvlib_modelling")

    report_id = 1

    conn = DatabaseConnection()
    db = DataManager(conn)

    simulation_data = db.fetch_modelchain_result(report_id)
    analyzer = Analyzer(simulation_data)
    analysis = analyzer.calculate_score()

    ac_aoi = db.fetch_ac_aoi_data(result_id=report_id)
    airmass = db.fetch_airmass_data(result_id=report_id)
    cell_temp = db.fetch_cell_temp_data(result_id=report_id)
    dc_output = db.fetch_dc_output_data(result_id=report_id)
    diode_params = db.fetch_diode_params_data(result_id=report_id)
    total_irradiance = db.fetch_total_irradiance_data(result_id=report_id)
    solar_position = db.fetch_solar_position_data(result_id=report_id)
    weather = db.fetch_weather_data(result_id=report_id)
    db.close()

    ac_aoi_chart = utils.ac_aoi_chart(ac_aoi, param="ac")
    airmass_chart = utils.airmass_chart(airmass, param="relative_airmass")
    cell_temp_chart = utils.cell_temp_chart(cell_temp)
    dc_output_chart = utils.dc_output_chart(dc_output, param="i_sc")
    diode_params_chart = utils.diode_params_chart(diode_params, param="i_l")
    total_irradiance_chart = utils.total_irradiance_chart(total_irradiance, param="poa_global")
    solar_position_chart = utils.solar_position_chart(solar_position, param="zenith")
    weather_chart = utils.weather_chart(weather, param="ghi")

    context = {
        "analysis": analysis,
        "ac_aoi_chart": ac_aoi_chart,
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

