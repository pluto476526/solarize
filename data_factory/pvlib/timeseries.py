import plotly.graph_objects as go
from plotly.offline import plot
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def _prepare_data(data, param=None):
    """
    Simple data preparation that handles Series, DataFrame, or tuple.
    Returns a dictionary with array names as keys and Series as values.
    """
    result = {}

    # Handle tuple of DataFrames (multiple arrays)
    if isinstance(data, tuple):
        for i, item in enumerate(data):
            array_name = f"Array_{i+1}"
            if isinstance(item, pd.DataFrame) and param and param in item.columns:
                series = item[param]
                if isinstance(series.index, pd.DatetimeIndex):
                    series = series.resample("D").mean()
                result[array_name] = series
            elif isinstance(item, pd.Series):
                series = item
                if isinstance(series.index, pd.DatetimeIndex):
                    series = series.resample("D").mean()
                result[array_name] = series

    # Handle single DataFrame
    elif isinstance(data, pd.DataFrame):
        if param and param in data.columns:
            series = data[param]
            if isinstance(series.index, pd.DatetimeIndex):
                series = series.resample("D").mean()
            result["Array"] = series

    # Handle single Series
    elif isinstance(data, pd.Series):
        series = data
        if isinstance(series.index, pd.DatetimeIndex):
            series = series.resample("D").mean()
        result["Array"] = series

    return result


def _create_chart(series_dict, title, y_axis_title):
    """Create a Plotly chart from series dictionary."""
    fig = go.Figure()

    has_data = False
    for name, series in series_dict.items():
        if series.empty or series.isna().all():
            continue

        valid_data = series.dropna()
        if not valid_data.empty:
            has_data = True
            fig.add_trace(
                go.Scatter(
                    x=valid_data.index,
                    y=valid_data.values,
                    mode="lines",
                    name=name,
                    hovertemplate=f"<b>{name}</b><br>Date: %{{x}}<br>{y_axis_title}: %{{y:.2f}}<extra></extra>",
                )
            )

    if not has_data:
        fig.update_layout(title=f"No data available", template="plotly_dark")
    else:
        fig.update_layout(
            template="plotly_dark",
            title=title,
            xaxis_title="Date",
            yaxis_title=y_axis_title,
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
            hovermode="x unified",
        )

    return plot(fig, output_type="div", include_plotlyjs=False)


# Unified chart function that works for all data types and parameters
def create_timeseries_chart(data, param=None, title=None, y_axis_title=None):
    """
    Create a timeseries chart that handles Series, DataFrame, or tuple data.

    Parameters:
        data: Series, DataFrame, or tuple of DataFrames
        param: Column name to plot (required for DataFrames)
        title: Chart title
        y_axis_title: Y-axis title
    """
    # Prepare data
    series_dict = _prepare_data(data, param)

    if not series_dict:
        return _create_chart({}, "No Data", "")

    # Set default titles
    if not title:
        if param:
            title = f"Daily {param.upper()}"
        else:
            title = "Time Series"

    if not y_axis_title:
        if param:
            # Simple mapping of common parameters to units
            units_map = {
                "ac": "Power (W)",
                "aoi": "Angle (°)",
                "temperature": "Temperature (°C)",
                "i_sc": "Current (A)",
                "v_oc": "Voltage (V)",
                "i_mp": "Current (A)",
                "v_mp": "Voltage (V)",
                "aoi_modifier": "Modifier",
            }
            y_axis_title = units_map.get(param, f"{param.upper()} (Units)")
        else:
            y_axis_title = "Value"

    return _create_chart(series_dict, title, y_axis_title)


# Specific chart functions for convenience
def ac_chart(data, param):
    return create_timeseries_chart(
        data, param, f"Daily {param.upper()}", f"{param.upper()} (W)"
    )


def aoi_chart(data, param):
    return create_timeseries_chart(
        data, param, f"Daily {param.upper()}", f"{param.upper()}"
    )


def cell_temp_chart(data):
    return create_timeseries_chart(
        data, "temperature", "Cell Temperature", "Temperature (°C)"
    )


def dc_output_chart(data, param):
    return create_timeseries_chart(
        data, param, f"Daily {param.upper()}", f"{param.upper()} (W)"
    )


def diode_params_chart(data, param):
    return create_timeseries_chart(data, param, f"Daily {param.upper()}")


def total_irradiance_chart(data, param):
    return create_timeseries_chart(
        data, param, f"Daily {param.upper()}", "Irradiance (W/m²)"
    )


def solar_position_chart(data, param):
    y_title = "Angle (°)" if "angle" in str(param).lower() else str(param)
    return create_timeseries_chart(data, param, f"Solar {param.upper()}", y_title)


def weather_chart(data, param):
    if "temp_air" in str(param).lower():
        y_title = "Temperature (°C)"
    elif "wind_speed" in str(param).lower():
        y_title = "Speed (Km/h)"
    else:
        y_title = f"{param} (W/m²)"
    return create_timeseries_chart(data, param, f"Weather {param.upper()}", y_title)
