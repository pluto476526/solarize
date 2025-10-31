## data_factory/solarize/environmental_metrics.py
## pkibuka@milky-way.space

from typing import Dict


class EnvironmentalImpact:
    def __init__(self, base_data: Dict, grid_carbon_intensity: float):
        self.base_data = base_data
        self.GCI = grid_carbon_intensity

    def calculate_environmental_impact(self):
        """Convert energy production to environmental metrics"""
        annual_energy = self.base_data["annual_total"]

        carbon_offset_tons = annual_energy * self.GCI / 1000
        equivalent_trees = int(annual_energy * 0.06)  # approx conversion
        equivalent_cars = annual_energy / 4000  # avg car emissions
        homes_powered = annual_energy / 1000  # avg home consumption
        peak_grid_relief = self.base_data["hourly_data"][
            "ac_power"
        ].max()  # grid support during peaks

        metrics = {
            "annual_carbon_offset_tons": round(carbon_offset_tons, 1),
            "equivalent_trees_planted": equivalent_trees,
            "equivalent_cars_off_road": round(equivalent_cars, 1),
            "homes_powered": round(homes_powered, 1),
            "peak_grid_relief_kw": round(peak_grid_relief, 1),
        }

        return metrics
