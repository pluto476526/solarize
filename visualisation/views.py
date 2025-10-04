from django.shortcuts import render
from django.conf import settings
from data_factory.database.manager import DataManager
from data_factory.database.connection import DatabaseConnection
import plotly.graph_objects as go
from plotly.offline import plot
import logging
import json
import os

logger = logging.getLogger(__name__)

# Create your views here.
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



