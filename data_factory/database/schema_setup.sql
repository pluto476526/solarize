-- data_factory/schema_setup.sql
-- pkibuka@milky-way.space

-- ===============================================================
-- Enable TimescaleDB Extension
-- ===============================================================
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- ===============================================================
-- 1. Irradiance Data Table (Hypertable)
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
    albedo JSONB,
    losses NUMERIC,
    spectral_modifier JSONB,
    tracking JSONB
);

-- ===============================================================
-- 3. PVlib Time-Series Tables
-- Each table includes `array_name` and a composite PK
-- ===============================================================

-- AC & AOI
CREATE TABLE IF NOT EXISTS ac_aoi (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    ac NUMERIC,
    i_sc NUMERIC,
    v_oc NUMERIC,
    i_mp NUMERIC,
    v_mp NUMERIC,
    i_x NUMERIC,
    i_xx NUMERIC,
    aoi NUMERIC,
    aoi_modifier NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('ac_aoi', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Airmass
CREATE TABLE IF NOT EXISTS airmass (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    airmass_relative NUMERIC,
    airmass_absolute NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('airmass', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Cell Temperature
CREATE TABLE IF NOT EXISTS cell_temperature (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    temperature NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('cell_temperature', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- DC Output
CREATE TABLE IF NOT EXISTS dc_output (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    i_sc NUMERIC,
    v_oc NUMERIC,
    i_mp NUMERIC,
    v_mp NUMERIC,
    p_mp NUMERIC,
    i_x NUMERIC,
    i_xx NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('dc_output', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Diode Parameters
CREATE TABLE IF NOT EXISTS diode_params (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    I_L NUMERIC,
    I_o NUMERIC,
    R_s NUMERIC,
    R_sh NUMERIC,
    nNsVth NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('diode_params', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Total Irradiance
CREATE TABLE IF NOT EXISTS total_irradiance (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    poa_global NUMERIC,
    poa_direct NUMERIC,
    poa_diffuse NUMERIC,
    poa_sky_diffuse NUMERIC,
    poa_ground_diffuse NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('total_irradiance', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Solar Position
CREATE TABLE IF NOT EXISTS solar_position (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    zenith NUMERIC,
    azimuth NUMERIC,
    elevation NUMERIC,
    apparent_zenith NUMERIC,
    apparent_elevation NUMERIC,
    equation_of_time NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('solar_position', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);

-- Weather Data
CREATE TABLE IF NOT EXISTS weather (
    result_id INT NOT NULL REFERENCES modelchain_results(result_id),
    utc_time TIMESTAMPTZ NOT NULL,
    array_name TEXT,
    ghi NUMERIC,
    dni NUMERIC,
    dhi NUMERIC,
    temp_air NUMERIC,
    wind_speed NUMERIC,
    PRIMARY KEY (result_id, utc_time, array_name)
);
SELECT create_hypertable('weather', 'utc_time', chunk_time_interval => INTERVAL '1 month', if_not_exists => TRUE);


CREATE TABLE IF NOT EXISTS weather_location (
    id BIGSERIAL PRIMARY KEY,
    provider TEXT NOT NULL,
    model TEXT,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION,
    timezone TEXT,
    tz_abbreviation TEXT,
    utc_offset_secs INTEGER,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- Enforce uniqueness for get_or_create_location
ALTER TABLE weather_location ADD CONSTRAINT unique_location UNIQUE(provider, latitude, longitude);



CREATE TABLE IF NOT EXISTS weather_current (
    id BIGSERIAL PRIMARY KEY,
    location_id BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    observation_time TIMESTAMPTZ NOT NULL,
    temperature_2m DOUBLE PRECISION,
    relative_humidity_2m DOUBLE PRECISION,
    apparent_temperature DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    rain DOUBLE PRECISION,
    showers DOUBLE PRECISION,
    weather_code SMALLINT,
    cloud_cover DOUBLE PRECISION,
    wind_speed_10m DOUBLE PRECISION,
    wind_direction_10m DOUBLE PRECISION,
    wind_gusts_10m DOUBLE PRECISION,
    fetched_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS weather_hourly (
    id BIGSERIAL NOT NULL,
    location_id BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    time TIMESTAMPTZ NOT NULL,
    temperature_2m DOUBLE PRECISION,
    precipitation_probability DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    rain DOUBLE PRECISION,
    showers DOUBLE PRECISION,
    shortwave_radiation DOUBLE PRECISION,
    diffuse_radiation DOUBLE PRECISION,
    direct_normal_irradiance DOUBLE PRECISION,
    sunshine_duration DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);



CREATE TABLE weather_daily (
    id BIGSERIAL NOT NULL,
    location_id BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    time TIMESTAMPTZ NOT NULL,
    sunrise BIGINT,
    sunset BIGINT,
    daylight_duration DOUBLE PRECISION,
    sunshine_duration DOUBLE PRECISION,
    uv_index_max DOUBLE PRECISION,
    uv_index_clear_sky_max DOUBLE PRECISION,
    rain_sum DOUBLE PRECISION,
    showers_sum DOUBLE PRECISION,
    precipitation_sum DOUBLE PRECISION,
    precipitation_hours DOUBLE PRECISION,
    precipitation_probability_max DOUBLE PRECISION,
    shortwave_radiation_sum DOUBLE PRECISION,
    wind_direction_10m_dominant DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);



CREATE TABLE IF NOT EXISTS air_quality_current (
    id BIGSERIAL PRIMARY KEY,
    location_id BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    observation_time TIMESTAMPTZ NOT NULL,
    european_aqi DOUBLE PRECISION,
    us_aqi DOUBLE PRECISION,
    pm10 DOUBLE PRECISION,
    pm2_5 DOUBLE PRECISION,
    carbon_monoxide DOUBLE PRECISION,
    nitrogen_dioxide DOUBLE PRECISION,
    sulphur_dioxide DOUBLE PRECISION,
    ozone DOUBLE PRECISION,
    aerosol_optical_depth DOUBLE PRECISION,
    dust DOUBLE PRECISION,
    uv_index DOUBLE PRECISION,
    fetched_at TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS air_quality_hourly (
    id BIGSERIAL PRIMARY KEY,
    location_id BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    time TIMESTAMPTZ NOT NULL,
    pm2_5 DOUBLE PRECISION,
    carbon_monoxide DOUBLE PRECISION,
    carbon_dioxide DOUBLE PRECISION,
    nitrogen_dioxide DOUBLE PRECISION,
    sulphur_dioxide DOUBLE PRECISION,
    ozone DOUBLE PRECISION,
    dust DOUBLE PRECISION,
    uv_index DOUBLE PRECISION,
    pm10 DOUBLE PRECISION,
    created_at TIMESTAMPTZ DEFAULT now()
);




-- ===============================================================
-- 4. Permissions
-- ===============================================================
GRANT USAGE ON SCHEMA public TO pluto;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pluto;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pluto;







