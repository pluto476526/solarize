## analytics/pvlib/plots.py
## pkibuka@milky-way.space

import plotly.graph_objects as go
from plotly.offline import plot
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def normalize_pv_tuple(data):
    """
    Aggregate PVLib tuple, Series, or DataFrame into a DataFrame with original columns.
    If multiple arrays are given (tuple), average per column across arrays, filling missing columns with NaN.

    Parameters:
        data: tuple, pd.Series, or pd.DataFrame

    Returns:
        pd.DataFrame or pd.Series: Aggregated system-level data
    """

    # Tuple of Series/DataFrames
    if isinstance(data, tuple):
        dfs = []
        for d in data:
            if isinstance(d, pd.Series):
                dfs.append(d.to_frame())
            elif isinstance(d, pd.DataFrame):
                dfs.append(d)
            else:
                raise TypeError(f"Unexpected type in tuple: {type(d)}")
        
        # Align all DataFrames by columns, filling missing columns with NaN
        aligned = pd.concat(dfs, axis=0, keys=range(len(dfs)))
        # Compute mean per original column across arrays
        averaged = aligned.groupby(level=1).mean()
        return averaged

    # Single Series
    if isinstance(data, pd.Series):
        return data.to_frame()

    # Single DataFrame
    if isinstance(data, pd.DataFrame):
        return data.copy()

    raise TypeError(f"Cannot normalize type: {type(data)}")





def chart(fig):
    fig.update_layout(template="plotly_dark", margin=dict(l=40, r=20, t=50, b=40))
    return plot(fig, output_type="div", include_plotlyjs=False)


# ================================================================
#   SOLAR GEOMETRY & IRRADIANCE
# ================================================================
def solar_elevation_chart(solar):
    fig = go.Figure(go.Scatter(x=solar.index, y=solar["elevation"], mode="lines"))
    fig.update_layout(title="Solar Elevation vs Time", xaxis_title="Time", yaxis_title="Elevation (°)")
    return chart(fig)


def sunpath_chart(solar):
    sample = solar.groupby(solar.index.date).head(100)
    fig = go.Figure(go.Scatterpolar(
        r=sample["elevation"], theta=sample["azimuth"], mode="markers", marker=dict(size=3)
    ))
    fig.update_layout(title="Sunpath Diagram", polar=dict(radialaxis=dict(title="Elevation (°)")))
    return chart(fig)


def poa_vs_ghi_chart(irradiance, weather):
    fig = go.Figure(go.Scatter(x=irradiance["poa_global"], y=weather["ghi"], mode="markers", opacity=0.5))
    fig.update_layout(title="POA vs GHI", xaxis_title="POA (W/m²)", yaxis_title="GHI (W/m²)")
    return chart(fig)


def irradiance_breakdown_chart(weather):
    weekly_weather = weather.resample("W-MON").mean()
    fig = go.Figure()
    for comp in ["ghi", "dni", "dhi"]:
        if comp in weekly_weather.columns:
            fig.add_trace(go.Scatter(x=weekly_weather.index, y=weekly_weather[comp], stackgroup="one", name=comp.upper()))
    fig.update_layout(title="Irradiance Breakdown (GHI / DNI / DHI)", xaxis_title="Time", yaxis_title="W/m²")
    return chart(fig)


def poa_heatmap(irradiance):
    df = irradiance.copy()
    df["day"] = df.index.dayofyear
    df["hour"] = df.index.hour
    pivot = df.pivot_table(index="day", columns="hour", values="poa_global")
    fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorbar=dict(title="W/m²")))
    fig.update_layout(title="POA Irradiance Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day of Year")
    return chart(fig)


# ================================================================
#   METEOROLOGICAL CONDITIONS
# ================================================================
def temp_wind_chart(weather):
    weekly_weather = weather.resample("W-MON").mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_weather.index, y=weekly_weather["temp_air"], name="Temp (°C)"))
    fig.add_trace(go.Scatter(x=weekly_weather.index, y=weekly_weather["wind_speed"], name="Wind (m/s)", yaxis="y2"))
    fig.update_layout(
        title="Temperature and Wind Speed",
        yaxis2=dict(overlaying="y", side="right", title="Wind Speed (m/s)")
    )
    return chart(fig)


def temp_vs_irradiance(cell_temp, irradiance):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=irradiance["poa_global"], y=cell_temp["temperature"], mode="markers", name="", opacity=0.5))
    fig.update_layout(title="Module Temperature vs Irradiance",
                      xaxis_title="Irradiance (W/m²)", yaxis_title="Temp (°C)")
    return chart(fig)

