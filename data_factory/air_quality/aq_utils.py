## data_factory/air_quality/aq_utils.py
## pkibuka@milky-way.space

import requests_cache
import openmeteo_requests
from retry_requests import retry
from data_factory.apis import data_utils


def fetch_openmeteo_airquality(location):
    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": location["lat"],
        "longitude": location["lon"],
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
        "timezone": location["tz"],
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]

    location_data = {
        "provider": "openmeteo",
        "name": location["name"],
        "latitude": response.Latitude(),
        "longitude": response.Longitude(),
        "elevation_m": response.Elevation(),
        "timezone": response.Timezone(),
        "tz_abbreviation": response.TimezoneAbbreviation(),
        "utc_offset_secs": response.UtcOffsetSeconds(),
        "model": "best_match",
    }

    current_df, hourly_df = data_utils.process_airquality_data(response)
    return location_data, current_df, hourly_df
