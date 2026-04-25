from pathlib import Path
import logging

ROOT_DIR = Path(__file__).parent.parent
DATA_RAW = ROOT_DIR / "data" / "raw"
DATA_PROCESSED = ROOT_DIR / "data" / "processed"
OUTPUT_FIGURES = ROOT_DIR / "output" / "figures"
OUTPUT_TABLES = ROOT_DIR / "output" / "tables"

DIRS = [DATA_RAW, DATA_PROCESSED, OUTPUT_FIGURES, OUTPUT_TABLES]

# CRS definitions
CRS_GEO = "EPSG:4326"       # WGS84 geographic — for loading and Folium
CRS_PROJ = "EPSG:32718"     # UTM Zone 18S — metric CRS for Peru, used in distance calculations


def setup_dirs():
    for d in DIRS:
        d.mkdir(parents=True, exist_ok=True)


def get_logger(name: str) -> logging.Logger:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    return logging.getLogger(name)


def normalize_col(series):
    """Min-max normalization to [0, 1]. Returns 0 everywhere if range is zero."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return series * 0.0
    return (series - mn) / (mx - mn)
