## data_factory/solarize/main.py
## pkibuka@milky-way.space

import pandas as pd
import numpy as np

from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
from decouple import config


from data_factory.pvwatts.scenario_modelling import ScenarioModelling
from data_factory.pvwatts.base_forecast import FetchNRELData
from data_factory.pvwatts.financials import FinancialMetrics
from data_factory.pvwatts.location_scoring import LocationScorer
from data_factory.pvwatts.seasonal_insights import SeasonalInsights
from data_factory.pvwatts.environmental_impact import EnvironmentalImpact
from data_factory.pvwatts.system_recommendations import SysRecommendations
from data_factory.pvwatts.comparative_analysis import ComparativeAnalysis

import logging


logger = logging.getLogger(__name__)


@dataclass
class SolarLocation:
    lat: float
    lon: float
    name: str = "Somewhere in the Milky Way."


class PVWattsSimulator:
    def __init__(self):
        self.locations = {}

    def add_location(self, name: str, lat: float, lon: float):
        """Add location for analysis"""
        self.locations[name] = SolarLocation(lat, lon, name)

    def generate_report(
        self,
        location_name: str,
        config: Dict,
        system_cost: float = 50000,
        electricity_rate: float = 0.15,
        grid_carbon_intensity: float = 0.4,
    ) -> Dict[str, Any]:
        """Main Unified Method"""
        location = self.locations[location_name]
        nrel_api = FetchNRELData(location=location, system_config=config)

        # Base energy forecast data
        base_data = nrel_api.get_base_forecast()

        # Scenario Modelling
        sm = ScenarioModelling(location)
        scenario_analysis = sm.compare_panel_config()

        # Financial Metrics
        fin = FinancialMetrics(base_data, 20000, 0.4)
        financial_analysis = fin.run_financial_analysis()

        # Location Scoring
        ls = LocationScorer(base_data)
        location_score = ls.calculate_location_score()

        # Seasonal Insights
        sn = SeasonalInsights(base_data)
        seasonal_insights = sn.analyse_seasonal_patterns()

        # Environmental Impact
        en = EnvironmentalImpact(base_data, grid_carbon_intensity=0.4)
        environmental_impact = en.calculate_environmental_impact()

        # System Recommendations
        sr = SysRecommendations(base_data)
        system_recommendations = sr.generate_sys_recommendations()

        # Comparative Analysis (locations)
        ca = ComparativeAnalysis(self.locations, config)
        comparative_analysis = ca.run_comparative_analysis()

        report = {
            "location_info": {
                "name": location.name,
                "coordinates": f"{location.lat}, {location.lon}",
                "report_date": datetime.now().isoformat(),
            },
            "scenario_analysis": scenario_analysis,
            "financial_analysis": financial_analysis,
            "location_score": location_score,
            "seasonal_insights": seasonal_insights,
            "environmental_impact": environmental_impact,
            "system_recommendations": system_recommendations,
            "comparative_analysis": comparative_analysis,
        }

        return report
