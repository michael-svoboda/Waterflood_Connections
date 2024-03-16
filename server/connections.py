import json
import pandas as pd
import numpy as np
from scipy.stats import pearsonr
from geopy.distance import geodesic
from dateutil.relativedelta import relativedelta
from datetime import datetime

# Existing code
csv_file_path = 'production_data.csv'
coordinates_file_path = 'well_locations.csv'

df = pd.read_csv(csv_file_path, parse_dates=['Date'])
df = df.sort_values(by='Date')

df_coords = pd.read_csv(coordinates_file_path)
df_coords['UWI_minus_1'] = df_coords['UWI'].str[:-1]

def calculate_change_and_normalize(df, column_name):
    df[f'{column_name} Change'] = df[column_name].diff()

    # Check for division by zero and handle special cases
    mask_numerator_zero = (df[f'{column_name} Change'] == 0) & (df[column_name] == 0)
    mask_denominator_zero = (df[f'{column_name} Change'] != 0) & (df[column_name] == 0)

    df[f'Normalized {column_name} Change'] = df[f'{column_name} Change'] / df[column_name]
    df.loc[mask_numerator_zero, f'Normalized {column_name} Change'] = 0
    df.loc[mask_denominator_zero, f'Normalized {column_name} Change'] = -1

calculate_change_and_normalize(df, 'PRD Calndr-Day Avg WTR Bbl/Day')
calculate_change_and_normalize(df, 'PRD Calndr-Day Avg OIL Bbl/Day')
calculate_change_and_normalize(df, 'INJ Inj-Day Avg Water Bbl')

df.to_csv('flow_changes.csv', index=False)
print("Flow changes saved to 'flow_changes.csv'")

# Additional code for connection strengths
connections = {}

