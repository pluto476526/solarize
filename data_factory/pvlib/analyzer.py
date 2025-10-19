from typing import Dict
import pandas as pd


class Analyzer:
    def __init__(self, simulation_data: Dict):
        self.simulation_data = simulation_data
        self.ac_power = simulation_data['ac_aoi']['ac']  # AC power in watts
        
    def get_rating_description(self, score: float) -> str:
        if score >= 90: return "Excellent"
        elif score >= 80: return "Very Good"
        elif score >= 70: return "Good"
        elif score >= 60: return "Fair"
        else: return "Poor"

    def calculate_annual_production(self) -> float:
        """Calculate total annual energy production in kWh"""
        # Convert from watts to kilowatt-hours
        hourly_energy_kwh = self.ac_power / 1000
        return hourly_energy_kwh.sum()

    def calculate_system_efficiency(self) -> float:
        """Calculate overall system efficiency: AC energy out / Solar energy in"""
        # Get total solar irradiance in the plane of array (W/m²)
        poa_global = self.simulation_data['total_irrad']['poa_global']
        
        # Calculate total solar energy available (assuming 1 m² for relative efficiency)
        total_solar_energy_wh = poa_global.sum()  # W/m² * hours = Wh/m²
        
        # Calculate total AC energy produced (Wh)
        total_ac_energy_wh = self.ac_power.sum()  # W * hours = Wh
        
        if total_solar_energy_wh > 0:
            return (total_ac_energy_wh / total_solar_energy_wh) * 100
        return 0

    def calculate_capacity_factor(self) -> float:
        """Calculate capacity factor based on peak observed power"""
        # Use maximum AC power as indicative of system capacity
        peak_power_kw = self.ac_power.max() / 1000  # Convert to kW
        
        if peak_power_kw > 0:
            annual_energy_kwh = self.calculate_annual_production()
            return (annual_energy_kwh / (peak_power_kw * 8760)) * 100
        return 0

    def calculate_performance_ratio(self) -> float:
        """Calculate performance ratio (actual output / theoretical output)"""
        # Theoretical output based on irradiance and system characteristics
        poa_global = self.simulation_data['total_irrad']['poa_global']
        cell_temp = self.simulation_data['cell_temperature']['temperature']
        
        # Simple theoretical model: power ≈ irradiance * temperature_factor
        # Temperature derating: typically -0.3% to -0.5% per °C above 25°C
        temp_coeff = -0.004  # -0.4% per °C
        temp_correction = 1 + (temp_coeff * (cell_temp - 25))
        
        # Theoretical DC power (simplified)
        theoretical_dc = poa_global * temp_correction
        
        # Compare actual AC to theoretical DC (accounting for inverter efficiency)
        actual_ac = self.ac_power
        
        # Filter only daylight hours for meaningful comparison
        daylight_mask = poa_global > 10  # W/m² threshold for daylight
        if daylight_mask.any():
            pr = (actual_ac[daylight_mask].sum() / theoretical_dc[daylight_mask].sum()) * 100
            return max(0, min(100, pr))  # Bound between 0-100%
        return 0

    def calculate_seasonal_consistency(self) -> float:
        """Calculate how consistent production is across seasons"""
        hourly_energy_kwh = self.ac_power / 1000
        
        if hourly_energy_kwh.index.tz is None:
            hourly_energy_kwh.index = pd.to_datetime(hourly_energy_kwh.index).tz_localize('UTC')
        
        monthly_energy = hourly_energy_kwh.groupby(hourly_energy_kwh.index.month).sum()
        
        if len(monthly_energy) > 0 and monthly_energy.max() > 0:
            # Use coefficient of variation (std/mean) for consistency measure
            cv = monthly_energy.std() / monthly_energy.mean()
            # Convert to score: lower variation = higher score
            return max(0, 100 - (cv * 100))
        return 0

    def calculate_peak_alignment(self) -> float:
        """Calculate how well production aligns with peak solar hours"""
        hourly_energy_kwh = self.ac_power / 1000
        total_energy = hourly_energy_kwh.sum()
        
        if total_energy > 0:
            # Peak solar hours (10 AM to 2 PM local time)
            peak_hours_mask = (hourly_energy_kwh.index.hour >= 10) & (hourly_energy_kwh.index.hour <= 14)
            peak_energy = hourly_energy_kwh[peak_hours_mask].sum()
            return (peak_energy / total_energy) * 100
        return 0

    def calculate_utilization_factor(self) -> float:
        """Calculate what percentage of daylight hours the system produces power"""
        poa_global = self.simulation_data['total_irrad']['poa_global']
        daylight_hours = poa_global > 10  # W/m² threshold
        
        if daylight_hours.any():
            producing_hours = (self.ac_power > 0) & daylight_hours
            return (producing_hours.sum() / daylight_hours.sum()) * 100
        return 0

    def calculate_score(self) -> Dict:
        """Calculate comprehensive solar performance score"""
        
        # Core metrics
        annual_energy = self.calculate_annual_production()
        system_efficiency = self.calculate_system_efficiency()
        capacity_factor = self.calculate_capacity_factor()
        performance_ratio = self.calculate_performance_ratio()
        seasonal_consistency = self.calculate_seasonal_consistency()
        peak_alignment = self.calculate_peak_alignment()
        utilization_factor = self.calculate_utilization_factor()

        # Component scores (normalized)
        efficiency_score = min(100, system_efficiency * 2)  # Scale 0-50% to 0-100
        consistency_score = seasonal_consistency
        performance_score = performance_ratio
        utilization_score = utilization_factor

        # Overall score with balanced weights
        overall_score = (
            efficiency_score * 0.25 +
            consistency_score * 0.25 +
            performance_score * 0.25 +
            utilization_score * 0.25
        )

        rating = self.get_rating_description(overall_score)
        
        return {
            "overall_score": round(overall_score, 1),
            "rating": rating,
            "production_metrics": {
                "annual_energy_kwh": round(annual_energy, 1),
                "capacity_factor_percent": round(capacity_factor, 1),
                "system_efficiency_percent": round(system_efficiency, 1),
                "performance_ratio_percent": round(performance_ratio, 1),
            },
            "component_scores": {
                "efficiency": round(efficiency_score, 1),
                "seasonal_consistency": round(consistency_score, 1),
                "system_performance": round(performance_score, 1),
                "utilization": round(utilization_score, 1),
            },
            "operational_metrics": {
                "peak_alignment_percent": round(peak_alignment, 1),
                "utilization_factor_percent": round(utilization_factor, 1),
            }
        }


