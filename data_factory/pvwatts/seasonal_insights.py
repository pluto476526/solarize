## data_factory/solarize/seasonal_metrics.py
## pkibuka@milky-way.space

from typing import Dict


class SeasonalInsights:
    def __init__(self, base_data: Dict):
        self.base_data = base_data

    def analyse_seasonal_patterns(self):
        """Provide seasonal performance characteristics"""
        hourly_data = self.base_data["hourly_data"]

        monthly_totals = hourly_data.groupby("month")["ac_power"].sum()

        best_month = monthly_totals.idxmax()
        worst_month = monthly_totals.idxmin()

        seasonal_variation = (
            (monthly_totals.max() - monthly_totals.min()) / monthly_totals.max() * 100
        )

        # Peak production day
        daily_totals = hourly_data.groupby(hourly_data["timestamp"].dt.date)[
            "ac_power"
        ].sum()
        best_day = daily_totals.idxmax()
        best_day_production = daily_totals.max()

        metrics = {
            "best_performing_month": int(best_month),
            "worst_performing_month": int(worst_month),
            "seasonal_variation_percent": round(seasonal_variation, 1),
            "summer_winter_ratio": round(
                monthly_totals[6] / monthly_totals[12], 2
            ),  # June/December
            "peak_daily_production": round(best_day_production, 2),
            "peak_production_date": best_day.strftime("%Y-%m-%d"),
            "monthly_breakdown": {
                month: round(energy, 2) for month, energy in monthly_totals.items()
            },
        }

        return metrics
