## data_factory/solarize/financials.py
## pkibuka@milky-way.space

from typing import Dict

class FinancialMetrics:
    def __init__(self, data: Dict, initial_cost: float = 20000, electricity_rate: float = 0.15):
        self.data = data
        self.initial_cost = initial_cost
        self.electricity_rate = electricity_rate

    
    def calculate_monthly_savings(self) -> Dict:
        hourly_data = self.data["hourly_data"]
        savings = hourly_data.groupby('month')['ac_power'].sum() * self.electricity_rate
        monthly_savings = {month: round(amt, 2) for month, amt in savings.items()}
        return monthly_savings


    def estimate_incentive_impact(self, annual_savings: float) -> Dict:
        tax_credit = self.initial_cost * 0.30  # Assume 30% federal tax credit
        effective_cost = self.initial_cost - tax_credit
        effective_payback = effective_cost / annual_savings
        
        estimations = {
            'estimated_tax_credit': round(tax_credit, 2),
            'effective_initial_cost': round(effective_cost, 2),
            'effective_payback_years': round(effective_payback, 1)
        }
        return estimations


    def run_financial_analysis(self) -> Dict:
        """Calculate financial metrics"""
        annual_energy = self.data["annual_total"]
        annual_savings = annual_energy * self.electricity_rate

        # Simple financial metrics
        payback_years = self.initial_cost / annual_savings
        twenty_year_savings = (annual_savings * 20) - self.initial_cost
        twenty_year_roi = (twenty_year_savings / self.initial_cost) * 100
        monthly_savings = self.calculate_monthly_savings()
        incentive_impact = self.estimate_incentive_impact(annual_savings=annual_savings)

        metrics = {
            "Initial_costs": self.initial_cost,
            "annual_energy_value": round(annual_savings, 2),
            "simple_payback_years": round(payback_years, 1),
            "20_year_net_savings": round(twenty_year_savings, 2),
            "20_year_ROI_percent": round(twenty_year_roi, 1),
            "monthly_savings_breakdown": monthly_savings,
            "incentive_impact": incentive_impact
        }

        return metrics
