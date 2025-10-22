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
    fig = go.Figure(go.Scatter(x=solar["utc_time"], y=solar["elevation"], mode="lines"))
    fig.update_layout(title="Solar Elevation vs Time", xaxis_title="Time", yaxis_title="Elevation (°)")
    return chart(fig)


def sunpath_chart(solar):
    sample = solar.groupby(solar["utc_time"].dt.date).head(100)
    fig = go.Figure(go.Scatterpolar(
        r=sample["elevation"], theta=sample["azimuth"], mode="markers", marker=dict(size=3)
    ))
    fig.update_layout(title="Sunpath Diagram", polar=dict(radialaxis=dict(title="Elevation (°)")))
    return chart(fig)


def poa_vs_ghi_chart(weather):
    fig = go.Figure(go.Scatter(x=weather["poa_global"], y=weather["ghi"], mode="markers", opacity=0.5))
    fig.update_layout(title="POA vs GHI", xaxis_title="POA (W/m²)", yaxis_title="GHI (W/m²)")
    return chart(fig)


def irradiance_breakdown_chart(weather):
    fig = go.Figure()
    for comp in ["poa_global", "dni", "dhi"]:
        if comp in weather.columns:
            fig.add_trace(go.Scatter(x=weather["utc_time"], y=weather[comp], stackgroup="one", name=comp.upper()))
    fig.update_layout(title="Irradiance Breakdown (POA / DNI / DHI)", xaxis_title="Time", yaxis_title="W/m²")
    return chart(fig)


def poa_heatmap(weather):
    df = weather.copy()
    df["day"] = df["utc_time"].dt.dayofyear
    df["hour"] = df["utc_time"].dt.hour
    pivot = df.pivot_table(index="day", columns="hour", values="poa_global")
    fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, colorbar=dict(title="W/m²")))
    fig.update_layout(title="POA Irradiance Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day of Year")
    return chart(fig)


# ================================================================
# 🌤 2. METEOROLOGICAL CONDITIONS
# ================================================================
def temp_wind_chart(weather):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weather["utc_time"], y=weather["temp_air"], name="Temp (°C)"))
    fig.add_trace(go.Scatter(x=weather["utc_time"], y=weather["wind_speed"], name="Wind Speed (m/s)", yaxis="y2"))
    fig.update_layout(
        title="Temperature and Wind Speed",
        yaxis2=dict(overlaying="y", side="right", title="Wind Speed (m/s)")
    )
    return chart(fig)


def temp_vs_irradiance(cell_temp, weather, array_names):
    fig = go.Figure()
    for i, df in enumerate(cell_temp):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        fig.add_trace(go.Scatter(
            x=weather["poa_global"], y=df["temp_cell"],
            mode="markers", name=label, opacity=0.5
        ))
    fig.update_layout(title="Module Temperature vs Irradiance",
                      xaxis_title="Irradiance (W/m²)", yaxis_title="Temp (°C)")
    return chart(fig)


def airmass_vs_spectral(airmass, spectral_modifier):
    fig = go.Figure(go.Scatter(x=airmass["airmass_absolute"], y=spectral_modifier, mode="markers"))
    fig.update_layout(title="Air Mass vs Spectral Modifier", xaxis_title="Air Mass", yaxis_title="Spectral Modifier")
    return chart(fig)


# ================================================================
# ⚡ 3. DC & AC ELECTRICAL PERFORMANCE
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


# ================================================================
# 🌡️ 4. LOSS ANALYSIS
# ================================================================
def loss_waterfall():
    stages = ["POA", "Effective", "DC", "AC"]
    fig = go.Figure(go.Waterfall(x=stages, y=[0, -50, -30, -20]))
    fig.update_layout(title="Loss Breakdown (Irradiance → AC)", yaxis_title="Loss (W/m²)")
    return chart(fig)


def effective_irradiance_hist(weather):
    fig = go.Figure(go.Histogram(x=weather["poa_global"], nbinsx=50))
    fig.update_layout(title="Effective Irradiance Distribution", xaxis_title="POA (W/m²)")
    return chart(fig)


def temp_derating(cell_temp, dc, array_names):
    fig = go.Figure()
    for i, (temp_df, dc_df) in enumerate(zip(cell_temp, dc)):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        fig.add_trace(go.Scatter(x=temp_df["temp_cell"], y=dc_df["p_mp"], mode="markers", name=label, opacity=0.5))
    fig.update_layout(title="Temperature Derating Impact", xaxis_title="Cell Temp (°C)", yaxis_title="DC Power (W)")
    return chart(fig)


