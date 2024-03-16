import geopandas as gpd

def filter_geojson(input_geojson, output_geojson, filter_column, filter_value):
    # Read the GeoJSON file into a GeoDataFrame
    gdf = gpd.read_file(input_geojson)

    # Check if the filter column exists in the GeoDataFrame
    if filter_column not in gdf.columns:
        raise ValueError(f"The specified filter column '{filter_column}' does not exist in the GeoDataFrame.")

    # Apply the filter
    filtered_gdf = gdf[gdf[filter_column] == filter_value]

    # Save the filtered GeoDataFrame to a new GeoJSON file
    filtered_gdf.to_file('well_data.geojson', driver='GeoJSON')

# Example usage:
input_geojson_path = 'path/to/your/input.geojson'
output_geojson_path = 'path/to/your/output.geojson'
filter_column_name = 'name'  # Replace with the column you want to filter on
filter_value_to_keep = 'Example Point 1'  # Replace with the value you want to filter on

filter_geojson(input_geojson_path, output_geojson_path, filter_column_name, filter_value_to_keep)
