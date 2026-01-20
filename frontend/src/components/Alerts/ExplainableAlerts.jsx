import { useState, useEffect } from 'react';
import { AlertTriangle, TrendingUp, Info } from 'lucide-react';
import './ExplainableAlerts.css';

const API_BASE = 'http://localhost:8080';

export const ExplainableAlerts = () => {
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  const loadAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/alerts/recent?limit=20`);
      const data = await response.json();
      setAlerts(data.alerts || []);
    } catch (error) {
      console.error('Failed to load alerts:', error);
      setAlerts([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
    const interval = setInterval(loadAlerts, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'Red': return 'bg-red-500';
      case 'Orange': return 'bg-orange-500';
      case 'Green': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  const getSeverityTextColor = (severity) => {
    switch (severity) {
      case 'Red': return 'text-red-400';
      case 'Orange': return 'text-orange-400';
      case 'Green': return 'text-green-400';
      default: return 'text-gray-400';
    }
  };

  const cleanMarkdown = (text) => {
    if (!text) return '';
    return text.replace(/\*\*/g, '').replace(/##/g, '').trim();
  };

  if (isLoading) {
    return (
      <div className="explainable-alerts-container">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading alerts...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="explainable-alerts-container">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <AlertTriangle className="w-6 h-6 text-yellow-500" />
          Explainable Alerts
        </h2>
        <button
          onClick={loadAlerts}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {alerts.length === 0 ? (
        <div className="text-center py-12 bg-slate-800 rounded-lg border border-slate-700">
          <Info className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400">No alerts available yet.</p>
          <p className="text-sm text-slate-500 mt-2">Alerts will appear here as disasters are detected.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alerts.map((alert) => (
            <div
              key={alert.alert_id}
              className="alert-card bg-slate-800 rounded-lg border border-slate-700 p-6 hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-white mb-2">{cleanMarkdown(alert.title)}</h3>
                  <p className="text-slate-400 flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    {cleanMarkdown(alert.location)}
                  </p>
                </div>
                <div className={`px-3 py-1 rounded-full ${getSeverityColor(alert.severity)} text-white text-sm font-medium`}>
                  {alert.severity}
                </div>
              </div>

              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-300">Risk Score</span>
                  <span className={`text-lg font-bold ${getSeverityTextColor(alert.severity)}`}>
                    {alert.risk_score.toFixed(1)}/10
                  </span>
                </div>
                <div className="w-full bg-slate-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${getSeverityColor(alert.severity)} transition-all`}
                    style={{ width: `${(alert.risk_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div className="mb-4">
                <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                  <TrendingUp className="w-4 h-4" />
                  Why this fired
                </h4>
                <ul className="space-y-2">
                  {alert.signals && alert.signals.length > 0 ? (
                    alert.signals.map((signal, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm">
                        <span className="text-blue-400 mt-1">•</span>
                        <div className="flex-1">
                          <span className="font-medium text-slate-300">{cleanMarkdown(signal.signal_name)}</span>
                          <span className="text-slate-500 ml-2">
                            (weight: {(signal.weight * 100).toFixed(0)}%)
                          </span>
                          {signal.description && (
                            <p className="text-slate-400 mt-1">{cleanMarkdown(signal.description)}</p>
                          )}
                        </div>
                      </li>
                    ))
                  ) : (
                    <li className="text-slate-400 text-sm">No signals available</li>
                  )}
                </ul>
              </div>

              {alert.summary && (
                <div className="mt-4 pt-4 border-t border-slate-700">
                  <p className="text-slate-300 leading-relaxed">{cleanMarkdown(alert.summary)}</p>
                </div>
              )}

              <div className="mt-4 text-xs text-slate-500">
                {new Date(alert.timestamp).toLocaleString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
