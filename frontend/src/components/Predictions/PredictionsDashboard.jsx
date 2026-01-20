import { useState, useEffect, useRef } from 'react';
import { AlertTriangle, TrendingUp, Activity, Zap } from 'lucide-react';
import './PredictionsDashboard.css';

export const PredictionsDashboard = () => {
  const [predictions, setPredictions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [alerts, setAlerts] = useState([]);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Debug: Log when component mounts
  useEffect(() => {
    console.log('✅ PredictionsDashboard component loaded');
  }, []);

  useEffect(() => {
    loadPredictions();
    connectWebSocket();
    
    // Refresh predictions every 30 seconds
    const interval = setInterval(loadPredictions, 30000);
    
    return () => {
      clearInterval(interval);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const connectWebSocket = () => {
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.hostname;
    const wsUrl = `${protocol}//${host}:8080/ws/predictions`;
    
    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('Prediction WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'PREDICTION_ALERT') {
            displayLiveAlert(data);
          } else if (data.type === 'connected') {
            console.log('WebSocket connection confirmed:', data.message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected, reconnecting in 5 seconds...');
        wsRef.current = null;
        reconnectTimeoutRef.current = setTimeout(() => {
          connectWebSocket();
        }, 5000);
      };
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      reconnectTimeoutRef.current = setTimeout(() => {
        connectWebSocket();
      }, 5000);
    }
  };

  const displayLiveAlert = (alert) => {
    const alertId = Date.now();
    const newAlert = { ...alert, id: alertId };
    setAlerts(prev => [...prev, newAlert]);
    
    // Auto-remove after 10 seconds
    setTimeout(() => {
      setAlerts(prev => prev.filter(a => a.id !== alertId));
    }, 10000);
  };

  const loadPredictions = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8080/api/predictions');
      const data = await response.json();
      setPredictions(data.predictions || []);
    } catch (error) {
      console.error('Failed to load predictions:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (confidence) => {
    switch (confidence?.toUpperCase()) {
      case 'HIGH':
        return 'text-green-400 bg-green-500/20 border-green-500/50';
      case 'MEDIUM':
        return 'text-yellow-400 bg-yellow-500/20 border-yellow-500/50';
      case 'LOW':
        return 'text-orange-400 bg-orange-500/20 border-orange-500/50';
      default:
        return 'text-slate-400 bg-slate-500/20 border-slate-500/50';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity?.toUpperCase()) {
      case 'RED':
      case 'CRITICAL':
        return <AlertTriangle className="w-5 h-5 text-red-400" />;
      case 'ORANGE':
      case 'HIGH':
        return <TrendingUp className="w-5 h-5 text-orange-400" />;
      case 'GREEN':
      case 'LOW':
        return <Activity className="w-5 h-5 text-green-400" />;
      default:
        return <Zap className="w-5 h-5 text-blue-400" />;
    }
  };

  return (
    <div className="predictions-dashboard h-full flex flex-col p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Zap className="w-6 h-6 text-yellow-400" />
          AI-Powered Disaster Predictions
        </h2>
        <button
          onClick={loadPredictions}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 text-white rounded-lg transition-colors text-sm"
        >
          {isLoading ? 'Loading...' : 'Refresh'}
        </button>
      </div>

      {/* Live Alerts */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`alert-banner ${alert.severity?.toLowerCase() || 'high'}`}
          >
            <div className="alert-content">
              <span className="alert-icon">🚨</span>
              <div className="alert-text">
                <strong>{alert.type || 'PREDICTION ALERT'}</strong>
                <p>{alert.message || 'New prediction alert'}</p>
                <span className="alert-time">
                  {new Date(alert.timestamp || Date.now()).toLocaleTimeString()}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Predictions Grid */}
      {isLoading && predictions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-400">Loading predictions...</div>
        </div>
      ) : predictions.length === 0 ? (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-slate-400 text-center">
            <Zap className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No predictions available at this time.</p>
            <p className="text-sm mt-2">Predictions are generated based on real-time pattern detection.</p>
          </div>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {predictions.map((pred, idx) => (
              <div key={idx} className="prediction-card">
                <div className="prediction-header">
                  <div className="flex items-center gap-2">
                    {getSeverityIcon(pred.severity)}
                    <h3 className="text-lg font-semibold text-white">{pred.event_title}</h3>
                  </div>
                  <span className={`confidence-badge ${getConfidenceColor(pred.confidence)}`}>
                    {pred.confidence || 'MEDIUM'} Confidence
                  </span>
                </div>
                
                <div className="prediction-meta mb-3">
                  <span className="text-xs text-slate-400">
                    Severity: <span className="font-semibold">{pred.severity || 'Unknown'}</span>
                  </span>
                  <span className="text-xs text-slate-400">
                    Risk Score: <span className="font-semibold">{pred.risk_score?.toFixed(1) || 'N/A'}/10</span>
                  </span>
                </div>
                
                <div className="prediction-content">
                  <div 
                    className="text-slate-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ 
                      __html: pred.prediction?.replace(/\n/g, '<br />') || 'No prediction available'
                    }}
                  />
                </div>
                
                <div className="prediction-footer">
                  <span className="text-xs text-slate-500">
                    Generated: {new Date(pred.timestamp).toLocaleString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
