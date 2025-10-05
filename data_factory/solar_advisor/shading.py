## data_factory/solarize/shading.py
## pkibuka@milky-way.space


class ShadingAnalyzer:
    def analyze_shading_impact(self, lat, lon, obstructions):
        """
        obstructions: list of {'height_m': 10, 'distance_m': 15, 'direction_deg': 45}
        """
        hourly_impact = []

        for hour in range(24):
            sun_position = self.calculate_sun_position(lat, lon, hour)
            shading_loss = 0

            for obstacle in obstructions:
                if self.is_shading(sun_position, obstacle):
                    shading_loss += self.calculate_shading_percentage(sun_position, obstacle)

            # Apply shading to theoretical production
            ideal_production = self.get_hourly_production(lat, lon, hour)
            actual_production = ideal_production * (1 - min(shading_loss, 1))

            hourly_impact.append({
                'hour': hour,
                'shading_loss_percent': shading_loss * 100,
                'production_with_shading': actual_production
            })

        annual_loss = sum([h['shading_loss_percent'] for h in hourly_impact]) / len(hourly_impact)
        return {'hourly_analysis': hourly_impact, 'average_annual_loss_percent': annual_loss}
