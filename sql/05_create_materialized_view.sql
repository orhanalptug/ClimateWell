DROP MATERIALIZED VIEW IF EXISTS climatewell_metrics_mv;

CREATE MATERIALIZED VIEW climatewell_metrics_mv AS

SELECT
    id,
    neighborhood,
    population,
    population_density_per_km2,
    park_access_300m_percent,
    density_risk_score,
    park_access_deficit_score,
    climatewell_priority_score

FROM climatewell_neighborhood_metrics;


CREATE UNIQUE INDEX idx_climatewell_metrics_mv_id
ON climatewell_metrics_mv (id);


CREATE INDEX idx_climatewell_metrics_mv_priority
ON climatewell_metrics_mv (climatewell_priority_score);