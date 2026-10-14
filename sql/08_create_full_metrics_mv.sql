DROP MATERIALIZED VIEW IF EXISTS climatewell_full_metrics_mv;

CREATE MATERIALIZED VIEW climatewell_full_metrics_mv AS

SELECT
    id,
    neighborhood,
    population,
    population_density_per_km2,
    park_access_300m_percent,
    density_risk_score,
    park_access_deficit_score,
    avg_summer_max_temp,
    hottest_day_temp,
    hot_days_35c,
    very_hot_days_38c,
    total_summer_days,
    heat_exposure_score,
    climatewell_score

FROM climatewell_full_metrics;


CREATE UNIQUE INDEX idx_climatewell_full_metrics_mv_id
ON climatewell_full_metrics_mv (id);


CREATE INDEX idx_climatewell_full_metrics_mv_score
ON climatewell_full_metrics_mv (climatewell_score);