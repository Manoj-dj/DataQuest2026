export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws';

export const DISASTER_TYPES = [
  { value: '', label: 'All Types' },
  { value: 'earthquake', label: 'Earthquake' },
  { value: 'wildfire', label: 'Wildfire' },
  { value: 'flood', label: 'Flood' },
  { value: 'cyclone', label: 'Cyclone' },
  { value: 'tsunami', label: 'Tsunami' },
  { value: 'volcano', label: 'Volcano' },
];

export const SEVERITY_LEVELS = [
  { value: '', label: 'All Severities' },
  { value: 'Red', label: 'Red Alert', color: '#dc2626' },
  { value: 'Orange', label: 'Orange Alert', color: '#f97316' },
  { value: 'Green', label: 'Green Alert', color: '#16a34a' },
];

export const QUICK_QUERIES = [
  'What are the most severe disasters right now?',
  'Show me all earthquakes in the last 48 hours',
  'Which wildfires are currently active?',
  'What disasters affect populated areas?',
  'Show me recent floods in Asia',
];
