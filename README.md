Análisis Espectral de Zonas Verdes en Polígonos 🌳🛰️
Esta herramienta en Python está diseñada específicamente para analizar la salud vegetal y la humedad de zonas verdes urbanas (parques, parcelas, jardines) basándose en imágenes de satélite multiespectrales o vuelos de dron.

El script analisis_poligonos.py cruza un archivo de geometría (.geojson) con las parcelas a analizar y una imagen ráster (.tif) para calcular y extraer automáticamente diversos índices espectrales valiosos para la gestión de las zonas verdes.

🌟 Características Principales
Recorte de Área Preciso (Masking): El modelo aísla algorítmicamente y en tiempo real el área que pertenece exclusivamente al interior de cada polígono.
Reproyección Automática: Independientemente del Sistema de Referencias de Coordenadas (CRS) en el que se encuentre tu .geojson (generalmente EPSG:4326), la herramienta es lo bastante inteligente para reproyectarlo de fondo al sistema coordinado exacto de la fotografía .tif.
Cálculo de Índices:
NDVI (Índice de Vegetación de Diferencia Normalizada): Detecta la salud y el nivel de biomasa de la vegetación (de -1 a 1).
NDWI (Índice Diferencial de Agua Normalizado): Detecta la humedad y el estrés hídrico de la planta y la tierra.
GCI (Índice de Clorofila Verde): Relacionado con los niveles de clorofila.
Calculadora de "Porcentaje Sano": Genera una métrica específica que cuenta exactamente qué porcentaje del polígono se compone de vegetación fuerte (NDVI > 0.4), evitando así medias irreales por las zonas de tierra/calle de una parcela.
Visualización Gráfica: Muestra paneles interactivos resaltando las zonas más valiosas mediante Matplotlib.
Extracción enriquecida de Datos: Guarda una tabla (.csv) y un .geojson enriquecido listas para Big Data/GIS.
🚀 Cómo utilizar el script
1. Requisitos Previos
Asegúrate de instalar los módulos de Python necesarios. Preferiblemente utiliza un entorno virtual:

pip install rasterio geopandas numpy matplotlib scipy
También es necesario disponer de:

Un archivo GeoJSON con los polígonos del parque o zonas verdes a vigilar.
Una imagen TIF (Ráster) que abarque dicha zona, de la cual se utilizarán 4 bandas: Red (Banda 1), Green (Banda 2), Blue (Banda 3) y NIR o Infrarrojo Cercano (Banda 4).
2. Ejecutar el código
Desplázate a la carpeta y ejecuta:

python analisis_poligonos.py
Durante la ejecución, la consola interactiva te preguntará en orden:

La ruta de tu archivo GeoJSON. (Ej. parques.geojson)
La columna de ID única para identificar tus zonas en el archivo anterior. (Ej. id_parcela)
La ruta a la imagen TIF multiespectral. (Ej. ortofoto_multiespectral.tif)
3. Resultados Obtenidos
Cuando termine, ocurrirán 3 cosas:

Gráficos en pantalla: Visualizarás unos Dashboard interactivos con los mapas de calor del área recortada.
Archivo CSV generado: Se guardará en la misma carpeta original un fichero en formato <tu_fichero>_estadisticas.csv con las medias tabuladas para uso sencillo en Excel u otras aplicaciones en la nube, perfecto para cruzar con MINT.
Archivo GeoJSON enriquecido: Para QGIS o ArcGIS, el script expide <tu_fichero>_resultados.geojson. A diferencia del tuyo inicial, al clickar la información de cualquier polígono, este contendrá además su estado hídrico y botánico de la toma.
