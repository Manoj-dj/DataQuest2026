import { useState, useEffect, useCallback } from 'react';
import { websocketService } from '../services/websocket';

export const useWebSocket = () => {
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [events, setEvents] = useState([]);

  useEffect(() => {
    websocketService.connect();

    const unsubscribe = websocketService.subscribe((data) => {
      if (data.type === 'connection') {
        setConnectionStatus(data.status);
      } else if (data.type === 'new_event') {
        setEvents((prev) => [data.event, ...prev].slice(0, 100));
      }
    });

    return () => {
      unsubscribe();
    };
  }, []);

  return {
    connectionStatus,
    events,
    isConnected: connectionStatus === 'connected',
  };
};
