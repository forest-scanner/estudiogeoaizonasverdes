import os
import rasterio
import rasterio.mask
import rasterio.features
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.patches as patches
from scipy.ndimage import label, find_objects

def process_polygon_indices(geojson_path, id_field, raster_path):
    print(f"\n[1] Cargando imagen raster: {raster_path}")
    
    with rasterio.open(raster_path) as src:
        raster_crs = src.crs
        print(f"[*] Sistema de coordenadas (CRS) del raster: {raster_crs}")
        
        print(f"\n[2] Cargando polígonos: {geojson_path}")
        gdf = gpd.read_file(geojson_path)
        
        if id_field not in gdf.columns:
            raise ValueError(f"El campo de ID '{id_field}' no existe en el GeoJSON proporcionado.")
        
        print(f"[*] Sistema de coordenadas (CRS) original del GeoJSON: {gdf.crs}")
        # Asegurar que el GeoJSON está en el mismo sistema de coordenadas que el Raster
        if gdf.crs != raster_crs:
            print(f"[*] Reproyectando polígonos a {raster_crs} para coincidir con la imagen...")
            gdf = gdf.to_crs(raster_crs)
            
        geometries = gdf.geometry.values
        
        print("\n[3] Recortando el raster usando las fronteras de los polígonos...")
        # Recortar el raster para dejar solo lo que hay DENTRO de los polígonos
        out_image, out_transform = rasterio.mask.mask(src, geometries, crop=True)
        
        # Asumiendo el orden de bandas estándar usado previamente: 1=Red, 2=Green, 3=Blue, 4=NIR
        red = out_image[0].astype(float)
        green = out_image[1].astype(float)
        blue = out_image[2].astype(float)
        nir = out_image[3].astype(float)
        
        np.seterr(divide='ignore', invalid='ignore')
        
        print("\n[4] Calculando índices (NDVI, NDWI, GCI)...")
        ndvi = np.where((nir + red) == 0., 0, (nir - red) / (nir + red))
        ndwi = np.where((green + nir) == 0., 0, (green - nir) / (green + nir))
        gci = np.where(green == 0., 0, (nir / green) - 1)
        
        # Enmascarar las áreas que están fuera de los polígonos (rellenadas con 0 por rasterio.mask)
        mask_out = (red == 0) & (green == 0) & (blue == 0) & (nir == 0)
        ndvi[mask_out] = np.nan
        ndwi[mask_out] = np.nan
        gci[mask_out] = np.nan
        
        # Normalizar RGB para visualización
        rgb = np.dstack((red, green, blue))
        rgb_min, rgb_max = np.nanpercentile(rgb, 2), np.nanpercentile(rgb, 98)
        rgb_norm = np.clip((rgb - rgb_min) / (rgb_max - rgb_min), 0, 1)
        rgb_norm[mask_out] = np.nan # Aplicar nan a los canales individualmente ya lo evalúa matplotlib
        
        print("\n[5] Generando gráficos...")
        # --- GRÁFICO 1: MAPAS GLOBALES ---
        fig = plt.figure(figsize=(18, 12)) 
        gs = GridSpec(2, 3, figure=fig)    
        
        ax_img = fig.add_subplot(gs[0, :])
        ax_img.imshow(rgb_norm)
        ax_img.set_title('Imagen Original (RGB) dentro de los polígonos', fontsize=16, fontweight='bold')
        ax_img.axis('off')
        
        ax_ndvi = fig.add_subplot(gs[1, 0])
        ndvi_map = ax_ndvi.imshow(ndvi, cmap='RdYlGn', vmin=-1, vmax=1)
        ax_ndvi.set_title('NDVI (Salud Vegetal)', fontsize=12)
        ax_ndvi.axis('off')
        fig.colorbar(ndvi_map, ax=ax_ndvi, shrink=0.8)
        
        ax_ndwi = fig.add_subplot(gs[1, 1])
        ndwi_map = ax_ndwi.imshow(ndwi, cmap='GnBu', vmin=-1, vmax=1)
        ax_ndwi.set_title('NDWI (Humedad/Agua)', fontsize=12)
        ax_ndwi.axis('off')
        fig.colorbar(ndwi_map, ax=ax_ndwi, shrink=0.8)
        
        ax_gci = fig.add_subplot(gs[1, 2])
        gci_map = ax_gci.imshow(gci, cmap='YlGn', vmin=0, vmax=5)
        ax_gci.set_title('GCI (Niveles de Clorofila)', fontsize=12)
        ax_gci.axis('off')
        fig.colorbar(gci_map, ax=ax_gci, shrink=0.8)
        
        plt.tight_layout()
        plt.show(block=False)  # Mostrar este gráfico un rato sin bloquear
        
        # --- GRÁFICO 2: DESTAQUE DE VALORES ALTOS ---
        fig2, axes = plt.subplots(1, 3, figsize=(18, 6))

        indices = [
            ('NDVI', ndvi, 'RdYlGn', -1, 1), 
            ('NDWI', ndwi, 'GnBu', -1, 1), 
            ('GCI', gci, 'YlGn', 0, 5)
        ]

        for ax, (title, matrix, cmap, vmin, vmax) in zip(axes, indices):
            matrix_plot = np.copy(matrix)
            matrix_plot[np.isnan(matrix_plot)] = 0 # para label
            
            img_plot = ax.imshow(matrix, cmap=cmap, vmin=vmin, vmax=vmax)
            fig2.colorbar(img_plot, ax=ax, shrink=0.8)
            ax.set_title(f'{title} (Valores Altos Resaltados)', fontsize=14)
            ax.axis('off')
            
            valid_pixels = matrix[~np.isnan(matrix)]
            if valid_pixels.size > 0:
                threshold = np.percentile(valid_pixels[valid_pixels > 0], 95) if np.any(valid_pixels > 0) else np.percentile(valid_pixels, 95)
                mask = matrix_plot > threshold
                
                labeled_array, num_features = label(mask)
                objects = find_objects(labeled_array)
                
                for obj in objects:
                    min_y, max_y = obj[0].start, obj[0].stop
                    min_x, max_x = obj[1].start, obj[1].stop
                    
                    width = max_x - min_x
                    height = max_y - min_y
                    
                    if width > 2 and height > 2:
                        rectangle = patches.Rectangle(
                            (min_x, min_y), width, height, 
                            linewidth=2, edgecolor='red', facecolor='none'
                        )
                        ax.add_patch(rectangle)

        plt.tight_layout()
        plt.show() # Mostrar gráfico bloqueando hasta que el usuario lo cierre
        
        # --- EXTRAS: Estadística por polígono ---
        print("\n[6] === Estadísticas Medias y Cobertura de Zonas Verdes ===")
        print(f"{'ID_Poligono':<15} | {'NDVI_Med':<10} | {'NDWI_Med':<10} | {'GCI_Med':<10} | {'%_Sano (>0.4)':<15}")
        print("-" * 75)
        
        for idx, row in gdf.iterrows():
            poly_id = row[id_field]
            
            # Crear una máscara específica para este único polígono
            poly_mask = rasterio.features.geometry_mask(
                [row.geometry], out_shape=out_image.shape[1:], transform=out_transform, invert=True)
            
            ndvi_poly = ndvi[poly_mask]
            ndwi_poly = ndwi[poly_mask]
            gci_poly = gci[poly_mask]
            
            ndvi_mean = np.nanmean(ndvi_poly) if np.any(~np.isnan(ndvi_poly)) else np.nan
            ndwi_mean = np.nanmean(ndwi_poly) if np.any(~np.isnan(ndwi_poly)) else np.nan
            gci_mean = np.nanmean(gci_poly) if np.any(~np.isnan(gci_poly)) else np.nan
            
            # Utilidad Zonas Verdes: Porcentaje de vegetación sana (NDVI > 0.4)
            valid_pixels = ndvi_poly[~np.isnan(ndvi_poly)]
            if valid_pixels.size > 0:
                sanos = np.sum(valid_pixels > 0.4)
                pct_sano = (sanos / valid_pixels.size) * 100
            else:
                pct_sano = np.nan
            
            # Guardamos para exportar
            gdf.at[idx, 'NDVI_mean'] = ndvi_mean
            gdf.at[idx, 'NDWI_mean'] = ndwi_mean
            gdf.at[idx, 'GCI_mean'] = gci_mean
            gdf.at[idx, 'pct_veg_sana'] = pct_sano
            
            print(f"{str(poly_id):<15} | {ndvi_mean:<10.3f} | {ndwi_mean:<10.3f} | {gci_mean:<10.3f} | {pct_sano:<13.2f}")

        print("\n[7] Exportando resultados enriquecidos...")
        out_geojson = geojson_path.replace('.geojson', '_resultados.geojson')
        out_csv = geojson_path.replace('.geojson', '_estadisticas.csv')
        
        # Guardar en CSV limpiando la geometría
        if not gdf.empty:
            df = gdf.drop(columns=['geometry'], errors='ignore')
            df.to_csv(out_csv, index=False)
            print(f"[*] CSV exportado correctamente: {out_csv}")
            
            # Guardar el GeoJSON original con todos los nuevos campos
            gdf.to_file(out_geojson, driver="GeoJSON")
            print(f"[*] GeoJSON enriquecido exportado: {out_geojson}")

if __name__ == "__main__":
    import sys
    print("=====================================================")
    print("      ANÁLISIS ESPECTRAL SOBRE POLÍGONOS GEOJSON")
    print("=====================================================")
    geojson_input = input("1. Ruta al archivo GeoJSON de polígonos: ")
    id_input = input("2. Nombre del campo de ID en el GeoJSON (ej. 'id'): ")
    raster_input = input("3. Ruta a la imagen TIF (Bandas R, G, B, NIR): ")
    
    if os.path.exists(geojson_input) and os.path.exists(raster_input):
        process_polygon_indices(geojson_input, id_input, raster_input)
    else:
        print("\n[ERROR] El archivo GeoJSON o el TIF no existen. Verifica las rutas introducidas.")
