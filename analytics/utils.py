## analytics/utils.py
## pkibuka@milky-way.space

from django.conf import settings
import plotly.graph_objects as go
from plotly.offline import plot
from typing import Dict
import logging
import pandas as pd
import json
import os
import calendar

logger = logging.getLogger(__name__)


def load_locations():
    path = os.path.join(settings.BASE_DIR, "config", "locations.json")

    with open(path, mode="r") as f:
        locations = json.load(f)
        return locations

def load_CEC_modules():
    path = os.path.join(settings.BASE_DIR, "config", "cec_modules.json")

    with open(path, mode="r") as f:
        modules = json.load(f)
        return modules

def load_CEC_inverters():
    path = os.path.join(settings.BASE_DIR, "config", "cec_inverters.json")

    with open(path, mode="r") as f:
        inverters = json.load(f)
        return inverters

        

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


def ac_aoi_chart(ac_aoi: pd.DataFrame, param: str):
    df = ac_aoi.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No data available for '{param}'",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)

def airmass_chart(airmass: pd.DataFrame, param: str):
    df = airmass.copy()
    # df[param] = df[param].fillna(0)

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)


def cell_temp_chart(cell_temp: pd.DataFrame):
    df = cell_temp.copy()
    # df.ffill()

    # Check if the entire series is NaN
    if df["cell_temperature"].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No cell temperature data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df["cell_temperature"],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title="Cell Temperature",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)


def dc_output_chart(dc_output: pd.DataFrame, param: str):
    df = dc_output.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)


def diode_params_chart(diode_params: pd.DataFrame, param: str):
    df = diode_params.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)



def total_irradiance_chart(total_irradiance: pd.DataFrame, param: str):
    df = total_irradiance.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)



def solar_position_chart(solar_position: pd.DataFrame, param: str):
    df = solar_position.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)


def weather_chart(weather: pd.DataFrame, param: str):
    df = weather.copy()

    # Check if the entire series is NaN
    if df[param].isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No {param} data available",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["day"],
        y=df[param],
        mode="lines",
        connectgaps=True
    ))

    fig.update_layout(
        template="plotly_dark",
        title=param,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)



