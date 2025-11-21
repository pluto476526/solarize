import plotly.graph_objects as go
import pandas as pd
import numpy as np


def create_solar_daily_plot(raw_data, insights):
    """Create daily solar radiation plot"""
    solar_data = raw_data[raw_data["parameter"] == "ALLSKY_SFC_SW_DWN"].copy()
    solar_data["date"] = pd.to_datetime(solar_data["date"])
    solar_data = solar_data.sort_values("date")
    solar_data["moving_avg_30"] = (
        solar_data["value"].rolling(window=30, center=True).mean()
    )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=solar_data["date"],
            y=solar_data["value"],
            mode="lines",
            name="Daily Solar Radiation",
            line=dict(color="orange", width=1),
            opacity=0.7,
        )
    )

    fig.add_trace(
        go.Scatter(
            x=solar_data["date"],
            y=solar_data["moving_avg_30"],
            mode="lines",
            name="30-day Moving Average",
            line=dict(color="red", width=2),
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Solar Radiation (kW-hr/m²/day)",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="solar_daily_plot")


def create_solar_monthly_plot(insights):
    """Create monthly solar radiation climatology plot"""
    monthly_clima = insights["ALLSKY_SFC_SW_DWN"]["seasonal_climatology_monthly"]
    months = list(monthly_clima.keys())
    values = list(monthly_clima.values())

    fig = go.Figure()
    fig.add_trace(
        go.Bar(x=months, y=values, marker_color="gold", name="Monthly Average")
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Solar Radiation (kW-hr/m²/day)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="solar_monthly_plot")


def create_solar_annual_plot(raw_data, insights):
    """Create annual solar radiation trends plot"""
    solar_data = raw_data[raw_data["parameter"] == "ALLSKY_SFC_SW_DWN"].copy()
    solar_data["date"] = pd.to_datetime(solar_data["date"])
    solar_data["year"] = solar_data["date"].dt.year
    annual_avg = solar_data.groupby("year")["value"].mean().reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=annual_avg["year"],
            y=annual_avg["value"],
            mode="lines+markers",
            name="Annual Average",
            line=dict(color="darkorange", width=3),
        )
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Average Solar Radiation (kW-hr/m²/day)",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="solar_annual_plot")


def create_temperature_daily_plot(raw_data, insights):
    """Create daily temperature time series plot"""
    temp_data = raw_data[
        raw_data["parameter"].isin(["T2M", "T2M_MAX", "T2M_MIN"])
    ].copy()
    temp_data["date"] = pd.to_datetime(temp_data["date"])
    temp_pivot = temp_data.pivot_table(
        index="date", columns="parameter", values="value"
    ).reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=temp_pivot["date"],
            y=temp_pivot["T2M"],
            mode="lines",
            name="Avg Temp",
            line=dict(color="blue", width=1),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=temp_pivot["date"],
            y=temp_pivot["T2M_MAX"],
            mode="lines",
            name="Max Temp",
            line=dict(color="red", width=1),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=temp_pivot["date"],
            y=temp_pivot["T2M_MIN"],
            mode="lines",
            name="Min Temp",
            line=dict(color="lightblue", width=1),
        )
    )

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Temperature (°C)", template="plotly_dark"
    )
    return fig.to_html(include_plotlyjs=False, div_id="temperature_daily_plot")


def create_temperature_climatology_plot(insights):
    """Create monthly temperature climatology plot"""
    t2m_clima = insights["T2M"]["seasonal_climatology_monthly"]
    t2m_max_clima = insights["T2M_MAX"]["seasonal_climatology_monthly"]
    t2m_min_clima = insights["T2M_MIN"]["seasonal_climatology_monthly"]

    months = list(t2m_clima.keys())

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=months,
            y=list(t2m_clima.values()),
            mode="lines+markers",
            name="Avg Temp",
            line=dict(color="blue", width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=months,
            y=list(t2m_max_clima.values()),
            mode="lines+markers",
            name="Max Temp",
            line=dict(color="red", width=3),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=months,
            y=list(t2m_min_clima.values()),
            mode="lines+markers",
            name="Min Temp",
            line=dict(color="lightblue", width=3),
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Temperature (°C)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="temperature_climatology_plot")


