from typing import Dict, List, Optional
from data_factory.pvlib import utils
import pvlib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class BifacialPVSimulator:
    """Simple simulator for bifacial PV systems."""
    
    def __init__(self, location_params: Dict, system_params: Dict, losses_params: Dict):
        """Initialize bifacial PV simulator.

        Args:
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
        
        # System parameters
        self.module = system_params["module"]
        self.module_type = system_params["module_type"]
        self.inverter = system_params["inverter"]
        self.modules_per_string = int(system_params["modules_per_string"])
        self.strings = int(system_params["strings"])
        self.surface_tilt = float(system_params["surface_tilt"])
        self.surface_azimuth = float(system_params["surface_azimuth"])
        self.bifaciality = system_params["bifaciality"]
        self.arrays = system_params.get("arrays_config", [])

        self.temp_model = system_params["temp_model"]
        self.temp_model_params = system_params["temp_model_params"]
        self.description = system_params["description"]
        self.year = int(system_params["year"])
        
        # Losses parameters
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
        
        # self._validate_inputs()

    def _validate_inputs(self) -> None:
        """Validate input parameters.

        Raises:
            ValueError: If any parameter is invalid.
        """
        issues = []
        
        # Validate timeframe
        # if not isinstance(self.timeframe_params, dict) or 'start' not in self.timeframe_params or 'end' not in self.timeframe_params:
        #     issues.append("timeframe_params must be a dict with 'start' and 'end' keys")
        
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

    def _create_location(self) -> pvlib.location.Location:
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

    def _create_mount(self, array_config):
        return pvlib.pvsystem.FixedMount(
            surface_tilt=float(array_config["surface_tilt"]),
            surface_azimuth=float(array_config["surface_azimuth"]),
        )

    def _get_irradiance(self, weather, solar_position):
        """
        Get rear and front side irradiance from pvfactors transposition engine
        Explicity simulate on pvarray with 3 rows, with sensor placed in middle row
        Users may select different values depending on needs
        """

        irrad = pvlib.bifacial.pvfactors.pvfactors_timeseries(
            solar_azimuth=solar_position["azimuth"],
            solar_zenith=solar_position["apparent_zenith"],
            surface_azimuth=self.surface_azimuth,
            surface_tilt=self.surface_tilt,
            axis_azimuth=self.surface_azimuth,
            timestamps=weather.index,
            dni=weather["dni"],
            dhi=weather["dhi"],
            gcr=self.bifaciality["gcr"],
            pvrow_height=self.bifaciality["pvrow_height"],
            pvrow_width=self.bifaciality["pvrow_width"],
            albedo=self.albedo,
            n_pvrows=self.bifaciality["n_pvrows"],
            index_observed_pvrow=self.bifaciality["index_observed_pvrow"],
            rho_front_pvrow=self.bifaciality["rho_front_pvrow"],
            rho_back_pvrow=self.bifaciality["rho_back_pvrow"],
            horizon_band_angle=self.bifaciality["horizon_band_angle"]
        )

        # turn into pandas DataFrame
        irrad = pd.concat(irrad, axis=1)

        # create bifacial effective irradiance using aoi-corrected timeseries values
        irrad["effective_irradiance"] = (
            irrad["total_abs_front"] + (irrad["total_abs_back"] * self.bifaciality["bifaciality"])
        )

        return irrad




    def simulation_setup(self) -> pvlib.modelchain.ModelChain:
        """Set up the bifacial PV system model chain.

        Returns:
            pvlib.modelchain.ModelChain: Configured model chain for simulation.
        """
        # Retrieve module and inverter parameters
        module_params, inverter_params = utils.fetch_cec_params(self.module, self.inverter)

        # Temperature model parameters
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

        # Load arrays from config file
        array_configs = getattr(self, "arrays", None)

        if not isinstance(array_configs, list):
            array_configs = []

        # Always append the "main array"
        array_configs.append({
            "name": "MainArray",
            "mount_type": "fixed_mount",
            "module_type": self.module_type,
            "surface_tilt": self.surface_tilt,
            "surface_azimuth": self.surface_azimuth,
            "modules_per_string": self.modules_per_string,
            "strings": self.strings,
            "albedo": self.albedo,
            "tracker_config": {},
            "array_losses": {
                "mismatch": self.mismatch,
                "wiring": self.wiring
            },
        })



        # Build PVLib Array objects
        arrays = []
        for config in array_configs:
            arr = pvlib.pvsystem.Array(
                name=config["name"],
                mount=self._create_mount(config),
                albedo=float(config["albedo"]),
                module_type=config["module_type"],
                module_parameters=module_params,
                temperature_model_parameters=temp_parameters,
                modules_per_string=int(config["modules_per_string"]),
                strings=int(config["strings"]),
                array_losses_parameters=config["array_losses"]
            )

            arrays.append(arr)
            

        # Combine all arrays into a PVSystem
        system = pvlib.pvsystem.PVSystem(
            arrays=arrays,
            inverter_parameters=inverter_params,
            losses_parameters=loss_params
        )

        # Initialize model chain
        return pvlib.modelchain.ModelChain(
            system=system,
            location=self._create_location(),
            aoi_model="ashrae",
            spectral_model="no_loss",
            dc_ohmic_model="no_loss",
        )


    def format_results(self, results: pvlib.modelchain.ModelChainResult):
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
            #"bifacial_gain": df["dc_power"] - df["dc_power"].min()) / df["dc_power"].mean()

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
        weather_data = weather_data or utils.fetch_TMY_data(self.lat, self.lon, self.year)
        location = self._create_location()
        solar_position = location.get_solarposition(weather_data.index)
        irrad = self._get_irradiance(weather_data, solar_position)
        mc = self.simulation_setup()
        mc.run_model_from_effective_irradiance(irrad)
        return mc.results

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
