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


    def save_modelchain_result(self, result, simulation_name="Trial Simulation", description="Nice Description"):
        with self.db.cursor() as cur:
            # 1. Insert simulation metadata
            cur.execute("""
                INSERT INTO modelchain_results (simulation_name, description, albedo, losses, spectral_modifier, tracking)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING result_id
            """, (
                simulation_name,
                description,
                result.albedo[0] if isinstance(result.albedo, tuple) else result.albedo,
                result.losses,
                result.spectral_modifier,
                None if result.tracking is None else json.dumps(result.tracking)
            ))
            result_id = cur.fetchone()[0]

            # Helper to insert DataFrame/Series
            def insert_timeseries(df, table_name):
                df = df.copy()
                df["result_id"] = int(result_id)
                df["utc_time"] = pd.to_datetime(df.index).to_pydatetime()

                # Convert entire DataFrame to native Python types
                for col in df.columns:
                    # Handle numeric, boolean, and object columns
                    if pd.api.types.is_numeric_dtype(df[col]) or pd.api.types.is_bool_dtype(df[col]):
                        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x.item() if hasattr(x, "item") else x)
                    else:
                        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

                cols = ["result_id", "utc_time"] + [c for c in df.columns if c not in ("result_id", "utc_time")]
                df = df[cols]

                # Convert DataFrame to list of tuples for execute_values
                records = [tuple(row) for row in df.to_numpy()]
                query = f"INSERT INTO {table_name} ({', '.join(cols)}) VALUES %s ON CONFLICT (result_id, utc_time) DO NOTHING"

                psycopg2.extras.execute_values(cur, query, records)


            # Keep track of fields already stored
            mapped_fields = set()

            # 2. Insert known Series/DataFrames
            if hasattr(result, "ac") and result.ac is not None:
                insert_timeseries(result.ac.to_frame(name="ac"), "ac_aoi")
                mapped_fields.add("ac")

            if hasattr(result, "aoi") and result.aoi is not None:
                df = pd.DataFrame({
                    "aoi": result.aoi,
                    "aoi_modifier": getattr(result, "aoi_modifier", pd.Series([None]*len(result.aoi)))
                }, index=result.aoi.index)
                insert_timeseries(df, "ac_aoi")
                mapped_fields.update(["aoi", "aoi_modifier"])

            if hasattr(result, "airmass") and result.airmass is not None:
                insert_timeseries(result.airmass, "airmass")
                mapped_fields.add("airmass")

            if hasattr(result, "cell_temperature") and result.cell_temperature is not None:
                insert_timeseries(result.cell_temperature.to_frame(name="temperature"), "cell_temperature")
                mapped_fields.add("cell_temperature")

            if hasattr(result, "dc") and result.dc is not None:
                insert_timeseries(result.dc, "dc_output")
                mapped_fields.add("dc")

            if hasattr(result, "diode_params") and result.diode_params is not None:
                insert_timeseries(result.diode_params, "diode_params")
                mapped_fields.add("diode_params")

            if hasattr(result, "total_irrad") and result.total_irrad is not None:
                insert_timeseries(result.total_irrad, "total_irradiance")
                mapped_fields.add("total_irrad")

            if hasattr(result, "solar_position") and result.solar_position is not None:
                insert_timeseries(result.solar_position, "solar_position")
                mapped_fields.add("solar_position")

            if hasattr(result, "weather") and result.weather is not None:
                insert_timeseries(result.weather, "weather")
                mapped_fields.add("weather")

        self.db.commit()
        return result_id


    def fetch_modelchain_result(self, result_id):
        """
        Fetch the full ModelChainResult from the database for a given result_id.

        Returns a dictionary with all fields, Series/DataFrames, and constants
        """
        result = {}

        with self.db.cursor() as cur:
            # 1. Fetch metadata and constants
            cur.execute("""
                SELECT simulation_name, description, albedo, losses, spectral_modifier, tracking
                FROM modelchain_results
                WHERE result_id = %s
            """, (result_id,))
            row = cur.fetchone()
            if row is None:
                logger.error(f"No ModelChainResult found for result_id={result_id}")
            
            result["simulation_name"] = row[0]
            result["description"] = row[1]
            result["albedo"] = row[2]
            result["losses"] = row[3]
            result["spectral_modifier"] = row[4]
            result["tracking"] = json.loads(row[5]) if row[5] else None

            # Helper to fetch time-series data into DataFrame
            def fetch_timeseries(table_name):
                sql = f"SELECT * FROM {table_name} WHERE result_id = %s ORDER BY utc_time"
                engine = sqlalchemy.create_engine(
                    f'postgresql+psycopg2://{config("DB_USER")}:{config("DB_PASS")}@{config("DB_HOST")}:{config("DB_PORT")}/{config("DB_NAME")}'
                )
                df = pd.read_sql(sql, engine, params=(result_id,))
                if df.empty:
                    return None
                df.set_index("utc_time", inplace=True)
                df.drop(columns="result_id", inplace=True)
                return df

            # 2. Fetch core time-series tables
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
