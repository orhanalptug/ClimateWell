CREATE TABLE parks (
    id SERIAL PRIMARY KEY,
    osm_id BIGINT NOT NULL,
    osm_type VARCHAR(20),
    name VARCHAR(200),
    geometry GEOMETRY(POLYGON, 4326)
);
