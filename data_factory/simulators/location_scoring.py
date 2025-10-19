## data_factory/solarize/locations.py
## pkibuka@milky-way.space

from typing import Dict


class LocationScorer:
    def __init__(self, base_data: Dict):
        self.base_data = base_data
        self.hourly_data = base_data["hourly_data"]
        self.capacity_factor = base_data["capacity_factor"]
     

    def get_rating_description(self, score: float) -> str:
        if score >= 90: return "Excellent"
        elif score >= 80: return "Very Good"
        elif score >= 70: return "Good"
        elif score >= 60: return "Fair"
        else: return "Poor"


    def calculate_location_score(self):
        """Rank multiple locations by solar potential"""
        ## (0-100 Scale) Normalize annual production to 5000 kWh/kwp
        annual_production_score = min(100, (self.base_data["annual_total"] / 5000) * 100)

        ## Seasonal consistency score (less variation is better)
        monthly_totals = self.hourly_data.groupby("month")["ac_power"].sum()
        seasonal_variation = (monthly_totals.max() - monthly_totals.min()) / monthly_totals.max()
        consistency_score = max(0, 100 - (seasonal_variation * 100))

        ## Peak production alignment with peak demand (afternoon hours)
        peak_hours_production = self.hourly_data[self.hourly_data["hour"].between(12, 18)]["ac_power"].sum()
        peak_alignment_score = (peak_hours_production / self.base_data["annual_total"]) * 100

        overall_score = (
            annual_production_score * 0.4 +
            consistency_score * 0.3 +
            peak_alignment_score * 0.3
        )

        rating = self.get_rating_description(overall_score)
        
        scores = {
            "overall_score": round(overall_score),
            "component_scores": {
                "annual_production": round(annual_production_score),
                "seasonal_consistency": round(consistency_score),
                "peak_alignment": round(peak_alignment_score),
            },
            "rating": rating,
            "capacity_factor_percent": round(self.capacity_factor, 1)
        }

        return scores


