import pandas as pd
import plotly.express as px
import json

# Read the CSV file into a DataFrame
df = pd.read_csv('connections.csv')
df_prod = pd.read_csv('production_data.csv')

unique_dates = df_prod['Date'].unique()

# Iterate over each unique date
for filterDate in unique_dates:
    # Filter production data for the current date
    df_prod_filtered = df_prod[df_prod['Date'] == filterDate]
    
    # Iterate over each unique producer UWI
    for producer_UWI in df_prod_filtered['UWI'].unique():
        
        # Filter production data for the current date and producer UWI
        prod_data = df_prod_filtered[df_prod_filtered['UWI'] == producer_UWI]
        
        # Calculate watercut for the current date and producer UWI
        watercut = (prod_data['PRD Calndr-Day Avg WTR Bbl/Day'] / 
                    (prod_data['PRD Calndr-Day Avg OIL Bbl/Day'] + prod_data['PRD Calndr-Day Avg WTR Bbl/Day'])).iloc[0]
        # print('oil prod:', prod_data['PRD Calndr-Day Avg OIL Bbl/Day'].iloc[0])
        # print('water prod:', prod_data['PRD Calndr-Day Avg WTR Bbl/Day'].iloc[0])
        # print('fluid prod:', (prod_data['PRD Calndr-Day Avg OIL Bbl/Day'] + prod_data['PRD Calndr-Day Avg WTR Bbl/Day']).iloc[0])
        
        print( filterDate, producer_UWI, watercut)


        # Find the corresponding row in the DataFrame and update the Watercut column
        df.loc[(df['Producer_UWI'] == producer_UWI) & 
               (df['Date'] == filterDate), 'Watercut'] = watercut

# Save the updated DataFrame to a CSV file
df.to_csv('connections_with_watercut.csv', index=False)

# Define the minimum and maximum allowed strength values
#min_allowed_strength = 0.001
min_allowed_strength = 0.0
max_allowed_strength = 0.02

# Filter out the DataFrame to drop all strength values less than min_allowed_strength
df = df[df['Strength'] >= min_allowed_strength]

# Cap out every strength value greater than max_allowed_strength
df['N_Strength'] = df['Strength'].apply(lambda x: max_allowed_strength if x > max_allowed_strength else x)

# Create another column that groups each strength into 10 even groups based on their percentile
df['PN_Strength'] = pd.qcut(df['N_Strength'], q=10, labels=range(1, 11))


# Get the minimum and maximum values from the Strength column
min_strength = df['N_Strength'].min()
max_strength = df['N_Strength'].max()

# Define the number of bins
num_bins = 20

# Calculate the bin width
bin_width = (max_strength - min_strength) / num_bins

# Generate the bins based on the calculated min and max values
strength_bins = [min_strength + i * bin_width for i in range(num_bins)]
strength_bins.append(float('inf'))  # Add infinity as the last bin endpoint


# Group the DataFrame by strength ranges and count the occurrences
strength_distribution = pd.cut(df['N_Strength'], bins=strength_bins).value_counts().sort_index()

# Create a Plotly bar chart
fig = px.bar(
    x=strength_distribution.index.astype(str),  # Convert the index to strings for plotting
    y=strength_distribution.values,
    labels={'x': 'Strength Range', 'y': 'Count'},
    title='Distribution of Connection Strength'
)

# Save the bar chart as an HTML file
fig.write_html("connection_strength_distribution.html")

# # Filter the DataFrame to include only connections with strength greater than 1
# df_filtered = df[df['N_Strength'] > 1]

# Define a function to create LineString geometry for each connection
def create_line_string(row):
    coordinates = [
        [row['Prod_Long'], row['Prod_Lat']],
        [row['Inj_Long'], row['Inj_Lat']]
    ]
    return {
        "type": "Feature",
        "properties": {
            "Strength": row['PN_Strength'],
            "Date": row['Date'],
            "Watercut": row['Watercut'],  # Include Watercut property
            "ConnectionName": f"{row['Producer_UWI']} - {row['Injector_UWI']}"  # Connection name property
        },
        "geometry": {
            "type": "LineString",
            "coordinates": coordinates
        }
    }



# Apply the function to each row of the filtered DataFrame
features = df.apply(create_line_string, axis=1).tolist()

# Create a FeatureCollection GeoJSON object
geojson_data = {
    "type": "FeatureCollection",
    "features": features
}

# Save the GeoJSON data to a file
with open("connections_geojson.geojson", "w") as f:
    json.dump(geojson_data, f)

