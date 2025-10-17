## data_factory/database/queries.py
## pkibuka@milky-way.space

def insert_irradiance_data_query():
    return """
    INSERT INTO irradiance_data (
        insert_date, parameter, value, units, lon, lat, elevation, source
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (insert_date, parameter, lon, lat) DO NOTHING;
    """

def irradiance_ohlc_query(bucket: str = "i week"):
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


def insert_CEC_modules():
    return """
    INSERT INTO pv_modules (
        module_name, manufacturer, technology, bifacial, 
        stc_power_w, area_m2, v_oc, i_sc, v_mp, i_mp, 
        efficiency_percent, temp_coeff_power, is_bipv
    ) VALUES %s
    ON CONFLICT (module_name) DO NOTHING;
    """

def CEC_modules_query():
    """
    Return a SQL query that selects all data for a specific PV module.
    """
    return """
    SELECT module_name
    FROM pv_modules
    ORDER BY module_name ASC;
    """


