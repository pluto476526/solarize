import pandas as pd
from typing import Dict, Tuple, List
from datetime import datetime

class SeasonalAnalyzer:
    def __init__(self, simulation_data: Dict):
        self.simulation_data = simulation_data
        self.ac_power = simulation_data['ac_aoi']['ac']  # AC power in watts
        self.hourly_energy_kwh = self.ac_power / 1000
        
    def calculate_monthly_production(self) -> pd.Series:
        """Calculate monthly energy production in kWh"""
        if self.hourly_energy_kwh.index.tz is None:
            self.hourly_energy_kwh.index = pd.to_datetime(self.hourly_energy_kwh.index).tz_localize('UTC')
        
        return self.hourly_energy_kwh.groupby(self.hourly_energy_kwh.index.month).sum()
    
    def get_best_worst_months(self) -> Tuple[Dict, Dict]:
        """Get best and worst performing months with details"""
        monthly_production = self.calculate_monthly_production()
        
        if monthly_production.empty:
            return {}, {}
        
        best_month_idx = monthly_production.idxmax()
        worst_month_idx = monthly_production.idxmin()
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        best_month = {
            'name': month_names[best_month_idx],
            'production_kwh': round(monthly_production[best_month_idx], 1),
            'month_number': best_month_idx
        }
        
        worst_month = {
            'name': month_names[worst_month_idx],
            'production_kwh': round(monthly_production[worst_month_idx], 1),
            'month_number': worst_month_idx
        }
        
        return best_month, worst_month
    
    def get_peak_hourly_production(self) -> Dict:
        """Get peak hourly production and when it occurred"""
        peak_hour_idx = self.hourly_energy_kwh.idxmax()
        peak_production = self.hourly_energy_kwh.max()
        
        return {
            'production_kwh': round(peak_production, 1),
            'timestamp': peak_hour_idx,
            'date': peak_hour_idx.strftime('%Y-%m-%d'),
            'time': peak_hour_idx.strftime('%H:%M')
        }
    
    def calculate_seasonal_variation(self) -> Dict:
        """Calculate seasonal variation metrics"""
        monthly_production = self.calculate_monthly_production()
        
        if monthly_production.empty:
            return {'variation_percent': 0, 'description': 'No Data'}
        
        max_production = monthly_production.max()
        min_production = monthly_production.min()
        
        if max_production > 0:
            variation_percent = ((max_production - min_production) / max_production) * 100
        else:
            variation_percent = 0
        
        # Categorize variation level
        if variation_percent < 20:
            description = "Low Variation"
            level = "low"
        elif variation_percent < 50:
            description = "Moderate Variation"
            level = "moderate"
        else:
            description = "High Variation"
            level = "high"
        
        return {
            'variation_percent': round(variation_percent, 1),
            'description': description,
            'level': level,
            'max_min_ratio': round(max_production / min_production, 2) if min_production > 0 else float('inf')
        }
    
    def get_seasonal_distribution(self) -> Dict[str, float]:
        """Get production distribution by season"""
        seasonal_mapping = {
            12: 'Winter', 1: 'Winter', 2: 'Winter',
            3: 'Spring', 4: 'Spring', 5: 'Spring',
            6: 'Summer', 7: 'Summer', 8: 'Summer',
            9: 'Fall', 10: 'Fall', 11: 'Fall'
        }
        
        monthly_production = self.calculate_monthly_production()
        seasonal_production = {}
        
        for month, production in monthly_production.items():
            season = seasonal_mapping[month]
            seasonal_production[season] = seasonal_production.get(season, 0) + production
        
        total_annual = sum(seasonal_production.values())
        
        if total_annual > 0:
            return {season: round((prod / total_annual) * 100, 1) 
                   for season, prod in seasonal_production.items()}
        return {}
    
    def get_monthly_efficiency(self) -> Dict:
        """Calculate monthly system efficiency"""
        monthly_efficiency = {}
        poa_global = self.simulation_data['total_irrad']['poa_global']
        
        if poa_global.index.tz is None:
            poa_global.index = pd.to_datetime(poa_global.index).tz_localize('UTC')
        
        # Group by month for both AC power and irradiance
        monthly_ac = self.ac_power.groupby(self.ac_power.index.month).sum()
        monthly_irradiance = poa_global.groupby(poa_global.index.month).sum()
        
        for month in monthly_ac.index:
            if monthly_irradiance.get(month, 0) > 0:
                efficiency = (monthly_ac[month] / monthly_irradiance[month]) * 100
                monthly_efficiency[month] = round(efficiency, 1)
        
        return monthly_efficiency
    
    def calculate_productivity_metrics(self) -> Dict:
        """Calculate various productivity metrics"""
        monthly_production = self.calculate_monthly_production()
        annual_production = monthly_production.sum()
        
        if len(monthly_production) > 0:
            avg_monthly = annual_production / len(monthly_production)
            monthly_std = monthly_production.std()
            cv = (monthly_std / avg_monthly * 100) if avg_monthly > 0 else 0
        else:
            avg_monthly = 0
            cv = 0
        
        return {
            'annual_production_kwh': round(annual_production, 1),
            'average_monthly_kwh': round(avg_monthly, 1),
            'monthly_coefficient_variation': round(cv, 1),
            'production_months': len(monthly_production[monthly_production > 0])
        }
    
    def get_seasonal_insights(self) -> List[str]:
        """Generate seasonal performance insights"""
        insights = []
        seasonal_dist = self.get_seasonal_distribution()
        variation = self.calculate_seasonal_variation()
        
        if not seasonal_dist:
            return insights
        
        # Find dominant season
        dominant_season = max(seasonal_dist.items(), key=lambda x: x[1])
        weakest_season = min(seasonal_dist.items(), key=lambda x: x[1])
        
        insights.append(f"Peak production occurs in {dominant_season[0]} ({dominant_season[1]}% of annual output)")
        insights.append(f"Lowest production in {weakest_season[0]} ({weakest_season[1]}% of annual output)")
        
        if variation['level'] == 'low':
            insights.append("Seasonal consistency is excellent with minimal variation throughout the year")
        elif variation['level'] == 'moderate':
            insights.append("Moderate seasonal variation - system performs well across most seasons")
        else:
            insights.append("High seasonal variation - consider this for energy storage planning")
        
        # Check for seasonal patterns
        summer_percent = seasonal_dist.get('Summer', 0)
        winter_percent = seasonal_dist.get('Winter', 0)
        
        if summer_percent > winter_percent * 1.5:
            insights.append("System shows strong summer performance characteristic of this location")
        
        return insights
    
    def generate_seasonal_report(self) -> Dict:
        """Generate comprehensive seasonal performance report"""
        best_month, worst_month = self.get_best_worst_months()
        peak_hourly = self.get_peak_hourly_production()
        variation = self.calculate_seasonal_variation()
        productivity = self.calculate_productivity_metrics()
        seasonal_dist = self.get_seasonal_distribution()
        monthly_efficiency = self.get_monthly_efficiency()
        insights = self.get_seasonal_insights()
        
        return {
            'best_month': best_month,
            'worst_month': worst_month,
            'peak_hourly': peak_hourly,
            'seasonal_variation': variation,
            'seasonal_distribution': seasonal_dist,
            'productivity_metrics': productivity,
            'monthly_efficiency': monthly_efficiency,
            'insights': insights,
            'monthly_production': {
                month: round(prod, 1) for month, prod in self.calculate_monthly_production().items()
            }
        }


# Usage example:
def analyze_seasonal_performance(simulation_data: Dict) -> Dict:
    """Convenience function to analyze seasonal performance"""
    analyzer = SeasonalAnalyzer(simulation_data)
    return analyzer.generate_seasonal_report()
