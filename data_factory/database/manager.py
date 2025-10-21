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
                    row["parameter"],
                    row["value"],
                    row["units"],
                    row["lon"],
                    row["lat"],
                    row["elev"],
                    row["source"],
                )
                for row in df.to_dict(orient="records")
            ]

            query = queries.insert_irradiance_data_query()
            
            with self.db.cursor() as cur:
                psycopg2.extras.execute_batch(cur, query, records, page_size=self.page_size)
            
            self.db.commit()
            logger.info(f"Inserted {len(records)} records to DB.")

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

    def save_modelchain_result(self, result, array_names, simulation_name="Trial Simulation", description="Nice Description"):
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
                json.dumps(result.spectral_modifier) if isinstance(result.spectral_modifier, tuple) else result.spectral_modifier,
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
            if hasattr(result, "ac") and result.ac is not None:
                insert_timeseries(result.ac.to_frame(name="ac"), "ac_aoi")

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
                SELECT simulation_name, description, albedo, losses, spectral_modifier, tracking
                FROM modelchain_results
                WHERE result_id = %s
            """, (result_id,))
            row = cur.fetchone()
            if not row:
                return None

            result.update({
                "simulation_name": row[0],
                "description": row[1],
                "albedo": row[2],
                "losses": row[3],
                "spectral_modifier": row[4],
                "tracking": json.loads(row[5]) if row[5] else None
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
            result["total_irrad"] = fetch_timeseries("total_irradiance")
            result["solar_position"] = fetch_timeseries("solar_position")
            result["weather"] = fetch_timeseries("weather")

        return result



    def fetch_ac_aoi_data(self, result_id):
        try:
            query = queries.fetch_ac_aoi_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_airmass_data(self, result_id):
        try:
            query = queries.fetch_airmass_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_cell_temp_data(self, result_id):
        try:
            query = queries.fetch_cell_temp_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_dc_output_data(self, result_id):
        try:
            query = queries.fetch_dc_output_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_diode_params_data(self, result_id):
        try:
            query = queries.fetch_diode_params_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_total_irradiance_data(self, result_id):
        try:
            query = queries.fetch_total_irradiance_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_solar_position_data(self, result_id):
        try:
            query = queries.fetch_solar_position_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()

    def fetch_weather_data(self, result_id):
        try:
            query = queries.fetch_weather_query(result_id=result_id)
            
            with self.db.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
            
            return pd.DataFrame(rows, columns=columns)

        except Exception as e:
            logger.error(f"No data: {e}")
            return pd.DataFrame()


    def close(self):
        self.db.close()
