-- ============================================================
-- ClimateWell v0.1
-- Initial PostgreSQL / PostGIS database schema
-- ============================================================


-- ------------------------------------------------------------
-- POSTGIS
-- ------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS postgis;


-- ------------------------------------------------------------
-- NEIGHBORHOODS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS neighborhoods (

    id SERIAL PRIMARY KEY,

    object_id INTEGER,

    name VARCHAR(100) NOT NULL,

    identity_no INTEGER,

    district_id VARCHAR(100),

    geometry GEOMETRY(POLYGON, 4326)

);


-- ------------------------------------------------------------
-- PARKS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS parks (

    id SERIAL PRIMARY KEY,

    osm_id BIGINT NOT NULL,

    osm_type VARCHAR(20),

    name VARCHAR(200),

    geometry GEOMETRY(POLYGON, 4326)

);


-- ------------------------------------------------------------
-- POPULATION STATS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS population_stats (

    id SERIAL PRIMARY KEY,

    neighborhood_id INTEGER NOT NULL
        REFERENCES neighborhoods(id)
        ON DELETE CASCADE,

    year INTEGER NOT NULL,

    population INTEGER NOT NULL
        CHECK (population >= 0),

    source VARCHAR(150) NOT NULL,

    UNIQUE (
        neighborhood_id,
        year
    )

);


-- ------------------------------------------------------------
-- TEMPERATURE RECORDS
-- ------------------------------------------------------------

CREATE TABLE IF NOT EXISTS temperature_records (

    id SERIAL PRIMARY KEY,

    neighborhood_id INTEGER NOT NULL
        REFERENCES neighborhoods(id)
        ON DELETE CASCADE,

    recorded_date DATE NOT NULL,

    max_temperature_c NUMERIC(5, 2),

    min_temperature_c NUMERIC(5, 2),

    source VARCHAR(100) NOT NULL,

    UNIQUE (
        neighborhood_id,
        recorded_date
    )

);