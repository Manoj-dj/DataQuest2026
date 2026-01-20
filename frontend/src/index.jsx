import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// CRITICAL: Verify React entry point is loading
console.log('🚀🚀🚀 REACT ENTRY POINT LOADED - index.jsx 🚀🚀🚀');
console.log('🚀 React entry point loaded at', new Date().toISOString());
console.log('🚀 Root element:', document.getElementById('root'));
console.log('🚀 If you see "Map initialized" from app.js, STOP - old app is loading!');

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