def calculate_correlation_and_delta(df, distance, date, producer_uwi, injector_uwi):

    #print(date)
    #print(type(date))

    # Assuming your current date is stored as a numpy.datetime64 object in monthly format
    current_date_monthly = np.datetime64(date, 'M')
    previous_month_date = current_date_monthly - np.timedelta64(1, 'M')
    next_month_date = current_date_monthly + np.timedelta64(1, 'M')

    # Convert dates back to np.datetime64 with 'ns' units
    previous_month_date_ns = np.datetime64(previous_month_date, 'ns')
    current_date_monthly_ns = np.datetime64(current_date_monthly, 'ns')
    next_month_date_ns = np.datetime64(next_month_date, 'ns')

    # Create a list containing the previous, current, and next month dates
    date_range = [previous_month_date_ns, current_date_monthly_ns, next_month_date_ns]

    # Filter the DataFrame based on values in date_range
    month_data = df[df['Date'].isin(date_range)]

    producer_data = month_data[month_data['UWI'] == producer_uwi]
    injector_data = month_data[month_data['UWI'] == injector_uwi]

    producer_oil = producer_data['PRD Calndr-Day Avg OIL Bbl/Day'].tolist()
    producer_wat = producer_data['PRD Calndr-Day Avg WTR Bbl/Day'].tolist()
    injector_wat = injector_data['INJ Inj-Day Avg Water Bbl'].tolist()

    oil_aggregated = df.groupby('Date')['PRD Calndr-Day Avg OIL Bbl/Day'].sum()
    wat_aggregated = df.groupby('Date')['PRD Calndr-Day Avg WTR Bbl/Day'].sum()
    inj_aggregated = df.groupby('Date')['INJ Inj-Day Avg Water Bbl'].sum()

    date_range = [previous_month_date, current_date_monthly, next_month_date]

    # Aggregate the production for each period
    period_oil_prod = []
    period_wat_prod = []
    period_injection = []

    for i in range(len(date_range)):
        #print(i)
        start_date = date_range[i]
        end_date = date_range[i]
        period_oil_prod.append(oil_aggregated.loc[start_date:end_date].sum())
        period_wat_prod.append(wat_aggregated.loc[start_date:end_date].sum())
        period_injection.append(inj_aggregated.loc[start_date:end_date].sum())

    #print(producer_oil, period_oil_prod)
    #print(producer_wat, period_wat_prod)
    #print(injector_wat, period_injection)

    # Define lambda function to calculate correlation with handling of NaN
    def calculate_corr(x, y):
        if(len(x)==len(y)):
            x = np.nan_to_num(x)
            y = np.nan_to_num(y)
            correlation = pearsonr(x, y)[0]
            if not np.isnan(correlation):
                return correlation
            else:
                return 0
        else:
            x = [x[0]] + x
            x = np.nan_to_num(x)
            y = np.nan_to_num(y)
            correlation = pearsonr(x, y)[0]
            if not np.isnan(correlation):
                return correlation
            else:
                return 0
            

            # print(x, y)
            # print(producer_oil, period_oil_prod)
            # print(producer_wat, period_wat_prod)
            # print(injector_wat, period_injection)
            # print(date)
            # print(injector_uwi)
            # exit()
        
    # Calculate correlations
    corr_oil = calculate_corr(producer_oil, period_oil_prod)
    corr_water = calculate_corr(producer_wat, period_wat_prod)
    corr_injection = calculate_corr(injector_wat, period_injection)

    #print(corr_oil, corr_water, corr_injection)

    normalized_delta_flow_producer = (producer_data.loc[producer_data['Date'] == date, 'PRD Calndr-Day Avg OIL Bbl/Day Change'].abs().iloc[0] / period_oil_prod[1] +
                                      producer_data.loc[producer_data['Date'] == date, 'PRD Calndr-Day Avg WTR Bbl/Day Change'].abs().iloc[0] / period_wat_prod[1]) / 2

    #print(producer_data.loc[producer_data['Date'] == date, 'PRD Calndr-Day Avg OIL Bbl/Day Change'].abs().iloc[0])
    #print(period_oil_prod[1])
    normalized_delta_flow_injector = injector_data.loc[injector_data['Date'] == date, 'INJ Inj-Day Avg Water Bbl Change'].abs().iloc[0] / period_injection[1]

    #print(normalized_delta_flow_producer)
    #print(normalized_delta_flow_injector)

    #exit()

    final_calculation_producer = ((np.abs(corr_oil) + np.abs(corr_water)) / 2) * (normalized_delta_flow_producer)
    final_calculation_injector = np.abs(corr_injection) * (normalized_delta_flow_injector)

    # final_calculation_injector_formula = (f"{final_calculation_injector} = abs({corr_injection}) * ({normalized_delta_flow_injector})")
    # print(f"Final calculation for injector: {final_calculation_injector_formula}")

    # final_calculation_producer_formula = (f"({final_calculation_producer} = (abs({corr_oil}) + abs({corr_water})) / 2) * ({normalized_delta_flow_producer})")
    # print(f"Final calculation for producer: {final_calculation_producer_formula}")

    return final_calculation_producer, final_calculation_injector

def calculate_distance(lat1, lon1, lat2, lon2):
    return geodesic((lat1, lon1), (lat2, lon2)).kilometers

# Initialize an empty list to store connection informations
connection_info = []

# Function to write connection information to CSV
def write_to_csv(connection_info):
    # Create a DataFrame from the connection information
    connection_df = pd.DataFrame(connection_info)
    # Save the DataFrame to a CSV file in append mode
    connection_df.to_csv('connection_info.csv', mode='a', header=False, index=False)

# Filter wells based on 'Type' column
prod_wells = df[df['Type'] == 'PROD'].loc[df['Type'] != 'INACTIVE', 'UWI'].unique()
inj_wells = df[df['Type'] == 'INJ'].loc[df['Type'] != 'INACTIVE', 'UWI'].unique()

well_coordinates = {}

print('Filtered')