def create_temperature_distribution_plot(raw_data, insights):
    """Create temperature distribution box plot"""
    temp_data = raw_data[
        raw_data["parameter"].isin(["T2M", "T2M_MAX", "T2M_MIN"])
    ].copy()

    fig = go.Figure()
    for temp_type, color in [
        ("T2M", "blue"),
        ("T2M_MAX", "red"),
        ("T2M_MIN", "lightblue"),
    ]:
        temp_values = temp_data[temp_data["parameter"] == temp_type]["value"]
        fig.add_trace(
            go.Box(y=temp_values, name=temp_type, marker_color=color, boxpoints=False)
        )

    fig.update_layout(yaxis_title="Temperature (°C)", template="plotly_dark")
    return fig.to_html(include_plotlyjs=False, div_id="temperature_distribution_plot")


def create_precipitation_daily_plot(raw_data, insights):
    """Create daily precipitation plot"""
    hydro_data = raw_data[raw_data["parameter"] == "PRECTOTCORR"].copy()
    hydro_data["date"] = pd.to_datetime(hydro_data["date"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hydro_data["date"],
            y=hydro_data["value"],
            mode="lines",
            name="Precipitation",
            line=dict(color="blue", width=1),
            fill="tozeroy",
            fillcolor="rgba(0,0,255,0.1)",
        )
    )

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Precipitation (mm/day)", template="plotly_dark"
    )
    return fig.to_html(include_plotlyjs=False, div_id="precipitation_daily_plot")


def create_humidity_daily_plot(raw_data, insights):
    """Create daily humidity plot"""
    hydro_data = raw_data[raw_data["parameter"] == "RH2M"].copy()
    hydro_data["date"] = pd.to_datetime(hydro_data["date"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=hydro_data["date"],
            y=hydro_data["value"],
            mode="lines",
            name="Humidity",
            line=dict(color="green", width=1),
        )
    )

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Relative Humidity (%)", template="plotly_dark"
    )
    return fig.to_html(include_plotlyjs=False, div_id="humidity_daily_plot")


def create_precipitation_climatology_plot(insights):
    """Create monthly precipitation climatology plot"""
    precip_clima = insights["PRECTOTCORR"]["seasonal_climatology_monthly"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(precip_clima.keys()),
            y=list(precip_clima.values()),
            name="Precipitation",
            marker_color="blue",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Precipitation (mm/day)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="precipitation_climatology_plot")


def create_humidity_climatology_plot(insights):
    """Create monthly humidity climatology plot"""
    rh_clima = insights["RH2M"]["seasonal_climatology_monthly"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(rh_clima.keys()),
            y=list(rh_clima.values()),
            name="Humidity",
            marker_color="green",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Relative Humidity (%)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="humidity_climatology_plot")


def create_wind_daily_plot(raw_data, insights):
    """Create daily wind speed plot"""
    wind_data = raw_data[raw_data["parameter"] == "WS10M"].copy()
    wind_data["date"] = pd.to_datetime(wind_data["date"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=wind_data["date"],
            y=wind_data["value"],
            mode="lines",
            name="Wind Speed",
            line=dict(color="purple", width=1),
        )
    )

    fig.update_layout(
        xaxis_title="Date", yaxis_title="Wind Speed (m/s)", template="plotly_dark"
    )
    return fig.to_html(include_plotlyjs=False, div_id="wind_daily_plot")


def create_wind_climatology_plot(insights):
    """Create monthly wind speed climatology plot"""
    wind_clima = insights["WS10M"]["seasonal_climatology_monthly"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(wind_clima.keys()),
            y=list(wind_clima.values()),
            name="Wind Speed",
            marker_color="purple",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Wind Speed (m/s)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="wind_climatology_plot")


def create_wind_annual_plot(raw_data, insights):
    """Create annual wind speed trends plot"""
    wind_data = raw_data[raw_data["parameter"] == "WS10M"].copy()
    wind_data["date"] = pd.to_datetime(wind_data["date"])
    wind_data["year"] = wind_data["date"].dt.year
    annual_wind = wind_data.groupby("year")["value"].mean().reset_index()

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=annual_wind["year"],
            y=annual_wind["value"],
            mode="lines+markers",
            name="Annual Avg",
            line=dict(color="purple", width=3),
        )
    )

    fig.update_layout(
        xaxis_title="Year",
        yaxis_title="Wind Speed (m/s)",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="wind_annual_plot")


