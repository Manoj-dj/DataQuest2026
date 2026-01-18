import axios from 'axios';
import { API_BASE_URL } from '../utils/constants';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error('API Error:', error.response.data);
    } else if (error.request) {
      console.error('Network Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export const queryRAG = async (query, topK = 5, filters = null) => {
  const response = await api.post('/query', {
    query,
    top_k: topK,
    filters,
  });
  return response.data;
};

export const getEvents = async (limit = 50, disasterType = null) => {
  const params = { limit };
  if (disasterType) params.disaster_type = disasterType;
  const response = await api.get('/events/latest', { params });
  return response.data;
};

export const getEventDetails = async (eventId) => {
  const response = await api.get(`/events/${eventId}`);
  return response.data;
};

export const getEventImagery = async (eventId) => {
  const response = await api.get(`/events/${eventId}/imagery`);
  return response.data;
};

export const analyzeImagery = async (imageUrl, context = null) => {
  const response = await api.post('/imagery/analyze', {
    image_url: imageUrl,
    context,
    event_context: context,
  });
  return response.data;
};

export const getStatistics = async () => {
  const response = await api.get('/stats');
  return response.data;
};

export const getHealth = async () => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
