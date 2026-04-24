import pandas as pd
import geopandas as gpd
from src.utils import DATA_PROCESSED, CRS_GEO, get_logger

log = get_logger(__name__)

def clean_ipress(df: pd.DataFrame) -> gpd.GeoDataFrame:
    """
    Limpia IPRESS: estandariza nombres, maneja duplicados, filtra coordenadas
    y prepara el objeto GeoDataFrame.
    """
    df = df.copy()
    
    # 1. Standardize column names
    # Basado en tu diagnóstico: 'NORTE', 'ESTE', 'Código Único'
    mapping = {
        'NORTE': 'latitud', 
        'ESTE': 'longitud',
        'Código Único': 'codigo_renaes',
        'Nombre del establecimiento': 'nombre_ipress',
        'UBIGEO': 'ubigeo'
    }
    df = df.rename(columns=mapping)
    
    # 2. Handle duplicates
    initial_rows = len(df)
    df = df.drop_duplicates(subset=['codigo_renaes'])
    log.info(f"Deduplicación IPRESS: de {initial_rows} a {len(df)} filas.")

    # 3. Remove invalid coordinates & format numeric
    # Como tu loader usa dtype=str, aquí forzamos la conversión
    for col in ['latitud', 'longitud']:
        df[col] = pd.to_numeric(df[col].str.replace(',', ''), errors='coerce')
    
    df = df.dropna(subset=['latitud', 'longitud'])
    
    # Limpieza de Ubigeo (asegurar 6 dígitos)
    if 'ubigeo' in df.columns:
        df['ubigeo'] = df['ubigeo'].str.split('.').str[0].str.zfill(6)

    # 4. Prepare geospatial objects correctly
    # Las IPRESS en Perú suelen estar en metros (UTM 18S)
    gdf = gpd.GeoDataFrame(
        df, 
        geometry=gpd.points_from_xy(df.longitud, df.latitud),
        crs="EPSG:32718" 
    ).to_crs(CRS_GEO) # CRS_GEO es 4326 según tu utils

    # 5. Save cleaned output
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    out_path = DATA_PROCESSED / "ipress_clean.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    log.info(f"Saved cleaned IPRESS to {out_path}")
    
    return gdf

def clean_emergencia(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpia emergencias: estandariza, maneja nulos y agrupa.
    """
    df = df.copy()
    mapping = {
        'CO_IPRESS': 'codigo_renaes',
        'NRO_TOTAL_ATENCIONES': 'emergencias_total'
    }
    df = df.rename(columns=mapping)
    
    # Convertir producción a numérico
    df['emergencias_total'] = pd.to_numeric(df['emergencias_total'], errors='coerce').fillna(0)
    
    # Agrupar (Handle duplicates/temporal data)
    df = df.groupby('codigo_renaes', as_index=False)['emergencias_total'].sum()
    
    # Save
    out_path = DATA_PROCESSED / "emergencia_clean.csv"
    df.to_csv(out_path, index=False)
    log.info(f"Saved cleaned Emergencias to {out_path}")
    
    return df

def clean_centros_poblados(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Limpia CCPP: estandariza y asegura geometría.
    """
    gdf = gdf.copy()
    mapping = {'NOM_POBLAD': 'nombre_cp'}
    gdf = gdf.rename(columns=mapping)
    
    # Eliminar geometrías nulas
    gdf = gdf[gdf.geometry.notna()]
    
    # Save
    out_path = DATA_PROCESSED / "ccpp_clean.geojson"
    gdf.to_file(out_path, driver="GeoJSON")
    log.info(f"Saved cleaned CCPP to {out_path}")