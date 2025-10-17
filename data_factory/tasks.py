## data_factory/tasks.py
## pkibuka@miky-way.space


from django.utils.timezone import now
from django.conf import settings
from datetime import datetime, timedelta
from celery import shared_task
import pandas as pd
import logging
import json
import pvlib
import requests
import os
import openmeteo_requests
from data_factory.database.connection import DatabaseConnection
from data_factory.database.manager import DataManager

logger = logging.getLogger(__name__)


def process_nasa_data(data):
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
    df = process_nasa_data(data)

    try:
        conn = DatabaseConnection()
        db = DataManager(conn)
        df_filtered = df[df["parameter"] == "ALLSKY_SFC_SW_DWN"]
        
        if not df_filtered.empty:
            db.insert_irradiance_data(df_filtered)
    
    except Exception as e:
        logger.error(f"Failed to save to db: {e}")


@shared_task(bind=True)
def fetch_CEC_modules(self):
    json_path = os.path.join(settings.BASE_DIR, "config", "cec_modules.json")
    SAM_URL = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Modules.csv"
    modules = pvlib.pvsystem.retrieve_sam(path=SAM_URL)
    modules_dict = {}

    for name, params in modules.items():
        if not name:
            continue
        manufacturer = params.get("Manufacturer", "Unknown")
        modules_dict[name] = manufacturer

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(modules_dict, f, indent=4, ensure_ascii=False)
            f.close()
        logger.info(f"Wrote {len(modules_dict)} modules to {json_path}")
    except Exception as e:
        logger.error(f"Failed to write modules JSON file: {e}")


@shared_task(bind=True)
def fetch_CEC_inverters(self):
    json_path = os.path.join(settings.BASE_DIR, "config", "cec_inverters.json")
    SAM_URL = "https://raw.githubusercontent.com/NREL/SAM/refs/heads/develop/deploy/libraries/CEC%20Inverters.csv"
    inverters = pvlib.pvsystem.retrieve_sam(path=SAM_URL) 
    inverters_dict = {}
    
    for name in inverters.keys():
        # Extract manufacturer from index (before the first colon)
        manufacturer = name.split("__")[0].strip() if "__" in name else "Unknown"
        inverters_dict[name] = manufacturer

    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(inverters_dict, f, indent=4, ensure_ascii=False)
        logger.info(f"Wrote {len(inverters_dict)} inverters to {json_path}")

    except Exception as e:
        logger.error(f"Failed to write inverters JSON file: {e}")
