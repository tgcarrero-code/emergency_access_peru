import pandas as pd
import geopandas as gpd
from pathlib import Path
from src.utils import DATA_RAW, CRS_GEO, get_logger

log = get_logger(__name__)


def _find(name_patterns: list[str]) -> Path:
    for pattern in name_patterns:
        matches = list(DATA_RAW.glob(f"*{pattern}*"))
        if matches:
            return matches[0]
    raise FileNotFoundError(
        f"Could not find a file matching any of {name_patterns} in {DATA_RAW}.\n"
    )

def load_ipress() -> pd.DataFrame:
    path = _find(["ipress", "IPRESS"])
    log.info(f"Loading IPRESS from {path.name}")
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, encoding="latin-1")
    log.info(f"  → {len(df):,} rows, columns: {list(df.columns)}")
    return df

def load_emergencia() -> pd.DataFrame:
    path = _find(["emergencia", "produccion", "EMERGENCIA", "PRODUCCION", "ConsultaC1", "consulta"])
    log.info(f"Loading Emergencia from {path.name}")
    if path.suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path, dtype=str)
    else:
        df = pd.read_csv(path, dtype=str, encoding="latin-1", sep = ";")
    log.info(f"  → {len(df):,} rows, columns: {list(df.columns)}")
    return df

def load_centros_poblados():
    candidates = list(DATA_RAW.rglob("*.shp"))
    # busca el que tenga CCPP en el nombre
    for c in candidates:
        if "CCPP" in c.name or "ccpp" in c.name:
            path = c
            break
    else:
        raise FileNotFoundError("No se encontró el shapefile de Centros Poblados")
    
    log.info(f"Loading Centros Poblados from {path.name}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_GEO)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(CRS_GEO)
    log.info(f"  → {len(gdf):,} rows")
    return gdf

import os
os.environ['SHAPE_RESTORE_SHX'] = 'YES'

def load_distritos() -> gpd.GeoDataFrame:
    path = _find(["emergencia", "produccion", "EMERGENCIA", "PRODUCCION", "ConsultaC1", "consulta"])
    if path.suffix != ".shp":
        # Try to find the .shp specifically
        candidates = list(DATA_RAW.rglob("*.shp"))
        if not candidates:
            raise FileNotFoundError("No .shp file found in data/raw/")
        path = candidates[0]
    log.info(f"Loading Distritos from {path.name}")
    gdf = gpd.read_file(path)
    if gdf.crs is None:
        gdf = gdf.set_crs(CRS_GEO)
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(CRS_GEO)
    log.info(f"  → {len(gdf):,} districts, CRS: {gdf.crs}")
    return gdf