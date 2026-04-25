# Emergency Healthcare Access Inequality in Peru

## What does the project do?
 Este proyecto construye un flujo de trabajo para medir y comparar las condiciones de acceso a cuidado de salud en caso de emergencia a lo largo de diversos distritos del país. Utiliza datasets con datos pertinentes y los consolida para crear un ranking del mejor al peor servicio.

## Main analytical goal
Responder cuál es el distrito peruano que ha mejorado o empeorado según la evidencia.

## Datasets used
| IPRESS Health Facilities | `data/raw/ipress.*` | MINSA |
| Emergency Care Production | `data/raw/emergencia.*` | MINSA |
| Centros Poblados | `data/raw/centros_poblados.*` | INEI |
| District Boundaries | `data/raw/DISTRITOS.shp` | IGN/MINSA |

## Data cleaning decisions
- Optimización de Memoria y Almacenamiento: Debido a restricciones de hardware y espacio en disco, se implementó un flujo de procesamiento que evite la generación de archivos geoespaciales intermedios pesados.
- Agregación por UBIGEO: Ante la ausencia de metadatos completos en algunos archivos, se procedió a una agregación basada en los códigos de UBIGEO validados de las fuentes de IPRESS y Centros Poblados.
- Tratamiento de Discreoancias en Tipos de Datos: Se forzó la conversión de ciertos identificadores para asegurar la integridad de los cruces entre tablas de distintas fuentes.

## District-level metric construction

- Se usaron metricas espaciales para unir tres fuentes de data: IPRESS, Centros Poblados y Records de Emergencia.
- Se contaron los valores únicos de IPRESS por distrito en base a su ubigeo.
- Se tomó en cuenta tambien las consultas por emergencia a distintas instituciones por cada ditrito


```bash
pip install -r requirements.txt
```

## Running the pipeline
1. Subir datasets: data_loader.py 
2. Limpiar datasets: cleaning.py   
3. Analisis Espacial: geospatial.py 
4. Conseguir indicadores: metrics.py  
5. Visualización: visualization.py 

## Running the Streamlit app

```bash
streamlit run app.py
```

## Main findings

- Distritos en la costa cuenta con mayor densidad de instituciones de atención médica de emergencia.
- Los distritos con menor abastecimiento se encuentran en la Amazonía rural y algunas regiones andinas.
## Main limitations

- La data en cuestiones de salud a nivel nacional cuenta con limitaciones principalmente de formato, lo cual dificulta el análisis por medio de la metodología de Data Science
- Data relacionada con la cantidad de población podría presentar un sesgo de error de medición 
