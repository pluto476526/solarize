## data_factory/weather/utils.py
## pkibuka@milky-way.space


import requests_cache
import openmeteo_requests
from retry_requests import retry
from data_factory.apis import data_utils


def fetch_weather_data(location):

    # Setup the Open-Meteo API client with cache and retry on error
    cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    # lat, lon = -1.2921, 36.8219
    url = "https://api.open-meteo.com/v1/forecast"

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
        "latitude": location["lat"],
        "longitude": location["lon"],
        "daily": daily_params,
        "hourly": hourly_params,
        "models": "best_match",
        "current": current_params,
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

    current_df, hourly_df, daily_df = data_utils.process_openmeteo_weather(response)
    return location_data, current_df, hourly_df, daily_df
