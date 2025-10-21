## data_factory/database/queries.py
## pkibuka@milky-way.space

def insert_irradiance_data_query():
    return f"""
    INSERT INTO irradiance_data (
        insert_date, parameter, value, units, lon, lat, elevation, source
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (insert_date, parameter, lon, lat) DO NOTHING;
    """

def irradiance_ohlc_query(bucket: str = "1 week"):
    return f"""
    SELECT time_bucket('{bucket}', insert_date) AS bucket,
        first(value, insert_date) AS open,
        max(value) AS high,
        min(value) AS low,
        last(value, insert_date) AS close
    FROM irradiance_data
    WHERE parameter = 'ALLSKY_SFC_SW_DWN'
    GROUP BY bucket
    ORDER BY bucket DESC
    LIMIT 160;
    """


def fetch_airmass_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(airmass_relative) AS relative_airmass,
        max(airmass_absolute) AS absolute_airmass
    FROM airmass
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_cell_temp_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(temperature) AS cell_temperature
    FROM cell_temperature
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_dc_output_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(i_sc) AS i_sc,
        max(v_oc) AS v_oc,
        max(i_mp) AS i_mp,
        max(v_mp) AS v_mp,
        max(p_mp) AS p_mp,
        max(i_x) AS i_x,
        max(i_xx) AS i_xx
    FROM dc_output
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_diode_params_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(I_L) AS i_l,
        max(I_o) AS i_o,
        max(R_s) AS r_s,
        max(R_sh) AS r_sh,
        max(nNsVth) AS nnsvth
    FROM diode_params
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_total_irradiance_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(poa_global) AS poa_global,
        max(poa_direct) AS poa_direct,
        max(poa_diffuse) AS poa_diffuse,
        max(poa_sky_diffuse) AS poa_sky_diffuse,
        max(poa_ground_diffuse) AS poa_ground_diffuse
    FROM total_irradiance
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_solar_position_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(zenith) AS zenith,
        max(azimuth) AS azimuth,
        max(elevation) AS elevation,
        max(apparent_zenith) AS apparent_zenith,
        max(apparent_elevation) AS apparent_elevation,
        max(equation_of_time) AS equation_of_time
    FROM solar_position
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """

def fetch_weather_query(result_id: float):
    return f"""
    SELECT
        date(utc_time) AS day,
        max(ghi) AS ghi,
        max(dni) AS dni,
        max(dhi) AS dhi,
        max(temp_air) AS temp_air,
        max(wind_speed) AS wind_speed
    FROM weather
    WHERE result_id = {result_id}
    GROUP BY DATE(utc_time)
    ORDER BY day DESC;
    """













