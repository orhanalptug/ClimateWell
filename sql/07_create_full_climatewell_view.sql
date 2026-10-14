DROP VIEW IF EXISTS climatewell_full_metrics;

CREATE VIEW climatewell_full_metrics AS

WITH summer_temperature AS (

    SELECT
        neighborhood_id,

        AVG(max_temperature_c) AS avg_summer_max_temp,

        MAX(max_temperature_c) AS hottest_day_temp,

        COUNT(*) FILTER (
            WHERE max_temperature_c >= 35
        ) AS hot_days_35c,

        COUNT(*) FILTER (
            WHERE max_temperature_c >= 38
        ) AS very_hot_days_38c,

        COUNT(*) AS total_summer_days

    FROM temperature_records

    GROUP BY neighborhood_id
),

base_data AS (

    SELECT
        m.id,
        m.neighborhood,
        m.population,
        m.population_density_per_km2,
        m.park_access_300m_percent,
        m.density_risk_score,
        m.park_access_deficit_score,

        st.avg_summer_max_temp,
        st.hottest_day_temp,
        st.hot_days_35c,
        st.very_hot_days_38c,
        st.total_summer_days,

        (
            100.0
            * st.hot_days_35c
            / NULLIF(st.total_summer_days, 0)
        ) AS heat_exposure_score

    FROM climatewell_neighborhood_metrics m

    JOIN summer_temperature st
        ON st.neighborhood_id = m.id
)

SELECT
    id,
    neighborhood,
    population,
    population_density_per_km2,
    park_access_300m_percent,
    density_risk_score,
    park_access_deficit_score,

    ROUND(
        avg_summer_max_temp::numeric,
        2
    ) AS avg_summer_max_temp,

    ROUND(
        hottest_day_temp::numeric,
        2
    ) AS hottest_day_temp,

    hot_days_35c,
    very_hot_days_38c,
    total_summer_days,

    ROUND(
        heat_exposure_score::numeric,
        2
    ) AS heat_exposure_score,

    ROUND(
        (
            park_access_deficit_score * 0.40
            +
            density_risk_score * 0.30
            +
            heat_exposure_score * 0.30
        )::numeric,
        2
    ) AS climatewell_score

FROM base_data;