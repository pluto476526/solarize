## data_factory/pvlib/single_axis_tracker_simulator.py
## pkibuka@milky-way.space

import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils, dual_axis_tracker_mount

logger = logging.getLogger(__name__)

class SingleDualAxisTracker:
    def __init__(self, timeframe_params, location_params, system_params, tracking_params, losses_params):
        self.name = location_params["name"]
        self.lat = float(location_params["lat"])
        self.lon = float(location_params["lon"])
        self.alt = float(location_params["alt"])
        self.tz = location_params["tz"]
        self.albedo = float(location_params["albedo"])
        
        # Single-axis tracker specific parameters
        self.axis_tilt = float(tracking_params.get("axis_tilt", 0))
        self.axis_azimuth = float(tracking_params.get("axis_azimuth", 0))
        self.max_angle = float(tracking_params.get("max_angle", 90))
        self.backtrack = bool(tracking_params.get("backtrack", True))
        self.gcr = float(tracking_params.get("gcr", 0.4))  # ground coverage ratio

        self.mount_type = "single_axis"
        
        # System parameters
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = float(system_params["modules_per_string"])
        self.strings = float(system_params["strings"])
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]
        self.arrays = system_params.get("arrays_config", [])
        self.racking_model = system_params.get("racking_model", "open_rack") #open_rack, close_mount, insulated_back, freestanding, insulated
        self.system_arrays = []

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

    def create_location(self):
        return pvlib.location.Location(
            name=self.name,
            latitude=self.lat,
            longitude=self.lon,
            altitude=self.alt,
            tz=self.tz
        )

    def create_mount(self, array_config) -> pvlib.pvsystem.AbstractMount:
        mount_type = array_config.get("mount_type")
        tracker_config = array_config.get("tracker_config")

        surface_tilt = float(array_config.get("surface_tilt", 30))
        surface_azimuth = float(array_config.get("surface_azimuth", 180))

        if mount_type == "single_axis":
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
            return dual_axis_tracker_mount.DualAxisTrackerMount()
        
        else:
            logger.error(f"Invalid mount type: {mount_type}")

    def simulation_setup(self):
        module_params, inverter_params = utils.fetch_cec_params(self.module, self.inverter)
        temp_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[self.temp_model][self.temp_model_params]

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
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo,
            "tracker_config": {
                "axis_tilt": self.axis_tilt,
                "axis_azimuth": self.axis_azimuth,
                "max_angle": self.max_angle,
                "backtrack": self.backtrack,
                "gcr": self.gcr
            },
            "array_losses": {
                "mismatch": self.mismatch,
                "wiring": self.wiring
            },
        }
        self.arrays.append(main_array_config)

        for config in self.arrays:
            mount = self.create_mount(config)

            arr = pvlib.pvsystem.Array(
                mount=mount,
                albedo=self.albedo,
                module_type=self.module_type,
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=config.get("modules_per_string"),
                strings=config.get("strings"),
                array_losses_parameters=config.get("array_losses")
            )
            self.system_arrays.append(arr)

        system = pvlib.pvsystem.PVSystem(
            arrays=self.system_arrays,
            inverter_parameters=inverter_params,
            racking_model=self.racking_model,
            losses_parameters=loss_params
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
        
        return mc.results


    def _analyze_tracker_performance(self, results):
        """Analyze tracker-specific performance metrics"""
        if hasattr(results, 'tracker_theta'):
            # Calculate tracking efficiency metrics
            tracking_angles = results.tracker_theta
            logger.info(
                f"Tracker angle statistics: min={tracking_angles.min():.1f}°, "
                f"max={tracking_angles.max():.1f}°, mean={tracking_angles.mean():.1f}°"
        )
        
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
        
        tracking_data = mount.get_orientation(
            solar_position['apparent_zenith'], 
            solar_position['azimuth']
        )

        return tracking_data

