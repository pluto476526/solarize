from typing import Dict, List, Optional, Union
import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils

logger = logging.getLogger(__name__)

class SpecSheetSimulator:
    """Advanced PV system simulator for fixed and tracking systems."""
    
    def __init__(self, timeframe_params, location_params, system_params, losses_params):
        """Initialize the PV simulator with system, location, and loss parameters.

        Args:
            timeframe_params: Dictionary with 'start' and 'end' for simulation period (e.g., {'start': '2025-01-01', 'end': '2025-12-31'}).
            location_params: Dictionary with location details (name, lat, lon, alt, tz, albedo).
            system_params: Dictionary with system configuration (module, inverter, mount_type, etc.).
            losses_params: Dictionary with loss parameters (soiling, shading, etc.).

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
        
        # Mount configuration
        self.mount_type = "fixed"
        self.mount_config = {}
        
        # System parameters
        self.module_type = system_params.get("module_type") # glass_glass, glass_polymer
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.arrays = system_params.get("arrays_config", [])
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]

        # Custom component parameters
        self.custom_module_params = system_params.get("module_params")
        self.custom_inverter_params = system_params.get("inverter_params")
        self.custom_temp_params = system_params.get("temp_params")

        # Losses parameters
        self.soiling = float(losses_params.get("soiling", 0))
        self.shading = float(losses_params.get("shading", 0))
        self.snow = float(losses_params.get("snow", 0))
        self.mismatch = float(losses_params.get("mismatch", 0))
        self.wiring = float(losses_params.get("wiring", 0))
        self.connections = float(losses_params.get("connections", 0))
        self.lid = float(losses_params.get("lid", 0))
        self.nameplate = float(losses_params.get("nameplate", 0))
        self.age = float(losses_params.get("age", 0))
        self.availability = float(losses_params.get("availability", 0))


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

    def _get_temperature_parameters(self) -> Dict:
        """Get temperature model parameters.

        Returns:
            Dict: Temperature model parameters, custom or standard.
        """
        if self.custom_temp_params:
            return self.custom_temp_params
        return pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[self.temp_model][self.temp_model_params]

    def _create_mount(self, array_config: Dict) -> pvlib.pvsystem.AbstractMount:
        """Create mount based on configuration.

        Args:
            array_config: Dictionary with mount configuration (mount_type, surface_tilt, etc.).

        Returns:
            pvlib.pvsystem.AbstractMount: Configured mount object.

        Raises:
            ValueError: If mount type or parameters are invalid.
        """
        mount_type = array_config.get("mount_type", self.mount_type)
        tracker_config = array_config.get("tracker_config", self.mount_config)

        # Common validation for tilt and azimuth
        surface_tilt = float(array_config.get("surface_tilt", 30))
        surface_azimuth = float(array_config.get("surface_azimuth", 180))
        

        if mount_type == "fixed":
            return pvlib.pvsystem.FixedMount(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth)
        
        elif mount_type == "single_axis":
            axis_tilt = float(tracker_config.get("axis_tilt", 0))
            axis_azimuth = float(tracker_config.get("axis_azimuth", 0))
            max_angle = float(tracker_config.get("max_angle", 90))
            gcr = float(tracker_config.get("gcr", 0.4))
            backtrack = bool(tracker_config.get("backtrack", True))
            
            return pvlib.pvsystem.SingleAxisTrackerMount(
                axis_tilt=axis_tilt,
                axis_azimuth=axis_azimuth,
                max_angle=max_angle,
                backtrack=backtrack,
                gcr=gcr
            )
        
        elif mount_type == "dual_axis":
            axis_tilt = float(tracker_config.get("axis_tilt", 0))
            axis_azimuth = float(tracker_config.get("axis_azimuth", 0))
            max_rotation = float(tracker_config.get("max_rotation", 360))
            
            return pvlib.pvsystem.DualAxisTrackerMount(
                axis_tilt=axis_tilt,
                axis_azimuth=axis_azimuth,
                max_rotation=max_rotation
            )
        
        elif mount_type == "custom" and self.custom_mount_params:
            logger.info("Using custom mount configuration")
            return pvlib.pvsystem.FixedMount(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth)
        
        else:
            logger.error(f"Invalid mount type: {mount_type}")

    def simulation_setup(self) -> pvlib.modelchain.ModelChain:
        """Set up the PV system model chain.

        Returns:
            pvlib.modelchain.ModelChain: Configured model chain for simulation.
        """
        # Retrieve module and inverter parameters
        module_params = self.custom_module_params
        inverter_params = self.custom_inverter_params
        temp_parameters = self._get_temperature_parameters()

        # System-wide losses
        loss_params = pvlib.pvsystem.pvwatts_losses(
            soiling=self.soiling,
            shading=self.shading,
            snow=self.snow,
            mismatch=self.mismatch,
            wiring=self.wiring,
            connections=self.connections,
            lid=self.lid,
            nameplate_rating=self.nameplate,
            age=self.age,
            availability=self.availability
        )

        # Build array configurations
        if not isinstance(self.arrays, list):
            self.arrays = []

        main_array_config = {
            "name": "MainArray",
            "mount_type": self.mount_type,
            "surface_tilt": 30,
            "surface_azimuth": 180,
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo,
            "tracker_config": {},
            "array_losses": {"mismatch": self.mismatch, "wiring": self.wiring}
        }
        self.arrays.append(main_array_config)

        # Build PVLib Array objects
        arrays = []
        for config in self.arrays:
            mount = self._create_mount(config)
            array_losses = config.get("array_losses", {"mismatch": self.mismatch, "wiring": self.wiring})
            albedo = float(config.get("albedo", self.albedo))
            
            arr = pvlib.pvsystem.Array(
                name=config["name"],
                mount=mount,
                albedo=albedo,
                module_type=self.module_type,
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=int(config["modules_per_string"]),
                strings=int(config["strings"]),
                array_losses_parameters=array_losses
            )
            arrays.append(arr)

        # Combine into PVSystem
        system = pvlib.pvsystem.PVSystem(
            arrays=arrays,
            inverter_parameters=inverter_params,
            losses_parameters=loss_params
        )

        # Initialize model chain
        aoi_model = "physical" if self.mount_type in ["single_axis", "dual_axis"] else "ashrae"
        mc = pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model=aoi_model,
            spectral_model="no_loss",
            dc_ohmic_model="no_loss",
        )
        return mc

    def format_results(self, results: pvlib.modelchain.ModelChainResult) -> pd.DataFrame:
        """Format simulation results into a structured DataFrame.

        Args:
            results: ModelChain results object.

        Returns:
            pd.DataFrame: Formatted results with key metrics and system summary in attrs.
        """
        df = pd.DataFrame({
            'ac_power': results.ac,
            'dc_power': results.dc['p_mp'],
            'ghi': results.weather['ghi'],
            'dni': results.weather['dni'],
            'dhi': results.weather['dhi'],
            'effective_irradiance': results.effective_irradiance,
            'cell_temperature': results.cell_temperature
        })
        df['timestamp'] = df.index
        df.attrs['system_summary'] = self.get_system_summary()
        return df

    def run_simulation(self, weather_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """Run PV system simulation with optional custom weather data.

        Args:
            weather_data: Optional DataFrame with weather data. If None, fetches TMY data.

        Returns:
            pd.DataFrame: Formatted simulation results.

        Raises:
            ValueError: If weather data is empty or invalid.
        """
        weather_data = weather_data or utils.fetch_TMY_data(self.lat, self.lon)
        start = pd.to_datetime(self.timeframe_params.get('start'))
        end = pd.to_datetime(self.timeframe_params.get('end'))
        # weather_data = weather_data.loc[start:end]
        
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        logger.info(f"Simulation completed successfully: {mc.results}")
        return self.format_results(mc.results)

    def get_system_summary(self) -> Dict:
        """Get a summary of the system configuration.

        Returns:
            Dict: System configuration details.
        """
        summary = {
            "system_type": "Advanced PV System",
            "mount_type": self.mount_type,
            "location": {
                "name": self.name,
                "latitude": self.lat,
                "longitude": self.lon
            },
            "components": {
                "custom_module": bool(self.custom_module_params),
                "custom_inverter": bool(self.custom_inverter_params)
            },
            "configuration": {
                "modules_per_string": self.modules_per_string,
                "strings": self.strings,
                "temperature_model": self.temp_model
            }
        }
        if self.mount_type in ["single_axis", "dual_axis"]:
            summary["tracker_config"] = self.mount_config
        return summary



