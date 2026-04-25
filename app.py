import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from pathlib import Path
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
PROCESSED = ROOT / "data" / "processed"
FIGURES = ROOT / "output" / "figures"
TABLES = ROOT / "output" / "tables"

st.set_page_config(
    page_title="Emergency Healthcare Access — Peru",
    page_icon="🏥",
    layout="wide",
)


@st.cache_data
def load_scores_table():
    path = TABLES / "district_scores.csv"
    if path.exists():
        return pd.read_csv(path, dtype={"ubigeo": str})
    return pd.DataFrame()

@st.cache_data
def load_scores_geo():
    path = PROCESSED / "district_scores.gpkg"
    if path.exists():
        return gpd.read_file(path)
    return gpd.GeoDataFrame()

@st.cache_data
def load_ipress_geo():
    path = PROCESSED / "ipress_clean.csv"
    if path.exists():
        df = pd.read_csv(path)
        if "latitud" in df.columns and "longitud" in df.columns:
            import geopandas as gpd
            return gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df["longitud"], df["latitud"]), crs="EPSG:4326"
            )
    return gpd.GeoDataFrame()

def show_image(name: str, caption: str = ""):
    path = FIGURES / name
    if path.exists():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.warning(f"Figure not found: {name}. Run the pipeline first.")


tab1, tab2, tab3, tab4 = st.tabs([
    "📋 Data & Methodology",
    "📊 Static Analysis",
    "🗺️ GeoSpatial Results",
    "🔍 Interactive Exploration",
])

# TAB 1 — Data & Methodology


with tab1:
    st.title("Emergency Healthcare Access Inequality in Peru")
    st.subheader("Problem Statement")
    st.markdown("""
    Emergency healthcare access is not uniform across Peru. Districts in remote
    Amazonian or Andean areas face very different conditions than Lima's urban
    core. This project builds a district-level Emergency Healthcare Access Score
    (EHAS) to quantify and compare those differences using four public datasets.
    """)

    st.subheader("Data Sources")
    st.markdown("""
    | Dataset | Source | Key variables |
    |---|---|---|
    | IPRESS Health Facilities | MINSA | Name, category, coordinates, ubigeo |
    | Emergency Care Production | MINSA | Facility code, total emergency consultations |
    | Centros Poblados | INEI | Name, coordinates, population |
    | District Boundaries | IGN/MINSA | Polygon geometries, ubigeo |
    """)

    st.subheader("Cleaning Summary")
    st.markdown("""
    - Standardised column names across all datasets via alias mapping.
    - Removed IPRESS records with missing or out-of-range coordinates (bounding
      box: lat −18.35 to −0.03, lon −81.33 to −68.65).
    - Removed duplicate IPRESS by `codigo_renaes`.
    - Emergency production aggregated to one row per facility (sum of monthly
      consultations where applicable).
    - Centros Poblados: removed duplicates on (lat, lon); null populations set to 0.
    - Distritos: dropped geometries that were null or invalid.
    - All ubigeo codes zero-padded to 6 digits for consistent joining.
    """)

    st.subheader("Methodological Decisions")
    st.markdown("""
    **Composite score (EHAS)** combines three components, each normalised to [0, 1]:

    | Component | Abbreviation | Measures |
    |---|---|---|
    | Facility Density Score | FDS | Number of IPRESS in district |
    | Emergency Activity Score | EAS | log₁⁺¹(emergency consultations), normalised |
    | Spatial Access Score | SAS | 1 − normalised(mean distance from centros poblados to nearest IPRESS) |

    **Baseline:**   EHAS = 0.33·FDS + 0.33·EAS + 0.34·SAS
    **Alternative:** EHAS = 0.20·FDS + 0.20·EAS + 0.60·SAS

    The log transform on emergency activity reduces the distorting effect of
    Lima, which handles an orders-of-magnitude larger volume than any other
    district. The alternative specification tests the hypothesis that geographic
    access is the dominant barrier in a country with Peru's geography.

    **CRS:**
    - EPSG:4326 (WGS84) for loading, storage, and Folium maps.
    - EPSG:32718 (UTM Zone 18S) for distance calculations — this metric
      projection minimises distortion across Peru's latitude range.
    """)

    st.subheader("Limitations")
    st.markdown("""
    - Facility counts do not distinguish capacity (a small health post vs a
      hospital both count as 1 facility).
    - Emergency consultations may reflect demand rather than supply — a district
      with no facility records zero consultations, not zero need.
    - Road-based travel time was not used; straight-line distance underestimates
      real access barriers in mountainous terrain.
    - Population data from Centros Poblados may be outdated (last census-based).
    """)


# TAB 2 — Static Analysis

