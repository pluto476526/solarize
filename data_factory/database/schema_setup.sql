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
-- 3. Tuple-Support Time-Series Tables
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
    id               BIGSERIAL PRIMARY KEY,
    provider         TEXT NOT NULL,
    model            TEXT,
    latitude         DOUBLE PRECISION NOT NULL,
    longitude        DOUBLE PRECISION NOT NULL,
    elevation_m      DOUBLE PRECISION,
    timezone         TEXT,
    tz_abbreviation  TEXT,
    utc_offset_secs  INTEGER,
    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now()
);

-- Enforce uniqueness for get_or_create_location
ALTER TABLE weather_location ADD CONSTRAINT unique_location UNIQUE(provider, latitude, longitude);



CREATE TABLE IF NOT EXISTS weather_current (
    id                             BIGSERIAL PRIMARY KEY,
    location_id                    BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    observation_time               TIMESTAMPTZ NOT NULL,
    temperature_2m                 DOUBLE PRECISION,
    relative_humidity_2m           DOUBLE PRECISION,        -- current_relative_humidity_2m (%)
    apparent_temperature           DOUBLE PRECISION,        -- current_apparent_temperature (°C)
    precipitation                  DOUBLE PRECISION,        -- current_precipitation (mm)
    rain                           DOUBLE PRECISION,        -- current_rain (mm)
    showers                        DOUBLE PRECISION,        -- current_showers (mm)
    weather_code                   SMALLINT,                -- current_weather_code (code)
    cloud_cover                    DOUBLE PRECISION,        -- current_cloud_cover (%)
    wind_speed_10m                 DOUBLE PRECISION,        -- current_wind_speed_10m (m/s)
    wind_direction_10m             DOUBLE PRECISION,        -- current_wind_direction_10m (degrees)
    wind_gusts_10m                 DOUBLE PRECISION,        -- current_wind_gusts_10m (m/s)
    fetched_at                     TIMESTAMPTZ DEFAULT now()
);


CREATE TABLE IF NOT EXISTS weather_hourly (
    id                           BIGSERIAL NOT NULL,
    location_id                  BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    time                         TIMESTAMPTZ NOT NULL,    -- corresponds to hourly.Time() -> pandas timestamps
    temperature_2m               DOUBLE PRECISION,        -- hourly_temperature_2m
    precipitation_probability    DOUBLE PRECISION,        -- hourly_precipitation_probability (% or 0-1 depending on source)
    precipitation                DOUBLE PRECISION,        -- hourly_precipitation (mm)
    rain                         DOUBLE PRECISION,        -- hourly_rain (mm)
    showers                      DOUBLE PRECISION,        -- hourly_showers (mm)
    shortwave_radiation          DOUBLE PRECISION,        -- hourly_shortwave_radiation (W/m2)
    diffuse_radiation            DOUBLE PRECISION,        -- hourly_diffuse_radiation (W/m2)
    direct_normal_irradiance     DOUBLE PRECISION,        -- hourly_direct_normal_irradiance (W/m2)
    sunshine_duration            DOUBLE PRECISION,        -- hourly_sunshine_duration (seconds)
    created_at                   TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);



CREATE TABLE weather_daily (
    id                                  BIGSERIAL NOT NULL,
    location_id                         BIGINT NOT NULL REFERENCES weather_location(id) ON DELETE CASCADE,
    time                                 TIMESTAMPTZ NOT NULL,   -- corresponds to daily.Time() -> start of day
    sunrise                             BIGINT,                 -- daily_sunrise (seconds since epoch) or use TIMESTAMPTZ if you prefer
    sunset                              BIGINT,                 -- daily_sunset (seconds since epoch) or TIMESTAMPTZ
    daylight_duration                   DOUBLE PRECISION,       -- daily_daylight_duration (seconds)
    sunshine_duration                   DOUBLE PRECISION,       -- daily_sunshine_duration (seconds)
    uv_index_max                        DOUBLE PRECISION,       -- daily_uv_index_max
    uv_index_clear_sky_max              DOUBLE PRECISION,       -- daily_uv_index_clear_sky_max
    rain_sum                            DOUBLE PRECISION,       -- daily_rain_sum (mm)
    showers_sum                         DOUBLE PRECISION,       -- daily_showers_sum (mm)
    precipitation_sum                   DOUBLE PRECISION,       -- daily_precipitation_sum (mm) -- keep for compatibility
    precipitation_hours                 DOUBLE PRECISION,       -- daily_precipitation_hours (hours or seconds per source)
    precipitation_probability_max       DOUBLE PRECISION,       -- daily_precipitation_probability_max (%)
    shortwave_radiation_sum             DOUBLE PRECISION,       -- daily_shortwave_radiation_sum (Wh/m2 or W/m2*hours depending on source)
    wind_direction_10m_dominant         DOUBLE PRECISION,       -- daily_wind_direction_10m_dominant (degrees)
    created_at                          TIMESTAMPTZ DEFAULT now(),
    PRIMARY KEY (id)
);



-- ===============================================================
-- 4. Permissions
-- ===============================================================
GRANT USAGE ON SCHEMA public TO pluto;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO pluto;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO pluto;







