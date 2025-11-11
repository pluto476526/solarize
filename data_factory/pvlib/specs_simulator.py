from typing import Dict, List, Optional, Union
from django.contrib import messages
import pvlib
import pandas as pd
import logging

from data_factory.pvlib import utils, dual_axis_tracker_mount


logger = logging.getLogger(__name__)


class SpecSheetSimulator:
    """Advanced PV system simulator for fixed and tracking systems."""

    def __init__(self, location_params, system_params, losses_params):
        """Initialize the PV simulator with system, location, and loss parameters.

        Args:
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
        self.year = int(system_params["year"])

        # Mount configuration
        self.mount_type = "fixed"
        self.mount_config = {}

        # System parameters
        self.module_type = system_params["module_type"]
        self.celltype = system_params["celltype"]
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.surface_tilt = system_params["surface_tilt"]
        self.surface_azimuth = system_params["surface_azimuth"]
        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]
        self.racking_model = system_params["racking_model"]
        self.arrays = system_params.get("arrays_config", [])

        # Custom component parameters
        self.custom_module_params = system_params.get("module_params")
        self.custom_inverter_params = system_params.get("inverter_params")
        self.custom_temp_coefficients = system_params.get("temp_coefficients")
        self.losses_params = losses_params


    def validate_inputs(self, request=None) -> bool:
        """
        Validate input parameters.
        Returns True if all inputs are valid, False otherwise.
        """
        issues = []

        if not isinstance(self.lat, (int, float)) or not (-90 <= self.lat <= 90):
            issues.append(f"Latitude {self.lat} must be a number between -90 and 90")
        if not isinstance(self.lon, (int, float)) or not (-180 <= self.lon <= 180):
            issues.append(f"Longitude {self.lon} must be a number between -180 and 180")
        if not isinstance(self.alt, (int, float)) or self.alt < 0:
            issues.append(f"Altitude {self.alt} must be non-negative")
        if not isinstance(self.albedo, (int, float)) or not (0 <= self.albedo <= 1):
            issues.append(f"Albedo {self.albedo} must be between 0 and 1")


        module_params = self.custom_module_params or {}

        if "v_mp" in module_params and module_params["v_mp"] <= 0:
            issues.append("Maximum power voltage (Vmp) must be positive")
        if "i_mp" in module_params and module_params["i_mp"] <= 0:
            issues.append("Maximum power current (Imp) must be positive")
        if "v_oc" in module_params and module_params["v_oc"] <= 0:
            issues.append("Open-circuit voltage (Voc) must be positive")
        if "i_sc" in module_params and module_params["i_sc"] <= 0:
            issues.append("Short-circuit current (Isc) must be positive")
        if "cells_in_series" in module_params and module_params["cells_in_series"] <= 0:
            issues.append("Cells in series must be a positive integer")

        if "v_mp" in module_params and "v_oc" in module_params:
            if module_params["v_mp"] >= module_params["v_oc"]:
                issues.append("Vmp must be less than Voc")
        if "i_mp" in module_params and "i_sc" in module_params:
            if module_params["i_mp"] >= module_params["i_sc"]:
                issues.append("Imp must be less than Isc")



        temp_coefficients = self.custom_temp_coefficients or {}

        if not (-0.001 <= temp_coefficients["alpha_sc"] <= 0.015):
            issues.append(f"alpha_sc out of typical range: {temp_coefficients['alpha_sc']:.3f} (expected -0.001 to +0.015)")

        if not (-0.20 <= temp_coefficients["beta_voc"] <= -0.05):
            issues.append(f"beta_voc out of typical range: {temp_coefficients['beta_voc']:.3f} (expected -0.20 to -0.05")

        # gamma_pmp → usually %/°C  (direct input)
        if not (-0.55 <= temp_coefficients["gamma_pmp"] <= -0.25):
            issues.append(f"gamma_pmp out of typical range: {temp_coefficients['gamma_pmp']:.3f} (expected -0.55 to -0.25")

        # --- Log and display issues ---
        if issues:
            for issue in issues:
                messages.warning(request, issue)
            return False

        return True


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
            tz=self.tz,
        )

    def _get_CEC_params(self) -> Dict:
        """Estimates parameters for the CEC single diode model (SDM) using the SAM SDK."""
        I_L_ref, I_o_ref, R_s, R_sh_ref, a_ref, Adjust = pvlib.ivtools.sdm.fit_cec_sam(
            celltype=self.celltype,
            v_mp=self.custom_module_params.get("v_mp"),
            i_mp=self.custom_module_params.get("i_mp"),
            v_oc=self.custom_module_params.get("v_oc"),
            i_sc=self.custom_module_params.get("i_sc"),
            alpha_sc=self.custom_temp_coefficients.get("alpha_sc"),
            beta_voc=self.custom_temp_coefficients.get("beta_voc"),
            gamma_pmp=self.custom_temp_coefficients.get("gamma_pmp"),
            cells_in_series=self.custom_module_params.get("cells_in_series"),
            temp_ref=25,
        )

        return {
            "I_L_ref": I_L_ref,
            "I_o_ref": I_o_ref,
            "R_s": R_s,
            "R_sh_ref": R_sh_ref,
            "a_ref": a_ref,
            "Adjust": Adjust,
            "alpha_sc": self.custom_temp_coefficients["alpha_sc"],
        }

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
            return pvlib.pvsystem.FixedMount(
                surface_tilt=surface_tilt, surface_azimuth=surface_azimuth
            )

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
                gcr=gcr,
            )

        elif mount_type == "dual_axis":
            return dual_axis_tracker_mount.DualAxisTrackerMount()

        else:
            logger.error(f"Invalid mount type: {mount_type}")

    def simulation_setup(self) -> pvlib.modelchain.ModelChain:
        """Set up the PV system model chain.

        Returns:
            pvlib.modelchain.ModelChain: Configured model chain for simulation.
        """
        temp_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[
            self.temp_model
        ][self.temp_model_params]

        # System-wide losses
        loss_params = pvlib.pvsystem.pvwatts_losses(
            soiling=float(self.losses_params["soiling"]),
            shading=float(self.losses_params["shading"]),
            snow=float(self.losses_params["snow"]),
            mismatch=float(self.losses_params["mismatch"]),
            wiring=float(self.losses_params["wiring"]),
            connections=float(self.losses_params["connections"]),
            lid=float(self.losses_params["lid"]),
            nameplate_rating=float(self.losses_params["nameplate"]),
            age=float(self.losses_params["age"]),
            availability=float(self.losses_params["availability"]),
        )

        # Build array configurations
        if not isinstance(self.arrays, list):
            self.arrays = []

        main_array_config = {
            "name": "MainArray",
            "mount_type": self.mount_type,
            "surface_tilt": self.surface_tilt,
            "surface_azimuth": self.surface_azimuth,
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo,
            "tracker_config": {},
            "array_losses": {},
        }
        self.arrays.append(main_array_config)

        # Build PVLib Array objects
        arrays = []
        for config in self.arrays:
            arr = pvlib.pvsystem.Array(
                name=config["name"],
                mount=self._create_mount(config),
                albedo=config["albedo"],
                module_type=self.module_type,
                module_parameters=self._get_CEC_params(),
                temperature_model_parameters=temp_parameters,
                modules_per_string=int(config["modules_per_string"]),
                strings=int(config["strings"]),
                array_losses_parameters=config["array_losses"],
            )
            arrays.append(arr)

        # Combine into PVSystem
        system = pvlib.pvsystem.PVSystem(
            arrays=arrays,
            inverter_parameters=self.custom_inverter_params,
            racking_model=self.racking_model,
            losses_parameters=loss_params,
        )

        # Initialize model chain
        aoi_model = (
            "physical" if self.mount_type in ["single_axis", "dual_axis"] else "ashrae"
        )
        mc = pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model=aoi_model,
            dc_model="cec",
            ac_model="pvwatts",
            spectral_model="no_loss",
            dc_ohmic_model="no_loss",
        )
        return mc

    def get_system_summary(self) -> Dict:
        """Get a detailed summary of the PV system configuration.

        Returns:
            Dict: Full system configuration details including location, components, 
                  electrical specs, temperature coefficients, and losses.
        """
        return {
            "system_type": "Custom PV System",
            "description": getattr(self, "description", ""),
            "location": {
                "name": self.name,
                "latitude": self.lat,
                "longitude": self.lon,
                "altitude": self.alt,
                "timezone": self.tz,
                "albedo": self.albedo,
            },
            "components": {
                "module": {
                    "type": getattr(self, "module_type", None),
                    "cell_type": getattr(self, "celltype", None),
                    "arrays": getattr(self, "arrays", []),
                    "custom_params": self.custom_module_params,
                },
                "inverter": self.custom_inverter_params,
            },
            "electrical_specs": {
                "v_mp": self.custom_module_params.get("v_mp") if self.custom_module_params else None,
                "i_mp": self.custom_module_params.get("i_mp") if self.custom_module_params else None,
                "v_oc": self.custom_module_params.get("v_oc") if self.custom_module_params else None,
                "i_sc": self.custom_module_params.get("i_sc") if self.custom_module_params else None,
                "cells_in_series": self.custom_module_params.get("cells_in_series"),
            },
            "temperature_model": {
                "model": getattr(self, "temp_model", None),
                "params": getattr(self, "temp_model_params", {}),
                "coefficients": self.custom_temp_coefficients,
            },
        }


    def run_simulation(
        self, weather_data: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        """Run PV system simulation with optional custom weather data.

        Args:
            weather_data: Optional DataFrame with weather data. If None, fetches TMY data.

        Returns:
            pd.DataFrame: Formatted simulation results.

        Raises:
            ValueError: If weather data is empty or invalid.
        """
        weather_data = weather_data or utils.fetch_TMY_data(
            self.lat, self.lon, self.year
        )
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        system_config = self.get_system_summary()
        return mc.results, system_config