def create_wind_distribution_plot(raw_data, insights):
    """Create wind speed distribution plot"""
    wind_data = raw_data[raw_data["parameter"] == "WS10M"].copy()

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=wind_data["value"], name="Distribution", marker_color="purple", nbinsx=30
        )
    )

    fig.update_layout(
        xaxis_title="Wind Speed (m/s)",
        yaxis_title="Frequency",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="wind_distribution_plot")


def create_et0_cwr_daily_plot(et0_df, cwr_df, insights):
    """Create daily ET0 and CWR plot"""
    et0_df["date"] = pd.to_datetime(et0_df["date"])
    cwr_df["date"] = pd.to_datetime(cwr_df["date"])

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=et0_df["date"],
            y=et0_df["ET0_mm_day"],
            mode="lines",
            name="ET₀",
            line=dict(color="green", width=1),
        )
    )

    fig.add_trace(
        go.Scatter(
            x=cwr_df["date"],
            y=cwr_df["CWR_mm_day"],
            mode="lines",
            name="CWR",
            line=dict(color="brown", width=1),
        )
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Water (mm/day)",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="et0_cwr_daily_plot")


def create_water_balance_monthly_plot(balance_df, insights):
    """Create monthly water balance plot"""
    balance_df["month"] = pd.to_datetime(balance_df["month"])

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=balance_df["month"],
            y=balance_df["CWR_mm_day"],
            name="Crop Water Requirement",
            marker_color="brown",
        )
    )

    fig.add_trace(
        go.Bar(
            x=balance_df["month"],
            y=balance_df["precip_mm_day"],
            name="Precipitation",
            marker_color="blue",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=balance_df["month"],
            y=balance_df["irrigation_need_mm_day"],
            mode="lines+markers",
            name="Irrigation Need",
            line=dict(color="red", width=3),
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Water (mm/day)",
        template="plotly_dark",
        barmode="group",
    )
    return fig.to_html(include_plotlyjs=False, div_id="water_balance_monthly_plot")


def create_et0_climatology_plot(insights):
    """Create ET0 monthly climatology plot"""
    et0_clima = insights["ET0"]["seasonal_climatology"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(et0_clima.keys()),
            y=list(et0_clima.values()),
            name="ET₀",
            marker_color="lightgreen",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="ET₀ (mm/day)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="et0_climatology_plot")


def create_cwr_climatology_plot(insights):
    """Create CWR monthly climatology plot"""
    cwr_clima = insights["CWR"]["seasonal_climatology"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(cwr_clima.keys()),
            y=list(cwr_clima.values()),
            name="CWR",
            marker_color="sandybrown",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="CWR (mm/day)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="cwr_climatology_plot")


def create_irrigation_need_monthly_plot(balance_df, insights):
    """Create monthly irrigation need plot"""
    balance_df["month"] = pd.to_datetime(balance_df["month"])

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=balance_df["month"],
            y=balance_df["irrigation_need_mm_day"],
            name="Irrigation Need",
            marker_color="red",
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Irrigation Need (mm/day)",
        template="plotly_dark",
    )
    return fig.to_html(include_plotlyjs=False, div_id="irrigation_need_monthly_plot")


def create_irrigation_deficit_annual_plot(balance_df, insights):
    """Create annual irrigation deficit plot"""
    balance_df["month"] = pd.to_datetime(balance_df["month"])
    balance_df["year"] = balance_df["month"].dt.year
    annual_deficit = (
        balance_df.groupby("year")["irrigation_need_mm_day"].sum().reset_index()
    )
    annual_deficit["deficit_mm"] = -annual_deficit["irrigation_need_mm_day"]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=annual_deficit["year"],
            y=annual_deficit["deficit_mm"],
            name="Annual Deficit",
            marker_color="darkred",
        )
    )

    fig.update_layout(
        xaxis_title="Year", yaxis_title="Annual Deficit (mm)", template="plotly_dark"
    )
    return fig.to_html(include_plotlyjs=False, div_id="irrigation_deficit_annual_plot")


