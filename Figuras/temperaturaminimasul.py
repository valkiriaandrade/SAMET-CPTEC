import geopandas as gpd
import netCDF4 as nc
import numpy as np
import os
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from cartopy.feature import ShapelyFeature
from shapely.geometry import box
from cartopy.io.shapereader import Reader

def ler_tmin(arquivo):
    ds = nc.Dataset(arquivo)
    tmin = ds.variables['tmin'][:]
    tmin = np.where(tmin == ds.variables['tmin']._FillValue, np.nan, tmin)
    ds.close()
    return tmin
pasta_dados_diarios = 'jul min/'
climatologia_janeiro = ler_tmin('SAMeT_CPTEC_TMIN_mean_jul.nc')
soma_anomalias = np.zeros_like(climatologia_janeiro)
contador = 0
for arquivo in os.listdir(pasta_dados_diarios):
    if arquivo.endswith('.nc'):
        caminho_completo = os.path.join(pasta_dados_diarios, arquivo)
        dados_diarios = ler_tmin(caminho_completo)
        anomalia = dados_diarios - climatologia_janeiro
        soma_anomalias += anomalia
        contador += 1
anomalia_media_mensal = soma_anomalias / contador
fig = plt.figure(figsize=(12, 10))
ax = plt.axes(projection=ccrs.PlateCarree())
ax.set_extent([-57.6, -48, -33.75, -22.5], crs=ccrs.PlateCarree()) 
with nc.Dataset('SAMeT_CPTEC_TMIN_mean_jul.nc') as ds:
    lon = ds.variables['lon'][:]
    lat = ds.variables['lat'][:]
levels = np.arange(-3, 3.5, 0.5)
contour = ax.contourf(lon, lat, anomalia_media_mensal.squeeze(), levels=levels, cmap='coolwarm', extend='both', transform=ccrs.PlateCarree())
cbar = plt.colorbar(contour, label='Anomalia de Temperatura (°C)', ticks=levels, shrink=0.9)
cbar.ax.set_yticklabels(['{:.1f}'.format(tick) for tick in levels]) 
gdf = gpd.read_file('BR_UF_2022.shp')
estados_norte = ['PR', 'SC', 'RS'] 
gdf_norte = gdf[gdf['SIGLA_UF'].isin(estados_norte)]
for geom in gdf_norte.geometry:
    ax.add_geometries([geom], ccrs.PlateCarree(), facecolor='none', edgecolor='black', linewidth=0.5)
exterior_mask_gdf = gpd.GeoDataFrame(geometry=gpd.GeoSeries(box(-180, -90, 180, 90)), crs=gdf.crs)
total_area = gpd.GeoDataFrame(geometry=[box(-180, -90, 180, 90)], crs="EPSG:4326")
gdf_norte = gdf_norte.to_crs(total_area.crs)
mask = gpd.overlay(total_area, gdf_norte, how='difference')
for geom in mask.geometry:
    ax.add_geometries([geom], ccrs.PlateCarree(), facecolor='white', edgecolor='none')
for geom in gdf_norte.geometry:
    ax.add_geometries([geom], ccrs.PlateCarree(), facecolor='none', edgecolor='black', linewidth=1)
line1, = ax.plot([], [], linestyle='-', color='black', label='Região Sul')
ax.legend(loc='upper left', handles=[line1])
plt.title('Anomalia de Temperatura Mínima - Julho 2024')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.savefig('anomalia_temperatura_minima_jul_Sul.png', dpi=300, bbox_inches='tight')
plt.show()
