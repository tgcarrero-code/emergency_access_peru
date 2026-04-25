import pandas as pd
import numpy as np
import geopandas as gpd
from src.utils import normalize_col, OUTPUT_TABLES, DATA_PROCESSED, get_logger

log = get_logger(__name__)

WEIGHTS_BASE = {"fds": 0.33, "eas": 0.33, "sas": 0.34}
WEIGHTS_ALT  = {"fds": 0.20, "eas": 0.20, "sas": 0.60}


def compute_scores(
    district_summary: pd.DataFrame,
    districts_gdf: gpd.GeoDataFrame,
) -> gpd.GeoDataFrame:
    df = district_summary.copy()

    # ── Component scores ──────────────────────────────────────────────────────
    df["fds"] = normalize_col(df["n_facilities"])

    if "emergencias_total" in df.columns:
        df["eas"] = normalize_col(np.log1p(df["emergencias_total"]))
    else:
        df["eas"] = 0.0
        log.warning("emergencias_total not found; EAS set to 0.")

    if "mean_dist_km" in df.columns:
        df["sas"] = 1 - normalize_col(df["mean_dist_km"])
    else:
        df["sas"] = 0.0
        log.warning("mean_dist_km not found; SAS set to 0.")

    df["ehas_base"] = (
        WEIGHTS_BASE["fds"] * df["fds"] +
        WEIGHTS_BASE["eas"] * df["eas"] +
        WEIGHTS_BASE["sas"] * df["sas"]
    )
    df["ehas_alt"] = (
        WEIGHTS_ALT["fds"] * df["fds"] +
        WEIGHTS_ALT["eas"] * df["eas"] +
        WEIGHTS_ALT["sas"] * df["sas"]
    )

    p20 = df["ehas_base"].quantile(0.20)
    p80 = df["ehas_base"].quantile(0.80)
    df["access_class"] = pd.cut(
        df["ehas_base"],
        bins=[-np.inf, p20, p80, np.inf],
        labels=["Underserved", "Moderate", "Well-served"],
    )

    df["rank_base"] = df["ehas_base"].rank(ascending=False)
    df["rank_alt"]  = df["ehas_alt"].rank(ascending=False)
    df["rank_shift"] = df["rank_base"] - df["rank_alt"]

    keep = [
        "ubigeo", "n_facilities", "emergencias_total", "n_centros_poblados",
        "poblacion_total", "mean_dist_km", "max_dist_km", "pct_cp_over30km",
        "fds", "eas", "sas", "ehas_base", "ehas_alt",
        "access_class", "rank_base", "rank_alt", "rank_shift",
    ]
    keep = [c for c in keep if c in df.columns]
    df = df[keep]

    dist_cols = [c for c in districts_gdf.columns if c != "geometry"] + ["geometry"]
    gdf = districts_gdf[dist_cols].merge(df, on="ubigeo", how="left")

    df.to_csv(OUTPUT_TABLES / "district_scores.csv", index=False)
    gdf.to_file(DATA_PROCESSED / "district_scores.gpkg", driver="GPKG")
    log.info(f"Scores computed for {df['ubigeo'].nunique():,} districts.")
    log.info(
        f"  Underserved: {(df['access_class'] == 'Underserved').sum()} | "
        f"Moderate: {(df['access_class'] == 'Moderate').sum()} | "
        f"Well-served: {(df['access_class'] == 'Well-served').sum()}"
    )
    return gdf
