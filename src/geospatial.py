import pandas as pd
import geopandas as gpd
import os
from src.geospatial import nearest_facility_distance


try:
    dfs_to_fix = {
        'IPRESS': gdf_ipress_raw, 
        'CCPP': gdf_cp_raw, 
        'Emergencias': df_emerg
    }

    for name, df in dfs_to_fix.items():
        if 'codigo_renaes' in df.columns:
            df['codigo_renaes'] = df['codigo_renaes'].astype(str).str.strip().str.replace('.0', '', regex=False)
        
        if 'ubigeo' in df.columns:
            if isinstance(df['ubigeo'], pd.DataFrame):
                df['ubigeo'] = df['ubigeo'].iloc[:, 0]
            df['ubigeo'] = df['ubigeo'].astype(str).str.strip().str.replace('.0', '', regex=False).str.zfill(6)

    if 'dist_nearest_km' not in gdf_cp_raw.columns:
        print("📏 Calculando distancias al establecimiento más cercano (KDTree)...")
        gdf_cp_raw['dist_nearest_km'] = nearest_facility_distance(gdf_cp_raw, gdf_ipress_raw)

    print("📊 Generando métricas por UBIGEO...")
    
    emerg_dist = df_emerg.groupby('ubigeo')['emergencias_total'].sum().reset_index()
    
    ipress_dist = gdf_ipress_raw.groupby('ubigeo').size().reset_index(name='n_facilities')
    
    cp_dist = gdf_cp_raw.groupby('ubigeo')['dist_nearest_km'].agg(['mean', 'max']).reset_index()
    cp_dist.columns = ['ubigeo', 'mean', 'max'] 
    
    cp_excl = gdf_cp_raw.groupby('ubigeo').apply(
        lambda x: (x['dist_nearest_km'] > 30).mean() * 100, include_groups=False
    ).reset_index(name='pct_cp_over30km')

    print("🔗 Uniendo tablas finales...")
    resumen_final = ipress_dist.merge(cp_dist, on='ubigeo', how='outer') \
                               .merge(emerg_dist, on='ubigeo', how='outer') \
                               .merge(cp_excl, on='ubigeo', how='outer')

    resumen_final['n_facilities'] = resumen_final['n_facilities'].fillna(0)
    resumen_final['emergencias_total'] = resumen_final['emergencias_total'].fillna(0)

    output_name = "district_spatial_summary.csv"
    resumen_final.to_csv(output_name, index=False)
    
    print(f"Archivo generado: {output_name}")
    display(resumen_final.head())

except Exception as e:
    print(f"Columnas IPRESS: {gdf_ipress_raw.columns.tolist()}")
    print(f"Columnas CCPP: {gdf_cp_raw.columns.tolist()}")