for date in df['Date'].unique():
    #print(date)

    date_data = df[(df['Date'] == date)]

    active_prod_wells = date_data[date_data['Type'] == 'PROD']['UWI'].unique()
    active_inj_wells = date_data[date_data['Type'] == 'INJ']['UWI'].unique()

    connection_df_ = pd.DataFrame(columns=['UWI', 'Prod_Conn', 'Inj_Conn'])


    for producer_uwi in active_prod_wells:

        for injector_uwi in active_inj_wells:
            producer_data = df[(df['UWI'] == producer_uwi) & (df['Date'] == date)]
            injector_data = df[(df['UWI'] == injector_uwi) & (df['Date'] == date)]

            #print(date, injector_uwi, producer_uwi)
            #print(producer_data['PRD Calndr-Day Avg OIL Bbl/Day'].iloc[0], producer_data['PRD Calndr-Day Avg WTR Bbl/Day'].iloc[0], injector_data['INJ Inj-Day Avg Water Bbl'].iloc[0])
            #exit()

            
            if ((producer_data['PRD Calndr-Day Avg OIL Bbl/Day'].iloc[0] != 0 
                or producer_data['PRD Calndr-Day Avg WTR Bbl/Day'].iloc[0] != 0)
                and injector_data['INJ Inj-Day Avg Water Bbl Change'].iloc[0] != 0
                and not df_coords.loc[df_coords['UWI_minus_1'] == injector_uwi[:-1], 'Latitude'].empty
                and not df_coords.loc[df_coords['UWI_minus_1'] == producer_uwi[:-1], 'Latitude'].empty
                and (calculate_distance(
                    df_coords.loc[df_coords['UWI_minus_1'] == producer_uwi[:-1], 'Latitude'].iloc[0],
                    df_coords.loc[df_coords['UWI_minus_1'] == producer_uwi[:-1], 'Longitude'].iloc[0],
                    df_coords.loc[df_coords['UWI_minus_1'] == injector_uwi[:-1], 'Latitude'].iloc[0],
                    df_coords.loc[df_coords['UWI_minus_1'] == injector_uwi[:-1], 'Longitude'].iloc[0]
                )) < 1.5
                ):


                wells = [producer_uwi, injector_uwi]

                #print("Connection: ", wells)

               
                

                # Iterate over unique UWIs
                for uwi in wells:
                    
                    # Get the latitude and longitude for the current UWI
                    try:
                        latitude = df_coords.loc[df_coords['UWI_minus_1'] == uwi[:-1], 'Latitude'].iloc[0]
                    except IndexError:
                        print(uwi[:-1])
                        print(df_coords.loc[df_coords['UWI_minus_1'] == uwi[:-1], 'Latitude'])

                    try:
                        longitude = df_coords.loc[df_coords['UWI_minus_1'] == uwi[:-1], 'Longitude'].iloc[0]
                    except IndexError:
                        print(uwi[:-1])
                        print(df_coords.loc[df_coords['UWI_minus_1'] == uwi[:-1], 'Longtiude'])
                    #print(latitude, longitude)
                    
                    # Store latitude and longitude as a tuple in the dictionary
                    well_coordinates[uwi] = (latitude, longitude)

                

                #print(well_coordinates)
                #print(producer_details)
                    
                distance = calculate_distance(well_coordinates[producer_uwi][0], well_coordinates[producer_uwi][1],
                                              well_coordinates[injector_uwi][0], well_coordinates[injector_uwi][1])
                
                
                


                connection_strength_producer, connection_strength_injector = calculate_correlation_and_delta(df, distance, date, producer_uwi, injector_uwi)
                connection_strength = (connection_strength_producer * connection_strength_injector) / distance

                connection_key = f"{producer_uwi}+{injector_uwi}"
                connections[connection_key] = connections.get(connection_key, []) + [connection_strength, date]

                print('connection ', connection_key, ' COMPLETED strength = ', connection_strength)

                # Iterate over the connections dictionary and extract information
                
                prod_lat, prod_long = well_coordinates[producer_uwi]
                inj_lat, inj_long = well_coordinates[injector_uwi]
                    
                # Append connection information to the list
                connection_info.append({
                        'Connection': connection_key,
                        'Producer_UWI': producer_uwi,
                        'Prod_Lat': prod_lat,
                        'Prod_Long': prod_long,
                        'Injector_UWI': injector_uwi,
                        'Inj_Lat': inj_lat,
                        'Inj_Long': inj_long,
                        'Connection_Strength': connection_strength,
                        'Date': date
                    })

                    # Check if the number of connections in the list exceeds a threshold (e.g., 1000)
                if len(connection_info) >= 10:
                        # Write the connection information to the CSV file
                        write_to_csv(connection_info)
                        print('----- SAVED CONNECTIONS -----')
                        # Clear the connection_info list to save memory
                        connection_info = []

