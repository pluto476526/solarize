-- data_factory/schema_setup.sql
-- pkibuka@milky-way.space

-- Enable TimescaleDB extension (for time-series optimization)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ===============================================================
-- 1. Irradiance Data Table (hypertable)
-- ===============================================================
CREATE TABLE IF NOT EXISTS irradiance_data (
    insert_date DATE NOT NULL,
    parameter TEXT NOT NULL,
    value DOUBLE PRECISION,
    units TEXT,
    lon DOUBLE PRECISION NOT NULL,
    lat DOUBLE PRECISION NOT NULL,
    elevation DOUBLE PRECISION,
    source TEXT,
    PRIMARY KEY (insert_date, parameter, lon, lat)
);

-- Convert to hypertable for time-series performance
SELECT create_hypertable(
    'irradiance_data',
    'insert_date',
    chunk_time_interval => INTERVAL '6 months',
    if_not_exists => TRUE
);

-- ===============================================================
-- 2. PVlib ModelChain Result Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS modelchain_results (
    result_id SERIAL PRIMARY KEY,
    simulation_name TEXT,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    albedo NUMERIC,
    losses NUMERIC,
    spectral_modifier NUMERIC,
    tracking JSONB
);

-- ===============================================================
-- 3. PVlib AC & AOI Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS ac_aoi (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    ac NUMERIC,
    aoi NUMERIC,
    aoi_modifier NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('ac_aoi', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 4. PVlib Airmass Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS airmass (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    airmass_relative NUMERIC,
    airmass_absolute NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('airmass', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 5. PVlib Cell Temparatures Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS cell_temperature (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    temperature NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('cell_temperature', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 6. PVlib DC Output Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS dc_output (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    i_sc NUMERIC,
    v_oc NUMERIC,
    i_mp NUMERIC,
    v_mp NUMERIC,
    p_mp NUMERIC,
    i_x NUMERIC,
    i_xx NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('dc_output', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 7. PVlib Diode Parameters Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS diode_params (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    I_L NUMERIC,
    I_o NUMERIC,
    R_s NUMERIC,
    R_sh NUMERIC,
    nNsVth NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('diode_params', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 8. PVlib Total Irradiance Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS total_irradiance (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    poa_global NUMERIC,
    poa_direct NUMERIC,
    poa_diffuse NUMERIC,
    poa_sky_diffuse NUMERIC,
    poa_ground_diffuse NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('total_irradiance', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 9. PVlib DC Solar Position Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS solar_position (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    zenith NUMERIC,
    azimuth NUMERIC,
    elevation NUMERIC,
    apparent_zenith NUMERIC,
    apparent_elevation NUMERIC,
    equation_of_time NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('solar_position', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 10. PVlib Weather Data Table
-- ===============================================================
CREATE TABLE IF NOT EXISTS weather (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    ghi NUMERIC,
    dni NUMERIC,
    dhi NUMERIC,
    temp_air NUMERIC,
    wind_speed NUMERIC,
    PRIMARY KEY (result_id, utc_time)
);

SELECT create_hypertable('weather', 'utc_time', chunk_time_interval => interval '1 month', if_not_exists => TRUE);

-- ===============================================================
-- 11. Permissions
-- ===============================================================
GRANT USAGE ON SCHEMA public TO pluto;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pluto;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pluto;

-- Usage:
-- psql -U pluto -d solarize -f schema_setup.sql
