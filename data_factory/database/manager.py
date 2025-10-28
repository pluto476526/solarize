import time
import logging
import json
from datetime import datetime, timedelta
import sqlalchemy
import psycopg2

import pandas as pd
from decouple import config

from data_factory.database.connection import DatabaseConnection
from data_factory.database import queries

logger = logging.getLogger(__name__)


class DataManager:
    def __init__(self, db: DatabaseConnection):
        self.db = db
        self.page_size = 500

    def insert_irradiance_data(self, df):
        if df is None or df.empty:
            return
       
        try:
            records = [
                (
                    pd.to_datetime(row["date"]).to_pydatetime(),
                    row["parameter"], row["value"], row["units"],
                    row["lon"], row["lat"], row["elev"], row["source"],
                )
                for row in df.to_dict(orient="records")
            ]

            query = queries.insert_irradiance_data_query()
            
            with self.db.cursor() as cur:
                psycopg2.extras.execute_batch(cur, query, records, page_size=self.page_size)
            
            self.db.commit()

        except Exception as e:
            logger.error(f"Irradiance data not saved: {e}")
            self.db.rollback()

    def get_irradiance_ohlc_data(self, bucket: str = "1 week"):
        try:
            query = queries.irradiance_ohlc_query(bucket)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def save_modelchain_result(self, result, array_names, simulation_name="Fixed Mount Simulation", description=""):
        with self.db.cursor() as cur:
            # Insert simulation metadata
            cur.execute("""
                INSERT INTO modelchain_results 
                    (simulation_name, description, albedo, losses, spectral_modifier, tracking)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING result_id
            """, (
                simulation_name,
                description,
                json.dumps(result.albedo) if isinstance(result.albedo, tuple) else result.albedo,
                result.losses,
                json.dumps(result.spectral_modifier),
                None if result.tracking is None else json.dumps(result.tracking)
            ))
            result_id = cur.fetchone()[0]

            # Helper: insert single DataFrame/Series or tuple
            def insert_timeseries(df, table_name):
                dfs = df if isinstance(df, tuple) else (df,)
                for idx, d in enumerate(dfs):
                    if d is None:
                        continue
                    d = d.copy()
                    d["result_id"] = int(result_id)
                    d["utc_time"] = pd.to_datetime(d.index)
                    d["array_name"] = array_names.get(str(idx))

                    # Convert all columns to native types
                    for col in d.columns:
                        if pd.api.types.is_numeric_dtype(d[col]) or pd.api.types.is_bool_dtype(d[col]):
                            d[col] = d[col].apply(lambda x: None if pd.isna(x) else x.item() if hasattr(x, "item") else x)
                        else:
                            d[col] = d[col].apply(lambda x: None if pd.isna(x) else x)

                    cols = ["result_id", "utc_time", "array_name"] + [c for c in d.columns if c not in ("result_id", "utc_time", "array_name")]
                    records = [tuple(row) for row in d[cols].to_numpy()]
                    query = f"""
                        INSERT INTO {table_name} ({', '.join(cols)})
                        VALUES %s
                        ON CONFLICT (result_id, utc_time, array_name) DO NOTHING
                    """
                    psycopg2.extras.execute_values(cur, query, records)

            
            # Insert all known fields with array-aware handling
            if result.ac is not None:
                # Handle Series case
                if isinstance(result.ac, pd.Series):
                    insert_timeseries(result.ac.to_frame(name="ac"), "ac_aoi")
                # Handle DataFrame case
                elif isinstance(result.ac, pd.DataFrame):
                    if "p_mp" in result.ac.columns:
                        df = result.ac.rename(columns={"p_mp": "ac"})
                        insert_timeseries(df, "ac_aoi")
                    elif "ac" in result.ac.columns:
                        insert_timeseries(result.ac, "ac_aoi")


            if hasattr(result, "aoi") and result.aoi is not None:
                aoi_tuple = result.aoi if isinstance(result.aoi, tuple) else (result.aoi,)
                mod_tuple = getattr(result, "aoi_modifier", None)
                if not isinstance(mod_tuple, tuple):
                    mod_tuple = (mod_tuple,) * len(aoi_tuple)
                dfs = []
                for aoi_data, aoi_mod in zip(aoi_tuple, mod_tuple):
                    if aoi_mod is None:
                        aoi_mod = pd.Series([None]*len(aoi_data), index=aoi_data.index)
                    dfs.append(pd.DataFrame({"aoi": aoi_data, "aoi_modifier": aoi_mod}, index=aoi_data.index))
                insert_timeseries(tuple(dfs), "ac_aoi")

            if hasattr(result, "airmass") and result.airmass is not None:
                dfs = result.airmass if isinstance(result.airmass, tuple) else (result.airmass,)
                insert_timeseries(dfs, "airmass")

            if hasattr(result, "cell_temperature") and result.cell_temperature is not None:
                dfs = tuple(ct.to_frame(name="temperature") for ct in result.cell_temperature) if isinstance(result.cell_temperature, tuple) else (result.cell_temperature.to_frame(name="temperature"),)
                insert_timeseries(dfs, "cell_temperature")

            if hasattr(result, "dc") and result.dc is not None:
                dfs = result.dc if isinstance(result.dc, tuple) else (result.dc,)
                insert_timeseries(dfs, "dc_output")

            if hasattr(result, "diode_params") and result.diode_params is not None:
                dfs = result.diode_params if isinstance(result.diode_params, tuple) else (result.diode_params,)
                insert_timeseries(dfs, "diode_params")

            if hasattr(result, "total_irrad") and result.total_irrad is not None:
                dfs = result.total_irrad if isinstance(result.total_irrad, tuple) else (result.total_irrad,)
                insert_timeseries(dfs, "total_irradiance")

            if hasattr(result, "solar_position") and result.solar_position is not None:
                dfs = result.solar_position if isinstance(result.solar_position, tuple) else (result.solar_position,)
                insert_timeseries(dfs, "solar_position")

            if hasattr(result, "weather") and result.weather is not None:
                dfs = result.weather if isinstance(result.weather, tuple) else (result.weather,)
                insert_timeseries(dfs, "weather")

        self.db.commit()
        return result_id

    def fetch_modelchain_result(self, result_id):
        result = {}
        with self.db.cursor() as cur:
            # Fetch metadata
            cur.execute("""
                SELECT simulation_name, description, created_at, albedo, losses, spectral_modifier, tracking
                FROM modelchain_results
                WHERE result_id = %s
            """, (result_id,))
            row = cur.fetchone()
            if not row:
                return None

            result.update({
                "simulation_name": row[0],
                "description": row[1],
                "created_at": row[2],
                "albedo": row[3],
                "losses": row[4],
                "spectral_modifier": row[5],
                "tracking": json.loads(row[6]) if row[6] else None
            })

            # Helper to fetch time-series and reassemble as tuple
            def fetch_timeseries(table_name):
                engine = sqlalchemy.create_engine(
                    f'postgresql+psycopg2://{config("DB_USER")}:{config("DB_PASS")}@{config("DB_HOST")}:{config("DB_PORT")}/{config("DB_NAME")}'
                )
                df = pd.read_sql(f"SELECT * FROM {table_name} WHERE result_id=%s ORDER BY utc_time, array_name", engine, params=(result_id,))
                if df.empty:
                    return None
                df.set_index("utc_time", inplace=True)
                array_groups = [g.drop(columns=["result_id", "array_name"]) for _, g in df.groupby("array_name")]
                return tuple(array_groups) if len(array_groups) > 1 else array_groups[0]

            # Fetch all fields
            result["ac_aoi"] = fetch_timeseries("ac_aoi")
            result["airmass"] = fetch_timeseries("airmass")
            result["cell_temperature"] = fetch_timeseries("cell_temperature")
            result["dc"] = fetch_timeseries("dc_output")
            result["diode_params"] = fetch_timeseries("diode_params")
            result["irradiance"] = fetch_timeseries("total_irradiance")
            result["solar_position"] = fetch_timeseries("solar_position")
            result["weather"] = fetch_timeseries("weather")

        return result



    def get_or_create_location(self, provider, latitude, longitude, elevation_m=None, timezone=None, tz_abbreviation=None, utc_offset_secs=None, model=None):
        """
        Insert or return existing location ID based on (provider, lat, lon).
        """
        with self.db.cursor() as cur:
            cur.execute("""
                INSERT INTO weather_location (
                    provider, model, latitude, longitude, elevation_m,
                    timezone, tz_abbreviation, utc_offset_secs
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (provider, latitude, longitude) DO UPDATE
                    SET updated_at = now()
                RETURNING id;
            """, (provider, model, latitude, longitude, elevation_m,
                  timezone, tz_abbreviation, utc_offset_secs))
            location_id = cur.fetchone()[0]
        self.db.commit()
        return location_id

  
    def insert_openmeteo_data(self, location_id, current_df, hourly_df, daily_df):
        """
        Insert current, hourly, and daily weather data efficiently.
        """
        with self.db.cursor() as cur:
            # --- Insert current snapshot ---
            if not current_df.empty:
                row = current_df.iloc[0]
                cur.execute("""
                    INSERT INTO weather_current (
                        location_id, observation_time, temperature_2m,
                        relative_humidity_2m, apparent_temperature,
                        precipitation, rain, showers, weather_code,
                        cloud_cover, wind_speed_10m, wind_direction_10m,
                        wind_gusts_10m
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    location_id,
                    pd.to_datetime(row["time"]).to_pydatetime(),
                    float(row.get("temperature_2m", 0)),
                    float(row.get("relative_humidity_2m", 0)),
                    float(row.get("apparent_temperature", 0)),
                    float(row.get("precipitation", 0)),
                    float(row.get("rain", 0)),
                    float(row.get("showers", 0)),
                    int(row.get("weather_code", 0)),
                    float(row.get("cloud_cover", 0)),
                    float(row.get("wind_speed_10m", 0)),
                    float(row.get("wind_direction_10m", 0)),
                    float(row.get("wind_gusts_10m", 0))
                ))

            # --- Insert hourly data ---
            if not hourly_df.empty:
                hourly_tuples = [
                    (
                        location_id,
                        pd.to_datetime(r["date"]).to_pydatetime(),
                        float(r.get("temperature_2m", 0)),
                        float(r.get("precipitation_probability", 0)),
                        float(r.get("precipitation", 0)),
                        float(r.get("rain", 0)),
                        float(r.get("showers", 0)),
                        float(r.get("shortwave_radiation", 0)),
                        float(r.get("diffuse_radiation", 0)),
                        float(r.get("direct_normal_irradiance", 0)),
                        float(r.get("sunshine_duration", 0))
                    )
                    for _, r in hourly_df.iterrows()
                ]
                psycopg2.extras.execute_values(cur, """
                    INSERT INTO weather_hourly (
                        location_id, time, temperature_2m, precipitation_probability,
                        precipitation, rain, showers, shortwave_radiation,
                        diffuse_radiation, direct_normal_irradiance, sunshine_duration
                    ) VALUES %s
                """, hourly_tuples)

            # --- Insert daily data ---
            if not daily_df.empty:
                daily_tuples = [
                    (
                        location_id,
                        pd.to_datetime(r["date"]).to_pydatetime(),
                        int(r.get("sunrise", 0)),
                        int(r.get("sunset", 0)),
                        float(r.get("daylight_duration", 0)),
                        float(r.get("sunshine_duration", 0)),
                        float(r.get("uv_index_max", 0)),
                        float(r.get("uv_index_clear_sky_max", 0)),
                        float(r.get("rain_sum", 0)),
                        float(r.get("showers_sum", 0)),
                        float(r.get("precipitation_sum", 0)),
                        float(r.get("precipitation_hours", 0)),
                        float(r.get("precipitation_probability_max", 0)),
                        float(r.get("shortwave_radiation_sum", 0)),
                        float(r.get("wind_direction_10m_dominant", 0))
                    )
                    for _, r in daily_df.iterrows()
                ]
                psycopg2.extras.execute_values(cur, """
                    INSERT INTO weather_daily (
                        location_id, time, sunrise, sunset, daylight_duration,
                        sunshine_duration, uv_index_max, uv_index_clear_sky_max,
                        rain_sum, showers_sum, precipitation_sum, precipitation_hours,
                        precipitation_probability_max, shortwave_radiation_sum,
                        wind_direction_10m_dominant
                    ) VALUES %s
                """, daily_tuples)

        self.db.commit()


    def fetch_openmeteo_data(self, lat: float, lon: float):
        """
        Retrieve and reconstruct current, hourly, and daily weather data 
        using SQLAlchemy and location coordinates.
        """
        engine = sqlalchemy.create_engine(
            f'postgresql+psycopg2://{config("DB_USER")}:{config("DB_PASS")}@{config("DB_HOST")}:{config("DB_PORT")}/{config("DB_NAME")}'
        )

        with engine.connect() as conn:
            # Step 1: Get location_id for the given coordinates
            location_query = sqlalchemy.sql.text("""
                SELECT * FROM weather_location
                WHERE ABS(latitude - :lat) < 0.0001 AND ABS(longitude - :lon) < 0.0001
                LIMIT 1
            """)
            location = conn.execute(location_query, {"lat": lat, "lon": lon}).fetchone()
            location_data = dict(location._mapping)


            if not location:
                raise ValueError(f"No location found for coordinates ({lat}, {lon})")

            location_id = location.id

            # Step 2: Retrieve weather data for that location_id
            current_df = pd.read_sql(
                sqlalchemy.sql.text("""
                    SELECT * FROM weather_current
                    WHERE location_id = :loc
                    ORDER BY observation_time DESC
                    LIMIT 1
                """),
                conn, params={"loc": location_id}
            )

            hourly_df = pd.read_sql(
                sqlalchemy.sql.text("""
                    SELECT time, temperature_2m, precipitation_probability,
                           precipitation, rain, showers, shortwave_radiation,
                           diffuse_radiation, direct_normal_irradiance, sunshine_duration
                    FROM weather_hourly
                    WHERE location_id = :loc
                    ORDER BY time ASC
                """),
                conn, params={"loc": location_id}
            )

            daily_df = pd.read_sql(
                sqlalchemy.sql.text("""
                    SELECT time, sunrise, sunset, daylight_duration,
                           sunshine_duration, uv_index_max, uv_index_clear_sky_max,
                           rain_sum, showers_sum, precipitation_sum, precipitation_hours,
                           precipitation_probability_max, shortwave_radiation_sum,
                           wind_direction_10m_dominant
                    FROM weather_daily
                    WHERE location_id = :loc
                    ORDER BY time ASC
                """),
                conn, params={"loc": location_id}
            )

        return location_data, current_df, hourly_df, daily_df


    def insert_air_quality_data(self, location_id, current_data, hourly_df):
        """
        Insert current and hourly air quality data into PostgreSQL.
        """
        row = current_data.iloc[0]

        # Helper to convert NaN/NaT to None
        def safe_float(val):
            if pd.isna(val):
                return None
            return float(val)

        with self.db.cursor() as cur:
            # --- Insert current snapshot ---
            cur.execute("""
                INSERT INTO air_quality_current (
                    location_id, observation_time, european_aqi, us_aqi, pm10, pm2_5,
                    carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone,
                    aerosol_optical_depth, dust, uv_index
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """, (
                location_id,
                pd.to_datetime(row["time"]).to_pydatetime(),
                safe_float(row["european_aqi"]), safe_float(row["us_aqi"]),
                safe_float(row["pm10"]), safe_float(row["pm2_5"]),
                safe_float(row["carbon_monoxide"]), safe_float(row["nitrogen_dioxide"]),
                safe_float(row["sulphur_dioxide"]), safe_float(row["ozone"]),
                safe_float(row["aerosol_optical_depth"]), safe_float(row["dust"]),
                safe_float(row["uv_index"])
            ))

            # --- Insert hourly data ---
            if not hourly_df.empty:
                hourly_tuples = [
                    (
                        location_id,
                        pd.to_datetime(r["date"]).to_pydatetime(),
                        safe_float(r["pm2_5"]), safe_float(r["carbon_monoxide"]), safe_float(r["carbon_dioxide"]),
                        safe_float(r["nitrogen_dioxide"]), safe_float(r["sulphur_dioxide"]),
                        safe_float(r["ozone"]), safe_float(r["dust"]), safe_float(r["uv_index"]), safe_float(r["pm10"])
                    )
                    for _, r in hourly_df.iterrows()
                ]

                psycopg2.extras.execute_values(cur, """
                    INSERT INTO air_quality_hourly (
                        location_id, time, pm2_5, carbon_monoxide, carbon_dioxide,
                        nitrogen_dioxide, sulphur_dioxide, ozone, dust, uv_index, pm10
                    ) VALUES %s
                """, hourly_tuples)

        self.db.commit()



    def fetch_air_quality_data(self, lat, lon):
        """
        Retrieve and reconstruct air quality data using SQLAlchemy.
        """
        engine = sqlalchemy.create_engine(
            f'postgresql+psycopg2://{config("DB_USER")}:{config("DB_PASS")}@'
            f'{config("DB_HOST")}:{config("DB_PORT")}/{config("DB_NAME")}'
        )

        with engine.connect() as conn:
            # --- Get location ID ---
            location_query = sqlalchemy.sql.text("""
                SELECT * FROM weather_location
                WHERE ABS(latitude - :lat) < 0.0001 AND ABS(longitude - :lon) < 0.0001
                LIMIT 1
            """)
            location = conn.execute(location_query, {"lat": lat, "lon": lon}).fetchone()
            location_data = dict(location._mapping)

            if not location:
                raise ValueError(f"No location found for coordinates ({lat}, {lon})")

            # --- Current data ---
            current_df = pd.read_sql(
                sqlalchemy.sql.text("""
                    SELECT * FROM air_quality_current
                    WHERE location_id = :loc
                    ORDER BY observation_time DESC
                    LIMIT 1
                """), conn, params={"loc": location.id}
            )

            # --- Hourly data ---
            hourly_df = pd.read_sql(
                sqlalchemy.sql.text("""
                    SELECT * FROM air_quality_hourly
                    WHERE location_id = :loc
                    ORDER BY time ASC
                """), conn, params={"loc": location.id}
            )

        return location_data, current_df, hourly_df

    def close(self):
        self.db.close()
