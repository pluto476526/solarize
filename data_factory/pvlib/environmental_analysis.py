from typing import Dict
import pandas as pd
from data_factory.pvlib import utils


class EnvironmentalAnalyzer:
    """
    Environmental impact analysis for solar PV systems.
    Calculates carbon emissions reduction and other environmental benefits.
    """

    def __init__(
        self, simulation_data: Dict, environmental_params: Optional[Dict] = None
    ):
        """
        Initialize the environmental analyzer with simulation data.

        Args:
            simulation_data: Dictionary containing solar simulation results
            environmental_params: Optional dictionary to override default environmental factors
        """
        # Extract AC power data from simulation
        self.ac_power = utils.aggregate_timeseries(
            simulation_data["ac_aoi"], column="ac"
        )

        # Set default environmental parameters (US averages)
        self.params = {
            # Carbon emissions factors (varies by grid region)
            "grid_carbon_intensity": 0.385,  # kg CO2 per kWh (US average)
            "lifecycle_carbon_intensity": 0.045,  # kg CO2 per kWh for solar manufacturing
            # Environmental equivalents
            "co2_per_gallon_gasoline": 8.887,  # kg CO2 per gallon
            "co2_per_mile_avg_car": 0.404,  # kg CO2 per mile (average car)
            "annual_co2_per_car": 4600,  # kg CO2 per car per year
            "co2_sequestered_per_tree": 21.77,  # kg CO2 per tree per year
            # Pollution factors
            "so2_per_kwh_grid": 0.0012,  # kg SO2 per kWh (sulfur dioxide)
            "nox_per_kwh_grid": 0.0015,  # kg NOx per kWh (nitrogen oxides)
            "pm25_per_kwh_grid": 0.0001,  # kg PM2.5 per kWh (particulate matter)
            # Water usage factors
            "water_use_thermo_kwh": 0.0016,  # m³ water per kWh for thermoelectric
            "water_use_solar_kwh": 0.0001,  # m³ water per kWh for solar (cleaning)
        }

        # Update with user-provided parameters
        if environmental_params:
            self.params.update(environmental_params)

        # Calculate annual energy production
        self.annual_energy_kwh = self._calculate_annual_energy()

    def _calculate_annual_energy(self) -> float:
        """
        Calculate total annual energy production from AC power data.

        Returns:
            Annual energy production in kilowatt-hours (kWh)
        """
        hourly_energy_kwh = self.ac_power / 1000
        return hourly_energy_kwh.sum()

    def calculate_carbon_reduction(self) -> Dict:
        """
        Calculate annual carbon dioxide reduction from solar generation.

        Returns:
            Dictionary with various CO2 reduction metrics and equivalents
        """
        # Net CO2 reduction accounts for lifecycle emissions of solar panels
        gross_co2_reduction = (
            self.annual_energy_kwh * self.params["grid_carbon_intensity"]
        )
        solar_lifecycle_emissions = (
            self.annual_energy_kwh * self.params["lifecycle_carbon_intensity"]
        )
        net_co2_reduction = gross_co2_reduction - solar_lifecycle_emissions

        # Calculate environmental equivalents
        equivalent_gallons_gasoline = (
            net_co2_reduction / self.params["co2_per_gallon_gasoline"]
        )
        equivalent_cars_removed = net_co2_reduction / self.params["annual_co2_per_car"]
        equivalent_trees_planted = (
            net_co2_reduction / self.params["co2_sequestered_per_tree"]
        )
        equivalent_miles_driven = (
            net_co2_reduction / self.params["co2_per_mile_avg_car"]
        )

        return {
            "gross_co2_reduction_kg": round(gross_co2_reduction, 1),
            "solar_lifecycle_emissions_kg": round(solar_lifecycle_emissions, 1),
            "net_co2_reduction_kg": round(net_co2_reduction, 1),
            "net_co2_reduction_tons": round(net_co2_reduction / 1000, 2),
            "equivalent_gallons_gasoline": round(equivalent_gallons_gasoline, 1),
            "equivalent_cars_removed": round(equivalent_cars_removed, 2),
            "equivalent_trees_planted": round(equivalent_trees_planted, 1),
            "equivalent_miles_driven": round(equivalent_miles_driven, 1),
        }

    def calculate_air_pollution_reduction(self) -> Dict:
        """
        Calculate reduction in air pollutants by displacing grid electricity.

        Returns:
            Dictionary with reductions in major air pollutants
        """
        so2_reduction = self.annual_energy_kwh * self.params["so2_per_kwh_grid"]
        nox_reduction = self.annual_energy_kwh * self.params["nox_per_kwh_grid"]
        pm25_reduction = self.annual_energy_kwh * self.params["pm25_per_kwh_grid"]

        return {
            "sulfur_dioxide_reduction_kg": round(so2_reduction, 3),
            "nitrogen_oxides_reduction_kg": round(nox_reduction, 3),
            "particulate_matter_reduction_kg": round(pm25_reduction, 4),
        }

    def calculate_water_savings(self) -> Dict:
        """
        Calculate water savings from reduced thermoelectric power generation.

        Returns:
            Dictionary with water savings metrics
        """
        # Water that would have been used for thermoelectric power generation
        water_saved_thermo = (
            self.annual_energy_kwh * self.params["water_use_thermo_kwh"]
        )

        # Water used for solar panel maintenance (cleaning)
        water_used_solar = self.annual_energy_kwh * self.params["water_use_solar_kwh"]

        # Net water savings
        net_water_savings = water_saved_thermo - water_used_solar

        return {
            "water_saved_thermo_m3": round(water_saved_thermo, 2),
            "water_used_solar_m3": round(water_used_solar, 3),
            "net_water_savings_m3": round(net_water_savings, 2),
            "net_water_savings_gallons": round(
                net_water_savings * 264.172, 1
            ),  # Convert to gallons
        }

    def calculate_lifetime_environmental_impact(self) -> Dict:
        """
        Calculate total environmental impact over the system's 25-year lifetime.

        Returns:
            Dictionary with lifetime environmental benefits
        """
        system_lifetime_years = 25
        degradation_rate = 0.005  # 0.5% annual degradation

        # Calculate cumulative energy production over system lifetime
        cumulative_energy = 0
        for year in range(system_lifetime_years):
            annual_degradation = (1 - degradation_rate) ** year
            cumulative_energy += self.annual_energy_kwh * annual_degradation

        # Calculate lifetime emissions reduction
        lifetime_co2_reduction = cumulative_energy * (
            self.params["grid_carbon_intensity"]
            - self.params["lifecycle_carbon_intensity"]
        )

        return {
            "lifetime_energy_production_kwh": round(cumulative_energy, 1),
            "lifetime_co2_reduction_tons": round(lifetime_co2_reduction / 1000, 1),
            "equivalent_lifetime_cars_removed": round(
                lifetime_co2_reduction
                / self.params["annual_co2_per_car"]
                / system_lifetime_years,
                1,
            ),
        }

    def _get_environmental_rating(self, score: float) -> str:
        """
        Categorize environmental performance based on score.

        Args:
            score: Environmental score (0-100)

        Returns:
            Descriptive rating string
        """
        if score >= 90:
            return "Exceptional"
        elif score >= 80:
            return "Excellent"
        elif score >= 70:
            return "Very Good"
        elif score >= 60:
            return "Good"
        elif score >= 50:
            return "Fair"
        else:
            return "Poor"

    def calculate_score(self) -> Dict:
        """
        Calculate comprehensive environmental performance score and metrics.

        Returns:
            Dictionary containing all environmental analysis results
        """
        # Calculate all environmental metrics
        carbon_reduction = self.calculate_carbon_reduction()
        air_pollution_reduction = self.calculate_air_pollution_reduction()
        water_savings = self.calculate_water_savings()
        lifetime_impact = self.calculate_lifetime_environmental_impact()

        # Calculate component scores (normalized to 0-100)
        # Carbon score based on net CO2 reduction per kW of system
        system_size_kw = self.ac_power.max() / 1000
        co2_per_kw = carbon_reduction["net_co2_reduction_kg"] / system_size_kw
        carbon_score = min(
            100, co2_per_kw / 500 * 100
        )  # Scale based on 500 kg/kW-year target

        # Air quality score based on pollutant reduction
        total_pollutant_reduction = (
            air_pollution_reduction["sulfur_dioxide_reduction_kg"]
            + air_pollution_reduction["nitrogen_oxides_reduction_kg"]
            * 10  # Weight NOx more heavily
            + air_pollution_reduction["particulate_matter_reduction_kg"]
            * 100  # Weight PM2.5 most heavily
        )
        air_quality_score = min(100, total_pollutant_reduction * 1000)

        # Water savings score
        water_score = min(100, water_savings["net_water_savings_m3"] * 10)

        # Overall environmental score
        overall_score = (
            carbon_score * 0.50  # Carbon reduction weight: 50%
            + air_quality_score * 0.30  # Air quality weight: 30%
            + water_score * 0.20  # Water savings weight: 20%
        )

        environmental_rating = self._get_environmental_rating(overall_score)

        return {
            "overall_environmental_score": round(overall_score, 1),
            "environmental_rating": environmental_rating,
            "carbon_reduction": carbon_reduction,
            "air_pollution_reduction": air_pollution_reduction,
            "water_savings": water_savings,
            "lifetime_impact": lifetime_impact,
            "component_scores": {
                "carbon_reduction_score": round(carbon_score, 1),
                "air_quality_score": round(air_quality_score, 1),
                "water_savings_score": round(water_score, 1),
            },
            "environmental_assumptions": self.params,
        }
