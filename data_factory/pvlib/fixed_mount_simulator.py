## data_factory/pvlib/fixed_mount_simulator.py
## pkibuka@milky-way.space


import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils

logger = logging.getLogger(__name__)

class FixedMountSimulator:
    def __init__(self, timeframe_params, location_params, system_params, losses_params):
        self.name = location_params["name"]
        self.lat = float(location_params["lat"])
        self.lon = float(location_params["lon"])
        self.alt = float(location_params["alt"])
        self.tz = location_params["tz"]
        self.albedo = float(location_params["albedo"])
        self.surface_tilt = float(system_params["surface_tilt"])
        self.surface_azimuth = float(system_params["surface_azimuth"])
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.arrays = system_params["arrays_config"]
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]

        self.soiling = float(losses_params.get("soiling"))
        self.shading = float(losses_params.get("shading"))
        self.snow = float(losses_params.get("snow"))
        self.mismatch = float(losses_params.get("mismatch"))
        self.wiring = float(losses_params.get("wiring"))
        self.connections = float(losses_params.get("connections"))
        self.lid = float(losses_params.get("lid"))
        self.nameplate = float(losses_params.get("nameplate"))
        self.age = float(losses_params.get("age"))
        self.availability = float(losses_params.get("availability"))

    def create_location(self):
        return pvlib.location.Location(
            name=self.name,
            latitude=self.lat,
            longitude=self.lon,
            altitude=self.alt,
            tz=self.tz
        )

    def simulation_setup(self):
        # Retrieve module and inverter parameters
        module_params, inverter_params = utils.fetch_cec_params(self.module, self.inverter)

        # Temperature model parameters
        temp_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
            self.temp_model
        ][self.temp_model_params]

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

        # Load arrays from config file
        array_configs = getattr(self, "arrays", None)

        if not isinstance(array_configs, list):
            array_configs = []

        # Always append the "main array"
        array_configs.append({
            "name": "MainArray",
            "surface_tilt": self.surface_tilt,
            "surface_azimuth": self.surface_azimuth,
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo
        })



        # Build PVLib Array objects
        arrays = []
        for cfg in array_configs:
            mount = pvlib.pvsystem.FixedMount(
                surface_tilt=float(cfg["surface_tilt"]),
                surface_azimuth=float(cfg["surface_azimuth"]),
            )

            array_losses = {"mismatch": self.mismatch, "wiring": self.wiring}

            arr = pvlib.pvsystem.Array(
                name=cfg["name"],
                mount=mount,
                albedo=float(cfg["albedo"]),
                module_type=self.module_type,
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=int(cfg["modules_per_string"]),
                strings=int(cfg["strings"]),
                array_losses_parameters=array_losses
            )

            arrays.append(arr)
            

        # Combine all arrays into a PVSystem
        system = pvlib.pvsystem.PVSystem(
            arrays=arrays,
            inverter_parameters=inverter_params,
            losses_parameters=loss_params
        )

        # Initialize model chain
        mc = pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model="ashrae",
            spectral_model="no_loss",
            dc_ohmic_model="no_loss",
        )

        return mc


    def run_simulation(self):
        weather_data = utils.fetch_TMY_data(self.lat, self.lon)
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        return mc.results



