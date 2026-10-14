CREATE INDEX IF NOT EXISTS idx_neighborhoods_geometry
ON neighborhoods
USING GIST (geometry);


CREATE INDEX IF NOT EXISTS idx_parks_geometry
ON parks
USING GIST (geometry);


CREATE INDEX IF NOT EXISTS idx_population_stats_neighborhood_year
ON population_stats (neighborhood_id, year);


CREATE INDEX IF NOT EXISTS idx_neighborhoods_geography
ON neighborhoods
USING GIST ((geometry::geography));


CREATE INDEX IF NOT EXISTS idx_parks_geography
ON parks
USING GIST ((geometry::geography));