## data_factory/pvwatts/base_forecast.py
## pkibuka@milky-way.space

from decouple import config
from typing import Dict
import requests_cache
import logging
import requests
import pandas as pd

logger = logging.getLogger(__name__)


class FetchNRELData:
    def __init__(self, location, system_config: Dict, cache_expire=3600):
        self.nrel_api_key = config("NREL_API_KEY")
        self.location = location
        self.config = system_config

        # Create a persistent cache file
        self.session = requests_cache.CachedSession(".cache", expire_after=3600)

    def get_base_forecast(self) -> Dict:
        """Get fundamental NREL data (cached)."""
        url = "https://developer.nrel.gov/api/pvwatts/v8.json"

        params = {
            "api_key": self.nrel_api_key,
            "lat": self.location.lat,
            "lon": self.location.lon,
            "system_capacity": self.config.get("system_capacity", 5),
            "azimuth": self.config.get("azimuth", 180),
            "tilt": self.config.get("tilt", 20),
            "array_type": self.config.get("array_type", 0),
            "module_type": self.config.get("module_type", 0),
            "losses": self.config.get("losses", 14),
            "timeframe": "hourly",
        }

        # Cached request
        response = self.session.get(url, params=params)
        data = response.json()

        hours = 8760
        timestamps = pd.date_range(start="2024-01-01", periods=hours, freq="h")

        base_forecast = {
            "location": self.location,
            "system_config": self.config,
            "hourly_data": pd.DataFrame(
                {
                    "timestamp": timestamps,
                    "ac_power": data["outputs"]["ac"],
                    "dc_power": data["outputs"]["dc"],
                    "poa_irradiance": data["outputs"]["poa"],
                    "month": timestamps.month,
                    "hour": timestamps.hour,
                    "day_of_year": timestamps.dayofyear,
                }
            ),
            "annual_total": sum(data["outputs"]["ac"]),
            "capacity_factor": data["outputs"]["capacity_factor"],
            "cached": getattr(response, "from_cache", False),
        }

        return base_forecast
