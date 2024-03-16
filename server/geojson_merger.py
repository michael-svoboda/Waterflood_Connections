import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Load the table with UWI, Latitude, and Longitude
location_data = pd.read_csv('well_locations.csv')

# Load the table with UWI and other data
other_data = pd.read_csv('production_data.csv')

# Merge the two tables on the 'UWI' column
merged_data = pd.merge(location_data, other_data, on='UWI', how='inner')

# Create a GeoDataFrame using the merged data
geometry = [Point(xy) for xy in zip(merged_data['Longitude'], merged_data['Latitude'])]
gdf = gpd.GeoDataFrame(merged_data, geometry=geometry, crs="EPSG:4326")

# Save the GeoDataFrame to a GeoJSON file
gdf.to_file('well_data.geojson', driver='GeoJSON')
