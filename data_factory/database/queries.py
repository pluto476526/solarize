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

def get_irradiance_ohlc_data(bucket: str = "i week"):
    return f"""
    SELECT time_bucket('{bucket}', insert_date) AS bucket,
        first(value, insert_date) AS open,
        max(value) AS high,
        min(value) AS low,
        last(value, insert_date) AS close
    FROM irradiance_data
    WHERE parameter = 'ALLSKY_SFC_SW_DWN'
    GROUP BY bucket
    ORDER BY bucket;
    """