# Write any remaining connection information to the CSV file
if connection_info:
    write_to_csv(connection_info)
    print('----- SAVED FINAL CONNECTIONS -----')
    



# # 2. Create DataFrame with Connection, Connection Strength, and Date columns
# connection_df = pd.DataFrame(list(connections.items()), columns=['Connection', 'Connection Strength', 'Date'])

# # 3. Group by Connection and aggregate Connection Strength
# aggregated_connections = connection_df.groupby(['Connection']).agg({'Connection Strength': 'sum', 'Date': 'first'}).reset_index()
# print("Completed Aggregation. Exporting...")

# aggregated_connections.to_csv('aggregated_connections.csv', index=False)
# print("Aggregated connections saved to 'aggregated_connections.csv'")

# # Convert aggregated connections DataFrame to GeoJSON format
# features = []
# for index, row in aggregated_connections.iterrows():
#     feature = {
#         "type": "Feature",
#         "properties": {
#             "Connection": row['Connection'],
#             "Connection_Strength": row['Connection Strength'],
#             "Date": row['Date']  # Include Date in properties
#         },
#         "geometry": None  # No geometry for aggregated connections
#     }
#     features.append(feature)

# geojson_data = {
#     "type": "FeatureCollection",
#     "features": features
# }

# # Save aggregated connections as GeoJSON
# with open('aggregated_connections.geojson', 'w') as f:
#     json.dump(geojson_data, f)

# print("Aggregated connections saved to 'aggregated_connections.geojson'")

# # Split 'Connection' column into 'producer_uwi' and 'injector_uwi'
# connection_df[['producer_uwi', 'injector_uwi']] = connection_df['Connection'].str.split('-', expand=True)

# print("After SPLIT: ", connection_df.head())

# # Function to look up latitude and longitude from well_coordinates dictionary
# def get_coordinates(uwi):
#     return well_coordinates.get(uwi)

# # Look up coordinates for producer and injector UWIs
# connection_df['prod_lat'], connection_df['prod_long'] = zip(*connection_df['producer_uwi'].apply(get_coordinates))
# connection_df['inj_lat'], connection_df['inj_long'] = zip(*connection_df['injector_uwi'].apply(get_coordinates))

# # Reorder columns for better readability
# connection_df = connection_df[['Connection', 'producer_uwi', 'prod_lat', 'prod_long', 'injector_uwi', 'inj_lat', 'inj_long', 'Connection Strength', 'Date']]

# # Save as CSV
# connection_df.to_csv('connections.csv', index=False)

# print('.csv created')

# # Convert DataFrame to GeoJSON format
# features = []
# for index, row in connection_df.iterrows():
#     feature = {
#         "type": "Feature",
#         "properties": {
#             "Connection": row['Connection'],
#             "producer_uwi": row['producer_uwi'],
#             "injector_uwi": row['injector_uwi'],
#             "Connection_Strength": row['Connection Strength'],
#             "Date": row['Date']
#         },
#         "geometry": {
#             "type": "LineString",
#             "coordinates": [
#                 [row['prod_long'], row['prod_lat']],
#                 [row['inj_long'], row['inj_lat']]
#             ]
#         }
#     }
#     features.append(feature)

# geojson_data = {
#     "type": "FeatureCollection",
#     "features": features
# }

# # Save as GeoJSON
# with open('connections.geojson', 'w') as f:
#     json.dump(geojson_data, f)

# print('geojson created')
