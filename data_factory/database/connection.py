import logging
import psycopg2
from decouple import config

logger = logging.getLogger(__name__)


class DatabaseConnection:
    def __init__(self):
        dbname = config("DB_NAME")
        user = config("DB_USER")
        password = config("DB_PASS")
        host = config("DB_HOST", default="localhost")
        port = config("DB_PORT", default=5432)

        try:
            self.conn = psycopg2.connect(
                dbname=dbname, user=user, password=password, host=host, port=port
            )
            logger.warning("DatabaseConnection: Connected to database")

        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def cursor(self):
        return self.conn.cursor()

    def commit(self):
        self.conn.commit()

    def rollback(self):
        self.conn.rollback()

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("DatabaseConnection: Closed connection")
