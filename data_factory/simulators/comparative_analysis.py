## data_factory/solarize/comparative_analysis.py
## pkibuka@milky-way.space

from data_factory.simulators.base_forecast import FetchNRELData
from data_factory.simulators.location_scoring import LocationScorer

from typing import Dict

class ComparativeAnalysis:
    def __init__(self, locations, config: Dict):
        self.locations = locations
        self.config = config


    def run_comparative_analysis(self) -> Dict:
        """Compare all added locations"""
        if len(self.locations) < 2:
            return {'message': 'Add multiple locations for comparative analysis'}

        comparisons = []
        for name, location in self.locations.items():

            nrel_api = FetchNRELData(location, system_config=self.config)
            base_data = nrel_api.get_base_forecast()
            
            ls = LocationScorer(base_data)
            score = ls.calculate_location_score()

            comparisons.append({
                'location_name': name,
                'coordinates': f"{location.lat}, {location.lon}",
                'annual_potential_kwh': round(base_data['annual_total']),
                'solar_score': score['overall_score'],
                'ranking': len([l for l in comparisons if l['solar_score'] > score['overall_score']]) + 1
            })

        return sorted(comparisons, key=lambda x: x['solar_score'], reverse=True)
