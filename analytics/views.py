## visualisation/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.conf import settings
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.pvwatts.simulator import PVWattsSimulator
from data_factory.pvlib.simulator import PvlibSimulator
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


def pvlib_modelling_view(request):
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
        request.session["pvlib_report"] = report_id
        return redirect("pvlib_report")

    context = {}
    return render(request, "analytics/pvlib_modelling.html", context)

def pvlib_report_view(request):
    report_id = request.session.get("pvlib_report")

    if not report_id:
        return redirect("pvlib_modelling")

    conn = DatabaseConnection()
    db = DataManager(conn)
    report = db.fetch_modelchain_result(report_id)
    logger.debug(report)

    # savings_chart = None

    # monthly_savings = report["financial_analysis"]["monthly_savings_breakdown"]
    # savings_chart = monthly_savings_chart(monthly_savings)
    # report["savings_chart"] = savings_chart

    # scenario_data = report["scenario_analysis"]
    # efficiency_chart = scenario_efficiency_chart(scenario_data)
    # report["efficiency_chart"] = efficiency_chart

    context = {
        "report": report,
    }

    return render(request, "analytics/pvlib_report.html", context)


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

