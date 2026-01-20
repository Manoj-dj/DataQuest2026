import { useState } from 'react';
import { LayoutDashboard, Map, MessageSquare, BarChart3, Settings, Filter, Zap, AlertTriangle, Play, History } from 'lucide-react';
import { DISASTER_TYPES, SEVERITY_LEVELS } from '../../utils/constants';

export const Sidebar = ({ 
  activeView, 
  onViewChange, 
  filters, 
  onFiltersChange,
  isOpen,
  onToggle 
}) => {
  const [filtersOpen, setFiltersOpen] = useState(false);

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'events', label: 'Events', icon: BarChart3 },
    { id: 'map', label: 'Map', icon: Map },
    { id: 'query', label: 'Query', icon: MessageSquare },
    { id: 'predictions', label: 'Predictions', icon: Zap },
    { id: 'alerts', label: 'Explainable Alerts', icon: AlertTriangle },
    { id: 'simulator', label: 'Scenario Simulator', icon: Play },
    { id: 'past-events', label: 'Past Events', icon: History },
    { id: 'settings', label: 'Alert Settings', icon: Settings },
  ];

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-0 top-20 z-40 p-2 bg-slate-900 text-white rounded-r-lg hover:bg-slate-800"
      >
        <Filter className="w-5 h-5" />
      </button>
    );
  }

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 h-[calc(100vh-73px)] overflow-y-auto">
      <div className="p-4">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Navigation</h2>
          <button
            onClick={onToggle}
            className="text-slate-400 hover:text-white"
          >
            ×
          </button>
        </div>

        <nav className="space-y-1 mb-6">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onViewChange(item.id)}
                className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                  isActive
                    ? 'bg-blue-500/20 text-blue-400 border border-blue-500/50'
                    : 'text-slate-300 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 pt-4">
          <button
            onClick={() => setFiltersOpen(!filtersOpen)}
            className="w-full flex items-center justify-between px-3 py-2 text-slate-300 hover:text-white"
          >
            <span className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Filters
            </span>
            <span>{filtersOpen ? '▼' : '▶'}</span>
          </button>

          {filtersOpen && (
            <div className="mt-3 space-y-4">
              <div>
                <label className="block text-sm text-slate-400 mb-2">Disaster Type</label>
                <select
                  value={filters.type || ''}
                  onChange={(e) => onFiltersChange({ ...filters, type: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {DISASTER_TYPES.map((type) => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm text-slate-400 mb-2">Severity</label>
                <select
                  value={filters.severity || ''}
                  onChange={(e) => onFiltersChange({ ...filters, severity: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {SEVERITY_LEVELS.map((level) => (
                    <option key={level.value} value={level.value}>
                      {level.label}
                    </option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => onFiltersChange({ type: '', severity: '' })}
                className="w-full px-3 py-2 text-sm bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors"
              >
                Clear Filters
              </button>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};