def create_irrigation_seasonal_pattern_plot(balance_df, insights):
    """Create seasonal deficit pattern plot"""
    balance_df["month"] = pd.to_datetime(balance_df["month"])
    balance_df["month_num"] = balance_df["month"].dt.month
    monthly_avg_deficit = (
        balance_df.groupby("month_num")["irrigation_need_mm_day"].mean().reset_index()
    )
    monthly_avg_deficit["deficit_mm"] = -monthly_avg_deficit["irrigation_need_mm_day"]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=monthly_avg_deficit["month_num"],
            y=monthly_avg_deficit["deficit_mm"],
            mode="lines+markers",
            name="Seasonal Pattern",
            line=dict(color="red", width=3),
        )
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Average Deficit (mm/day)",
        xaxis=dict(
            tickmode="array",
            tickvals=list(range(1, 13)),
            ticktext=[
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ],
        ),
        template="plotly_dark",
    )
    return fig.to_html(
        include_plotlyjs=False, div_id="irrigation_seasonal_pattern_plot"
    )


def create_irrigation_deficit_distribution_plot(balance_df, insights):
    """Create irrigation deficit distribution plot"""
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=-balance_df["irrigation_need_mm_day"],
            name="Deficit Distribution",
            marker_color="red",
            nbinsx=20,
        )
    )

    fig.update_layout(
        xaxis_title="Irrigation Need (mm/day)",
        yaxis_title="Frequency",
        template="plotly_dark",
    )
    return fig.to_html(
        include_plotlyjs=False, div_id="irrigation_deficit_distribution_plot"
    )


# Main function to generate all plots
def generate_all_plots(data_dict):
    """Generate all plots for the agricultural solar monitoring dashboard"""

    plots = {}

    # Solar plots
    plots["solar_daily"] = create_solar_daily_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["solar_monthly"] = create_solar_monthly_plot(data_dict["insights"])
    plots["solar_annual"] = create_solar_annual_plot(
        data_dict["raw_data"], data_dict["insights"]
    )

    # Temperature plots
    plots["temperature_daily"] = create_temperature_daily_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["temperature_climatology"] = create_temperature_climatology_plot(
        data_dict["insights"]
    )
    plots["temperature_distribution"] = create_temperature_distribution_plot(
        data_dict["raw_data"], data_dict["insights"]
    )

    # Hydrological plots
    plots["precipitation_daily"] = create_precipitation_daily_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["humidity_daily"] = create_humidity_daily_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["precipitation_climatology"] = create_precipitation_climatology_plot(
        data_dict["insights"]
    )
    plots["humidity_climatology"] = create_humidity_climatology_plot(
        data_dict["insights"]
    )

    # Wind plots
    plots["wind_daily"] = create_wind_daily_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["wind_climatology"] = create_wind_climatology_plot(data_dict["insights"])
    plots["wind_annual"] = create_wind_annual_plot(
        data_dict["raw_data"], data_dict["insights"]
    )
    plots["wind_distribution"] = create_wind_distribution_plot(
        data_dict["raw_data"], data_dict["insights"]
    )

    # Agricultural water plots
    plots["et0_cwr_daily"] = create_et0_cwr_daily_plot(
        data_dict["et0_df"], data_dict["cwr_df"], data_dict["insights"]
    )
    plots["water_balance_monthly"] = create_water_balance_monthly_plot(
        data_dict["balance_df"], data_dict["insights"]
    )
    plots["et0_climatology"] = create_et0_climatology_plot(data_dict["insights"])
    plots["cwr_climatology"] = create_cwr_climatology_plot(data_dict["insights"])

    # Irrigation balance plots
    plots["irrigation_need_monthly"] = create_irrigation_need_monthly_plot(
        data_dict["balance_df"], data_dict["insights"]
    )
    plots["irrigation_deficit_annual"] = create_irrigation_deficit_annual_plot(
        data_dict["balance_df"], data_dict["insights"]
    )
    plots["irrigation_seasonal_pattern"] = create_irrigation_seasonal_pattern_plot(
        data_dict["balance_df"], data_dict["insights"]
    )
    plots["irrigation_deficit_distribution"] = (
        create_irrigation_deficit_distribution_plot(
            data_dict["balance_df"], data_dict["insights"]
        )
    )

    return plots
