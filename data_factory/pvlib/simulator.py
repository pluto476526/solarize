## data_factory/pvlib/solarize.py
## pkibuka@milky-way.space


import pvlib
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class PvlibSimulator:
    def __init__(
        self,
        name: str,
        lat: float,
        lon: float,
        alt: float,
        tz: str,
        module: str,
        inverter: str,
        surface_tilt: float,
        surface_azimuth: float,
        temp_model:str,
        temp_model_params: str
    ):
        self.name = name
        self.lat = float(lat)
        self.lon = float(lon)
        self.alt = float(alt)
        self.tz = tz
        self.module = module
        self.inverter = inverter
        self.surface_tilt = float(surface_tilt)
        self.surface_azimuth = float(surface_azimuth)
        self.temp_model = temp_model
        self.temp_model_params = temp_model_params
    
    def create_location(self):
        return pvlib.location.Location(
            name=self.name,
            latitude=self.lat,
            longitude=self.lon,
            altitude=self.alt,
            tz=self.tz
        )


    def fetch_TMY_data(self):
        weather, _ = pvlib.iotools.get_pvgis_tmy(
            latitude=self.lat,
            longitude=self.lon,
            url="https://re.jrc.ec.europa.eu/api/v5_2/"
        )

        weather.index.name = "utc_time"
        return weather


    def simulation_setup(self):
        # Retrieve modules and inverter database
        cec_modules_db = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Modules.csv"
        cec_inverters_db = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Inverters.csv"

        module_db = pvlib.pvsystem.retrieve_sam(path=cec_modules_db)
        inverter_db = pvlib.pvsystem.retrieve_sam(path=cec_inverters_db)

        # Select a specific module and inverter parameters
        module_params = module_db[self.module]
        inverter_params = inverter_db[self.inverter]

        # Create mount
        mount = pvlib.pvsystem.FixedMount(
            surface_tilt=self.surface_tilt,
            surface_azimuth=self.surface_azimuth
        )

        # Define temp model parameters
        temp_parameters = pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS[self.temp_model][self.temp_model_params]

        # Create array with mount, module and temp model
        array = pvlib.pvsystem.Array(
            mount=mount,
            module_parameters=module_params,
            temperature_model_parameters=temp_parameters,
            modules_per_string=1,
            strings=1,
            array_losses_parameters=None,
        )

        # Create PV system with array and inverter
        system = pvlib.pvsystem.PVSystem(
            arrays=[array],
            inverter_parameters=inverter_params
        )

        # Create a ModelChain to link location and system for simulation
        mc = pvlib.modelchain.ModelChain(
            system=system,
            location=self.create_location(),
            aoi_model="physical"
        )
        return mc

    def run_pvlib_simulation(self):
        weather_data = self.fetch_TMY_data()
        mc = self.simulation_setup()
        mc.run_model(weather_data)
        return mc.results

