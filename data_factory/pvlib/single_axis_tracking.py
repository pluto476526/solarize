## data_factory/pvlib/single_axis_tracker_simulator.py
## pkibuka@milky-way.space

import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils

logger = logging.getLogger(__name__)

class SingleAxisTrackerSimulator:
    def __init__(self, location_params, system_params, timeframe_params):
        self.name = location_params["name"]
        self.lat = float(location_params["lat"])
        self.lon = float(location_params["lon"])
        self.alt = float(location_params["alt"])
        self.tz = location_params["tz"]
        self.albedo = float(location_params["albedo"])
        
        # Single-axis tracker specific parameters
        self.axis_tilt = float(system_params.get("axis_tilt", 0))
        self.axis_azimuth = float(system_params.get("axis_azimuth", 0))
        self.max_angle = float(system_params.get("max_angle", 90))
        self.backtrack = bool(system_params.get("backtrack", True))
        self.gcr = float(system_params.get("gcr", 0.4))  # ground coverage ratio
        
        # System parameters (unchanged from fixed mount)
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = float(system_params["modules_per_string"])
        self.strings = float(system_params["strings"])
        self.total_arrays = int(system_params["total_arrays"])
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]

    def create_location(self):
        return pvlib.location.Location(
            name=self.name,
            latitude=self.lat,
            longitude=self.lon,
            altitude=self.alt,
            tz=self.tz
        )

    def simulation_setup(self):
        module_params, inverter_params = utils.fetch_cec_params(self.module, self.inverter)

        # Single-axis tracker mount instead of fixed mount
        mount = pvlib.pvsystem.SingleAxisTrackerMount(
            axis_tilt=self.axis_tilt,
            axis_azimuth=self.axis_azimuth,
            max_angle=self.max_angle,
            backtrack=self.backtrack,
            gcr=self.gcr
        )

        temp_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[self.temp_model][self.temp_model_params]
        arrays = []

        for i in range(self.total_arrays):
            arr = pvlib.pvsystem.Array(
                mount=mount,
                albedo=self.albedo,
                module_type=self.module_type,
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=self.modules_per_string,
                strings=self.strings,
                array_losses_parameters=None,
                name=f"tracker_array_{i}"
            )
            arrays.append(arr)

        system = pvlib.pvsystem.PVSystem(
            arrays=arrays,
            inverter_parameters=inverter_params
        )

        mc = pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model="physical",
            spectral_model="no_loss",
        )
        return mc

    def run_simulation(self):
        weather_data = utils.fetch_TMY_data(self.lat, self.lon)
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        logger.debug(mc.results)
        
        # Add tracker-specific analysis if needed
        self._analyze_tracker_performance(mc.results)
        
        return mc.results

    def _analyze_tracker_performance(self, results):
        """Analyze tracker-specific performance metrics"""
        if hasattr(results, 'tracker_theta'):
            # Calculate tracking efficiency metrics
            tracking_angles = results.tracker_theta
            logger.info(f"Tracker angle statistics: min={tracking_angles.min():.1f}°, "
                       f"max={tracking_angles.max():.1f}°, mean={tracking_angles.mean():.1f}°")
        
        # Log backtracking information if applicable
        if self.backtrack:
            logger.info("Backtracking enabled with GCR: {self.gcr}")

    def get_tracking_geometry(self, times):
        """Get the tracker geometry for specific times"""
        location = self.create_location()
        solar_position = location.get_solarposition(times)
        
        mount = pvlib.pvsystem.SingleAxisTrackerMount(
            axis_tilt=self.axis_tilt,
            axis_azimuth=self.axis_azimuth,
            max_angle=self.max_angle,
            backtrack=self.backtrack,
            gcr=self.gcr
        )
        
        tracking_data = mount.get_orientation(solar_position['apparent_zenith'], 
                                            solar_position['azimuth'])
        return tracking_data

