
import pandas as pd
import logging


def process_openmeteo_weather(response):
    # Process current data. The order of variables needs to be the same as requested.
    current = response.Current()
    current_data = {
    	"time": [pd.to_datetime(current.Time(), unit="s", utc=True)],
    	"temperature_2m": [current.Variables(0).Value()],
    	"relative_humidity_2m": [current.Variables(1).Value()],
    	"apparent_temperature": [current.Variables(2).Value()],
    	"precipitation": [current.Variables(3).Value()],
    	"rain": [current.Variables(4).Value()],
    	"showers": [current.Variables(5).Value()],
    	"weather_code": [current.Variables(6).Value()],
    	"cloud_cover": [current.Variables(7).Value()],
    	"wind_speed_10m": [current.Variables(8).Value()],
    	"wind_direction_10m": [current.Variables(9).Value()],
    	"wind_gusts_10m": [current.Variables(10).Value()]
    }
    current_dataframe = pd.DataFrame(data=current_data)

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy()
    hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
    hourly_precipitation = hourly.Variables(2).ValuesAsNumpy()
    hourly_rain = hourly.Variables(3).ValuesAsNumpy()
    hourly_showers = hourly.Variables(4).ValuesAsNumpy()
    hourly_shortwave_radiation = hourly.Variables(5).ValuesAsNumpy()
    hourly_diffuse_radiation = hourly.Variables(6).ValuesAsNumpy()
    hourly_direct_normal_irradiance = hourly.Variables(7).ValuesAsNumpy()
    hourly_sunshine_duration = hourly.Variables(8).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
        end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds = hourly.Interval()),
        inclusive="left"
    )}

    hourly_data["temperature_2m"] = hourly_temperature_2m
    hourly_data["precipitation_probability"] = hourly_precipitation_probability
    hourly_data["precipitation"] = hourly_precipitation
    hourly_data["rain"] = hourly_rain
    hourly_data["showers"] = hourly_showers
    hourly_data["shortwave_radiation"] = hourly_shortwave_radiation
    hourly_data["diffuse_radiation"] = hourly_diffuse_radiation
    hourly_data["direct_normal_irradiance"] = hourly_direct_normal_irradiance
    hourly_data["sunshine_duration"] = hourly_sunshine_duration
    hourly_dataframe = pd.DataFrame(data=hourly_data)

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_sunrise = daily.Variables(0).ValuesInt64AsNumpy()
    daily_sunset = daily.Variables(1).ValuesInt64AsNumpy()
    daily_daylight_duration = daily.Variables(2).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(3).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(4).ValuesAsNumpy()
    daily_uv_index_clear_sky_max = daily.Variables(5).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(6).ValuesAsNumpy()
    daily_showers_sum = daily.Variables(7).ValuesAsNumpy()
    daily_precipitation_sum = daily.Variables(8).ValuesAsNumpy()
    daily_precipitation_hours = daily.Variables(9).ValuesAsNumpy()
    daily_precipitation_probability_max = daily.Variables(10).ValuesAsNumpy()
    daily_shortwave_radiation_sum = daily.Variables(11).ValuesAsNumpy()
    daily_wind_direction_10m_dominant = daily.Variables(12).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}

    daily_data["sunrise"] = daily_sunrise
    daily_data["sunset"] = daily_sunset
    daily_data["daylight_duration"] = daily_daylight_duration
    daily_data["sunshine_duration"] = daily_sunshine_duration
    daily_data["uv_index_max"] = daily_uv_index_max
    daily_data["uv_index_clear_sky_max"] = daily_uv_index_clear_sky_max
    daily_data["rain_sum"] = daily_rain_sum
    daily_data["showers_sum"] = daily_showers_sum
    daily_data["precipitation_sum"] = daily_precipitation_sum
    daily_data["precipitation_hours"] = daily_precipitation_hours
    daily_data["precipitation_probability_max"] = daily_precipitation_probability_max
    daily_data["shortwave_radiation_sum"] = daily_shortwave_radiation_sum
    daily_data["wind_direction_10m_dominant"] = daily_wind_direction_10m_dominant
    daily_dataframe = pd.DataFrame(data=daily_data)

    return current_dataframe, hourly_dataframe, daily_dataframe




def process_airquality_data(response):
    # Process current data. The order of variables needs to be the same as requested.
    current = response.Current()
    current_data = {
        "time": [pd.to_datetime(current.Time(), unit="s", utc=True)],
        "european_aqi": [current.Variables(0).Value()],
        "us_aqi": [current.Variables(1).Value()],
        "pm10": [current.Variables(2).Value()],
        "pm2_5": [current.Variables(3).Value()],
        "carbon_monoxide": [current.Variables(4).Value()],
        "nitrogen_dioxide": [current.Variables(5).Value()],
        "sulphur_dioxide": [current.Variables(6).Value()],
        "ozone": [current.Variables(7).Value()],
        "aerosol_optical_depth": [current.Variables(8).Value()],
        "dust": [current.Variables(9).Value()],
        "uv_index": [current.Variables(10).Value()]
    }
    current_dataframe = pd.DataFrame(data=current_data)

    # Process hourly data. The order of variables needs to be the same as requested.
    hourly = response.Hourly()
    hourly_pm2_5 = hourly.Variables(0).ValuesAsNumpy()
    hourly_carbon_monoxide = hourly.Variables(1).ValuesAsNumpy()
    hourly_carbon_dioxide = hourly.Variables(2).ValuesAsNumpy()
    hourly_nitrogen_dioxide = hourly.Variables(3).ValuesAsNumpy()
    hourly_sulphur_dioxide = hourly.Variables(4).ValuesAsNumpy()
    hourly_ozone = hourly.Variables(5).ValuesAsNumpy()
    hourly_dust = hourly.Variables(6).ValuesAsNumpy()
    hourly_uv_index = hourly.Variables(7).ValuesAsNumpy()
    hourly_pm10 = hourly.Variables(8).ValuesAsNumpy()

    hourly_data = {"date": pd.date_range(
        start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
        end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
        freq = pd.Timedelta(seconds = hourly.Interval()),
        inclusive = "left"
    )}

    hourly_data["pm2_5"] = hourly_pm2_5
    hourly_data["carbon_monoxide"] = hourly_carbon_monoxide
    hourly_data["carbon_dioxide"] = hourly_carbon_dioxide
    hourly_data["nitrogen_dioxide"] = hourly_nitrogen_dioxide
    hourly_data["sulphur_dioxide"] = hourly_sulphur_dioxide
    hourly_data["ozone"] = hourly_ozone
    hourly_data["dust"] = hourly_dust
    hourly_data["uv_index"] = hourly_uv_index
    hourly_data["pm10"] = hourly_pm10
    hourly_dataframe = pd.DataFrame(data = hourly_data)

    return current_dataframe, hourly_dataframe
    