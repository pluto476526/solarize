import time
import logging
from datetime import datetime, timedelta

import pandas as pd
from psycopg2 import extras

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
                extras.execute_batch(cur, query, records, page_size=self.page_size)
            
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


    def close(self):
        self.db.close()
