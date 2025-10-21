from typing import Dict, Optional
import pandas as pd
import numpy as np
from data_factory.pvlib import utils

class FinancialAnalyzer:
    """
    Comprehensive financial analysis for solar PV systems.
    Calculates key financial metrics including ROI, payback period, NPV, and LCOE.
    """
    
    def __init__(self, simulation_data: Dict, financial_params: Optional[Dict] = None):
        """
        Initialize the financial analyzer with simulation data and financial parameters.
        
        Args:
            simulation_data: Dictionary containing solar simulation results
            financial_params: Optional dictionary to override default financial assumptions
        """
        # Extract AC power data from simulation results
        self.ac_power = utils.aggregate_timeseries(simulation_data['ac_aoi'], column='ac')
        
        # Set default financial parameters (typical US residential solar values)
        self.params = {
            # System cost assumptions
            'system_cost_per_watt': 2.50,  # Average cost per watt for residential systems
            'installation_cost': 0.00,     # Additional fixed installation costs
            'inverter_replacement_cost': 0.00,  # Cost to replace inverter during system life
            
            # Energy pricing and escalation
            'electricity_rate': 0.15,      # Current retail electricity rate ($/kWh)
            'escalation_rate': 0.025,      # Annual electricity price inflation rate (2.5%)
            
            # Government incentives and rebates
            'tax_credit_rate': 0.30,       # Federal Investment Tax Credit (30%)
            'state_rebate': 0.00,          # Additional state/local rebates
            'net_metering_value': 0.12,    # Value of exported energy ($/kWh)
            
            # System performance and lifetime
            'system_lifetime_years': 25,   # Expected system operational lifetime
            'inverter_replacement_year': 15,  # Year when inverter typically needs replacement
            'degradation_rate': 0.005,     # Annual power output degradation (0.5%)
            
            # Operational expenses
            'annual_maintenance_cost': 200,  # Routine maintenance costs ($/year)
            'insurance_cost_per_year': 150,  # System insurance ($/year)
            
            # Financial analysis parameters
            'discount_rate': 0.06,         # Discount rate for NPV calculations (6%)
        }
        
        # Update default parameters with user-provided values
        if financial_params:
            self.params.update(financial_params)
        
        # Calculate derived system characteristics
        self.system_size_kw = self.ac_power.max() / 1000  # Convert peak power to kW
        self.total_system_cost = self._calculate_total_system_cost()
        self.annual_energy_kwh = self._calculate_annual_energy()

    def _calculate_total_system_cost(self) -> float:
        """
        Calculate total installed cost of the solar system.
        
        Returns:
            Total system cost in dollars
        """
        # Base cost = system size (watts) × cost per watt
        base_cost = self.system_size_kw * 1000 * self.params['system_cost_per_watt']
        # Add any additional installation costs
        total_cost = base_cost + self.params['installation_cost']
        return total_cost

    def _calculate_annual_energy(self) -> float:
        """
        Calculate total annual energy production from AC power data.
        
        Returns:
            Annual energy production in kilowatt-hours (kWh)
        """
        # Convert hourly power (watts) to hourly energy (kWh) and sum for the year
        hourly_energy_kwh = self.ac_power / 1000
        return hourly_energy_kwh.sum()

    def calculate_simple_payback(self) -> float:
        """
        Calculate simple payback period without considering time value of money.
        
        Returns:
            Payback period in years. Returns infinity if no savings.
        """
        # Annual energy cost savings = energy produced × electricity rate
        annual_savings = self.annual_energy_kwh * self.params['electricity_rate']
        
        # Net system cost after incentives and rebates
        incentive_adjustment = self.params['tax_credit_rate'] + self.params['state_rebate']
        net_system_cost = self.total_system_cost * (1 - incentive_adjustment)
        
        # Calculate payback period
        if annual_savings > 0:
            return net_system_cost / annual_savings
        return float('inf')

    def calculate_net_present_value(self) -> float:
        """
        Calculate Net Present Value (NPV) of the solar investment.
        NPV represents the present value of all future cash flows.
        
        Returns:
            NPV in dollars. Positive NPV indicates profitable investment.
        """
        # Initial net system cost (negative cash flow)
        incentive_adjustment = self.params['tax_credit_rate'] + self.params['state_rebate']
        net_system_cost = self.total_system_cost * (1 - incentive_adjustment)
        npv = -net_system_cost
        
        # Calculate cash flows for each year of system lifetime
        for year in range(1, self.params['system_lifetime_years'] + 1):
            # Apply annual degradation to energy production
            degradation_factor = (1 - self.params['degradation_rate']) ** (year - 1)
            degraded_energy = self.annual_energy_kwh * degradation_factor
            
            # Apply electricity price escalation
            escalation_factor = (1 + self.params['escalation_rate']) ** (year - 1)
            escalated_rate = self.params['electricity_rate'] * escalation_factor
            
            # Calculate annual energy savings
            year_savings = degraded_energy * escalated_rate
            
            # Subtract annual operational costs
            operational_costs = (self.params['annual_maintenance_cost'] + 
                               self.params['insurance_cost_per_year'])
            year_net_cash_flow = year_savings - operational_costs
            
            # Account for inverter replacement in specified year
            if year == self.params['inverter_replacement_year']:
                year_net_cash_flow -= self.params['inverter_replacement_cost']
            
            # Discount future cash flow to present value
            discount_factor = (1 + self.params['discount_rate']) ** year
            discounted_cash_flow = year_net_cash_flow / discount_factor
            npv += discounted_cash_flow
        
        return npv

    def calculate_internal_rate_of_return(self) -> float:
        """
        Calculate Internal Rate of Return (IRR) - the annualized effective return rate.
        Simplified calculation using average annual returns.
        
        Returns:
            IRR as a percentage
        """
        try:
            # Calculate average annual savings
            annual_savings = self.annual_energy_kwh * self.params['electricity_rate']
            
            # Calculate net system cost after incentives
            incentive_adjustment = self.params['tax_credit_rate'] + self.params['state_rebate']
            net_system_cost = self.total_system_cost * (1 - incentive_adjustment)
            
            # Simplified IRR calculation (average annual return / initial investment)
            avg_annual_return = annual_savings / net_system_cost
            return avg_annual_return * 100  # Convert to percentage
            
        except ZeroDivisionError:
            return 0.0

    def calculate_levelized_cost_of_energy(self) -> float:
        """
        Calculate Levelized Cost of Energy (LCOE).
        LCOE represents the average cost per kWh over the system lifetime.
        
        Returns:
            LCOE in dollars per kWh
        """
        total_lifetime_cost = 0
        total_lifetime_energy = 0
        
        # Initial investment (net of incentives)
        incentive_adjustment = self.params['tax_credit_rate'] + self.params['state_rebate']
        total_lifetime_cost += self.total_system_cost * (1 - incentive_adjustment)
        
        # Calculate costs and energy production for each year
        for year in range(1, self.params['system_lifetime_years'] + 1):
            # Annual operational costs
            year_cost = (self.params['annual_maintenance_cost'] + 
                        self.params['insurance_cost_per_year'])
            
            # Add inverter replacement cost in specified year
            if year == self.params['inverter_replacement_year']:
                year_cost += self.params['inverter_replacement_cost']
            
            # Discount costs to present value
            discounted_cost = year_cost / ((1 + self.params['discount_rate']) ** year)
            total_lifetime_cost += discounted_cost
            
            # Calculate energy production with degradation
            degradation_factor = (1 - self.params['degradation_rate']) ** (year - 1)
            year_energy = self.annual_energy_kwh * degradation_factor
            
            # Discount energy to present value (energy today is more valuable)
            discounted_energy = year_energy / ((1 + self.params['discount_rate']) ** year)
            total_lifetime_energy += discounted_energy
        
        # LCOE = total lifetime cost / total lifetime energy
        if total_lifetime_energy > 0:
            return total_lifetime_cost / total_lifetime_energy
        return float('inf')

    def calculate_annual_cash_flows(self) -> Dict:
        """
        Calculate detailed annual cash flows for the first 5 years.
        Useful for understanding short-term financial performance.
        
        Returns:
            Dictionary with detailed cash flow analysis for years 1-5
        """
        cash_flows = {}
        
        for year in range(1, 6):  # Analyze first 5 years
            # Apply system degradation to energy production
            degradation_factor = (1 - self.params['degradation_rate']) ** (year - 1)
            degraded_energy = self.annual_energy_kwh * degradation_factor
            
            # Apply electricity price escalation
            escalation_factor = (1 + self.params['escalation_rate']) ** (year - 1)
            escalated_rate = self.params['electricity_rate'] * escalation_factor
            
            # Calculate annual energy cost savings
            annual_savings = degraded_energy * escalated_rate
            
            # Total operational costs
            operational_costs = (self.params['annual_maintenance_cost'] + 
                               self.params['insurance_cost_per_year'])
            
            # Net annual cash flow (savings minus costs)
            net_cash_flow = annual_savings - operational_costs
            
            cash_flows[f'year_{year}'] = {
                'energy_production_kwh': round(degraded_energy, 1),
                'electricity_rate': round(escalated_rate, 3),
                'annual_savings': round(annual_savings, 2),
                'operational_costs': round(operational_costs, 2),
                'net_cash_flow': round(net_cash_flow, 2)
            }
        
        return cash_flows

    def _get_roi_rating(self, roi: float) -> str:
        """
        Categorize the return on investment based on percentage.
        
        Args:
            roi: Return on investment as a percentage
            
        Returns:
            Descriptive rating string
        """
        if roi >= 20: return "Excellent"
        elif roi >= 15: return "Very Good"
        elif roi >= 10: return "Good"
        elif roi >= 5: return "Fair"
        else: return "Poor"

    def calculate_score(self) -> Dict:
        """
        Calculate comprehensive financial performance score and metrics.
        
        Returns:
            Dictionary containing all financial analysis results with scores and ratings
        """
        # Calculate core financial metrics
        simple_payback = self.calculate_simple_payback()
        npv = self.calculate_net_present_value()
        irr = self.calculate_internal_rate_of_return()
        lcoe = self.calculate_levelized_cost_of_energy()
        
        # Calculate component scores (normalized to 0-100 scale)
        # Payback score: shorter payback = higher score (0-20 years maps to 100-0)
        payback_score = max(0, min(100, (20 - simple_payback) * 10)) if simple_payback != float('inf') else 0
        
        # NPV score: positive NPV = good, scaled by system cost
        npv_score = max(0, min(100, npv / self.total_system_cost * 100)) if npv > 0 else 0
        
        # IRR score: higher return = higher score (0-50% maps to 0-100)
        irr_score = min(100, irr * 2)
        
        # LCOE score: lower than grid electricity = better (compared to $0.30/kWh)
        lcoe_score = max(0, min(100, (0.30 - lcoe) * 500)) if lcoe != float('inf') else 0

        # Calculate overall financial score with weighted components
        overall_score = (
            payback_score * 0.30 +    # Payback period weight: 30%
            npv_score * 0.25 +        # NPV weight: 25%
            irr_score * 0.25 +        # IRR weight: 25%
            lcoe_score * 0.20         # LCOE weight: 20%
        )

        # Get ROI rating category
        roi_rating = self._get_roi_rating(irr)
        
        # Calculate additional analyses
        cash_flows = self.calculate_annual_cash_flows()
        
        return {
            "overall_financial_score": round(overall_score, 1),
            "roi_rating": roi_rating,
            "key_metrics": {
                "simple_payback_years": round(simple_payback, 1),
                "net_present_value": round(npv, 2),
                "internal_rate_of_return_percent": round(irr, 1),
                "levelized_cost_of_energy": round(lcoe, 3),
                "system_cost": round(self.total_system_cost, 2),
                "system_size_kw": round(self.system_size_kw, 2),
                "annual_energy_production_kwh": round(self.annual_energy_kwh, 1),
                "annual_energy_savings": round(self.annual_energy_kwh * self.params['electricity_rate'], 2),
            },
            "component_scores": {
                "payback_period_score": round(payback_score, 1),
                "npv_score": round(npv_score, 1),
                "irr_score": round(irr_score, 1),
                "lcoe_score": round(lcoe_score, 1),
            },
            "cash_flow_analysis": cash_flows,
            "financial_assumptions": {
                k: v for k, v in self.params.items() if not isinstance(v, dict)
            }
        }
