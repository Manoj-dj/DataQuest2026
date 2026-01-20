import { useState } from 'react';
import { Play, AlertCircle, TrendingUp } from 'lucide-react';
import './ScenarioSimulator.css';

const API_BASE = 'http://localhost:8080';

export const ScenarioSimulator = () => {
  const [formData, setFormData] = useState({
    hazard_type: 'earthquake',
    magnitude: 6.5,
    location: '',
    latitude: 0.0,
    longitude: 0.0,
    population_density: 1000,
    infrastructure_score: 7.0
  });

  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'latitude' || name === 'longitude' || name === 'magnitude' || 
              name === 'population_density' || name === 'infrastructure_score' 
        ? parseFloat(value) || 0 
        : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`${API_BASE}/api/simulate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) {
        throw new Error(`Simulation failed: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
      console.error('Simulation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const getRiskColor = (score) => {
    if (score >= 7.5) return 'text-red-400';
    if (score >= 5.0) return 'text-orange-400';
    return 'text-green-400';
  };

  const getRiskBgColor = (score) => {
    if (score >= 7.5) return 'bg-red-500';
    if (score >= 5.0) return 'bg-orange-500';
    return 'bg-green-500';
  };

  const cleanMarkdown = (text) => {
    if (!text) return '';
    return text.replace(/\*\*/g, '').replace(/##/g, '').trim();
  };

  return (
    <div className="scenario-simulator-container">
      <div className="flex items-center gap-2 mb-6">
        <Play className="w-6 h-6 text-blue-500" />
        <h2 className="text-2xl font-bold text-white">Scenario Simulator</h2>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4">Simulation Parameters</h3>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Hazard Type
              </label>
              <select
                name="hazard_type"
                value={formData.hazard_type}
                onChange={handleInputChange}
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="earthquake">Earthquake</option>
                <option value="wildfire">Wildfire</option>
                <option value="flood">Flood</option>
                <option value="cyclone">Cyclone</option>
                <option value="tsunami">Tsunami</option>
                <option value="volcano">Volcano</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Magnitude
              </label>
              <input
                type="number"
                name="magnitude"
                value={formData.magnitude}
                onChange={handleInputChange}
                step="0.1"
                min="0"
                max="10"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Location
              </label>
              <input
                type="text"
                name="location"
                value={formData.location}
                onChange={handleInputChange}
                placeholder="e.g., San Francisco, CA"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Latitude
                </label>
                <input
                  type="number"
                  name="latitude"
                  value={formData.latitude}
                  onChange={handleInputChange}
                  step="0.0001"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Longitude
                </label>
                <input
                  type="number"
                  name="longitude"
                  value={formData.longitude}
                  onChange={handleInputChange}
                  step="0.0001"
                  className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Population Density (per km²)
              </label>
              <input
                type="number"
                name="population_density"
                value={formData.population_density}
                onChange={handleInputChange}
                min="0"
                step="100"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Infrastructure Score (0-10)
              </label>
              <input
                type="number"
                name="infrastructure_score"
                value={formData.infrastructure_score}
                onChange={handleInputChange}
                min="0"
                max="10"
                step="0.1"
                className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Simulating...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Run Simulation
                </>
              )}
            </button>
          </form>

          {error && (
            <div className="mt-4 p-4 bg-red-900/20 border border-red-500/50 rounded-lg">
              <p className="text-red-400 text-sm">{error}</p>
            </div>
          )}
        </div>

        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            Simulation Results
          </h3>

          {!result ? (
            <div className="text-center py-12">
              <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-4" />
              <p className="text-slate-400">Run a simulation to see predicted impacts</p>
            </div>
          ) : (
            <div className="space-y-6">
              <div className="text-center p-6 bg-slate-900 rounded-lg border border-slate-700">
                <div className="text-sm text-slate-400 mb-2">Predicted Risk Score</div>
                <div className={`text-5xl font-bold ${getRiskColor(result.predicted_risk_score)}`}>
                  {result.predicted_risk_score.toFixed(1)}
                </div>
                <div className="text-slate-500 text-sm mt-2">out of 10.0</div>
                <div className="mt-4 w-full bg-slate-700 rounded-full h-3">
                  <div
                    className={`h-3 rounded-full ${getRiskBgColor(result.predicted_risk_score)} transition-all`}
                    style={{ width: `${(result.predicted_risk_score / 10) * 100}%` }}
                  ></div>
                </div>
              </div>

              {result.predicted_impacts && result.predicted_impacts.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold text-white mb-3">Predicted Impacts</h4>
                  <ul className="space-y-2">
                    {result.predicted_impacts.map((impact, idx) => (
                      <li key={idx} className="flex items-start gap-3 text-sm">
                        <span className="text-blue-400 mt-1">•</span>
                        <span className="text-slate-300 flex-1">{cleanMarkdown(impact)}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {result.explanation && (
                <div className="pt-4 border-t border-slate-700">
                  <h4 className="text-sm font-semibold text-white mb-2">Explanation</h4>
                  <p className="text-slate-300 text-sm leading-relaxed">
                    {cleanMarkdown(result.explanation)}
                  </p>
                </div>
              )}

              <div className="text-xs text-slate-500 pt-4 border-t border-slate-700">
                Simulated at {new Date(result.timestamp).toLocaleString()}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
