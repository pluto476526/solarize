import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional

class WeatherAnalyzer:
    def __init__(self, location_data: Dict, current_weather: pd.DataFrame, 
                 hourly_weather: pd.DataFrame, daily_weather: pd.DataFrame):
        """
        Initialize the WeatherAnalyzer with weather data.
        
        Args:
            location_data: Dictionary containing location information
            current_weather: DataFrame with current weather data
            hourly_weather: DataFrame with hourly forecast data
            daily_weather: DataFrame with daily forecast data
        """
        self.location_data = location_data
        self.current_df = current_weather
        self.hourly_df = hourly_weather
        self.daily_df = daily_weather
        
        # Convert time columns to datetime if they exist
        if not self.hourly_df.empty and 'time' in self.hourly_df.columns:
            self.hourly_df['time'] = pd.to_datetime(self.hourly_df['time'])
        if not self.daily_df.empty and 'time' in self.daily_df.columns:
            self.daily_df['time'] = pd.to_datetime(self.daily_df['time'])

    def _round_value(self, value: Optional[float], decimals: int = 1) -> Optional[float]:
        """Safely round a value, handling None and NaN values."""
        if value is None or pd.isna(value):
            return None
        return round(float(value), decimals)

    def _format_timestamp(self, timestamp: Any) -> Optional[str]:
        """Convert timestamp to ISO format string, handling various input types."""
        if timestamp is None or pd.isna(timestamp):
            return None
        
        if isinstance(timestamp, (pd.Timestamp, datetime)):
            return timestamp.isoformat()
        elif isinstance(timestamp, str):
            try:
                return pd.to_datetime(timestamp).isoformat()
            except:
                return None
        return str(timestamp)

    def analyze_weather(self) -> Dict[str, Any]:
        """
        Comprehensive weather analysis that returns all results in formatted dictionaries.
        
        Returns:
            Dictionary containing all weather analysis results
        """
        return {
            "location_info": self._get_location_info(),
            "current_conditions": self._analyze_current_conditions(),
            "hourly_analysis": self._analyze_hourly_data(),
            "daily_analysis": self._analyze_daily_data(),
            "weather_alerts": self._generate_weather_alerts(),
            "summary": self._generate_summary(),
            "timestamps": {
                "analysis_time": datetime.now(timezone.utc).isoformat(),
                "data_freshness": self._check_data_freshness()
            }
        }

    def _get_location_info(self) -> Dict[str, Any]:
        """Extract and format location information."""
        return {
            "latitude": self._round_value(self.location_data.get('latitude'), 4),
            "longitude": self._round_value(self.location_data.get('longitude'), 4),
            "location_id": self.location_data.get('id'),
            "elevation": self._round_value(self.location_data.get('elevation')),
            "timezone": self.location_data.get('timezone'),
            "location_name": self.location_data.get('name', 'Unknown')
        }

    def _analyze_current_conditions(self) -> Dict[str, Any]:
        """Analyze current weather conditions."""
        if self.current_df.empty:
            return {"error": "No current weather data available"}
        
        current = self.current_df.iloc[0]
        feels_like = self._calculate_feels_like(
            current.get('temperature_2m'),
            current.get('relative_humidity_2m'),
            current.get('wind_speed_10m')
        )
        
        return {
            "temperature": {
                "value": self._round_value(current.get('temperature_2m')),
                "unit": "°C",
                "feels_like": self._round_value(feels_like)
            },
            "precipitation": {
                "current": self._round_value(current.get('precipitation')),
                "unit": "mm",
                "type": self._determine_precipitation_type(current)
            },
            "wind": {
                "speed": self._round_value(current.get('wind_speed_10m')),
                "direction": self._round_value(current.get('wind_direction_10m'), 0),
                "gusts": self._round_value(current.get('wind_gusts_10m')),
                "unit": "km/h"
            },
            "humidity": {
                "value": self._round_value(current.get('relative_humidity_2m'), 0),
                "unit": "%"
            },
            "cloud_cover": {
                "value": self._round_value(current.get('cloud_cover'), 0),
                "unit": "%"
            },
            "visibility": {
                "value": self._round_value(current.get('visibility'), 0),
                "unit": "m"
            },
            "condition_code": self._get_weather_condition(current),
            "observation_time": self._format_timestamp(current.get('observation_time'))
        }

    def _analyze_hourly_data(self) -> Dict[str, Any]:
        """Analyze hourly forecast data."""
        if self.hourly_df.empty:
            return {"error": "No hourly weather data available"}
        
        # Next 24 hours analysis
        next_24h = self.hourly_df.head(24)
        
        return {
            "time_period": "next_24_hours",
            "temperature_analysis": {
                "max_temp": self._round_value(next_24h['temperature_2m'].max()),
                "min_temp": self._round_value(next_24h['temperature_2m'].min()),
                "avg_temp": self._round_value(next_24h['temperature_2m'].mean()),
                "trend": self._analyze_temperature_trend(next_24h),
                "comfort_hours": len(next_24h[
                    (next_24h['temperature_2m'] >= 18) & 
                    (next_24h['temperature_2m'] <= 26)
                ])
            },
            "precipitation_analysis": {
                "total_precipitation": self._round_value(next_24h['precipitation'].sum()),
                "precipitation_hours": len(next_24h[next_24h['precipitation'] > 0]),
                "max_precipitation_rate": self._round_value(next_24h['precipitation'].max()),
                "precipitation_probability_avg": self._round_value(next_24h['precipitation_probability'].mean(), 0),
                "heavy_precipitation_hours": len(next_24h[next_24h['precipitation'] > 2.5])
            },
            "solar_analysis": {
                "total_sunshine_hours": self._round_value(next_24h['sunshine_duration'].sum() / 3600),
                "peak_radiation": self._round_value(next_24h['shortwave_radiation'].max()),
                "solar_energy_total": self._round_value(next_24h['shortwave_radiation'].sum()),
                "best_sunlight_hours": self._find_best_sunlight_hours(next_24h)
            },
            "hourly_breakdown": self._get_hourly_breakdown(next_24h)
        }

    def _analyze_daily_data(self) -> Dict[str, Any]:
        """Analyze daily forecast data."""
        if self.daily_df.empty:
            return {"error": "No daily weather data available"}
        
        # Next 7 days analysis
        next_7_days = self.daily_df.head(7)
        
        return {
            "time_period": "next_7_days",
            "summary_stats": {
                "total_precipitation": self._round_value(next_7_days['precipitation_sum'].sum()),
                "total_sunshine_hours": self._round_value(next_7_days['sunshine_duration'].sum() / 3600),
                "avg_uv_index": self._round_value(next_7_days['uv_index_max'].mean(), 1)
            },
            "daily_breakdown": [
                {
                    "date": self._format_timestamp(row['time']),
                    "sunrise": self._format_timestamp(row.get('sunrise')),
                    "sunset": self._format_timestamp(row.get('sunset')),
                    "daylight_hours": self._round_value(row.get('daylight_duration', 0) / 3600),
                    "max_temperature": self._round_value(row.get('temperature_2m_max')),
                    "min_temperature": self._round_value(row.get('temperature_2m_min')),
                    "precipitation": {
                        "total": self._round_value(row.get('precipitation_sum')),
                        "probability": self._round_value(row.get('precipitation_probability_max'), 0),
                        "hours": self._round_value(row.get('precipitation_hours'), 0)
                    },
                    "solar": {
                        "sunshine_hours": self._round_value(row.get('sunshine_duration', 0) / 3600),
                        "uv_index_max": self._round_value(row.get('uv_index_max'), 1),
                        "solar_energy": self._round_value(row.get('shortwave_radiation_sum'))
                    },
                    "wind": {
                        "dominant_direction": self._round_value(row.get('wind_direction_10m_dominant'), 0)
                    },
                    "weather_condition": self._get_daily_weather_condition(row)
                }
                for _, row in next_7_days.iterrows()
            ],
            "best_days": {
                "sunniest_day": self._find_extreme_day(next_7_days, 'sunshine_duration', 'max'),
                "rainiest_day": self._find_extreme_day(next_7_days, 'precipitation_sum', 'max')
            }
        }

    def _generate_weather_alerts(self) -> List[Dict[str, Any]]:
        """Generate weather alerts based on current and forecast data."""
        alerts = []
        
        # Check current conditions
        if not self.current_df.empty:
            current = self.current_df.iloc[0]
            current_temp = current.get('temperature_2m', 0)
            current_precip = current.get('precipitation', 0)
            
            # Temperature alerts
            if current_temp > 35:
                alerts.append({
                    "type": "EXTREME_HEAT",
                    "level": "SEVERE",
                    "message": "Extreme heat warning",
                    "details": f"Temperature is {self._round_value(current_temp)}°C"
                })
            elif current_temp < -10:
                alerts.append({
                    "type": "EXTREME_COLD",
                    "level": "SEVERE",
                    "message": "Extreme cold warning",
                    "details": f"Temperature is {self._round_value(current_temp)}°C"
                })
            
            # Precipitation alerts
            if current_precip > 10:
                alerts.append({
                    "type": "HEAVY_RAIN",
                    "level": "MODERATE",
                    "message": "Heavy precipitation",
                    "details": f"Current precipitation: {self._round_value(current_precip)}mm"
                })
        
        # Check hourly forecast for upcoming alerts
        if not self.hourly_df.empty:
            next_6h = self.hourly_df.head(6)
            
            # High precipitation probability
            high_precip_hours = next_6h[next_6h['precipitation_probability'] > 80]
            if not high_precip_hours.empty:
                alerts.append({
                    "type": "HIGH_RAIN_PROBABILITY",
                    "level": "MODERATE",
                    "message": "High probability of rain in next 6 hours",
                    "details": f"Up to {self._round_value(high_precip_hours['precipitation_probability'].max(), 0)}% chance"
                })
            
            # High UV alert from daily data
            if not self.daily_df.empty and self.daily_df.iloc[0]['uv_index_max'] > 8:
                alerts.append({
                    "type": "HIGH_UV",
                    "level": "MODERATE",
                    "message": "High UV index today",
                    "details": f"UV index: {self._round_value(self.daily_df.iloc[0]['uv_index_max'], 1)}"
                })
        
        return {"alerts": alerts, "total": len(alerts)}

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate an overall weather summary."""
        summary = {
            "overall_condition": "UNKNOWN",
            "key_highlights": [],
            "recommendations": []
        }
        
        if self.current_df.empty:
            return summary
        
        current = self.current_df.iloc[0]
        current_temp = current.get('temperature_2m', 0)
        current_precip = current.get('precipitation', 0)
        
        # Determine overall condition
        if current_temp > 30:
            summary["overall_condition"] = "HOT"
        elif current_temp < 5:
            summary["overall_condition"] = "COLD"
        elif current_precip > 5:
            summary["overall_condition"] = "RAINY"
        else:
            summary["overall_condition"] = "FAIR"
        
        # Add highlights
        if current_temp > 25:
            summary["key_highlights"].append(f"Warm temperatures today ({self._round_value(current_temp)}°C)")
        if current_precip > 0:
            summary["key_highlights"].append(f"Precipitation: {self._round_value(current_precip)}mm")
        
        # Add recommendations
        if current_precip > 0:
            summary["recommendations"].append("Carry an umbrella")
        if not self.daily_df.empty and self.daily_df.iloc[0]['uv_index_max'] > 6:
            summary["recommendations"].append("Use sun protection")
        if current_temp < 10:
            summary["recommendations"].append("Dress warmly")
        
        return summary

    # Helper methods
    def _calculate_feels_like(self, temperature: float, humidity: float, wind_speed: float) -> float:
        """Calculate feels-like temperature considering humidity and wind."""
        if pd.isna(temperature) or pd.isna(humidity) or pd.isna(wind_speed):
            return temperature
        
        # Simple wind chill and heat index approximation
        if temperature < 10:
            # Wind chill approximation
            return 13.12 + 0.6215 * temperature - 11.37 * (wind_speed ** 0.16) + 0.3965 * temperature * (wind_speed ** 0.16)
        elif temperature > 27:
            # Heat index approximation
            return temperature + 0.5 * (humidity / 100) * (temperature - 27)
        else:
            return temperature

    def _determine_precipitation_type(self, current_data: pd.Series) -> str:
        """Determine precipitation type based on temperature and precipitation data."""
        temp = current_data.get('temperature_2m', 0)
        rain = current_data.get('rain', 0)
        showers = current_data.get('showers', 0)
        
        if temp < 0:
            return "SNOW"
        elif showers > 0:
            return "SHOWERS"
        elif rain > 0:
            return "RAIN"
        else:
            return "NONE"

    def _get_weather_condition(self, current_data: pd.Series) -> str:
        """Determine weather condition based on multiple factors."""
        cloud_cover = current_data.get('cloud_cover', 0)
        precipitation = current_data.get('precipitation', 0)
        
        if precipitation > 5:
            return "HEAVY_RAIN"
        elif precipitation > 0:
            return "LIGHT_RAIN"
        elif cloud_cover > 80:
            return "OVERCAST"
        elif cloud_cover > 30:
            return "PARTLY_CLOUDY"
        else:
            return "CLEAR"

    def _analyze_temperature_trend(self, hourly_data: pd.DataFrame) -> str:
        """Analyze temperature trend for the next 24 hours."""
        if len(hourly_data) < 2:
            return "STABLE"
        
        first_half = hourly_data['temperature_2m'].iloc[:12].mean()
        second_half = hourly_data['temperature_2m'].iloc[12:].mean()
        
        if second_half - first_half > 2:
            return "WARMING"
        elif first_half - second_half > 2:
            return "COOLING"
        else:
            return "STABLE"

    def _find_best_sunlight_hours(self, hourly_data: pd.DataFrame) -> List[Dict]:
        """Find the hours with best sunlight conditions."""
        best_hours = []
        for _, row in hourly_data.iterrows():
            radiation = row.get('shortwave_radiation', 0)
            sunshine = row.get('sunshine_duration', 0)
            
            if radiation > 500 and sunshine > 0:
                best_hours.append({
                    "hour": self._format_timestamp(row['time']),
                    "radiation": self._round_value(radiation),
                    "sunshine_duration": self._round_value(sunshine)
                })
        
        return sorted(best_hours, key=lambda x: x['radiation'], reverse=True)[:3]



    def _get_hourly_breakdown(self, hourly_data: pd.DataFrame) -> List[Dict]:
        """Create detailed hourly breakdown."""
        return [
            {
                "time": self._format_timestamp(row['time']),
                "temperature": self._round_value(row.get('temperature_2m')),
                "precipitation": {
                    "probability": self._round_value(row.get('precipitation_probability'), 0),
                    "amount": self._round_value(row.get('precipitation'))
                },
                "solar": {
                    "radiation": self._round_value(row.get('shortwave_radiation')),
                    "sunshine": self._round_value(row.get('sunshine_duration'))
                },
                "condition": self._get_hourly_condition(row)
            }
            for _, row in hourly_data.iterrows()
        ]

    def _get_hourly_condition(self, hourly_data: pd.Series) -> str:
        """Determine condition for hourly data."""
        precip_prob = hourly_data.get('precipitation_probability', 0)
        radiation = hourly_data.get('shortwave_radiation', 0)
        
        if precip_prob > 50:
            return "RAINY"
        elif radiation > 300:
            return "SUNNY"
        elif radiation > 100:
            return "PARTLY_CLOUDY"
        else:
            return "CLOUDY"

    def _get_daily_weather_condition(self, daily_data: pd.Series) -> str:
        """Determine weather condition for a day."""
        precip = daily_data.get('precipitation_sum', 0)
        sunshine = daily_data.get('sunshine_duration', 0) / 3600
        
        if precip > 10:
            return "RAINY"
        elif precip > 0:
            return "OCCASIONAL_RAIN"
        elif sunshine > 8:
            return "SUNNY"
        elif sunshine > 4:
            return "PARTLY_CLOUDY"
        else:
            return "CLOUDY"

    def _find_extreme_day(self, daily_data: pd.DataFrame, column: str, extreme_type: str) -> Dict:
        """Find day with extreme value for given column."""
        if daily_data.empty:
            return {"date": "Unknown", "value": None, "condition": "UNKNOWN"}
            
        if extreme_type == 'max':
            idx = daily_data[column].idxmax()
        else:
            idx = daily_data[column].idxmin()
        
        row = daily_data.loc[idx]
        return {
            "date": self._format_timestamp(row['time']),
            "value": self._round_value(row[column]),
            "condition": self._get_daily_weather_condition(row)
        }

    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check how fresh the weather data is."""
        freshness = {
            "current_data_age": "UNKNOWN",
            "forecast_currentness": "UNKNOWN"
        }
        
        if not self.current_df.empty and 'observation_time' in self.current_df.columns:
            obs_time = pd.to_datetime(self.current_df.iloc[0]['observation_time'])
            age_hours = (datetime.now(timezone.utc) - obs_time).total_seconds() / 3600
            freshness["current_data_age"] = f"{self._round_value(age_hours, 1)} hours"
        
        if not self.hourly_df.empty and 'time' in self.hourly_df.columns:
            latest_forecast = self.hourly_df['time'].max()
            freshness["forecast_currentness"] = self._format_timestamp(latest_forecast)
        
        return freshness