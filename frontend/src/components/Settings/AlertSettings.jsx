import { useState, useEffect } from 'react';
import { Settings, Save, CheckCircle } from 'lucide-react';
import './AlertSettings.css';

const API_BASE = 'http://localhost:8080';

export const AlertSettings = () => {
  const [selectedRole, setSelectedRole] = useState('citizen');
  const [settings, setSettings] = useState({
    min_severity: 'Red',
    channels: ['websocket'],
    show_predictions: true,
    show_confirmed_only: false
  });
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const loadSettings = async (role) => {
    try {
      const response = await fetch(`${API_BASE}/api/alert-settings/${role}`);
      const data = await response.json();
      setSettings(data.settings);
    } catch (error) {
      console.error('Failed to load settings:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadSettings(selectedRole);
  }, [selectedRole]);

  const handleRoleChange = (e) => {
    setSelectedRole(e.target.value);
    setIsLoading(true);
  };

  const handleSettingChange = (field, value) => {
    setSettings(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleChannelToggle = (channel) => {
    setSettings(prev => ({
      ...prev,
      channels: prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel]
    }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setSaveSuccess(false);

    try {
      const response = await fetch(`${API_BASE}/api/alert-settings/${selectedRole}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          role: selectedRole,
          ...settings
        })
      });

      if (!response.ok) {
        throw new Error('Failed to save settings');
      }

      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error('Failed to save settings:', error);
      alert('Failed to save settings. Please try again.');
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="alert-settings-container">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-slate-400">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="alert-settings-container">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-white flex items-center gap-2">
          <Settings className="w-6 h-6 text-blue-500" />
          Alert Settings
        </h2>
        {saveSuccess && (
          <div className="flex items-center gap-2 text-green-400">
            <CheckCircle className="w-5 h-5" />
            <span>Settings saved!</span>
          </div>
        )}
      </div>

      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <div className="mb-6">
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Role
          </label>
          <select
            value={selectedRole}
            onChange={handleRoleChange}
            className="w-full max-w-xs px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="citizen">Citizen</option>
            <option value="responder">Responder</option>
            <option value="admin">Admin</option>
          </select>
          <p className="text-xs text-slate-500 mt-2">
            {selectedRole === 'citizen' && 'Receive only high-severity alerts'}
            {selectedRole === 'responder' && 'Receive moderate and high-severity alerts'}
            {selectedRole === 'admin' && 'Receive all alerts including low-severity'}
          </p>
        </div>

        <div className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Minimum Severity to Alert
            </label>
            <select
              value={settings.min_severity}
              onChange={(e) => handleSettingChange('min_severity', e.target.value)}
              className="w-full max-w-xs px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="Red">Red (High Severity Only)</option>
              <option value="Orange">Orange (Moderate and High)</option>
              <option value="Green">Green (All Severities)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-3">
              Alert Channels
            </label>
            <div className="space-y-2">
              {['websocket', 'email', 'sms'].map((channel) => (
                <label key={channel} className="flex items-center gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.channels.includes(channel)}
                    onChange={() => handleChannelToggle(channel)}
                    className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
                  />
                  <span className="text-slate-300 capitalize">{channel}</span>
                  {channel === 'email' && (
                    <span className="text-xs text-slate-500">(Coming soon)</span>
                  )}
                  {channel === 'sms' && (
                    <span className="text-xs text-slate-500">(Coming soon)</span>
                  )}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.show_predictions}
                onChange={(e) => handleSettingChange('show_predictions', e.target.checked)}
                className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-slate-300">Show Predictions</span>
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-8">
              Display AI-generated predictions alongside confirmed events
            </p>
          </div>

          <div>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={settings.show_confirmed_only}
                onChange={(e) => handleSettingChange('show_confirmed_only', e.target.checked)}
                className="w-5 h-5 rounded border-slate-600 bg-slate-700 text-blue-600 focus:ring-2 focus:ring-blue-500"
              />
              <span className="text-slate-300">Show Confirmed Events Only</span>
            </label>
            <p className="text-xs text-slate-500 mt-1 ml-8">
              Hide predictions and only show confirmed disaster events
            </p>
          </div>

          <div className="pt-4 border-t border-slate-700">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-blue-800 disabled:cursor-not-allowed text-white font-semibold rounded-lg transition-colors flex items-center gap-2"
            >
              {isSaving ? (
                <>
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                  Saving...
                </>
              ) : (
                <>
                  <Save className="w-5 h-5" />
                  Save Settings
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
