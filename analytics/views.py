## visualisation/views.py
## pkibuka@milky-way.space

from django.shortcuts import render, redirect
from django.conf import settings
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
from data_factory.solar_advisor.solarize import SolarAdvisor
import plotly.graph_objects as go
from plotly.offline import plot
from typing import Dict
import logging
import json
import os
import calendar

logger = logging.getLogger(__name__)


def import_locations():
    path = os.path.join(settings.BASE_DIR, "config", "locations.json")

    with open(path, mode="r") as f:
        locations = json.load(f)
        return locations

def monthly_savings_chart(monthly_savings: Dict):
    # Sort months (1–12) and map to names
    months = sorted(map(int, monthly_savings.keys()))
    month_names = [calendar.month_abbr[m] for m in months]
    savings = [monthly_savings[str(m)] for m in months]

    # Create line chart
    fig = go.Figure(data=[
        go.Scatter(
            x=month_names,
            y=savings,
            mode="lines+markers",
            name="Savings"
        )
    ])

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Savings",
        xaxis=dict(tickmode="array", tickvals=month_names),
        xaxis_rangeslider_visible=False,
        template="plotly_dark"
    )

    # Convert figure to HTML div
    savings_chart = plot(fig, output_type="div", include_plotlyjs=False)
    return savings_chart

def scenario_efficiency_chart(scenario_data: Dict):
    scenarios = [d["scenario"] for d in scenario_data]
    annual_kwh = [d["annual_kwh"] for d in scenario_data]
    efficiency = [d["efficiency_ratio"] for d in scenario_data]
    percent_opt = [d["percent_of_optional"] for d in scenario_data]

    # Build bubble chart
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=efficiency,
        y=annual_kwh,
        mode="markers",
        text=scenarios,
        textposition="top center",
        marker=dict(
            size=[p/2 for p in percent_opt],  # scale bubble size
            sizemode="area",
            color=percent_opt,
            colorscale="Viridis",
            showscale=True,
            line=dict(width=1, color="DarkSlateGrey")
        ),
        hovertemplate="<b>%{text}</b><br>Efficiency: %{x}<br>Annual kWh: %{y}<br>Optional: %{marker.size}<extra></extra>"
    ))

    fig.update_layout(
        xaxis_title="Efficiency Ratio",
        yaxis_title="Annual kWh",
        template="plotly_dark"
    )

    efficiency_chart = plot(fig, output_type="div", include_plotlyjs=False)
    return efficiency_chart


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
    return render(request, "analytics/index.html", context)


def pvwatts_modelling_view(request):
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
        savings_chart = monthly_savings_chart(monthly_savings)
        report["savings_chart"] = savings_chart

        scenario_data = report["scenario_analysis"]
        efficiency_chart = scenario_efficiency_chart(scenario_data)
        report["efficiency_chart"] = efficiency_chart

    context = {
        "reports": reports,
    }

    return render(request, "analytics/pvwatts_report.html", context)


def pvlib_modelling_view(request):
    context = {}
    return render(request, "analytics/pvlib_modelling.html", context)


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

