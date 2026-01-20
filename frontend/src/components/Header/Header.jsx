import { Globe, Wifi, WifiOff, Activity, Zap } from 'lucide-react';
import { useHealth } from '../../hooks/useHealth';
import { useWebSocket } from '../../hooks/useWebSocket';
import { useState, useEffect } from 'react';

export const Header = () => {
  const { data: health } = useHealth();
  const { connectionStatus } = useWebSocket();
  const [predictionsActive, setPredictionsActive] = useState(false);

  const isHealthy = health?.status === 'healthy';
  const isConnected = connectionStatus === 'connected';

  // Check if predictions are available
  useEffect(() => {
    const checkPredictions = async () => {
      try {
        const response = await fetch('http://localhost:8080/api/predictions');
        const data = await response.json();
        const hasPredictions = data.total > 0 || (data.predictions && data.predictions.length > 0);
        setPredictionsActive(hasPredictions);
        console.log('Predictions status:', hasPredictions, data);
      } catch (error) {
        console.log('Predictions check failed:', error);
        setPredictionsActive(false);
      }
    };

    checkPredictions();
    // Refresh every 30 seconds
    const interval = setInterval(checkPredictions, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="bg-slate-900 border-b border-slate-800 px-6 py-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <Globe className="w-8 h-8 text-blue-500" />
        <div>
          <h1 className="text-xl font-bold text-white">DisasterLens AI</h1>
          <p className="text-sm text-slate-400">Real-Time Climate Emergency Intelligence</p>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800">
          {isConnected ? (
            <>
              <Wifi className="w-4 h-4 text-green-400" />
              <span className="text-sm text-green-400">Connected</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-red-400" />
              <span className="text-sm text-red-400">Disconnected</span>
            </>
          )}
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800 border border-slate-700">
          <Zap className={`w-4 h-4 ${predictionsActive ? 'text-yellow-400' : 'text-yellow-500'}`} />
          <span className={`text-sm font-medium ${predictionsActive ? 'text-yellow-400' : 'text-yellow-500'}`}>
            {predictionsActive ? 'Predictions Active' : 'Predictions'}
          </span>
        </div>

        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800">
          <Activity className={`w-4 h-4 ${isHealthy ? 'text-green-400' : 'text-red-400'}`} />
          <span className={`text-sm ${isHealthy ? 'text-green-400' : 'text-red-400'}`}>
            {health?.status || 'Unknown'}
          </span>
        </div>

        {health?.active_events !== undefined && (
          <div className="px-3 py-1.5 rounded-lg bg-blue-500/20 border border-blue-500/50">
            <span className="text-sm font-semibold text-blue-400">
              {health.active_events} Events
            </span>
          </div>
        )}
      </div>
    </header>
  );
};
