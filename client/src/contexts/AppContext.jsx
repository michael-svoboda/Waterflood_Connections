// AppContext.js
import React, { createContext, useContext, useState } from 'react';

const AppContext = createContext();

export const useAppContext = () => {
  return useContext(AppContext);
};

export const AppContextProvider = ({ children }) => {
  const [sharedState, setSharedState] = useState({
    // your initial shared state goes here
    exampleValue: 'Hello from context!',
  });

  const updateSharedState = (newState) => {
    setSharedState((prev) => ({ ...prev, ...newState }));
  };

  return (
    <AppContext.Provider value={{ sharedState, updateSharedState }}>
      {children}
    </AppContext.Provider>
  );
};
