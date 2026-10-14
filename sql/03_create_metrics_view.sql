CREATE OR REPLACE VIEW climatewell_neighborhood_metrics AS

WITH park_access AS (

    SELECT
        n.id,

        ST_Union(
            ST_Intersection(
                n.geometry,
                ST_Transform(
                    ST_Buffer(
                        ST_Transform(p.geometry, 32636),
                        300
                    ),
                    4326
                )
            )
        ) AS accessible_area

    FROM neighborhoods n

    LEFT JOIN parks p
        ON ST_DWithin(
            n.geometry::geography,
            p.geometry::geography,
            300
        )

    GROUP BY n.id
),

base_data AS (

    SELECT
        n.id,
        n.name AS neighborhood,
        ps.population,

        (
            ps.population
            /
            (
                ST_Area(n.geometry::geography)
                / 1000000.0
            )
        ) AS population_density,

        (
            100.0 *
            COALESCE(
                ST_Area(pa.accessible_area::geography),
                0
            )
            /
            ST_Area(n.geometry::geography)
        ) AS park_access_percent

    FROM neighborhoods n

    JOIN population_stats ps
        ON ps.neighborhood_id = n.id

    LEFT JOIN park_access pa
        ON pa.id = n.id

    WHERE ps.year = 2025
),

normalized AS (

    SELECT
        *,

        100.0 *
        (
            population_density
            - MIN(population_density) OVER ()
        )
        /
        NULLIF(
            MAX(population_density) OVER ()
            - MIN(population_density) OVER (),
            0
        ) AS density_risk_score,

        100.0 - park_access_percent
            AS park_access_deficit_score

    FROM base_data
)

SELECT
    id,
    neighborhood,
    population,

    ROUND(
        population_density::numeric,
        0
    ) AS population_density_per_km2,

    ROUND(
        park_access_percent::numeric,
        2
    ) AS park_access_300m_percent,

    ROUND(
        density_risk_score::numeric,
        2
    ) AS density_risk_score,

    ROUND(
        park_access_deficit_score::numeric,
        2
    ) AS park_access_deficit_score,

    ROUND(
        (
            density_risk_score * 0.50
            +
            park_access_deficit_score * 0.50
        )::numeric,
        2
    ) AS climatewell_priority_score

FROM normalized;