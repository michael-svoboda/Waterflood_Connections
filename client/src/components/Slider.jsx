import React, { useState } from 'react';
import Slider from '@mui/material/Slider';

const BasicSlider = () => {
  const [value, setValue] = useState(50);

  const handleChange = (event, newValue) => {
    setValue(newValue);
  };

  return (
    <div style={{ width: '300px', margin: 'auto', padding: '20px' }}>
      <Slider
        value={value}
        onChange={handleChange}
        valueLabelDisplay="auto"
        aria-labelledby="basic-slider"
      />
      <p>Value: {value}</p>
    </div>
  );
};

export default BasicSlider;
