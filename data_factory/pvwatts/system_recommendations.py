## data_factory/solarize/system_recommendations.py
## pkibuka@milky-way.space

from typing import Dict, List


class SysRecommendations:
    def __init__(self, base_data: Dict):
        self.base_data = base_data

    def calculate_optimal_tilt(self) -> float:
        # Simple rule: optimal tilt ≈ latitude for year-round production
        location = self.base_data["location"]
        return round(location.lat)

    def suggest_system_size(self) -> float:
        # Simple recommendation based on annual production potential
        annual_kwh = self.base_data["annual_total"]

        if annual_kwh > 7000:
            return 8.0
        elif annual_kwh > 5000:
            return 6.0
        else:
            return 4.0

    def assess_battery_needs(self) -> str:
        # Simple assessment based on evening production
        hourly_data = self.base_data["hourly_data"]
        evening_production = hourly_data[hourly_data["hour"].between(17, 21)][
            "ac_power"
        ].mean()

        if evening_production < 0.1:
            return "High - Low evening production"
        elif evening_production < 0.3:
            return "Medium - Moderate evening production"
        else:
            return "Low - Good evening production"

    def generate_maintenance_schedule(self) -> List[str]:
        # Basic maintenance recommendations
        return [
            "Clean panels quarterly in dusty areas",
            "Annual professional inspection recommended",
            "Monitor production monthly for degradation",
            "Trim vegetation seasonally to prevent shading",
        ]

    def generate_sys_recommendations(self):
        """Optimal system recommendations"""
        optimal_tilt = self.calculate_optimal_tilt()
        recommended_sys_size = self.suggest_system_size()
        battery_recommendation = self.assess_battery_needs()
        maintenance_schedule = self.generate_maintenance_schedule()

        system = {
            "recommended_system_size_kw": recommended_sys_size,
            "optimal_tilt_angle": optimal_tilt,
            "optimal_azimuth": 180,
            "estimated_annual_production_kwh": round(self.base_data["annual_total"]),
            "battery_sorage_recommendation": battery_recommendation,
            "maintenance_schedule": maintenance_schedule,
        }

        return system