with tab2:
    st.title("Static Analysis")

    st.subheader("Score Distribution")
    st.markdown("""
    **Why this chart?** A histogram reveals skewness — in Peru, we expect a
    right-skewed distribution because Lima districts concentrate resources while
    rural districts cluster near zero. This confirms whether our metric captures
    real inequality rather than an artefact of normalisation.
    """)
    show_image("score_distribution.png", "Distribution of Baseline and Alternative EHAS Scores")

    st.subheader("Facility Density vs Spatial Access")
    st.markdown("""
    **Why this chart?** A scatter plot of FDS vs SAS tests correlation between
    facility presence and physical proximity. In highly unequal systems, these
    can diverge: urban districts score high on FDS but some peri-urban districts
    score high on SAS simply because they are small and dense. This is more
    informative than a bar chart because it reveals structural patterns, not
    just rankings.
    """)
    show_image("fds_vs_sas_scatter.png", "Facility Density Score vs Spatial Access Score")

    st.subheader("Component Distribution by Access Class")
    st.markdown("""
    **Why this chart?** Box plots confirm that the three access classes are
    statistically separated on each individual component — a necessary validation
    of the composite classification. A violin plot would show the same information
    but is harder to read for non-specialist audiences.
    """)
    show_image("boxplots_by_class.png", "Component Score Distribution by Access Class")

    st.subheader("Top and Bottom Districts")
    st.markdown("""
    **Why this chart?** Bar charts make the best and worst performers concrete
    and nameable — essential for policy communication. A table alone lacks
    visual impact; a choropleth alone lacks legibility at the district name level.
    """)
    show_image("top_bottom_districts.png", "Top 20 and Bottom 20 Districts by Baseline EHAS Score")

    st.subheader("Sensitivity: Rank Shift")
    st.markdown("""
    **Why this chart?** A scatter of baseline rank vs rank shift directly
    answers Question 4. It shows which districts gain or lose when distance
    weight triples, and whether the methodology reverses conclusions for
    many districts. This is more informative than a correlation coefficient
    because it reveals *which* districts are sensitive.
    """)
    show_image("rank_shift_sensitivity.png", "Rank Shift: Baseline vs Alternative Specification")


# TAB 3 — GeoSpatial Results

with tab3:
    st.title("GeoSpatial Results")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Baseline Access Score")
        show_image("choropleth_ehas_baseline.png", "Baseline EHAS Score by District")
    with col2:
        st.subheader("Access Classification")
        show_image("classification_map.png", "Underserved / Moderate / Well-served Districts")

    st.subheader("District-Level Results Table")
    df = load_scores_table()
    if not df.empty:
        display_cols = [
            c for c in [
                "ubigeo", "nombre_distrito", "nombre_departamento",
                "n_facilities", "emergencias_total", "mean_dist_km",
                "ehas_base", "ehas_alt", "access_class", "rank_base",
            ] if c in df.columns
        ]
        st.dataframe(
            df[display_cols]
            .sort_values("ehas_base", ascending=False)
            .reset_index(drop=True),
            use_container_width=True,
            height=400,
        )

        st.subheader("Summary Statistics")
        col_a, col_b, col_c = st.columns(3)
        if "access_class" in df.columns:
            col_a.metric("Underserved districts", int((df["access_class"] == "Underserved").sum()))
            col_b.metric("Moderate districts", int((df["access_class"] == "Moderate").sum()))
            col_c.metric("Well-served districts", int((df["access_class"] == "Well-served").sum()))
    else:
        st.info("Run the pipeline to generate district scores.")

# TAB 4 — Interactive Exploration

with tab4:
    st.title("Interactive Exploration")

    st.subheader("Interactive Access Score Map")
    choropleth_path = FIGURES / "map_choropleth.html"
    if choropleth_path.exists():
        with open(choropleth_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=600, scrolling=True)
    else:
        gdf = load_scores_geo()
        if not gdf.empty:
            from src.visualization import make_folium_choropleth
            m = make_folium_choropleth(gdf)
            st_folium(m, width=900, height=550)
        else:
            st.info("Run the pipeline to generate the interactive map.")

    st.subheader("Facilities & Centros Poblados Map")
    facilities_path = FIGURES / "map_facilities.html"
    if facilities_path.exists():
        with open(facilities_path, "r", encoding="utf-8") as f:
            st.components.v1.html(f.read(), height=600, scrolling=True)
    else:
        st.info("Run the pipeline to generate the facilities map.")

    st.subheader("Baseline vs Alternative: District Comparison")
    df = load_scores_table()
    if not df.empty and "ehas_base" in df.columns and "ehas_alt" in df.columns:
        dep_options = ["All"] + sorted(df["nombre_departamento"].dropna().unique().tolist()) \
            if "nombre_departamento" in df.columns else ["All"]
        selected_dep = st.selectbox("Filter by department:", dep_options)

        df_view = df if selected_dep == "All" else df[df["nombre_departamento"] == selected_dep]
        df_view = df_view.sort_values("ehas_base", ascending=False).head(50)

        label_col = "nombre_distrito" if "nombre_distrito" in df_view.columns else "ubigeo"
        fig, ax = plt.subplots(figsize=(12, max(5, len(df_view) * 0.22)))
        x = range(len(df_view))
        ax.plot(x, df_view["ehas_base"].values, "o-", label="Baseline", color="#2166ac", markersize=4)
        ax.plot(x, df_view["ehas_alt"].values, "s--", label="Alternative", color="#d73027", markersize=4)
        ax.set_xticks(list(x))
        ax.set_xticklabels(df_view[label_col].values, rotation=90, fontsize=7)
        ax.set_ylabel("EHAS Score")
        ax.set_title(f"Baseline vs Alternative — {selected_dep} (top 50 by baseline score)")
        ax.legend()
        plt.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        st.subheader("Largest Rank Shifts")
        if "rank_shift" in df.columns:
            show_cols = [c for c in ["nombre_distrito", "nombre_departamento",
                                     "ehas_base", "ehas_alt", "rank_base", "rank_alt", "rank_shift"]
                         if c in df.columns]
            st.dataframe(
                df[show_cols].sort_values("rank_shift", key=abs, ascending=False).head(30),
                use_container_width=True,
            )
    else:
        st.info("Run the pipeline to populate the comparison view.")
