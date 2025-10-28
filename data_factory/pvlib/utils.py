## data_factory/pvlib/utils.py
## pkibuka@milky-way.space


import pvlib
import pandas as pd


def fetch_TMY_data(lat, lon):
    weather, _ = pvlib.iotools.get_pvgis_tmy(
        latitude=lat,
        longitude=lon,
        url="https://re.jrc.ec.europa.eu/api/v5_2/",
        coerce_year=2025
    )

    weather.index.name = "utc_time"
    return weather


def fetch_cec_params(module, inverter):
    cec_modules_db = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Modules.csv"
    cec_inverters_db = "https://raw.githubusercontent.com/NREL/SAM/develop/deploy/libraries/CEC%20Inverters.csv"
    module_db = pvlib.pvsystem.retrieve_sam(path=cec_modules_db)
    inverter_db = pvlib.pvsystem.retrieve_sam(path=cec_inverters_db)
    module_params = module_db[module]
    inverter_params = inverter_db[inverter]
    return module_params, inverter_params

def aggregate_timeseries(data, column: str = None):
    # If not a tuple, return the Series or column from DataFrame
    if not isinstance(data, tuple):
        if isinstance(data, pd.DataFrame) and column is not None:
            return data[column]
        return data

    # Collect Series from tuple elements
    series_list = []
    for d in data:
        if isinstance(d, pd.DataFrame):
            if column is None or column not in d:
                raise ValueError(f"Column '{column}' must exist in DataFrame")
            series_list.append(d[column])
        elif isinstance(d, pd.Series):
            series_list.append(d)
        else:
            raise TypeError(f"Expected pd.Series or pd.DataFrame, got {type(d)}")

    # Compute row-wise average
    if len(series_list) == 1:
        return series_list[0]
    else:
        return pd.concat(series_list, axis=1).mean(axis=1)




