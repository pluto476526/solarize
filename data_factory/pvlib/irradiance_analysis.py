class IrradianceAnalyzer:
    """
    Analyze solar irradiance components and their impact on system performance.
    """

    def __init__(self, simulation_data: Dict):
        self.total_irrad = simulation_data["total_irrad"]
        self.weather = simulation_data["weather"]
        self.solar_position = simulation_data["solar_position"]

    def calculate_irradiance_components(self) -> Dict:
        """Analyze the composition of solar irradiance"""
        # Aggregate across all arrays
        poa_global = utils.aggregate_timeseries(self.total_irrad, column="poa_global")
        poa_direct = utils.aggregate_timeseries(self.total_irrad, column="poa_direct")
        poa_diffuse = utils.aggregate_timeseries(self.total_irrad, column="poa_diffuse")

        daylight_mask = poa_global > 10

        if daylight_mask.any():
            total_irrad = poa_global[daylight_mask].sum()
            direct_fraction = (poa_direct[daylight_mask].sum() / total_irrad) * 100
            diffuse_fraction = (poa_diffuse[daylight_mask].sum() / total_irrad) * 100

            # Calculate irradiance variability
            irrad_variability = (
                poa_global[daylight_mask].std() / poa_global[daylight_mask].mean() * 100
            )
        else:
            direct_fraction = diffuse_fraction = irrad_variability = 0

        return {
            "direct_irradiance_fraction_percent": round(direct_fraction, 1),
            "diffuse_irradiance_fraction_percent": round(diffuse_fraction, 1),
            "irradiance_variability_percent": round(irrad_variability, 1),
            "annual_irradiance_kwh_m2": round(
                poa_global.sum() / 1000, 1
            ),  # Convert to kWh/m²
            "peak_irradiance_w_m2": round(poa_global.max(), 1),
        }
