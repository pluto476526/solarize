from typing import Dict, List, Optional
import pvlib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BifacialPVSimulator:
    """Simple simulator for bifacial PV systems."""
    
    def __init__(self, timeframe_params: Dict, location_params: Dict, system_params: Dict, losses_params: Dict):
        """Initialize bifacial PV simulator.

        Args:
            timeframe_params: Dict with 'start' and 'end' for simulation period (e.g., {'start': '2025-01-01', 'end': '2025-12-31'}).
            location_params: Dict with location details (name, lat, lon, alt, tz, albedo).
            system_params: Dict with system config (module, inverter, mount_type, bifaciality, etc.).
            losses_params: Dict with loss parameters (soiling, mismatch, etc.).

        Raises:
            ValueError: If input parameters are invalid.
        """
        # Location parameters
        self.name = location_params["name"]
        self.lat = float(location_params["lat"])
        self.lon = float(location_params["lon"])
        self.alt = float(location_params["alt"])
        self.tz = location_params["tz"]
        self.albedo = float(location_params["albedo"])
        
        # Timeframe parameters
        self.timeframe_params = timeframe_params
        
        # System parameters
        self.mount_type = system_params.get("mount_type", "fixed")
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.bifaciality = float(system_params["bifaciality"])
        self.gcr = float(system_params.get("gcr", 0.4))
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]
        
        # Losses parameters
        self.soiling = float(losses_params.get("soiling", 0))
        self.shading = float(losses_params.get("shading", 0))
        self.mismatch = float(losses_params.get("mismatch", 0))
        self.wiring = float(losses_params.get("wiring", 0))
        self.connections = float(losses_params.get("connections", 0))
        
        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Validate input parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        issues = []
        
        # Validate timeframe
        if not isinstance(self.timeframe_params, dict) or 'start' not in self.timeframe_params or 'end' not in self.timeframe_params:
            issues.append("timeframe_params must be a dict with 'start' and 'end' keys")
        
        # Validate location
        if not (-90 <= self.lat <= 90):
            issues.append(f"Latitude {self.lat} must be between -90 and 90")
        if not (-180 <= self.lon <= 180):
            issues.append(f"Longitude {self.lon} must be between -180 and 180")
        if self.alt < 0:
            issues.append(f"Altitude {self.alt} must be non-negative")
        if not 0 <= self.albedo <= 1:
            issues.append(f"Albedo {self.albedo} must be between 0 and 1")
        
        # Validate system parameters
        if not 0 <= self.bifaciality <= 1:
            issues.append(f"Bifaciality {self.bifaciality} must be between 0 and 1")
        if not 0 <= self.gcr <= 1:
            issues.append(f"GCR {self.gcr} must be between 0 and 1")
        
        # Validate losses
        for param, value in [
            ("soiling", self.soiling), ("shading", self.shading), 
            ("mismatch", self.mismatch), ("wiring", self.wiring), 
            ("connections", self.connections)
        ]:
            if not 0 <= value <= 1:
                issues.append(f"{param} must be between 0 and 1, got {value}")

        if issues:
            logger.error(f"Validation failed: {issues}")
            raise ValueError(f"Input validation failed: {issues}")

    def create_location(self) -> pvlib.location.Location:
        """Create a pvlib Location object.

        Returns:
            pvlib.location.Location: Configured location object.
        """
        return pvlib.location.Location(
            name=self.name,
            latitude=self.lat,
            longitude=self.lon,
            altitude=self.alt,
            tz=self.tz
        )

    def _create_mount(self) -> pvlib.pvsystem.FixedMount:
        """Create fixed mount for bifacial system.

        Returns:
            pvlib.pvsystem.FixedMount: Configured mount object.
        """
        surface_tilt = float(self.system_params.get("surface_tilt", 30))
        surface_azimuth = float(self.system_params.get("surface_azimuth", 180))
        
        if not 0 <= surface_tilt <= 90:
            raise ValueError(f"Surface tilt {surface_tilt} must be between 0 and 90")
        if not 0 <= surface_azimuth <= 360:
            raise ValueError(f"Surface azimuth {surface_azimuth} must be between 0 and 360")
            
        return pvlib.pvsystem.FixedMount(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth
        )

    def simulation_setup(self) -> pvlib.modelchain.ModelChain:
        """Set up the bifacial PV system model chain.

        Returns:
            pvlib.modelchain.ModelChain: Configured model chain for simulation.
        """
        module_params = pvlib.pvsystem.retrieve_sam('cecmod')[self.module]
        module_params['bifaciality'] = self.bifaciality
        module_params['bifacial_ground_clearance'] = self.system_params.get('ground_clearance', 1.0)
        
        inverter_params = pvlib.pvsystem.retrieve_sam('cecinverter')[self.inverter]
        temp_params = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[self.temp_model][self.temp_model_params]
        
        array = pvlib.pvsystem.Array(
            mount=self._create_mount(),
            albedo=self.albedo,
            module_type=self.module_type,
            module_parameters=module_params,
            temperature_model_parameters=temp_params,
            modules_per_string=self.modules_per_string,
            strings=self.strings
        )
        
        system = pvlib.pvsystem.PVSystem(
            arrays=[array],
            inverter_parameters=inverter_params,
            losses_parameters={
                'soiling': self.soiling,
                'shading': self.shading,
                'mismatch': self.mismatch,
                'wiring': self.wiring,
                'connections': self.connections
            }
        )
        
        return pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model="physical",
            spectral_model="no_loss",
            dc_ohmic_model="no_loss",
            bifacial=True
        )

    def format_results(self, results: pvlib.modelchain.ModelChainResults) -> pd.DataFrame:
        """Format simulation results into a DataFrame.

        Args:
            results: ModelChain results object.

        Returns:
            pd.DataFrame: Formatted results with key metrics.
        """
        df = pd.DataFrame({
            'ac_power': results.ac,
            'dc_power': results.dc['p_mp'],
            'ghi': results.weather['ghi'],
            'dni': results.weather['dni'],
            'dhi': results.weather['dhi'],
            'effective_irradiance': results.effective_irradiance,
            'cell_temperature': results.cell_temperature,
            'bifacial_gain': results.dc['p_mp'] / results.dc['p_mp'].mean() if results.dc['p_mp'].mean() > 0 else 0
        })
        df['timestamp'] = df.index
        df.attrs['system_summary'] = self.get_system_summary()
        return df

    def run_simulation(self, weather_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Run bifacial PV system simulation.

        Args:
            weather_data: Optional DataFrame with weather data. If None, uses TMY data.

        Returns:
            pd.DataFrame: Formatted simulation results.

        Raises:
            ValueError: If weather data is invalid or empty.
        """
        logger.info(f"Starting bifacial simulation for {self.name} (lat: {self.lat}, lon: {self.lon})")
        weather_data = weather_data or pvlib.iotools.get_pvgis_tmy(self.lat, self.lon)[0]
        start = pd.to_datetime(self.timeframe_params.get('start'))
        end = pd.to_datetime(self.timeframe_params.get('end'))
        weather_data = weather_data.loc[start:end]
        
        if weather_data.empty:
            logger.error("No weather data available for the specified timeframe")
            raise ValueError("Weather data is empty for the specified timeframe")
        
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        logger.info("Bifacial simulation completed successfully")
        return self.format_results(mc.results)

    def get_system_summary(self) -> Dict:
        """Get a summary of the bifacial system configuration.

        Returns:
            Dict: System configuration details.
        """
        return {
            "system_type": "Bifacial PV System",
            "mount_type": self.mount_type,
            "location": {
                "name": self.name,
                "latitude": self.lat,
                "longitude": self.lon,
                "albedo": self.albedo
            },
            "components": {
                "module": self.module,
                "inverter": self.inverter,
                "bifaciality": self.bifaciality
            },
            "configuration": {
                "modules_per_string": self.modules_per_string,
                "strings": self.strings,
                "temperature_model": self.temp_model,
                "gcr": self.gcr
            }
        }