def temp_derating(cell_temp, dc):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cell_temp["temperature"], y=dc["p_mp"], mode="markers", opacity=0.5))
    fig.update_layout(title="Temperature Derating Impact", xaxis_title="Cell Temp (°C)", yaxis_title="DC Power (W)")
    return chart(fig)


# ================================================================
#   DC & AC ELECTRICAL PERFORMANCE
# ================================================================
def dc_vs_irradiance(dc, irr):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=irr["poa_global"], y=dc["p_mp"], mode="markers", opacity=0.5))
    fig.update_layout(title="DC Power vs Irradiance", xaxis_title="POA (W/m²)", yaxis_title="DC Power (W)")
    return chart(fig)


def dc_vs_ac(dc, ac):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dc["p_mp"], y=ac["ac"], mode="markers", name="DC/AC", opacity=0.5))
    fig.update_layout(title="DC vs AC Power", xaxis_title="DC Power (W)", yaxis_title="AC Power (W)")
    return chart(fig)


def inverter_efficiency(dc, ac):
    fig = go.Figure()
    efficiency = ac["ac"] / dc["p_mp"]
    fig.add_trace(go.Scatter(x=dc["p_mp"], y=efficiency, mode="markers", name="", opacity=0.4))
    fig.update_layout(title="Inverter Efficiency Curve", xaxis_title="DC Power (W)", yaxis_title="Efficiency")
    return chart(fig)


def power_timeseries(dc, ac):
    weekly_dc = dc.resample('W-MON').mean()
    weekly_ac = ac.resample('W-MON').mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weekly_dc.index, y=weekly_dc["p_mp"], name="DC Power"))
    fig.add_trace(go.Scatter(x=weekly_ac.index, y=weekly_ac["ac"], name="AC Power"))
    fig.update_layout(
        title="Weekly Average Power Time Series",
        xaxis_title="Time",
        yaxis_title="Power (W)"
    )
    return chart(fig)

def monthly_yield(ac):
    fig = go.Figure()
    monthly = ac.groupby(ac.index.month)["ac"].sum() / 1000
    fig.add_trace(go.Bar(x=monthly.index, y=monthly.values, name=""))
    fig.update_layout(title="Monthly Energy Yield", xaxis_title="Month", yaxis_title="Energy (kWh)")
    return chart(fig)

def power_heatmap(ac):
    df = ac.copy()
    df["day"] = df.index.dayofyear
    df["hour"] = df.index.hour
    fig = go.Figure()
    pivot = df.pivot_table(index="day", columns="hour", values="ac")
    fig.add_trace(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, name="", colorbar=dict(title="AC")))
    fig.update_layout(title="Power Output Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day of Year")
    return chart(fig)


# ================================================================
#   ANOMALY DETECTION
# ================================================================

def peak_power_vs_irradiance(ac, irradiance):
    fig = go.Figure()
    daily_peak = ac.groupby(ac.index.date)["ac"].max()
    mean_irr = irradiance.groupby(irradiance.index.date)["poa_global"].mean()
    fig.add_trace(go.Scatter(x=mean_irr, y=daily_peak, mode="markers", name=""))
    fig.update_layout(title="Daily Peak Power vs Irradiance", xaxis_title="Avg Irradiance (W/m²)", yaxis_title="Peak AC Power (W)")
    return chart(fig)


# ================================================================
#   TEMPORAL & ENERGY SUMMARY
# ================================================================
def daily_yield(ac):
    daily = ac.groupby(ac.index.date)["ac"].sum() / 1000
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=daily.index, y=daily.values, mode="lines", name=""))
    fig.update_layout(title="Daily Energy Yield", xaxis_title="Date", yaxis_title="Energy (kWh)")
    return chart(fig)


def capacity_factor(ac):
    monthly = ac.groupby(ac.index.month)["ac"].sum() / 1000
    cap_factor = monthly / monthly.max()
    fig = go.Figure()
    fig.add_trace(go.Bar(x=cap_factor.index, y=cap_factor.values, name=""))
    fig.update_layout(title="Monthly Capacity Factor", xaxis_title="Month", yaxis_title="Capacity Factor")
    return chart(fig)


def cumulative_energy(ac):
    cumulative = ac["ac"].cumsum() / 1000
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ac.index, y=cumulative, mode="lines", name=""))
    fig.update_layout(title="Cumulative Energy (kWh)", xaxis_title="Time", yaxis_title="kWh")
    return chart(fig)


def performance_ratio(ac, irradiance):
    ac = ac.resample("W-MON").mean()
    irradiance = irradiance.resample("W-MON").mean()
    pr = ac["ac"] / irradiance["poa_global"]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ac.index, y=pr, mode="lines", name=""))
    fig.update_layout(title="Performance Ratio (PR) over Time", xaxis_title="Time", yaxis_title="PR")
    return chart(fig)





