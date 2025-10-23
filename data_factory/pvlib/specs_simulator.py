from typing import Dict, List, Optional, Union
import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils

logger = logging.getLogger(__name__)

class AdvancedPVSimulator:
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
        self.mount_type = system_params.get("mount_type", "fixed")  # fixed, single_axis, dual_axis
        self.mount_config = system_params.get("mount_config", {})
        
        # System parameters
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.arrays = system_params.get("arrays_config", [])  # Default to empty list
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]

        # Custom component parameters
        self.custom_module_params = system_params.get("custom_module_params")
        self.custom_inverter_params = system_params.get("custom_inverter_params")
        self.custom_temp_params = system_params.get("custom_temp_params")
        self.custom_mount_params = system_params.get("custom_mount_params")

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

        self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Validate input parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        issues = []
        
        # Validate timeframe_params
        if not isinstance(self.timeframe_params, dict) or 'start' not in self.timeframe_params or 'end' not in self.timeframe_params:
            issues.append("timeframe_params must be a dict with 'start' and 'end' keys")

        # Validate location parameters
        if not (-90 <= self.lat <= 90):
            issues.append(f"Latitude {self.lat} must be between -90 and 90")
        if not (-180 <= self.lon <= 180):
            issues.append(f"Longitude {self.lon} must be between -180 and 180")
        if self.alt < 0:
            issues.append(f"Altitude {self.alt} must be non-negative")
        if not 0 <= self.albedo <= 1:
            issues.append(f"Albedo {self.albedo} must be between 0 and 1")

        # Validate numeric losses parameters
        for param, value in [
            ("soiling", self.soiling), ("shading", self.shading), ("snow", self.snow),
            ("mismatch", self.mismatch), ("wiring", self.wiring), ("connections", self.connections),
            ("lid", self.lid), ("nameplate", self.nameplate), ("age", self.age),
            ("availability", self.availability)
        ]:
            if not 0 <= value <= 1:
                issues.append(f"{param} must be between 0 and 1, got {value}")

        # Validate custom module parameters
        if self.custom_module_params:
            required_fields = ['pdc0', 'v_mp', 'i_mp', 'v_oc', 'i_sc']
            for field in required_fields:
                if field not in self.custom_module_params:
                    issues.append(f"Missing required module parameter: {field}")
                elif not isinstance(self.custom_module_params[field], (int, float)) or self.custom_module_params[field] <= 0:
                    issues.append(f"Module parameter {field} must be a positive number")

        # Validate custom inverter parameters
        if self.custom_inverter_params:
            required_fields = ['pdc0', 'pdc_max', 'vdcmax', 'idcmax']
            for field in required_fields:
                if field not in self.custom_inverter_params:
                    issues.append(f"Missing required inverter parameter: {field}")
                elif not isinstance(self.custom_inverter_params[field], (int, float)) or self.custom_inverter_params[field] <= 0:
                    issues.append(f"Inverter parameter {field} must be a positive number")

        # Validate tracker parameters for single_axis
        if self.mount_type == "single_axis":
            required_fields = ['axis_azimuth', 'max_angle']
            for field in required_fields:
                if field not in self.mount_config:
                    issues.append(f"Missing required tracker parameter: {field}")

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

    def _get_temperature_parameters(self) -> Dict:
        """Get temperature model parameters.

        Returns:
            Dict: Temperature model parameters, custom or standard.
        """
        if self.custom_temp_params:
            logger.info(f"Using custom temperature parameters for {self.temp_model}")
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
        surface_tilt = float(array_config.get("surface_tilt", self.custom_mount_params.get("surface_tilt", 30) if self.custom_mount_params else 30))
        surface_azimuth = float(array_config.get("surface_azimuth", self.custom_mount_params.get("surface_azimuth", 180) if self.custom_mount_params else 180))
        
        if not 0 <= surface_tilt <= 90:
            raise ValueError(f"Surface tilt {surface_tilt} must be between 0 and 90")
        if not 0 <= surface_azimuth <= 360:
            raise ValueError(f"Surface azimuth {surface_azimuth} must be between 0 and 360")

        if mount_type == "fixed":
            return pvlib.pvsystem.FixedMount(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth)
        
        elif mount_type == "single_axis":
            axis_tilt = float(tracker_config.get("axis_tilt", 0))
            axis_azimuth = float(tracker_config.get("axis_azimuth", 0))
            max_angle = float(tracker_config.get("max_angle", 90))
            gcr = float(tracker_config.get("gcr", 0.4))
            
            if not 0 <= max_angle <= 90:
                raise ValueError(f"Max angle {max_angle} must be between 0 and 90")
            if not 0 <= gcr <= 1:
                raise ValueError(f"GCR {gcr} must be between 0 and 1")
            
            return pvlib.pvsystem.SingleAxisTrackerMount(
                axis_tilt=axis_tilt,
                axis_azimuth=axis_azimuth,
                max_angle=max_angle,
                backtrack=bool(tracker_config.get("backtrack", True)),
                gcr=gcr
            )
        
        elif mount_type == "dual_axis":
            axis_tilt = float(tracker_config.get("axis_tilt", 0))
            axis_azimuth = float(tracker_config.get("axis_azimuth", 0))
            max_rotation = float(tracker_config.get("max_rotation", 360))
            
            if not 0 <= max_rotation <= 360:
                raise ValueError(f"Max rotation {max_rotation} must be between 0 and 360")
            
            return pvlib.pvsystem.DualAxisTrackerMount(
                axis_tilt=axis_tilt,
                axis_azimuth=axis_azimuth,
                max_rotation=max_rotation
            )
        
        elif mount_type == "custom" and self.custom_mount_params:
            logger.info("Using custom mount configuration")
            return pvlib.pvsystem.FixedMount(surface_tilt=surface_tilt, surface_azimuth=surface_azimuth)
        
        else:
            raise ValueError(f"Invalid mount type: {mount_type}")

    def simulation_setup(self) -> pvlib.modelchain.ModelChain:
        """Set up the PV system model chain.

        Returns:
            pvlib.modelchain.ModelChain: Configured model chain for simulation.
        """
        # Retrieve module and inverter parameters
        module_params = self.custom_module_params or pvlib.pvsystem.retrieve_sam('cecmod')[self.module]
        inverter_params = self.custom_inverter_params or pvlib.pvsystem.retrieve_sam('cecinverter')[self.inverter]
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
        array_configs = self.arrays[:]
        main_array_config = {
            "name": "MainArray",
            "mount_type": self.mount_type,
            "surface_tilt": 30,
            "surface_azimuth": 180,
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo,
            "tracker_config": self.mount_config if self.mount_type in ["single_axis", "dual_axis"] else {},
            "array_losses": {"mismatch": self.mismatch, "wiring": self.wiring}
        }
        array_configs.append(main_array_config)

        # Build PVLib Array objects
        arrays = []
        for cfg in array_configs:
            mount = self._create_mount(cfg)
            array_losses = cfg.get("array_losses", {"mismatch": self.mismatch, "wiring": self.wiring})
            albedo = float(cfg.get("albedo", self.albedo))
            
            arr = pvlib.pvsystem.Array(
                name=cfg["name"],
                mount=mount,
                albedo=albedo,
                module_type=self.module_type,
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=int(cfg["modules_per_string"]),
                strings=int(cfg["strings"]),
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

    def format_results(self, results: pvlib.modelchain.ModelChainResults) -> pd.DataFrame:
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
        logger.info(f"Starting simulation for {self.name} (lat: {self.lat}, lon: {self.lon}, mount: {self.mount_type})")
        weather_data = weather_data or utils.fetch_TMY_data(self.lat, self.lon)
        start = pd.to_datetime(self.timeframe_params.get('start'))
        end = pd.to_datetime(self.timeframe_params.get('end'))
        logger.debug(f"Filtering weather data from {start} to {end}")
        weather_data = weather_data.loc[start:end]
        
        if weather_data.empty:
            logger.error("No weather data available for the specified timeframe")
            raise ValueError("Weather data is empty for the specified timeframe")
        
        mc = self.simulation_setup()
        logger.debug("Model chain initialized, running simulation")
        mc.run_model(weather_data)
        logger.info("Simulation completed successfully")
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
                "module": self.module,
                "inverter": self.inverter,
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













        {
  "timeframe_params": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },
  "location_params": {
    "name": "Albuquerque Site",
    "lat": 35.0844,
    "lon": -106.6504,
    "alt": 1619.0,
    "tz": "America/Denver",
    "albedo": 0.3
  },
  "system_params": {
    "mount_type": "fixed",
    "mount_config": {
      "surface_tilt": 35,
      "surface_azimuth": 180
    },
    "module": "Jinko_Solar_Co___Ltd_JKM330PP_72",
    "module_type": "polycrystalline",
    "inverter": "Fronius_USA_Fronius_Primo_10_0_1__208_240V_",
    "modules_per_string": 8,
    "strings": 6,
    "arrays_config": [
      {
        "name": "FixedArrayNorth",
        "mount_type": "fixed",
        "surface_tilt": 30,
        "surface_azimuth": 180,
        "modules_per_string": 10,
        "strings": 5,
        "albedo": 0.28,
        "array_losses": {
          "mismatch": 0.015,
          "wiring": 0.008
        }
      },
      {
        "name": "SingleAxisArray",
        "mount_type": "single_axis",
        "surface_tilt": 0,
        "surface_azimuth": 180,
        "modules_per_string": 12,
        "strings": 4,
        "albedo": 0.32,
        "tracker_config": {
          "axis_tilt": 5,
          "axis_azimuth": 180,
          "max_angle": 60,
          "backtrack": true,
          "gcr": 0.35
        },
        "array_losses": {
          "mismatch": 0.02,
          "wiring": 0.01
        }
      },
      {
        "name": "DualAxisArray",
        "mount_type": "dual_axis",
        "surface_tilt": 0,
        "surface_azimuth": 180,
        "modules_per_string": 10,
        "strings": 3,
        "albedo": 0.3,
        "tracker_config": {
          "axis_tilt": 0,
          "axis_azimuth": 180,
          "max_rotation": 270
        },
        "array_losses": {
          "mismatch": 0.018,
          "wiring": 0.009
        }
      },
      {
        "name": "CustomFixedArray",
        "mount_type": "custom",
        "surface_tilt": 25,
        "surface_azimuth": 170,
        "modules_per_string": 9,
        "strings": 4,
        "albedo": 0.29,
        "array_losses": {
          "mismatch": 0.017,
          "wiring": 0.007
        }
      }
    ],
    "temp_model": "sapm",
    "temp_model_params": "open_rack_glass_polymer",
    "description": "Multi-array PV system with fixed, single-axis, dual-axis, and custom mounts in Albuquerque",
    "custom_module_params": {
      "pdc0": 330,
      "v_mp": 37.2,
      "i_mp": 8.87,
      "v_oc": 46.1,
      "i_sc": 9.36
    },
    "custom_inverter_params": {
      "pdc0": 10000,
      "pdc_max": 10500,
      "vdcmax": 600,
      "idcmax": 30
    },
    "custom_temp_params": {
      "a": -3.56,
      "b": -0.075,
      "deltaT": 3
    },
    "custom_mount_params": {
      "surface_tilt": 25,
      "surface_azimuth": 170
    }
  },
  "losses_params": {
    "soiling": 0.03,
    "shading": 0.02,
    "snow": 0.01,
    "mismatch": 0.015,
    "wiring": 0.008,
    "connections": 0.004,
    "lid": 0.01,
    "nameplate": 0.005,
    "age": 0.002,
    "availability": 0.995
  }
}