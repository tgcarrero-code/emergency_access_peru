import pandas as pd
import geopandas as gpd
import numpy as np
from scipy.spatial import KDTree
from src.utils import DATA_PROCESSED, CRS_GEO, CRS_PROJ, get_logger

log = get_logger(__name__)


def make_ipress_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitud"], df["latitud"]),
        crs=CRS_GEO,
    )
    return gdf


def make_cp_gdf(df: pd.DataFrame) -> gpd.GeoDataFrame:
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitud"], df["latitud"]),
        crs=CRS_GEO,
    )
    return gdf


def assign_to_districts(
    points_gdf: gpd.GeoDataFrame,
    districts_gdf: gpd.GeoDataFrame,
    point_label: str = "points",
) -> gpd.GeoDataFrame:
    """
    Spatial join: assign each point to the district it falls within.
    Points that fall outside any district boundary are dropped with a warning.
    """
    log.info(f"Assigning {point_label} to districts...")
    assert points_gdf.crs == districts_gdf.crs, "CRS mismatch before spatial join"

    dist_cols = ["ubigeo", "nombre_distrito", "nombre_provincia", "nombre_departamento", "geometry"]
    dist_cols = [c for c in dist_cols if c in districts_gdf.columns]

    joined = gpd.sjoin(
        points_gdf,
        districts_gdf[dist_cols],
        how="left",
        predicate="within",
    )
    n_unmatched = joined["ubigeo"].isna().sum() if "ubigeo" in joined.columns else 0
    if n_unmatched > 0:
        log.warning(f"  {n_unmatched:,} {point_label} did not fall within any district boundary.")
    log.info(f"  Assigned {len(joined) - n_unmatched:,} / {len(joined):,} {point_label}")
    return joined


def nearest_facility_distance(
    cp_gdf: gpd.GeoDataFrame,
    ipress_gdf: gpd.GeoDataFrame,
) -> pd.Series:
    """
    For each populated center, compute distance (in km) to the nearest IPRESS.
    Uses UTM Zone 18S projection for accurate metric distances in Peru.
    Returns a pd.Series indexed like cp_gdf.
    """
    log.info("Computing nearest-facility distances (UTM 18S)...")
    cp_proj = cp_gdf.to_crs(CRS_PROJ)
    ip_proj = ipress_gdf.to_crs(CRS_PROJ)

    cp_coords = np.array(list(zip(cp_proj.geometry.x, cp_proj.geometry.y)))
    ip_coords = np.array(list(zip(ip_proj.geometry.x, ip_proj.geometry.y)))

    tree = KDTree(ip_coords)
    distances_m, _ = tree.query(cp_coords, k=1)
    distances_km = distances_m / 1000.0
    log.info(f"  Mean nearest distance: {distances_km.mean():.1f} km")
    return pd.Series(distances_km, index=cp_gdf.index, name="dist_nearest_km")


def build_district_spatial_summary(
    ipress_gdf: gpd.GeoDataFrame,
    cp_gdf: gpd.GeoDataFrame,
    emergencia_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate all spatial information to district level.

    Returns a DataFrame with one row per district (ubigeo) containing:
      - n_facilities:          number of IPRESS in the district
      - emergencias_total:     total emergency consultations (joined via codigo_renaes)
      - n_centros_poblados:    number of populated centers
      - poblacion_total:       total population of populated centers
      - mean_dist_km:          mean distance from CP to nearest IPRESS
      - max_dist_km:           max distance from CP to nearest IPRESS
      - pct_cp_over30km:       % of populated centers more than 30 km from an IPRESS
    """
    log.info("Building district-level spatial summary...")

    # 1. Facility counts per district
    fac_agg = (
        ipress_gdf.groupby("ubigeo")
        .size()
        .reset_index(name="n_facilities")
    )

    # 2. Emergency production — join to ipress on codigo_renaes, then aggregate to district
    if "codigo_renaes" in ipress_gdf.columns and not emergencia_df.empty:
        ipress_emerg = ipress_gdf[["ubigeo", "codigo_renaes"]].merge(
            emergencia_df, on="codigo_renaes", how="left"
        )
        emerg_agg = (
            ipress_emerg.groupby("ubigeo")["emergencias_total"]
            .sum()
            .reset_index()
        )
    else:
        emerg_agg = pd.DataFrame(columns=["ubigeo", "emergencias_total"])

    # 3. Populated center aggregates per district
    cp_dist_col = "ubigeo" if "ubigeo" in cp_gdf.columns else "ubigeo_distrito"
    cp_temp = cp_gdf.copy()
    if "ubigeo_distrito" in cp_temp.columns and "ubigeo" not in cp_temp.columns:
        cp_temp = cp_temp.rename(columns={"ubigeo_distrito": "ubigeo"})

    cp_agg = cp_temp.groupby("ubigeo").agg(
        n_centros_poblados=("dist_nearest_km", "count"),
        mean_dist_km=("dist_nearest_km", "mean"),
        max_dist_km=("dist_nearest_km", "max"),
        poblacion_total=("poblacion", "sum") if "poblacion" in cp_temp.columns else ("dist_nearest_km", "count"),
    ).reset_index()

    pct_over30 = (
        cp_temp[cp_temp["dist_nearest_km"] > 30]
        .groupby("ubigeo")
        .size()
        .div(cp_temp.groupby("ubigeo").size())
        .reset_index(name="pct_cp_over30km")
    )

    # 4. Merge everything
    summary = fac_agg
    for tbl in [emerg_agg, cp_agg, pct_over30]:
        if not tbl.empty:
            summary = summary.merge(tbl, on="ubigeo", how="outer")
    summary = summary.fillna(0)
    summary["ubigeo"] = summary["ubigeo"].astype(str).str.zfill(6)

    log.info(f"  District spatial summary: {len(summary):,} districts")
    summary.to_csv(DATA_PROCESSED / "district_spatial_summary.csv", index=False)
    return summary