# ================================================================
# 🧭 5. COMPARATIVE / MULTI-ARRAY
# ================================================================
def ac_boxplot(ac_aoi, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        fig.add_trace(go.Box(y=df["ac"], name=label))
    fig.update_layout(title="AC Power Comparison Across Arrays", yaxis_title="AC Power (W)")
    return chart(fig)


def power_heatmap(ac_aoi, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        data = df.copy()
        data["day"] = data["utc_time"].dt.dayofyear
        data["hour"] = data["utc_time"].dt.hour
        pivot = data.pivot_table(index="day", columns="hour", values="ac")
        fig.add_trace(go.Heatmap(z=pivot.values, x=pivot.columns, y=pivot.index, name=label, showscale=False))
    fig.update_layout(title="Power Output Heatmap (Day vs Hour)", xaxis_title="Hour", yaxis_title="Day of Year")
    return chart(fig)


def poa_vs_dc(weather, dc, array_names):
    fig = go.Figure()
    for i, df in enumerate(dc):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        fig.add_trace(go.Scatter(x=weather["poa_global"], y=df["p_mp"], mode="markers", name=label, opacity=0.5))
    fig.update_layout(title="POA vs DC Power", xaxis_title="POA (W/m²)", yaxis_title="DC Power (W)")
    return chart(fig)


# ================================================================
# 🕒 6. TEMPORAL & ENERGY SUMMARY
# ================================================================
def daily_yield(ac_aoi, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        daily = df.groupby(df["utc_time"].dt.date)["ac"].sum() / 1000
        fig.add_trace(go.Scatter(x=daily.index, y=daily.values, mode="lines", name=label))
    fig.update_layout(title="Daily Energy Yield", xaxis_title="Date", yaxis_title="Energy (kWh)")
    return chart(fig)


def capacity_factor(ac_aoi, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        monthly = df.groupby(df["utc_time"].dt.month)["ac"].sum() / 1000
        cap_factor = monthly / monthly.max()
        fig.add_trace(go.Bar(x=cap_factor.index, y=cap_factor.values, name=label))
    fig.update_layout(title="Monthly Capacity Factor", xaxis_title="Month", yaxis_title="Capacity Factor")
    return chart(fig)


def cumulative_energy(ac_aoi, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        df = df.sort_values("utc_time")
        cumulative = df["ac"].cumsum() / 1000
        fig.add_trace(go.Scatter(x=df["utc_time"], y=cumulative, mode="lines", name=label))
    fig.update_layout(title="Cumulative Energy (kWh)", xaxis_title="Time", yaxis_title="kWh")
    return chart(fig)


def performance_ratio(ac_aoi, weather, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        pr = df["ac"] / weather["poa_global"]
        fig.add_trace(go.Scatter(x=df["utc_time"], y=pr, mode="lines", name=label))
    fig.update_layout(title="Performance Ratio (PR) over Time", xaxis_title="Time", yaxis_title="PR")
    return chart(fig)


# ================================================================
# 🧩 7. DIAGNOSTIC & ANOMALY DETECTION
# ================================================================
def ac_residuals(measured, modeled):
    residuals = measured - modeled
    fig = go.Figure(go.Scatter(x=measured.index, y=residuals, mode="lines"))
    fig.update_layout(title="AC Residuals (Measured - Modeled)", xaxis_title="Time", yaxis_title="Residual (W)")
    return chart(fig)


def temp_efficiency(temp, efficiency):
    fig = go.Figure(go.Scatter(x=temp, y=efficiency, mode="markers", opacity=0.5))
    fig.update_layout(title="Temperature-Corrected Efficiency", xaxis_title="Temp (°C)", yaxis_title="Efficiency")
    return chart(fig)


def peak_power_vs_irradiance(ac_aoi, weather, array_names):
    fig = go.Figure()
    for i, df in enumerate(ac_aoi):
        label = array_names.get(str(i + 1), f"Array {i + 1}")
        daily_peak = df.groupby(df["utc_time"].dt.date)["ac"].max()
        mean_irr = weather.groupby(weather["utc_time"].dt.date)["poa_global"].mean()
        fig.add_trace(go.Scatter(x=mean_irr, y=daily_peak, mode="markers", name=label))
    fig.update_layout(title="Daily Peak Power vs Irradiance", xaxis_title="Avg Irradiance (W/m²)", yaxis_title="Peak AC Power (W)")
    return chart(fig)



