import os
import json

import pandas as pd
import psycopg2
import pydeck as pdk
import streamlit as st
import streamlit.components.v1 as components

from dotenv import load_dotenv


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="ClimateWell",
    page_icon="🌱",
    layout="wide"
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


conn = get_connection()


# ============================================================
# LOAD DATA
# ============================================================

@st.cache_data
def load_metrics():

    query = """
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
        FROM climatewell_full_metrics_mv
        ORDER BY climatewell_score DESC;
    """

    return pd.read_sql(
        query,
        conn
    )


@st.cache_data
def load_neighborhood_map():

    query = """
        SELECT
            n.id,
            n.name AS neighborhood,
            m.population,
            m.population_density_per_km2,
            m.park_access_300m_percent,
            m.hot_days_35c,
            m.heat_exposure_score,
            m.climatewell_score,

            ST_Y(
                ST_Centroid(n.geometry)
            ) AS latitude,

            ST_X(
                ST_Centroid(n.geometry)
            ) AS longitude,

            ST_AsGeoJSON(
                n.geometry
            ) AS geometry

        FROM neighborhoods n

        JOIN climatewell_full_metrics_mv m
            ON m.id = n.id

        ORDER BY n.name;
    """

    return pd.read_sql(
        query,
        conn
    )


@st.cache_data
def load_parks():

    query = """
        SELECT
            p.id,
            COALESCE(
                p.name,
                'Unnamed Park'
            ) AS park_name,

            ST_AsGeoJSON(
                p.geometry
            ) AS geometry

        FROM parks p

        WHERE EXISTS (
            SELECT 1
            FROM neighborhoods n
            WHERE ST_Intersects(
                p.geometry,
                n.geometry
            )
        );
    """

    return pd.read_sql(
        query,
        conn
    )


def refresh_metrics():

    cursor = conn.cursor()

    cursor.execute(
        """
        REFRESH MATERIALIZED VIEW
        climatewell_full_metrics_mv;
        """
    )

    conn.commit()
    cursor.close()

    st.cache_data.clear()


# ============================================================
# GEOMETRY HELPERS
# ============================================================

def geometry_to_coordinates(geometry_text):

    if not geometry_text:
        return []

    geometry = json.loads(
        geometry_text
    )

    geometry_type = geometry.get(
        "type"
    )

    coordinates = geometry.get(
        "coordinates",
        []
    )

    if geometry_type == "Polygon":

        if coordinates:
            return coordinates[0]

    if geometry_type == "MultiPolygon":

        if coordinates and coordinates[0]:
            return coordinates[0][0]

    return []


def score_to_color(score):

    score = float(score)

    score = max(
        0,
        min(score, 100)
    )

    # 0 = green
    # 50 = yellow
    # 100 = red

    if score <= 50:

        ratio = score / 50

        red = int(
            255 * ratio
        )

        green = 200

    else:

        ratio = (
            score - 50
        ) / 50

        red = 255

        green = int(
            200 * (1 - ratio)
        )

    return [
        red,
        green,
        40,
        190
    ]


# ============================================================
# PREPARE DATA
# ============================================================

metrics_df = load_metrics()

map_df = load_neighborhood_map()

parks_df = load_parks()


map_df["coordinates"] = (
    map_df["geometry"]
    .apply(
        geometry_to_coordinates
    )
)


parks_df["coordinates"] = (
    parks_df["geometry"]
    .apply(
        geometry_to_coordinates
    )
)


map_df = map_df[
    map_df["coordinates"]
    .apply(len) >= 3
].copy()


parks_df = parks_df[
    parks_df["coordinates"]
    .apply(len) >= 3
].copy()


map_df["fill_color"] = (
    map_df["climatewell_score"]
    .apply(
        score_to_color
    )
)


map_df["climatewell_score"] = (
    map_df["climatewell_score"]
    .astype(float)
    .round(2)
)


map_df["park_access_300m_percent"] = (
    map_df[
        "park_access_300m_percent"
    ]
    .astype(float)
    .round(2)
)


map_df["hot_days_35c"] = (
    map_df[
        "hot_days_35c"
    ]
    .astype(int)
)


