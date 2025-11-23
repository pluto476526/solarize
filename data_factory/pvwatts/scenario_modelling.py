## data_factory/solarize/configurations.py
## pkibuka@milky-way.space

from data_factory.pvwatts.base_forecast import FetchNRELData
import plotly.graph_objects as go
from plotly.offline import plot


class ScenarioModelling:
    def __init__(self, location):
        self.location = location

    def compare_panel_config(self):
        """Compare different panel setups at same location"""
        scenarios = [
            {
                "name": "Standard Residential",
                "tilt": 20,
                "azimuth": 180,
                "system_size": 5,
            },
            {"name": "Optimized Tilt", "tilt": 30, "azimuth": 180, "system_size": 5},
            {"name": "Flat Roof", "tilt": 5, "azimuth": 180, "system_size": 5},
            {"name": "East-Facing", "tilt": 20, "azimuth": 90, "system_size": 5},
            {"name": "West-Facing", "tilt": 20, "azimuth": 270, "system_size": 5},
        ]
        results = []

        for scenario in scenarios:
            nrel_api = FetchNRELData(self.location, scenario)
            data = nrel_api.get_base_forecast()
            annual_kwh = data["annual_total"]

            results.append(
                {
                    "scenario": scenario["name"],
                    "annual_kwh": round(annual_kwh),
                    "efficiency_ratio": round(
                        annual_kwh / (scenario["system_size"] * 365), 2
                    ),
                    "configuration": f"{scenario["tilt"]}° tilt, {scenario["azimuth"]}° azimuth",
                    "percent_of_optional": (
                        round(
                            annual_kwh / max([r["annual_kwh"] for r in results]) * 100
                        )
                        if results
                        else 100
                    ),
                }
            )

        return sorted(results, key=lambda x: x["annual_kwh"], reverse=True)

    def scenario_efficiency_chart(self, scenario_data):
        scenarios = [d["scenario"] for d in scenario_data]
        annual_kwh = [d["annual_kwh"] for d in scenario_data]
        efficiency = [d["efficiency_ratio"] for d in scenario_data]
        percent_opt = [d["percent_of_optional"] for d in scenario_data]

        # Build bubble chart
        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=efficiency,
                y=annual_kwh,
                mode="markers",
                text=scenarios,
                textposition="top center",
                marker=dict(
                    size=[p / 2 for p in percent_opt],  # scale bubble size
                    sizemode="area",
                    color=percent_opt,
                    colorscale="Viridis",
                    showscale=True,
                    line=dict(width=1, color="DarkSlateGrey"),
                ),
                hovertemplate="<b>%{text}</b><br>Efficiency: %{x}<br>Annual kWh: %{y}<br>Optional: %{marker.size}<extra></extra>",
            )
        )

        fig.update_layout(
            xaxis_title="Efficiency Ratio", yaxis_title="Annual kWh", template="plotly_dark"
        )

        efficiency_chart = plot(fig, output_type="div", include_plotlyjs=False)
        return efficiency_chart
