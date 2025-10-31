## data_factory/tasks.py
## pkibuka@miky-way.space


import requests_cache
from retry_requests import retry
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
from decouple import config
from data_factory.apis import data_utils

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
    return pd.DataFrame(
        columns=["date", "parameter", "value", "units", "lon", "lat", "elev", "source"]
    )


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

    RE_params = "ALLSKY_SFC_SW_DWN,ALLSKY_KT"
    params = {
        "parameters": RE_params,
        "community": "RE",
        "longitude": 36.8219,
        "latitude": -1.2921,
        "start": start_date.strftime("%Y%m%d"),
        "end": end_date.strftime("%Y%m%d"),
        "format": "JSON",
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
            db.close()

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


@shared_task(bind=True)
def fetch_climacell_data(self):
    lat, lon = -1.2921, 36.8219
    params = {
        "location": f"{lat},{lon}",
        "apikey": config("CLIMACELL_API_KEY"),
    }

    response = requests.get(
        "https://api.tomorrow.io/v4/weather/realtime",
        headers={"accept": "application/json"},
        params=params,
    )
    print(response.json())


@shared_task(bind=True)
def fetch_openmeteo_weather(self):

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://api.open-meteo.com/v1/forecast"
    lat, lon = -1.2921, 36.8219

    daily_params = [
        "sunrise",
        "sunset",
        "daylight_duration",
        "sunshine_duration",
        "uv_index_max",
        "uv_index_clear_sky_max",
        "rain_sum",
        "showers_sum",
        "precipitation_sum",
        "precipitation_hours",
        "precipitation_probability_max",
        "shortwave_radiation_sum",
        "wind_direction_10m_dominant",
    ]
    hourly_params = [
        "temperature_2m",
        "precipitation_probability",
        "precipitation",
        "rain",
        "showers",
        "shortwave_radiation",
        "diffuse_radiation",
        "direct_normal_irradiance",
        "sunshine_duration",
    ]
    current_params = [
        "temperature_2m",
        "relative_humidity_2m",
        "apparent_temperature",
        "precipitation",
        "rain",
        "showers",
        "weather_code",
        "cloud_cover",
        "wind_speed_10m",
        "wind_direction_10m",
        "wind_gusts_10m",
    ]

    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": daily_params,
        "hourly": hourly_params,
        "models": "best_match",
        "current": current_params,
        "timezone": "auto",
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    conn = DatabaseConnection()
    db = DataManager(conn)

    location_idx = db.get_or_create_location(
        provider="openmeteo",
        latitude=lat,
        longitude=lon,
        elevation_m=response.Elevation(),
        timezone=response.Timezone(),
        tz_abbreviation=response.TimezoneAbbreviation(),
        utc_offset_secs=response.UtcOffsetSeconds(),
        model="best_match",
    )

    current_df, hourly_df, daily_df = data_utils.process_openmeteo_weather(response)

    db.insert_openmeteo_data(location_idx, current_df, hourly_df, daily_df)
    db.close()


@shared_task(bind=True)
def fetch_openmeteo_airquality(self):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    lat, lon = -1.2921, 36.8219

    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": [
            "pm2_5",
            "carbon_monoxide",
            "carbon_dioxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "dust",
            "uv_index",
            "pm10",
        ],
        "current": [
            "european_aqi",
            "us_aqi",
            "pm10",
            "pm2_5",
            "carbon_monoxide",
            "nitrogen_dioxide",
            "sulphur_dioxide",
            "ozone",
            "aerosol_optical_depth",
            "dust",
            "uv_index",
        ],
        "timezone": "auto",
    }
    responses = openmeteo.weather_api(url, params=params)

    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]

    conn = DatabaseConnection()
    db = DataManager(conn)

    location_idx = db.get_or_create_location(
        provider="openmeteo",
        latitude=lat,
        longitude=lon,
        elevation_m=response.Elevation(),
        timezone=response.Timezone(),
        tz_abbreviation=response.TimezoneAbbreviation(),
        utc_offset_secs=response.UtcOffsetSeconds(),
        model="best_match",
    )

    current_df, hourly_df = data_utils.process_airquality_data(response)

    db.insert_air_quality_data(location_idx, current_df, hourly_df)
    db.close()

    print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation: {response.Elevation()} m asl")
    print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")
