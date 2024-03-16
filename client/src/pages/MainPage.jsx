import React, { useState, useEffect } from 'react';
import Map from '../components/map';
import BasicSlider from '../components/Slider';

const MainPage = () => {
  const [geojsonData, setGeojsonData] = useState(null);

  useEffect(() => {
    // Fetch GeoJSON data from the endpoint
    fetch('http://localhost:3001/well-data')
      .then(response => response.json())
      .then(data => {
        setGeojsonData(data);
      });
  }, []);

  return (
    <div>
      {geojsonData && (
        <>
          <Map data={geojsonData} />
          {/* Other components or content */}
        </>
      )}
    </div>
  );
};

export default MainPage;

