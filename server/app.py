from flask import Flask, jsonify, send_file
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

@app.route('/well-data')
def get_well_data():
    # Path to your GeoJSON file
    geojson_file_path = 'well_data.geojson'

    # Check if the file exists
    if os.path.exists(geojson_file_path):
        # Read GeoJSON data from the file
        with open(geojson_file_path, 'r') as file:
            geojson_data = json.load(file)
        
        return jsonify(geojson_data)
    else:
        # Return an error response if the file does not exist
        return jsonify({"error": "GeoJSON file not found"}), 404

@app.route('/connection-data')
def get_connection_data():
    # Path to your GeoJSON file for connections
    connections_geojson_file_path = 'connections_geojson.geojson'

    # Check if the file exists
    if os.path.exists(connections_geojson_file_path):
        # Return the GeoJSON file for connections
        return send_file(connections_geojson_file_path, mimetype='application/json')
    else:
        # Return an error response if the file does not exist
        return jsonify({"error": "Connection GeoJSON file not found"}), 404

if __name__ == '__main__':
    app.run(debug=True, port=3001)
