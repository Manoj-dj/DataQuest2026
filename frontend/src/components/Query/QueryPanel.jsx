import { useState } from 'react';
import { Search, Send, Sparkles, Loader2, ExternalLink } from 'lucide-react';
import { marked } from 'marked';
import { queryRAG } from '../../services/api';
import { QUICK_QUERIES } from '../../utils/constants';
import './QueryPanel.css';

// Configure marked for safe rendering with better formatting
marked.setOptions({
  breaks: true, // Convert \n to <br>
  gfm: true, // GitHub Flavored Markdown
  headerIds: false,
  mangle: false
});

export const QueryPanel = () => {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const result = await queryRAG(query.trim());
      setResponse(result);
    } catch (err) {
      setError(err.message || 'Failed to process query');
    } finally {
      setIsLoading(false);
    }
  };

  const handleQuickQuery = (quickQuery) => {
    setQuery(quickQuery);
  };

  return (
    <div className="h-full flex flex-col p-6">
      <h2 className="text-2xl font-bold text-white mb-6">Ask About Current Disasters</h2>

      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., What earthquakes happened in the last 24 hours?"
              className="w-full pl-10 pr-4 py-3 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !query.trim()}
            className="px-6 py-3 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-lg transition-colors flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <>
                <Send className="w-5 h-5" />
                Query
              </>
            )}
          </button>
        </div>
      </form>

      <div className="mb-6">
        <p className="text-sm text-slate-400 mb-2">Quick queries:</p>
        <div className="flex flex-wrap gap-2">
          {QUICK_QUERIES.map((quickQuery, idx) => (
            <button
              key={idx}
              onClick={() => handleQuickQuery(quickQuery)}
              className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 border border-slate-700 rounded-lg text-sm text-slate-300 hover:text-white transition-colors"
            >
              {quickQuery}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-500/20 border border-red-500/50 rounded-lg text-red-400">
          {error}
        </div>
      )}

      {response && (
        <div className="flex-1 overflow-y-auto space-y-4">
          <div className="response-card">
            <div className="response-header">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-400" />
                <span className="response-label">Response</span>
              </div>
              {response.latency_ms && (
                <div className="response-meta">
                  <span>Latency: {Math.round(response.latency_ms)}ms</span>
                  <span>Retrieved at {new Date().toLocaleTimeString()}</span>
                </div>
              )}
            </div>
            <div 
              className="formatted-markdown"
              dangerouslySetInnerHTML={{ 
                __html: marked.parse(response.answer || '')
              }}
            />
          </div>

          {response.risk_assessment && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
              <h4 className="text-sm font-semibold text-red-400 mb-2">Risk Assessment</h4>
              <p className="text-red-300 text-sm">{response.risk_assessment}</p>
            </div>
          )}

          {response.sources && response.sources.length > 0 && (
            <div className="p-4 bg-slate-800 border border-slate-700 rounded-lg">
              <h4 className="text-sm font-semibold text-white mb-3">Sources</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {response.sources.map((source, idx) => (
                  <div key={idx} className="p-3 bg-slate-900 rounded-lg border border-slate-700">
                    <h5 className="font-medium text-white mb-1">
                      {source.disaster_type}
                    </h5>
                    <p className="text-xs text-slate-400 mb-1">{source.location}</p>
                    <p className="text-xs text-slate-500">{source.event_time}</p>
                    {source.url && (
                      <a
                        href={source.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300 mt-2"
                      >
                        View Source <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
