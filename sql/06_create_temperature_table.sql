CREATE TABLE IF NOT EXISTS temperature_records (
    id SERIAL PRIMARY KEY,

    neighborhood_id INTEGER NOT NULL
        REFERENCES neighborhoods(id),

    recorded_date DATE NOT NULL,

    max_temperature_c NUMERIC(5,2),

    min_temperature_c NUMERIC(5,2),

    source VARCHAR(100) NOT NULL,

    UNIQUE (
        neighborhood_id,
        recorded_date
    )
);
