import plotly.graph_objects as go
from plotly.offline import plot
import pandas as pd


def _plot_timeseries(series, title, y_axis_title=None):
    """
    Helper function to create a Plotly chart from a time series.
    """
    # Handle all-NaN case
    if series.isna().all():
        fig = go.Figure()
        fig.update_layout(
            title=f"No data available for '{title}'",
            template="plotly_dark"
        )
        return plot(fig, output_type="div", include_plotlyjs=False)

    # Plot the data
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=series.index,
        y=series.values,
        mode="lines",
        connectgaps=True,
        name=f"Avg Daily {title}"
    ))

    y_axis_title = y_axis_title or title
    
    fig.update_layout(
        template="plotly_dark",
        title=title,
        xaxis_title="Day",
        yaxis_title=y_axis_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return plot(fig, output_type="div", include_plotlyjs=False)


def _prepare_and_resample_data(df, param):
    """
    Helper function to prepare data and resample to daily averages.
    """
    df = pd.DataFrame(df)
    
    # Resample to get daily averages if we have a datetime index
    if isinstance(df.index, pd.DatetimeIndex):
        return df[param].resample('D').mean()
    else:
        # Fallback if no datetime index
        return df[param]


def ac_aoi_chart(ac_aoi, array, param):
    """Plot the average daily AC power for a given array."""
    array_idx = ac_aoi.columns[array] if isinstance(array, int) else array
    data = ac_aoi[array_idx]
    daily_avg = _prepare_and_resample_data(data, param)
    title = f"{array}, Daily {param.upper()}"
    y_axis_title = f"{param.upper()} (W)"
    return _plot_timeseries(daily_avg, title, y_axis_title)


def cell_temp_chart(cell_temp, array, param):
    """Plot cell temperature data."""
    array_idx = cell_temp.columns[array] if isinstance(array, int) else array
    data = cell_temp[array_idx]
    daily_avg = _prepare_and_resample_data(data, param)
    title = f"{array}, Cell Temperature"
    return _plot_timeseries(daily_avg, title, "Temperature (°C)")


def dc_output_chart(dc_output, array, param):
    """Plot DC output parameters."""
    array_idx = dc_output.columns[array] if isinstance(array, int) else array
    data = dc_output[array_idx]
    daily_avg = _prepare_and_resample_data(data, param)
    title = f"{array}, {param.upper()}"
    return _plot_timeseries(daily_avg, title, f"{param} (W)")


def diode_params_chart(diode_params, array, param):
    """Plot diode parameters."""
    array_idx = diode_params.columns[array] if isinstance(array, int) else array
    data = diode_params[array_idx]
    daily_avg = _prepare_and_resample_data(data, param)
    return _plot_timeseries(daily_avg, f"{array}, {param.upper()}")


def total_irradiance_chart(total_irradiance, array, param):
    """Plot total irradiance parameters."""
    array_idx = total_irradiance.columns[array] if isinstance(array, int) else array
    data = total_irradiance[array_idx]
    daily_avg = _prepare_and_resample_data(data, param)
    title = f"{array}, {param.upper()}"
    return _plot_timeseries(daily_avg, title, "Irradiance (W/m²)")


def solar_position_chart(solar_position, param):
    """Plot solar position parameters."""
    daily_avg = _prepare_and_resample_data(solar_position, param)
    y_axis_title = "Angle (°)" if "angle" in param.lower() else param
    return _plot_timeseries(daily_avg, param.upper(), y_axis_title)


def weather_chart(weather, param):
    """Plot weather parameters."""
    daily_avg = _prepare_and_resample_data(weather, param)
    if "temp_air" in param.lower():
        y_axis_title = "Temperature (°C)"
    elif "wind_speed" in param.lower():
        y_axis_title = "Speed (Km/h)"
    else:
        y_axis_title = f"{param} (W/m²)"
        
    return _plot_timeseries(daily_avg, param.upper(), y_axis_title)