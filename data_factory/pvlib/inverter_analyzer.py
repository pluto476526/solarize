class DiodeParametersAnalyzer:
    """
    Analyze diode parameters for system health monitoring.
    """

    def __init__(self, simulation_data: Dict):
        self.diode_params = simulation_data["diode_params"]

    def analyze_diode_health(self) -> Dict:
        """Analyze diode parameters for system health indicators"""
        health_metrics = {}

        for i, array_params in enumerate(self.diode_params):
            # Analyze key diode parameters
            daylight_mask = array_params["i_l"] > 0.1  # Significant light current

            if daylight_mask.any():
                params_daylight = array_params[daylight_mask]

                health_metrics[f"array_{i+1}"] = {
                    "avg_light_current": round(params_daylight["i_l"].mean(), 3),
                    "avg_saturation_current": round(params_daylight["i_o"].mean(), 12),
                    "avg_series_resistance": round(params_daylight["r_s"].mean(), 4),
                    "avg_shunt_resistance": round(params_daylight["r_sh"].mean(), 0),
                    "parameter_stability": round(
                        params_daylight.std().mean()
                        / params_daylight.mean().mean()
                        * 100,
                        1,
                    ),
                }

        return health_metrics
