import { useState, useEffect } from 'react';
import { History, CheckCircle, XCircle, AlertTriangle, TrendingDown } from 'lucide-react';
import './PastEvents.css';

const API_BASE = 'http://localhost:8080';

export const PastEvents = () => {
  const [alerts, setAlerts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [impactForm, setImpactForm] = useState({
    actual_impact: '',
    actual_people_affected: '',
    was_false_alarm: false
  });

  const loadAlerts = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/alerts/recent?limit=50`);
      const data = await response.json();
      // Filter alerts that have impact data or can be updated
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
    const interval = setInterval(loadAlerts, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const getAccuracyBadge = (alert) => {
    if (alert.was_false_alarm) {
      return {
        label: 'False Alarm',
        icon: XCircle,
        color: 'text-red-400',
        bgColor: 'bg-red-900/20',
        borderColor: 'border-red-500/50'
      };
    }

    if (alert.prediction_error === undefined || alert.prediction_error === null) {
      return null;
    }

    if (alert.prediction_error === 0) {
      return {
        label: 'Accurate',
        icon: CheckCircle,
        color: 'text-green-400',
        bgColor: 'bg-green-900/20',
        borderColor: 'border-green-500/50'
      };
    } else if (alert.prediction_error > 0 && alert.actual_people_affected) {
      // Check if we overestimated or underestimated
      const predictedBucket = alert.risk_score >= 7.5 ? 3 : alert.risk_score >= 5.0 ? 2 : 1;
      const actualBucket = alert.actual_people_affected >= 100000 ? 3 : 
                          alert.actual_people_affected >= 10000 ? 2 : 1;
      
      if (predictedBucket > actualBucket) {
        return {
          label: 'Overestimated',
          icon: TrendingDown,
          color: 'text-orange-400',
          bgColor: 'bg-orange-900/20',
          borderColor: 'border-orange-500/50'
        };
      } else {
        return {
          label: 'Underestimated',
          icon: AlertTriangle,
          color: 'text-yellow-400',
          bgColor: 'bg-yellow-900/20',
          borderColor: 'border-yellow-500/50'
        };
      }
    }

    return null;
  };

  const handleImpactSubmit = async (alertId) => {
    try {
      const response = await fetch(`${API_BASE}/api/alerts/${alertId}/impact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          actual_impact: impactForm.actual_impact || null,
          actual_people_affected: impactForm.actual_people_affected ? parseInt(impactForm.actual_people_affected) : null,
          was_false_alarm: impactForm.was_false_alarm
        })
      });

      if (!response.ok) {
        throw new Error('Failed to update impact');
      }

      // Reload alerts
      await loadAlerts();
      setSelectedAlert(null);
      setImpactForm({
        actual_impact: '',
        actual_people_affected: '',
        was_false_alarm: false
      });
    } catch (error) {
      console.error('Failed to update impact:', error);
      alert('Failed to update impact. Please try again.');
    }
  };

  const cleanMarkdown = (text) => {
    if (!text) return '';
    return text.replace(/\*\*/g, '').replace(/##/g, '').trim();
  };

  if (isLoading) {
    return (
      <div className="past-events-container">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading past events...</p>
        </div>
      </div>
    );
  }

  const alertsWithImpact = alerts.filter(a => 
    a.actual_impact || a.actual_people_affected !== null || a.was_false_alarm !== null
  );

  return (
    <div className="past-events-container">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <History className="w-6 h-6 text-blue-500" />
          Past Events & Impact Analysis
        </h2>
        <button
          onClick={loadAlerts}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          Refresh
        </button>
      </div>

      {alertsWithImpact.length === 0 ? (
        <div className="text-center py-12 bg-slate-800 rounded-lg border border-slate-700">
          <History className="w-12 h-12 text-slate-500 mx-auto mb-4" />
          <p className="text-slate-400">No past events with impact data yet.</p>
          <p className="text-sm text-slate-500 mt-2">Update alerts with actual impact data to see prediction accuracy.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {alertsWithImpact.map((alert) => {
            const badge = getAccuracyBadge(alert);
            const BadgeIcon = badge?.icon;

            return (
              <div
                key={alert.alert_id}
                className="past-event-card bg-slate-800 rounded-lg border border-slate-700 p-6 hover:border-slate-600 transition-colors"
              >
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-xl font-semibold text-white mb-2">{cleanMarkdown(alert.title)}</h3>
                    <p className="text-slate-400">{cleanMarkdown(alert.location)}</p>
                  </div>
                  {badge && (
                    <div className={`px-3 py-1 rounded-full ${badge.bgColor} ${badge.borderColor} border flex items-center gap-2`}>
                      {BadgeIcon && <BadgeIcon className={`w-4 h-4 ${badge.color}`} />}
                      <span className={`text-sm font-medium ${badge.color}`}>{badge.label}</span>
                    </div>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4 mb-4">
                  <div>
                    <div className="text-xs text-slate-500 mb-1">Predicted Risk</div>
                    <div className="text-lg font-semibold text-white">{alert.risk_score.toFixed(1)}/10</div>
                  </div>
                  {alert.actual_people_affected !== null && (
                    <div>
                      <div className="text-xs text-slate-500 mb-1">Actual People Affected</div>
                      <div className="text-lg font-semibold text-white">
                        {alert.actual_people_affected.toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>

                {alert.actual_impact && (
                  <div className="mb-4 p-4 bg-slate-900 rounded-lg border border-slate-700">
                    <div className="text-sm font-semibold text-slate-300 mb-2">Actual Impact</div>
                    <p className="text-slate-400 text-sm leading-relaxed">{cleanMarkdown(alert.actual_impact)}</p>
                  </div>
                )}

                {alert.prediction_error !== null && alert.prediction_error !== undefined && (
                  <div className="text-xs text-slate-500">
                    Prediction Error: {alert.prediction_error.toFixed(1)} severity buckets
                  </div>
                )}

                {!alert.actual_impact && !alert.actual_people_affected && alert.was_false_alarm === null && (
                  <button
                    onClick={() => setSelectedAlert(alert.alert_id)}
                    className="mt-4 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                  >
                    Update Impact
                  </button>
                )}

                {selectedAlert === alert.alert_id && (
                  <div className="mt-4 p-4 bg-slate-900 rounded-lg border border-slate-700">
                    <h4 className="text-sm font-semibold text-white mb-3">Update Impact Data</h4>
                    <div className="space-y-3">
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Actual Impact Description</label>
                        <textarea
                          value={impactForm.actual_impact}
                          onChange={(e) => setImpactForm(prev => ({ ...prev, actual_impact: e.target.value }))}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          rows="3"
                          placeholder="Describe the actual impact..."
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-slate-400 mb-1">Actual People Affected</label>
                        <input
                          type="number"
                          value={impactForm.actual_people_affected}
                          onChange={(e) => setImpactForm(prev => ({ ...prev, actual_people_affected: e.target.value }))}
                          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                          placeholder="0"
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={impactForm.was_false_alarm}
                          onChange={(e) => setImpactForm(prev => ({ ...prev, was_false_alarm: e.target.checked }))}
                          className="w-4 h-4 rounded border-slate-600 bg-slate-700 text-blue-600"
                        />
                        <label className="text-sm text-slate-300">This was a false alarm</label>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleImpactSubmit(alert.alert_id)}
                          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors"
                        >
                          Save
                        </button>
                        <button
                          onClick={() => {
                            setSelectedAlert(null);
                            setImpactForm({
                              actual_impact: '',
                              actual_people_affected: '',
                              was_false_alarm: false
                            });
                          }}
                          className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white text-sm rounded-lg transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                <div className="mt-4 text-xs text-slate-500">
                  {new Date(alert.timestamp).toLocaleString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
