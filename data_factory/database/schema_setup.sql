-- data_factory/schema_setup.sql
-- pkibuka@milky-way.space

CREATE EXTENSION IF NOT EXISTS timescaledb;

CREATE TABLE IF NOT EXISTS irradiance_data (
   insert_date DATE NOT NULL,
   parameter TEXT NOT NULL,
   value DOUBLE PRECISION,
   units TEXT,
   lon DOUBLE PRECISION,
   lat DOUBLE PRECISION,
   elevation DOUBLE PRECISION,
   source TEXT,
   PRIMARY KEY (insert_date, parameter, lon, lat)
);

SELECT create_hypertable(
    'irradiance_data',
    'insert_date',
    chunk_time_interval => INTERVAL '6 months'
);

GRANT USAGE ON SCHEMA public TO pluto;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pluto;


-- psql -u pluto -d solarize -f schema_setup.sql


