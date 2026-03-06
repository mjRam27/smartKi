import axios from 'axios';

const API_BASE = process.env.REACT_APP_BACKEND_URL;
const API = `${API_BASE}/api`;

// Create axios instance
const apiClient = axios.create({
  baseURL: API,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API}/auth/refresh`, {
            refresh_token: refreshToken,
          });
          
          const { access_token, refresh_token } = response.data;
          localStorage.setItem('access_token', access_token);
          localStorage.setItem('refresh_token', refresh_token);
          
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return apiClient(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authAPI = {
  register: (data) => apiClient.post('/auth/register', data),
  login: (data) => apiClient.post('/auth/login', data),
  refresh: (refreshToken) => apiClient.post('/auth/refresh', { refresh_token: refreshToken }),
  me: () => apiClient.get('/auth/me'),
};

// Organizations API
export const organizationsAPI = {
  list: () => apiClient.get('/organizations/'),
  get: (id) => apiClient.get(`/organizations/${id}`),
  create: (data) => apiClient.post('/organizations/', data),
  update: (id, data) => apiClient.put(`/organizations/${id}`, data),
};

// Kitchens API
export const kitchensAPI = {
  list: () => apiClient.get('/kitchens/'),
  get: (id) => apiClient.get(`/kitchens/${id}`),
  create: (data) => apiClient.post('/kitchens/', data),
  update: (id, data) => apiClient.put(`/kitchens/${id}`, data),
  delete: (id) => apiClient.delete(`/kitchens/${id}`),
};

// Recipes API
export const recipesAPI = {
  list: (params) => apiClient.get('/recipes/', { params }),
  get: (id) => apiClient.get(`/recipes/${id}`),
  create: (data) => apiClient.post('/recipes/', data),
  update: (id, data) => apiClient.put(`/recipes/${id}`, data),
  delete: (id) => apiClient.delete(`/recipes/${id}`),
  approve: (id) => apiClient.post(`/recipes/${id}/approve`),
  generate: (data) => apiClient.post('/recipes/generate', data),
};

// Ingredients API
export const ingredientsAPI = {
  list: (params) => apiClient.get('/ingredients/', { params }),
  get: (id) => apiClient.get(`/ingredients/${id}`),
  create: (data) => apiClient.post('/ingredients/', data),
  update: (id, data) => apiClient.put(`/ingredients/${id}`, data),
  delete: (id) => apiClient.delete(`/ingredients/${id}`),
};

// Inventory API
export const inventoryAPI = {
  list: (params) => apiClient.get('/inventory/', { params }),
  get: (id) => apiClient.get(`/inventory/${id}`),
  create: (data) => apiClient.post('/inventory/', data),
  adjust: (id, params) => apiClient.put(`/inventory/${id}/adjust`, null, { params }),
  delete: (id) => apiClient.delete(`/inventory/${id}`),
};

// Suppliers API
export const suppliersAPI = {
  list: (params) => apiClient.get('/suppliers/', { params }),
  get: (id) => apiClient.get(`/suppliers/${id}`),
  create: (data) => apiClient.post('/suppliers/', data),
  update: (id, data) => apiClient.put(`/suppliers/${id}`, data),
  rate: (id, rating) => apiClient.put(`/suppliers/${id}/rate`, null, { params: { rating } }),
  delete: (id) => apiClient.delete(`/suppliers/${id}`),
};

// Procurement API
export const procurementAPI = {
  listOrders: (params) => apiClient.get('/procurement/orders', { params }),
  getOrder: (id) => apiClient.get(`/procurement/orders/${id}`),
  createOrder: (data) => apiClient.post('/procurement/orders', data),
  approveOrder: (id) => apiClient.put(`/procurement/orders/${id}/approve`),
  receiveOrder: (id) => apiClient.put(`/procurement/orders/${id}/receive`),
  cancelOrder: (id) => apiClient.put(`/procurement/orders/${id}/cancel`),
};

// Waste API
export const wasteAPI = {
  list: (params) => apiClient.get('/waste/', { params }),
  get: (id) => apiClient.get(`/waste/${id}`),
  create: (data) => apiClient.post('/waste/', data),
  summary: (params) => apiClient.get('/waste/summary', { params }),
  delete: (id) => apiClient.delete(`/waste/${id}`),
};

// Production API
export const productionAPI = {
  list: (params) => apiClient.get('/production/', { params }),
  get: (id) => apiClient.get(`/production/${id}`),
  create: (data) => apiClient.post('/production/', data),
  start: (id) => apiClient.put(`/production/${id}/start`),
  complete: (id, params) => apiClient.put(`/production/${id}/complete`, null, { params }),
  cancel: (id) => apiClient.delete(`/production/${id}`),
};

// Analytics API
export const analyticsAPI = {
  dashboard: (params) => apiClient.get('/analytics/dashboard', { params }),
  wasteTrends: (params) => apiClient.get('/analytics/waste-trends', { params }),
  profitability: (params) => apiClient.get('/analytics/profitability', { params }),
  supplierPerformance: () => apiClient.get('/analytics/supplier-performance'),
  inventoryAlerts: (params) => apiClient.get('/analytics/inventory-alerts', { params }),
};

export default apiClient;
