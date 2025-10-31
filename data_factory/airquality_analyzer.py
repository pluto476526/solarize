import pandas as pd
import numpy as np
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


class AirQualityAnalyzer:
    def __init__(
        self,
        location_data: Dict,
        current_weather: pd.DataFrame,
        hourly_weather: pd.DataFrame,
    ):
        """
        Initialize the AirQualityAnalyzer with air quality data.

        Args:
            location_data: Dictionary containing location information
            current_weather: DataFrame with current air quality data
            hourly_weather: DataFrame with hourly forecast data
        """
        self.location_data = location_data
        self.current_df = current_weather
        self.hourly_df = hourly_weather

        # Convert time columns to datetime if they exist
        if not self.hourly_df.empty and "date" in self.hourly_df.columns:
            self.hourly_df["date"] = pd.to_datetime(self.hourly_df["date"])

    def _round_value(
        self, value: Optional[float], decimals: int = 2
    ) -> Optional[float]:
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

    def analyze_air_quality(self) -> Dict[str, Any]:
        """
        Comprehensive air quality analysis that returns all results in formatted dictionaries.

        Returns:
            Dictionary containing all air quality analysis results
        """
        return {
            "location_info": self._get_location_info(),
            "current_conditions": self._analyze_current_conditions(),
            "hourly_analysis": self._analyze_hourly_data(),
            "aqi_analysis": self._analyze_aqi_data(),
            "health_recommendations": self._generate_health_recommendations(),
            "pollutant_analysis": self._analyze_pollutants(),
            "alerts": self._generate_air_quality_alerts(),
            "summary": self._generate_summary(),
            "timestamps": {
                "analysis_time": datetime.now(timezone.utc).isoformat(),
                "data_freshness": self._check_data_freshness(),
            },
        }

    def _get_location_info(self) -> Dict[str, Any]:
        """Extract and format location information."""
        return {
            "latitude": self._round_value(self.location_data.get("latitude"), 4),
            "longitude": self._round_value(self.location_data.get("longitude"), 4),
            "location_id": self.location_data.get("id"),
            "elevation": self._round_value(self.location_data.get("elevation_m")),
            "timezone": self.location_data.get("timezone"),
            "location_name": self.location_data.get("name", "Unknown"),
        }

    def _analyze_current_conditions(self) -> Dict[str, Any]:
        """Analyze current air quality conditions."""
        if self.current_df.empty:
            return {"error": "No current air quality data available"}

        current = self.current_df.iloc[0]

        return {
            "aqi_indices": {
                "european_aqi": {
                    "value": self._round_value(current.get("european_aqi"), 0),
                    "category": self._get_european_aqi_category(
                        current.get("european_aqi")
                    ),
                    "level": self._get_aqi_level(current.get("european_aqi")),
                },
                "us_aqi": {
                    "value": self._round_value(current.get("us_aqi"), 0),
                    "category": self._get_us_aqi_category(current.get("us_aqi")),
                    "level": self._get_aqi_level(current.get("us_aqi")),
                },
            },
            "primary_pollutants": {
                "pm2_5": {
                    "value": self._round_value(current.get("pm2_5")),
                    "unit": "μg/m³",
                    "category": self._get_pm25_category(current.get("pm2_5")),
                },
                "pm10": {
                    "value": self._round_value(current.get("pm10")),
                    "unit": "μg/m³",
                    "category": self._get_pm10_category(current.get("pm10")),
                },
            },
            "gas_pollutants": {
                "carbon_monoxide": {
                    "value": self._round_value(current.get("carbon_monoxide")),
                    "unit": "μg/m³",
                },
                "nitrogen_dioxide": {
                    "value": self._round_value(current.get("nitrogen_dioxide")),
                    "unit": "μg/m³",
                },
                "sulphur_dioxide": {
                    "value": self._round_value(current.get("sulphur_dioxide")),
                    "unit": "μg/m³",
                },
                "ozone": {
                    "value": self._round_value(current.get("ozone")),
                    "unit": "μg/m³",
                },
            },
            "other_indicators": {
                "aerosol_optical_depth": self._round_value(
                    current.get("aerosol_optical_depth")
                ),
                "dust": self._round_value(current.get("dust")),
                "uv_index": self._round_value(current.get("uv_index"), 1),
            },
            "dominant_pollutant": self._get_dominant_pollutant(current),
            "observation_time": self._format_timestamp(current.get("observation_time")),
        }

    def _analyze_hourly_data(self) -> Dict[str, Any]:
        """Analyze hourly forecast data."""
        if self.hourly_df.empty:
            return {"error": "No hourly air quality data available"}

        # Next 24 hours analysis
        next_24h = self.hourly_df.head(24)

        return {
            "time_period": "next_24_hours",
            "pollutant_trends": {
                "pm2_5": self._analyze_pollutant_trend(next_24h, "pm2_5"),
                "pm10": self._analyze_pollutant_trend(next_24h, "pm10"),
                "ozone": self._analyze_pollutant_trend(next_24h, "ozone"),
                "nitrogen_dioxide": self._analyze_pollutant_trend(
                    next_24h, "nitrogen_dioxide"
                ),
            },
            "peak_periods": {
                "worst_air_quality": self._find_worst_air_quality_period(next_24h),
                "best_air_quality": self._find_best_air_quality_period(next_24h),
            },
            "statistical_summary": {
                "pm2_5": {
                    "max": self._round_value(next_24h["pm2_5"].max()),
                    "min": self._round_value(next_24h["pm2_5"].min()),
                    "avg": self._round_value(next_24h["pm2_5"].mean()),
                    "above_unhealthy_hours": len(next_24h[next_24h["pm2_5"] > 35.4]),
                },
                "pm10": {
                    "max": self._round_value(next_24h["pm10"].max()),
                    "min": self._round_value(next_24h["pm10"].min()),
                    "avg": self._round_value(next_24h["pm10"].mean()),
                    "above_unhealthy_hours": len(next_24h[next_24h["pm10"] > 154]),
                },
            },
            "hourly_breakdown": self._get_hourly_breakdown(next_24h),
        }

    def _analyze_aqi_data(self) -> Dict[str, Any]:
        """Analyze AQI data and trends."""
        if self.current_df.empty or self.hourly_df.empty:
            return {"error": "Insufficient data for AQI analysis"}

        current = self.current_df.iloc[0]
        next_24h = self.hourly_df.head(24)

        # Calculate estimated AQI from pollutants for hourly data
        hourly_aqi_estimates = [
            self._calculate_aqi_from_pollutants(row) for _, row in next_24h.iterrows()
        ]

        return {
            "current_aqi": {
                "european": self._round_value(current.get("european_aqi"), 0),
                "us": self._round_value(current.get("us_aqi"), 0),
                "overall_category": self._get_overall_aqi_category(current),
            },
            "forecast_trend": {
                "trend_direction": self._analyze_aqi_trend(hourly_aqi_estimates),
                "peak_aqi_time": self._find_peak_aqi_period(next_24h),
                "improvement_time": self._find_air_quality_improvement_period(next_24h),
            },
            "historical_comparison": self._compare_with_standards(),
        }

    def _analyze_pollutants(self) -> Dict[str, Any]:
        """Detailed analysis of individual pollutants."""
        if self.current_df.empty:
            return {"error": "No pollutant data available"}

        current = self.current_df.iloc[0]

        return {
            "particulate_matter": {
                "pm2_5": {
                    "value": self._round_value(current.get("pm2_5")),
                    "health_impact": self._get_pm25_health_impact(current.get("pm2_5")),
                    "sources": "Vehicle emissions, industrial processes, combustion",
                },
                "pm10": {
                    "value": self._round_value(current.get("pm10")),
                    "health_impact": self._get_pm10_health_impact(current.get("pm10")),
                    "sources": "Dust, pollen, mold, construction",
                },
            },
            "gaseous_pollutants": {
                "ozone": {
                    "value": self._round_value(current.get("ozone")),
                    "health_impact": self._get_ozone_health_impact(
                        current.get("ozone")
                    ),
                    "sources": "Photochemical reactions from NOx and VOCs",
                },
                "nitrogen_dioxide": {
                    "value": self._round_value(current.get("nitrogen_dioxide")),
                    "health_impact": self._get_no2_health_impact(
                        current.get("nitrogen_dioxide")
                    ),
                    "sources": "Fuel combustion, vehicle emissions",
                },
                "sulphur_dioxide": {
                    "value": self._round_value(current.get("sulphur_dioxide")),
                    "health_impact": self._get_so2_health_impact(
                        current.get("sulphur_dioxide")
                    ),
                    "sources": "Burning fossil fuels, industrial processes",
                },
                "carbon_monoxide": {
                    "value": self._round_value(current.get("carbon_monoxide")),
                    "health_impact": self._get_co_health_impact(
                        current.get("carbon_monoxide")
                    ),
                    "sources": "Incomplete combustion, vehicle exhaust",
                },
            },
        }

    def _generate_health_recommendations(self) -> Dict[str, Any]:
        """Generate health recommendations based on air quality."""
        if self.current_df.empty:
            return {"error": "No data for health recommendations"}

        current = self.current_df.iloc[0]
        recommendations = {
            "general_population": [],
            "sensitive_groups": [],
            "outdoor_activities": [],
            "indoor_air_quality": [],
        }

        pm25 = current.get("pm2_5", 0)
        pm10 = current.get("pm10", 0)
        ozone = current.get("ozone", 0)

        # PM2.5 based recommendations
        if pm25 > 35.4:
            recommendations["sensitive_groups"].append("Avoid all outdoor activities")
            recommendations["general_population"].append(
                "Reduce prolonged outdoor exertion"
            )
        elif pm25 > 12:
            recommendations["sensitive_groups"].append("Reduce outdoor activities")

        # PM10 based recommendations
        if pm10 > 154:
            recommendations["outdoor_activities"].append(
                "Consider rescheduling outdoor events"
            )

        # Ozone based recommendations
        if ozone > 100:
            recommendations["sensitive_groups"].append(
                "Avoid afternoon outdoor activities"
            )
            recommendations["outdoor_activities"].append(
                "Schedule activities for morning hours"
            )

        # General recommendations
        if pm25 > 12 or pm10 > 50:
            recommendations["indoor_air_quality"].append(
                "Use air purifiers with HEPA filters"
            )
            recommendations["indoor_air_quality"].append(
                "Keep windows closed during high pollution hours"
            )

        # UV index recommendations
        uv_index = current.get("uv_index", 0)
        if uv_index > 6:
            recommendations["outdoor_activities"].append(
                "Use sun protection - high UV levels"
            )

        return recommendations

    def _generate_air_quality_alerts(self) -> List[Dict[str, Any]]:
        """Generate air quality alerts based on current and forecast data."""
        alerts = []

        if self.current_df.empty:
            return alerts

        current = self.current_df.iloc[0]

        # PM2.5 alerts
        pm25 = current.get("pm2_5", 0)
        if pm25 > 55.4:
            alerts.append(
                {
                    "type": "HAZARDOUS_PM25",
                    "level": "SEVERE",
                    "pollutant": "PM2.5",
                    "value": self._round_value(pm25),
                    "message": "Hazardous PM2.5 levels - Avoid outdoor activities",
                    "details": f"PM2.5 concentration: {self._round_value(pm25)} μg/m³",
                }
            )
        elif pm25 > 35.4:
            alerts.append(
                {
                    "type": "UNHEALTHY_PM25",
                    "level": "HIGH",
                    "pollutant": "PM2.5",
                    "value": self._round_value(pm25),
                    "message": "Unhealthy PM2.5 levels - Sensitive groups should avoid outdoor activities",
                    "details": f"PM2.5 concentration: {self._round_value(pm25)} μg/m³",
                }
            )

        # PM10 alerts
        pm10 = current.get("pm10", 0)
        if pm10 > 254:
            alerts.append(
                {
                    "type": "HAZARDOUS_PM10",
                    "level": "SEVERE",
                    "pollutant": "PM10",
                    "value": self._round_value(pm10),
                    "message": "Hazardous PM10 levels - Poor air quality",
                    "details": f"PM10 concentration: {self._round_value(pm10)} μg/m³",
                }
            )

        # Ozone alerts
        ozone = current.get("ozone", 0)
        if ozone > 100:
            alerts.append(
                {
                    "type": "HIGH_OZONE",
                    "level": "MODERATE",
                    "pollutant": "Ozone",
                    "value": self._round_value(ozone),
                    "message": "Elevated ozone levels",
                    "details": f"Ozone concentration: {self._round_value(ozone)} μg/m³",
                }
            )

        # Check hourly forecast for upcoming alerts
        if not self.hourly_df.empty:
            next_12h = self.hourly_df.head(12)
            high_pm25_hours = next_12h[next_12h["pm2_5"] > 35.4]
            if not high_pm25_hours.empty:
                alerts.append(
                    {
                        "type": "FORECAST_HIGH_PM25",
                        "level": "MODERATE",
                        "pollutant": "PM2.5",
                        "message": "High PM2.5 levels forecast in next 12 hours",
                        "details": f"Peak PM2.5: {self._round_value(high_pm25_hours["pm2_5"].max())} μg/m³",
                    }
                )

        return alerts

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate an overall air quality summary."""
        summary = {
            "overall_quality": "UNKNOWN",
            "primary_concern": "None",
            "outlook": "UNKNOWN",
            "key_findings": [],
        }

        if self.current_df.empty:
            return summary

        current = self.current_df.iloc[0]
        pm25 = current.get("pm2_5", 0)
        pm10 = current.get("pm10", 0)

        # Determine overall quality
        if pm25 <= 12 and pm10 <= 50:
            summary["overall_quality"] = "GOOD"
        elif pm25 <= 35.4 and pm10 <= 154:
            summary["overall_quality"] = "MODERATE"
        elif pm25 <= 55.4 and pm10 <= 254:
            summary["overall_quality"] = "UNHEALTHY_FOR_SENSITIVE_GROUPS"
        elif pm25 <= 150.4 and pm10 <= 354:
            summary["overall_quality"] = "UNHEALTHY"
        else:
            summary["overall_quality"] = "HAZARDOUS"

        # Determine primary concern
        pollutants = {
            "PM2.5": pm25,
            "PM10": pm10,
            "Ozone": current.get("ozone", 0),
            "NO2": current.get("nitrogen_dioxide", 0),
        }
        primary_pollutant = max(pollutants, key=pollutants.get)
        summary["primary_concern"] = primary_pollutant

        # Add key findings
        if pm25 > 12:
            summary["key_findings"].append(
                f"Elevated PM2.5 levels ({self._round_value(pm25)} μg/m³)"
            )
        if pm10 > 50:
            summary["key_findings"].append(
                f"Elevated PM10 levels ({self._round_value(pm10)} μg/m³)"
            )

        # Determine outlook
        if not self.hourly_df.empty:
            next_6h_avg = self.hourly_df.head(6)["pm2_5"].mean()
            if next_6h_avg > pm25 * 1.2:
                summary["outlook"] = "DETERIORATING"
            elif next_6h_avg < pm25 * 0.8:
                summary["outlook"] = "IMPROVING"
            else:
                summary["outlook"] = "STABLE"

        return summary

    # Helper methods for categorization and analysis
    def _get_european_aqi_category(self, aqi: Optional[float]) -> str:
        """Convert European AQI to category."""
        if aqi is None or pd.isna(aqi):
            return "UNKNOWN"
        aqi = float(aqi)
        if aqi <= 25:
            return "VERY_GOOD"
        elif aqi <= 50:
            return "GOOD"
        elif aqi <= 75:
            return "MODERATE"
        elif aqi <= 100:
            return "POOR"
        else:
            return "VERY_POOR"

    def _get_us_aqi_category(self, aqi: Optional[float]) -> str:
        """Convert US AQI to category."""
        if aqi is None or pd.isna(aqi):
            return "UNKNOWN"
        aqi = float(aqi)
        if aqi <= 50:
            return "GOOD"
        elif aqi <= 100:
            return "MODERATE"
        elif aqi <= 150:
            return "UNHEALTHY_FOR_SENSITIVE_GROUPS"
        elif aqi <= 200:
            return "UNHEALTHY"
        elif aqi <= 300:
            return "VERY_UNHEALTHY"
        else:
            return "HAZARDOUS"

    def _get_aqi_level(self, aqi: Optional[float]) -> int:
        """Get AQI level (1-6)."""
        if aqi is None or pd.isna(aqi):
            return 0
        aqi = float(aqi)
        if aqi <= 50:
            return 1
        elif aqi <= 100:
            return 2
        elif aqi <= 150:
            return 3
        elif aqi <= 200:
            return 4
        elif aqi <= 300:
            return 5
        else:
            return 6

    def _get_pm25_category(self, pm25: Optional[float]) -> str:
        """Categorize PM2.5 levels."""
        if pm25 is None or pd.isna(pm25):
            return "UNKNOWN"
        pm25 = float(pm25)
        if pm25 <= 12:
            return "GOOD"
        elif pm25 <= 35.4:
            return "MODERATE"
        elif pm25 <= 55.4:
            return "UNHEALTHY_FOR_SENSITIVE_GROUPS"
        elif pm25 <= 150.4:
            return "UNHEALTHY"
        elif pm25 <= 250.4:
            return "VERY_UNHEALTHY"
        else:
            return "HAZARDOUS"

    def _get_pm10_category(self, pm10: Optional[float]) -> str:
        """Categorize PM10 levels."""
        if pm10 is None or pd.isna(pm10):
            return "UNKNOWN"
        pm10 = float(pm10)
        if pm10 <= 50:
            return "GOOD"
        elif pm10 <= 154:
            return "MODERATE"
        elif pm10 <= 254:
            return "UNHEALTHY_FOR_SENSITIVE_GROUPS"
        elif pm10 <= 354:
            return "UNHEALTHY"
        elif pm10 <= 424:
            return "VERY_UNHEALTHY"
        else:
            return "HAZARDOUS"

    def _get_dominant_pollutant(self, current_data: pd.Series) -> str:
        """Determine the dominant pollutant."""
        pollutants = {
            "PM2.5": current_data.get("pm2_5", 0),
            "PM10": current_data.get("pm10", 0),
            "Ozone": current_data.get("ozone", 0),
            "NO2": current_data.get("nitrogen_dioxide", 0),
            "SO2": current_data.get("sulphur_dioxide", 0),
            "CO": current_data.get("carbon_monoxide", 0),
        }
        return max(pollutants, key=pollutants.get)

    def _analyze_pollutant_trend(
        self, hourly_data: pd.DataFrame, pollutant: str
    ) -> Dict[str, Any]:
        """Analyze trend for a specific pollutant."""
        if len(hourly_data) < 2:
            return {"trend": "STABLE", "change_percent": 0}

        first_half = hourly_data[pollutant].iloc[:6].mean()
        second_half = hourly_data[pollutant].iloc[6:12].mean()

        if pd.isna(first_half) or pd.isna(second_half) or first_half == 0:
            return {"trend": "STABLE", "change_percent": 0}

        change_percent = ((second_half - first_half) / first_half) * 100

        if change_percent > 10:
            trend = "INCREASING"
        elif change_percent < -10:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        return {"trend": trend, "change_percent": self._round_value(change_percent, 1)}

    def _find_worst_air_quality_period(
        self, hourly_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Find period with worst air quality in next 24 hours."""
        if hourly_data.empty:
            return {"time": "Unknown", "pm2_5": None, "pm10": None}

        worst_idx = hourly_data["pm2_5"].idxmax()
        worst_row = hourly_data.loc[worst_idx]

        return {
            "time": self._format_timestamp(worst_row["time"]),
            "pm2_5": self._round_value(worst_row["pm2_5"]),
            "pm10": self._round_value(worst_row["pm10"]),
            "overall_quality": self._get_pm25_category(worst_row["pm2_5"]),
        }

    def _find_best_air_quality_period(
        self, hourly_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Find period with best air quality in next 24 hours."""
        if hourly_data.empty:
            return {"time": "Unknown", "pm2_5": None, "pm10": None}

        best_idx = hourly_data["pm2_5"].idxmin()
        best_row = hourly_data.loc[best_idx]

        return {
            "time": self._format_timestamp(best_row["time"]),
            "pm2_5": self._round_value(best_row["pm2_5"]),
            "pm10": self._round_value(best_row["pm10"]),
            "overall_quality": self._get_pm25_category(best_row["pm2_5"]),
        }

    def _get_hourly_breakdown(self, hourly_data: pd.DataFrame) -> List[Dict]:
        """Create detailed hourly breakdown."""
        return [
            {
                "time": self._format_timestamp(row["time"]),
                "pm2_5": {
                    "value": self._round_value(row.get("pm2_5")),
                    "category": self._get_pm25_category(row.get("pm2_5")),
                },
                "pm10": {
                    "value": self._round_value(row.get("pm10")),
                    "category": self._get_pm10_category(row.get("pm10")),
                },
                "ozone": self._round_value(row.get("ozone")),
                "nitrogen_dioxide": self._round_value(row.get("nitrogen_dioxide")),
                "sulphur_dioxide": self._round_value(row.get("sulphur_dioxide")),
                "carbon_monoxide": self._round_value(row.get("carbon_monoxide")),
                "uv_index": self._round_value(row.get("uv_index"), 1),
                "overall_quality": self._get_pm25_category(row.get("pm2_5")),
            }
            for _, row in hourly_data.iterrows()
        ]

    def _calculate_aqi_from_pollutants(self, row: pd.Series) -> float:
        """Calculate estimated AQI from pollutant concentrations."""
        # Simple weighted average based on major pollutants
        pm25 = row.get("pm2_5", 0) or 0
        pm10 = row.get("pm10", 0) or 0
        ozone = row.get("ozone", 0) or 0

        # Normalize and weight (simplified calculation)
        aqi_estimate = (pm25 * 0.4 + pm10 * 0.3 + ozone * 0.3) * 2
        return max(0, min(500, aqi_estimate))

    def _analyze_aqi_trend(self, hourly_aqi: List[float]) -> str:
        """Analyze AQI trend direction."""
        if len(hourly_aqi) < 6:
            return "STABLE"

        first_quarter = np.mean(hourly_aqi[:6])
        last_quarter = np.mean(hourly_aqi[-6:])

        if last_quarter > first_quarter * 1.1:
            return "DETERIORATING"
        elif last_quarter < first_quarter * 0.9:
            return "IMPROVING"
        else:
            return "STABLE"

    def _find_peak_aqi_period(self, hourly_data: pd.DataFrame) -> Dict[str, Any]:
        """Find period with peak AQI conditions."""
        return self._find_worst_air_quality_period(hourly_data)

    def _find_air_quality_improvement_period(
        self, hourly_data: pd.DataFrame
    ) -> Dict[str, Any]:
        """Find when air quality is expected to improve."""
        return self._find_best_air_quality_period(hourly_data)

    def _get_overall_aqi_category(self, current_data: pd.Series) -> str:
        """Get overall AQI category based on multiple pollutants."""
        pm25_cat = self._get_pm25_category(current_data.get("pm2_5"))
        pm10_cat = self._get_pm10_category(current_data.get("pm10"))

        # Return the worst category
        categories = [
            "GOOD",
            "MODERATE",
            "UNHEALTHY_FOR_SENSITIVE_GROUPS",
            "UNHEALTHY",
            "VERY_UNHEALTHY",
            "HAZARDOUS",
        ]
        pm25_level = categories.index(pm25_cat) if pm25_cat in categories else 0
        pm10_level = categories.index(pm10_cat) if pm10_cat in categories else 0

        return categories[max(pm25_level, pm10_level)]

    def _compare_with_standards(self) -> Dict[str, Any]:
        """Compare current levels with health standards."""
        if self.current_df.empty:
            return {"error": "No data for standards comparison"}

        current = self.current_df.iloc[0]

        return {
            "who_guidelines": {
                "pm2_5": {
                    "current": self._round_value(current.get("pm2_5")),
                    "who_annual_limit": 5,
                    "who_daily_limit": 15,
                    "within_limits": current.get("pm2_5", 0) <= 15,
                },
                "pm10": {
                    "current": self._round_value(current.get("pm10")),
                    "who_annual_limit": 15,
                    "who_daily_limit": 45,
                    "within_limits": current.get("pm10", 0) <= 45,
                },
            },
            "us_epa_standards": {
                "pm2_5": {
                    "current": self._round_value(current.get("pm2_5")),
                    "epa_annual_limit": 12,
                    "within_limits": current.get("pm2_5", 0) <= 12,
                }
            },
        }

    # Health impact assessment methods
    def _get_pm25_health_impact(self, pm25: Optional[float]) -> str:
        if pm25 is None or pd.isna(pm25):
            return "Unknown"
        pm25 = float(pm25)
        if pm25 <= 12:
            return "Low health risk"
        elif pm25 <= 35.4:
            return "Moderate risk - Unusual sensitivity possible"
        elif pm25 <= 55.4:
            return "Increased risk for sensitive groups"
        elif pm25 <= 150.4:
            return "Health alert - Everyone may experience effects"
        else:
            return "Health warnings of emergency conditions"

    def _get_pm10_health_impact(self, pm10: Optional[float]) -> str:
        if pm10 is None or pd.isna(pm10):
            return "Unknown"
        pm10 = float(pm10)
        if pm10 <= 50:
            return "Low health risk"
        elif pm10 <= 154:
            return "Moderate risk"
        elif pm10 <= 254:
            return "Unhealthy for sensitive groups"
        else:
            return "Health alert"

    def _get_ozone_health_impact(self, ozone: Optional[float]) -> str:
        if ozone is None or pd.isna(ozone):
            return "Unknown"
        ozone = float(ozone)
        if ozone <= 50:
            return "Good"
        elif ozone <= 100:
            return "Moderate"
        else:
            return "Poor - Respiratory irritation possible"

    def _get_no2_health_impact(self, no2: Optional[float]) -> str:
        if no2 is None or pd.isna(no2):
            return "Unknown"
        no2 = float(no2)
        if no2 <= 50:
            return "Good"
        elif no2 <= 100:
            return "Moderate"
        else:
            return "Poor - Respiratory effects"

    def _get_so2_health_impact(self, so2: Optional[float]) -> str:
        if so2 is None or pd.isna(so2):
            return "Unknown"
        so2 = float(so2)
        if so2 <= 50:
            return "Good"
        elif so2 <= 100:
            return "Moderate"
        else:
            return "Poor - Respiratory irritation"

    def _get_co_health_impact(self, co: Optional[float]) -> str:
        if co is None or pd.isna(co):
            return "Unknown"
        co = float(co)
        if co <= 5000:
            return "Good"
        elif co <= 10000:
            return "Moderate"
        else:
            return "Poor - Potential health effects"

    def _check_data_freshness(self) -> Dict[str, Any]:
        """Check how fresh the air quality data is."""
        freshness = {"current_data_age": "UNKNOWN", "forecast_currentness": "UNKNOWN"}

        if not self.current_df.empty and "observation_time" in self.current_df.columns:
            obs_time = pd.to_datetime(self.current_df.iloc[0]["observation_time"])
            age_hours = (datetime.now(timezone.utc) - obs_time).total_seconds() / 3600
            freshness["current_data_age"] = f"{self._round_value(age_hours, 1)} hours"

        if not self.hourly_df.empty and "date" in self.hourly_df.columns:
            latest_forecast = self.hourly_df["date"].max()
            freshness["forecast_currentness"] = self._format_timestamp(latest_forecast)

        return freshness
