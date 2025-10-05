## data_factory/tasks.py
## pkibuka@miky-way.space


from django.utils.timezone import now
from datetime import datetime, timedelta
from celery import shared_task
import pandas as pd
import logging
import requests
from data_factory.database.connection import DatabaseConnection
from data_factory.database.manager import DataManager

logger = logging.getLogger(__name__)


def process_data(data):
    coords = data["geometry"]["coordinates"]
    lon, lat, elev = coords
    all_dfs = []

    for param, values in data["properties"]["parameter"].items():
        df = pd.DataFrame.from_dict(values, orient="index", columns=["value"])
        df.index = pd.to_datetime(df.index, format="%Y%m%d")
        df.reset_index(inplace=True)
        df.rename(columns={"index": "date"}, inplace=True)

        df["value"] = df["value"].replace(-999.0, pd.NA)

        if df["value"].isna().all():
            logger.warning(f"Skipping {param}: all values missing.")
            continue

        df["parameter"] = param
        df["units"] = data["parameters"][param]["units"]
        df["lon"] = lon
        df["lat"] = lat
        df["elev"] = elev
        df["source"] = "NASA_POWER"
        
        df = df[["date", "parameter", "value", "units", "lon", "lat", "elev", "source"]]
        all_dfs.append(df)

    if all_dfs:
        return pd.concat(all_dfs, ignore_index=True)
    return pd.DataFrame(columns=["date", "parameter", "value", "units", "lon", "lat", "elev", "source"])


@shared_task(bind=True)
def fetch_nasa_data(self):
    NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"
    
    # Get last 30 days of data (NASA typically has 2-3 day latency)
    # end_date = now() - timedelta(days=365)
    # start_date = end_date - timedelta(days=400)
    end_date = "2025-05-31"
    start_date = "2015-05-1"
    
    end_date = datetime.strptime(end_date, "%Y-%m-%d")
    start_date = datetime.strptime(start_date, "%Y-%m-%d")

    RE_params = (
        "ALLSKY_SFC_SW_DWN,ALLSKY_KT"
    )
    params = {
        "parameters": RE_params,
        "community": "RE",
        "longitude": 36.8219,
        "latitude": -1.2921,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON"
    }
    response = requests.get(NASA_POWER_API, params=params)
    
    if response.status_code != 200:
        logger.error(f"Failed to fetch NASA data: {response}")
        return None

    data = response.json()
    df = process_data(data)

    try:
        conn = DatabaseConnection()
        db = DataManager(conn)
        df_filtered = df[df["parameter"] == "ALLSKY_SFC_SW_DWN"]
        
        if not df_filtered.empty:
            db.insert_irradiance_data(df_filtered)
    
    except Exception as e:
        logger.error(f"Failed to save to db: {e}")