map_df["population"] = (
    map_df[
        "population"
    ]
    .astype(int)
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title(
    "🌱 ClimateWell"
)


st.sidebar.caption(
    "Urban Climate & Well-being Analytics"
)


selected_neighborhood = (
    st.sidebar.selectbox(
        "Select neighborhood",
        metrics_df[
            "neighborhood"
        ].tolist()
    )
)


show_parks = (
    st.sidebar.checkbox(
        "Show mapped parks",
        value=True
    )
)


focus_selected = (
    st.sidebar.checkbox(
        "Focus map on selected neighborhood",
        value=False
    )
)


st.sidebar.divider()


if st.sidebar.button(
    "🔄 Refresh calculated metrics"
):

    try:

        refresh_metrics()

        st.sidebar.success(
            "Metrics refreshed successfully."
        )

        st.rerun()

    except Exception as error:

        conn.rollback()

        st.sidebar.error(
            f"Refresh failed: {error}"
        )


# ============================================================
# SELECTED DATA
# ============================================================

selected_data = (
    metrics_df[
        metrics_df["neighborhood"]
        == selected_neighborhood
    ]
    .iloc[0]
)


selected_map_df = (
    map_df[
        map_df["neighborhood"]
        == selected_neighborhood
    ]
    .copy()
)


# ============================================================
# HEADER
# ============================================================

st.title(
    "🌱 ClimateWell"
)


st.subheader(
    "Urban Climate & Well-being Analytics"
)


st.caption(
    "A PostgreSQL/PostGIS-based prototype combining "
    "park accessibility, population density and "
    "summer heat exposure."
)


st.info(
    "ClimateWell is a comparative exploratory prototype. "
    "It is not an official health, climate-risk or "
    "municipal assessment system."
)


# ============================================================
# TABS
# ============================================================

tab_overview, tab_explorer, tab_data = st.tabs(
    [
        "🗺️ Overview",
        "🔎 Neighborhood Explorer",
        "📊 Data & Methodology"
    ]
)


# ============================================================
# TAB 1 — OVERVIEW
# ============================================================

with tab_overview:

    highest_priority = (
        metrics_df.iloc[0]
    )


    average_score = float(
        metrics_df[
            "climatewell_score"
        ].mean()
    )


    average_park_access = float(
        metrics_df[
            "park_access_300m_percent"
        ].mean()
    )


    total_population = int(
        metrics_df[
            "population"
        ].sum()
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    with col1:

        st.metric(
            "Highest Priority",
            highest_priority[
                "neighborhood"
            ]
        )


    with col2:

        st.metric(
            "Average Score",
            f"{average_score:.1f}"
        )


    with col3:

        st.metric(
            "Average Park Access",
            f"{average_park_access:.1f}%"
        )


    with col4:

        st.metric(
            "Pilot Population",
            f"{total_population:,}"
        )


    st.divider()


    st.header(
        "ClimateWell Priority Map"
    )


    st.caption(
        "Green represents lower comparative priority, "
        "yellow represents intermediate values, "
        "and red represents higher comparative priority."
    )


    layers = []


    # --------------------------------------------------------
    # NEIGHBORHOOD LAYER
    # --------------------------------------------------------

    neighborhood_layer = pdk.Layer(

        "PolygonLayer",

        data=map_df,

        get_polygon="coordinates",

        get_fill_color="fill_color",

        get_line_color=[
            70,
            70,
            70,
            230
        ],

        get_line_width=2,

        line_width_min_pixels=1,

        pickable=True,

        auto_highlight=True,

        highlight_color=[
            255,
            255,
            255,
            180
        ]
    )


    layers.append(
        neighborhood_layer
    )


    # --------------------------------------------------------
    # PARK LAYER
    # --------------------------------------------------------

    if show_parks:

        park_layer = pdk.Layer(

            "PolygonLayer",

            data=parks_df,

            get_polygon="coordinates",

            get_fill_color=[
                20,
                170,
                70,
                155
            ],

            get_line_color=[
                20,
                130,
                60,
                220
            ],

            get_line_width=1,

            line_width_min_pixels=1,

            pickable=False
        )


        layers.append(
            park_layer
        )


    # --------------------------------------------------------
    # SELECTED NEIGHBORHOOD OUTLINE
    # --------------------------------------------------------

    selected_layer = pdk.Layer(

        "PolygonLayer",

        data=selected_map_df,

        get_polygon="coordinates",

        filled=False,

        stroked=True,

        get_line_color=[
            255,
            255,
            255,
            255
        ],

        get_line_width=7,

        line_width_min_pixels=4,

        pickable=False
    )


    layers.append(
        selected_layer
    )


    # --------------------------------------------------------
    # MAP POSITION
    # --------------------------------------------------------

    if (
        focus_selected
        and not selected_map_df.empty
    ):

        map_latitude = float(
            selected_map_df.iloc[0][
                "latitude"
            ]
        )

        map_longitude = float(
            selected_map_df.iloc[0][
                "longitude"
            ]
        )

        map_zoom = 12.0

    else:

        map_latitude = 39.90
        map_longitude = 32.82
        map_zoom = 10.7


    view_state = pdk.ViewState(

        latitude=map_latitude,

        longitude=map_longitude,

        zoom=map_zoom,

        pitch=0,

        bearing=0
    )


    # --------------------------------------------------------
    # TOOLTIP
    # --------------------------------------------------------

    tooltip = {

        "html": """
            <b>{neighborhood}</b><br>
            Score: <b>{climatewell_score}</b><br>
            Park access: <b>{park_access_300m_percent}%</b><br>
            ≥35°C days: <b>{hot_days_35c}</b>
        """,

        "style": {
            "backgroundColor": "#111827",
            "color": "#FFFFFF",
            "fontSize": "12px",
            "padding": "6px",
            "borderRadius": "4px"
        }
    }


    deck = pdk.Deck(

        layers=layers,

        initial_view_state=view_state,

        tooltip=tooltip,

        map_style="dark"
    )


    # --------------------------------------------------------
    # PYDECK HTML RENDER
    # --------------------------------------------------------

    deck_html = deck.to_html(
        as_string=True
    )


    components.html(
        deck_html,
        height=650,
        scrolling=False
    )


    # --------------------------------------------------------
    # LEGEND
    # --------------------------------------------------------

    st.markdown(
        """
**Priority scale:**  
🟢 Lower priority &nbsp;&nbsp;&nbsp;
🟡 Intermediate &nbsp;&nbsp;&nbsp;
🔴 Higher priority

🌳 Green polygons represent mapped OpenStreetMap parks.
"""
    )


    st.divider()


    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    st.header(
        "ClimateWell Score Ranking"
    )


    ranking_df = (
        metrics_df[
            [
                "neighborhood",
                "climatewell_score"
            ]
        ]
        .set_index(
            "neighborhood"
        )
    )


    st.bar_chart(
        ranking_df
    )


# ============================================================
# TAB 2 — NEIGHBORHOOD EXPLORER
# ============================================================

with tab_explorer:

    st.header(
        selected_neighborhood
    )


    col1, col2, col3, col4 = (
        st.columns(4)
    )


    with col1:

        st.metric(
            "Population",
            f"{int(selected_data['population']):,}"
        )


    with col2:

        st.metric(
            "Population Density",
            (
                f"{float(selected_data['population_density_per_km2']):,.0f} / km²"
            )
        )


    with col3:

        st.metric(
            "300m Park Access",
            (
                f"{float(selected_data['park_access_300m_percent']):.1f}%"
            )
        )


    with col4:

        st.metric(
            "Days ≥35°C",
            int(
                selected_data[
                    "hot_days_35c"
                ]
            )
        )


    col1, col2, col3 = (
        st.columns(3)
    )


    with col1:

        st.metric(
            "Average Summer Max",
            (
                f"{float(selected_data['avg_summer_max_temp']):.2f} °C"
            )
        )


    with col2:

        st.metric(
            "Hottest Day",
            (
                f"{float(selected_data['hottest_day_temp']):.2f} °C"
            )
        )


    with col3:

        st.metric(
            "ClimateWell Score",
            (
                f"{float(selected_data['climatewell_score']):.2f}"
            )
        )


    st.divider()


    st.subheader(
        "Score Components"
    )


    component_df = pd.DataFrame(
        {
            "Indicator": [
                "Population Density Risk",
                "Park Access Deficit",
                "Heat Exposure"
            ],

            "Score": [
                float(
                    selected_data[
                        "density_risk_score"
                    ]
                ),

                float(
                    selected_data[
                        "park_access_deficit_score"
                    ]
                ),

                float(
                    selected_data[
                        "heat_exposure_score"
                    ]
                )
            ]
        }
    )


    st.bar_chart(
        component_df.set_index(
            "Indicator"
        )
    )


    st.subheader(
        "Why this score?"
    )


    density = float(
        selected_data[
            "population_density_per_km2"
        ]
    )


    park_access = float(
        selected_data[
            "park_access_300m_percent"
        ]
    )


    hot_days = int(
        selected_data[
            "hot_days_35c"
        ]
    )


    climatewell_score = float(
        selected_data[
            "climatewell_score"
        ]
    )


    st.markdown(
        f"""
**{selected_neighborhood}** has a ClimateWell Score of
**{climatewell_score:.2f}**.

Its current indicators include:

- **{density:,.0f} people/km²** population density
- **{park_access:.1f}%** of the neighborhood area within
  300 meters of a mapped park
- **{hot_days} days ≥35°C** during the analyzed summer period

The prototype score combines:

**40% Park Access Deficit  
+ 30% Population Density Risk  
+ 30% Heat Exposure**
"""
    )


# ============================================================
# TAB 3 — DATA & METHODOLOGY
# ============================================================

with tab_data:

    st.header(
        "Pilot Dataset"
    )


    display_df = (
        metrics_df
        .drop(
            columns=[
                "id"
            ]
        )
        .rename(
            columns={
                "neighborhood":
                    "Neighborhood",

                "population":
                    "Population",

                "population_density_per_km2":
                    "Population Density / km²",

                "park_access_300m_percent":
                    "Park Access 300m (%)",

                "density_risk_score":
                    "Density Risk Score",

                "park_access_deficit_score":
                    "Park Access Deficit",

                "avg_summer_max_temp":
                    "Average Summer Max °C",

                "hottest_day_temp":
                    "Highest Max °C",

                "hot_days_35c":
                    "Days ≥35°C",

                "very_hot_days_38c":
                    "Days ≥38°C",

                "total_summer_days":
                    "Summer Days",

                "heat_exposure_score":
                    "Heat Exposure Score",

                "climatewell_score":
                    "ClimateWell Score"
            }
        )
    )


    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    csv_data = (
        display_df
        .to_csv(
            index=False
        )
        .encode(
            "utf-8-sig"
        )
    )


    st.download_button(
        label="⬇ Download Pilot Dataset",
        data=csv_data,
        file_name=(
            "climatewell_pilot_metrics.csv"
        ),
        mime="text/csv"
    )


    st.divider()


    st.header(
        "Methodology"
    )


    st.markdown(
        """
### ClimateWell v0.1

ClimateWell combines three prototype indicators.

#### 🌳 Park Access Deficit — 40%

Mapped park polygons are obtained from OpenStreetMap.

PostGIS calculates how much of a neighborhood lies within
**300 meters of a mapped park**.

A lower park-access percentage produces a higher
park-access-deficit score.

---

#### 👥 Population Density Risk — 30%

Population density is calculated as:

`Population / Neighborhood Area (km²)`

Values are normalized comparatively across the
current eight-neighborhood pilot dataset.

---

#### 🌡️ Heat Exposure — 30%

Historical daily maximum temperatures are obtained from
the Open-Meteo Historical Weather API.

Heat exposure is calculated as:

`Days ≥35°C / Total Summer Days × 100`

The 35°C threshold is a prototype analytical threshold
and should not be interpreted as a universal health threshold.

---

### Final Formula

`ClimateWell Score =`

`0.40 × Park Access Deficit`

`+ 0.30 × Population Density Risk`

`+ 0.30 × Heat Exposure`
"""
    )


    st.divider()


    st.header(
        "Data Sources"
    )


    st.markdown(
        """
- **Neighborhood boundaries:** Ankara Metropolitan Municipality
- **Mapped parks:** OpenStreetMap
- **Population:** 2025 neighborhood population data
- **Historical temperature:** Open-Meteo Historical Weather API
- **Spatial analysis:** PostgreSQL + PostGIS
"""
    )


    st.divider()


    st.header(
        "Limitations"
    )


    st.markdown(
        """
ClimateWell v0.1 is an exploratory prototype.

Current limitations include:

- only eight neighborhoods are included,
- OpenStreetMap park completeness may vary,
- only mapped parks are currently included,
- other green-space categories are not fully covered,
- 300-meter accessibility is geometric rather than pedestrian-network accessibility,
- temperature values are grid-based historical estimates,
- neighborhood-level physical temperature sensors are not used,
- population-density normalization depends on the pilot dataset,
- indicator weights are prototype design choices,
- the ClimateWell Score has not been scientifically, medically or municipally validated.

Results should therefore be interpreted as
**comparative exploratory indicators**.
"""
    )