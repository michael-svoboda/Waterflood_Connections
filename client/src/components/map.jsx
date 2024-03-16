import React, { useRef, useState, useEffect } from 'react';
import mapboxgl from 'mapbox-gl';
import Slider from '@mui/material/Slider';
import Typography from '@mui/material/Typography';

const Map = ({ data }) => {
  const [hoveredFeature, setHoveredFeature] = useState(null);
  const [filterDate, setFilterDate] = useState('2005-11-01');
  const mapContainerRef = useRef(null);
  const mapRef = useRef(null);
  const sliderRef = useRef(null);

  const startDate = new Date('1979-09-01');
  const endDate = new Date('2023-12-01');
  const monthRange = generateMonthRange(startDate, endDate);

  const handleSliderChange = (event, newValue) => {
    const sliderValue = monthRange[newValue];
    setFilterDate(sliderValue);
  };

  useEffect(() => {
    mapboxgl.accessToken = 'pk.eyJ1IjoibWljaGFlbC1zdm9ib2RhIiwiYSI6ImNsZWd0bHQ0MzBhYWEzcXBoMzQ0bnF5djgifQ.17y-XKuBkorntWJCXiEWRw';

    if (!mapRef.current) {
      mapRef.current = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/dark-v11',
        center: [-119.153950, 55.286813],
        zoom: 12,
      });

      mapRef.current.on('load', async () => {
        const url = `http://localhost:3001/connection-data`;
        const response = await fetch(url);
        const geojsonData = await response.json();

        const filteredFeatures = geojsonData.features.filter(feature => feature.properties.Date === filterDate);
        const connectionNames = filteredFeatures.map(feature => feature.properties.ConnectionName);

        const maxStrength = Math.max(...filteredFeatures.map(feature => feature.properties.Strength));

        // filteredFeatures.forEach(feature => {
        //     feature.properties.NormalizedStrength = feature.properties.Strength / maxStrength;
        // });

         mapRef.current.addSource('connections-data', {
            type: 'geojson',
            data: {
                type: 'FeatureCollection',
                features: filteredFeatures
            },
            lineMetrics: true // Enable lineMetrics for the source
        });




        
        
        
        // Iterate through each connection name in the list
        connectionNames.forEach(connectionName => {
            // Filter features for the current connection name
            const filteredFeatures = geojsonData.features.filter(feature => feature.properties.ConnectionName === connectionName);

            // Get the watercut value for the connection
            const watercut1 = filteredFeatures[0].properties.Watercut; // Assuming watercut is the same for all features of the same connection

            const watercut = 1 - watercut1
            // Set num1 and num2 equal to the watercut
            let watercut_L;
            let watercut_U;

            if (watercut === 0) {
                watercut_L = 0.01;
                watercut_U = 0.02;
            } else {
                // Adjust watercut_L and watercut_U based on the watercut value
                watercut_L = watercut - (0.15 * (watercut));
                watercut_U = watercut + (0.15 * (1-watercut));
                //watercut_L = watercut - (0.01);
                //watercut_U = watercut + (0.01);
            }

            console.log(watercut_L)
            console.log(watercut_U)
            
            //const num1 = watercut;
            //const num2 = watercut;

            // Add layer for the current connection
            mapRef.current.addLayer({
                id: `connections-layer-${connectionName}`,
                type: 'line',
                filter: ['==', 'ConnectionName', connectionName],
                source: 'connections-data',
                paint: {
                    // 'line-gradient': [
                    //     'interpolate',
                    //     ['linear'],
                    //     ['line-progress'],
                    //     0,
                    //     'green',
                    //     watercut_L,
                    //     'green',
                    //     watercut_U,
                    //     'blue',
                    //     1,
                    //     'blue'
                    // ],
                    'line-color': [
                      'interpolate',
                      ['linear'],
                      ['get', 'Strength'],
                      0, 'blue', // Lowest strength value
                      11, 'red' // Highest strength value
                  ],
                    'line-opacity': [
                        'interpolate', ['linear'], ['get', 'Strength'],
                        0, 0.1,
                        11, 1
                    ],
                    'line-width': [
                        'interpolate', ['linear'], ['get', 'Strength'],
                        0, 1,
                        11, 10
                    ]
                },
            });
        });


        // Fetch the well data from the provided URL
        const wellDataUrl = 'http://localhost:3001/well-data';
        const wellDataResponse = await fetch(wellDataUrl);
        const wellGeojsonData = await wellDataResponse.json();

        // Filter features based on the date
        const filteredWellFeatures = wellGeojsonData.features.filter(feature => feature.properties.Date === filterDate);
        
        let maxFluid = 0;
        filteredWellFeatures.forEach(feature => {
            const oilProduction = feature.properties['PRD Prdcg-Day Avg OIL Bbl/Day'] || 0;
            const waterProduction = feature.properties['PRD Prdcg-Day Avg WTR Bbl/Day'] || 0;
            const waterInjection = feature.properties['INJ Inj-Day Avg Water Bbl'] || 0;
            const fluid = oilProduction + waterInjection + waterProduction;
            maxFluid = Math.max(maxFluid, fluid);
        });

        // Modify the GeoJSON data to include the combined normalized fluid rate as the radius property
        filteredWellFeatures.forEach(feature => {
            const oilProduction = feature.properties['PRD Prdcg-Day Avg OIL Bbl/Day'] || 0;
            const waterProduction = feature.properties['PRD Prdcg-Day Avg WTR Bbl/Day'] || 0;
            const waterInjection = feature.properties['INJ Inj-Day Avg Water Bbl'] || 0;
            const fluid = oilProduction + waterProduction + waterInjection;
            feature.properties.radius = 1.2 * fluid / maxFluid;
        });

        // Create a GeoJSON FeatureCollection object
        const filteredWellFeatureCollection = {
          type: "FeatureCollection",
          features: filteredWellFeatures
        };

        mapRef.current.addSource('geojson-data', {
          type: 'geojson',
          data: filteredWellFeatureCollection,
        });

        

        mapRef.current.addLayer({
          id: 'geojson-layer',
          type: 'circle',
          source: 'geojson-data',
          paint: {
            'circle-radius': [
                'interpolate',
                ['linear'],
                ['zoom'],
                6, ['max', ['*', 2, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 6
                8, ['max', ['*', 4, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 8
                10, ['max', ['*', 6, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 10
                11, ['max', ['*', 8, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 11
                12, ['max', ['*', 10, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 12
                14, ['max', ['*', 10, ['get', 'radius']], 4], // Minimum size of 2 at zoom level 14
            ],

            'circle-color': [
              'match',
              ['get', 'Type'],
              'PROD', '#02f05d',
              'INJ', '#57b4fa',
              '#808080',
            ],
            'circle-stroke-width': 1,
            'circle-stroke-color': [
              'match',
              ['get', 'Type'],
              'PROD', '#000000', // Black stroke for producers
              'INJ', '#FFFFFF', // White stroke for injectors
              '#000000', // Default stroke color
          ],
          },
        });

        const handleDateChange = (newFilterDate) => {
          const dateFilterExpression = ['==', ['to-string', ['get', 'Date']], newFilterDate];
          mapRef.current.setFilter('geojson-layer', dateFilterExpression);
        };

        // const intervalId = setInterval(async () => {
        //   const newFilterDate = filterDate;
        //   handleDateChange(newFilterDate);
        // }, 3000);

         // Add a popup to show feature information on hover
      mapRef.current.on('mouseenter', 'geojson-layer', (e) => {
        mapRef.current.getCanvas().style.cursor = 'pointer';
        setHoveredFeature(e.features[0]);
      });

      mapRef.current.on('mouseleave', 'geojson-layer', () => {
        mapRef.current.getCanvas().style.cursor = '';
        setHoveredFeature(null);
      });

        return () => {
          // clearInterval(intervalId);
        };
      });
    } else {
      const dateFilterExpression = ['==', ['to-string', ['get', 'Date']], filterDate];
      mapRef.current.setFilter('geojson-layer', dateFilterExpression);
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [filterDate]);

  return (
    <div>
      <div ref={mapContainerRef} style={{ width: '100%', height: '100vh' }}></div>
      {hoveredFeature && (
        <div style={{
          position: 'absolute',
          top: 10,
          right: 15,
          background: 'rgba(255, 255, 255, 0)',
          padding: 10,
          borderRadius: 5,
          color: '#FFFFFF',
          fontWeight: 'bold',
          transition: 'color 0.3s ease',
          fontSize: '24px',
        }}>
          <p>{"UWI: " + hoveredFeature.properties.UWI}</p>
          <p>{"Type: " + hoveredFeature.properties['Type']}</p>
          <p>{"Status: " + hoveredFeature.properties['Status Description']}</p>
          <p>{"Oil Prod: " + hoveredFeature.properties['PRD Calndr-Day Avg OIL Bbl\/Day']}</p>
          <p>{"Water Prod: " + hoveredFeature.properties['PRD Calndr-Day Avg WTR Bbl\/Day']}</p>
          <p>{"Water Inject: " + hoveredFeature.properties['INJ Inj-Day Avg Water Bbl']}</p>
          <p>{"Water Cut: " + (hoveredFeature.properties['PRD Calndr-Day Avg WTR Bbl\/Day']/(hoveredFeature.properties['PRD Calndr-Day Avg WTR Bbl\/Day']+hoveredFeature.properties['PRD Calndr-Day Avg OIL Bbl\/Day'])).toFixed(2)}</p>
        </div>
      )}

      <div style={{ position: 'absolute', bottom: 20, left: 20, zIndex: 1, width: '97%' }}>
        <Typography id="date-slider" gutterBottom>
          Select Month:
        </Typography>
        <Slider
          ref={sliderRef}
          value={monthRange.indexOf(filterDate)}
          min={0}
          max={monthRange.length - 1}
          step={1}
          valueLabelDisplay="off"
          onChangeCommitted={handleSliderChange}
          aria-labelledby="date-slider"
          sx={{ color: 'rgba(200, 200, 200, 0.7)' }}
        />
      </div>
      <Typography variant="h6" style={{ position: 'absolute', bottom: 70, left: 20, color: '#FFFFFF' }}>
        {filterDate}
      </Typography>
    </div>
  );
};

const generateMonthRange = (startDate, endDate) => {
  const monthRange = [];
  let currentDate = new Date(startDate);

  while (currentDate <= endDate) {
    const month = (currentDate.getMonth() + 1).toString().padStart(2, '0');
    const year = currentDate.getFullYear();
    const formattedDate = `${year}-${month}-01`;
    monthRange.push(formattedDate);
    currentDate.setMonth(currentDate.getMonth() + 1);
  }

  return monthRange;
};

export default Map;

