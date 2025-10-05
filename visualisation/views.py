from django.shortcuts import render
from django.conf import settings
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.solar_advisor.solarize import SolarAdvisor
import plotly.graph_objects as go
from plotly.offline import plot
import logging
import json
import os

logger = logging.getLogger(__name__)


def import_locations():
    path = os.path.join(settings.BASE_DIR, "config", "locations.json")

    with open(path, mode="r") as f:
        locations = json.load(f)
        return locations

def index_view(request):
    locations = import_locations()
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
    return render(request, "visualisation/index.html", context)


def energy_forecasts_view(request):
    advisor = SolarAdvisor()
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

            advisor.add_location(name=loc_name, lat=float(lat), lon=float(lon))

            report = advisor.generate_report(loc_name, config=system_config)
            reports.append(report)

            location_idx += 1
        
        request.session["energy_forecasts"] = reports
        return redirect("energy_forecasts_report")

    context = {}
    return render(request, "visualisation/energy_forecasts.html", context)


def energy_forecasts_report_view(request):
    reports = request.session.get("energy_forecasts")
    context = {"reports": reports}
    logger.debug(context)
    return render(request, "visualisation/energy_forecast_report.html", context)
