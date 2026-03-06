import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { kitchensAPI, organizationsAPI } from '../services/api';
import { useAuth } from './AuthContext';

const AppContext = createContext(null);

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};

export const AppProvider = ({ children }) => {
  const { user, isAuthenticated } = useAuth();
  const [kitchens, setKitchens] = useState([]);
  const [selectedKitchen, setSelectedKitchen] = useState(null);
  const [organization, setOrganization] = useState(null);
  const [loading, setLoading] = useState(false);

  // Load kitchens and organization when user is authenticated
  useEffect(() => {
    const loadData = async () => {
      if (!isAuthenticated || !user) return;
      
      setLoading(true);
      try {
        // Load kitchens
        const kitchensRes = await kitchensAPI.list();
        setKitchens(kitchensRes.data);
        
        // Set first kitchen as selected if none selected
        if (kitchensRes.data.length > 0 && !selectedKitchen) {
          setSelectedKitchen(kitchensRes.data[0]);
        }
        
        // Load organization
        if (user.organization_id) {
          const orgRes = await organizationsAPI.get(user.organization_id);
          setOrganization(orgRes.data);
        }
      } catch (err) {
        console.error('Failed to load app data:', err);
      } finally {
        setLoading(false);
      }
    };
    
    loadData();
  }, [isAuthenticated, user]);

  const refreshKitchens = useCallback(async () => {
    try {
      const response = await kitchensAPI.list();
      setKitchens(response.data);
      return response.data;
    } catch (err) {
      console.error('Failed to refresh kitchens:', err);
      return [];
    }
  }, []);

  const selectKitchen = useCallback((kitchen) => {
    setSelectedKitchen(kitchen);
    localStorage.setItem('selectedKitchenId', kitchen?.id);
  }, []);

  const value = {
    kitchens,
    selectedKitchen,
    organization,
    loading,
    refreshKitchens,
    selectKitchen,
    setOrganization,
  };

  return (
    <AppContext.Provider value={value}>
      {children}
    </AppContext.Provider>
  );
};

export default AppContext;
