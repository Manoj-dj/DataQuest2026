import { useState } from 'react';
import { Search, Send, Sparkles, Loader2, ExternalLink, AlertTriangle, CheckCircle, Lightbulb } from 'lucide-react';
import { queryRAG } from '../../services/api';
import { QUICK_QUERIES } from '../../utils/constants';
import './QueryPanel.css';

// Simple function to clean bold markdown from individual text items
const cleanBoldMarkdown = (text) => {
  if (!text) return '';
  // Remove ** and wrap content in <strong> tags - handle multiple bold sections
  return text.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-semibold text-yellow-300">$1</strong>');
};

// Utility function to parse markdown text and convert to clean HTML
const parseMarkdownToHTML = (text) => {
  if (!text) return '';
  
  // First, replace all **text** with <strong> tags globally (handles all cases)
  // Use a more robust regex that handles edge cases
  let processed = text.replace(/\*\*([^*\n]+?)\*\*/g, '<strong class="font-semibold text-yellow-300">$1</strong>');
  
  // Split by lines to process headings and lists
  const lines = processed.split('\n');
  const result = [];
  let inList = false;
  let listType = null; // 'ul' or 'ol'
  
  for (let i = 0; i < lines.length; i++) {
    const trimmedLine = lines[i].trim();
    
    // Empty line - close lists and add spacing
    if (!trimmedLine) {
      if (inList) {
        result.push(listType === 'ol' ? '</ol>' : '</ul>');
        inList = false;
        listType = null;
      }
      result.push('<br />');
      continue;
    }
    
    // Handle h2 headings (## Heading)
    if (trimmedLine.startsWith('## ')) {
      if (inList) {
        result.push(listType === 'ol' ? '</ol>' : '</ul>');
        inList = false;
        listType = null;
      }
      const headingText = trimmedLine.substring(3).trim();
      result.push(`<h2 class="text-xl font-semibold text-blue-400 mt-6 mb-3 pb-2 border-b border-blue-500/30">${headingText}</h2>`);
      continue;
    }
    
    // Handle h3 headings (### Heading)
    if (trimmedLine.startsWith('### ')) {
      if (inList) {
        result.push(listType === 'ol' ? '</ol>' : '</ul>');
        inList = false;
        listType = null;
      }
      const headingText = trimmedLine.substring(4).trim();
      result.push(`<h3 class="text-lg font-semibold text-blue-300 mt-5 mb-2">${headingText}</h3>`);
      continue;
    }
    
    // Handle bullet points (- or *)
    if (trimmedLine.match(/^[-*]\s+/)) {
      if (!inList || listType !== 'ul') {
        if (inList && listType === 'ol') {
          result.push('</ol>');
        }
        result.push('<ul class="list-none space-y-2 my-3">');
        inList = true;
        listType = 'ul';
      }
      const listItem = trimmedLine.replace(/^[-*]\s+/, '').trim();
      result.push(`<li class="flex items-start gap-2"><span class="flex-shrink-0 w-2 h-2 rounded-full bg-blue-400 mt-2"></span><span class="text-slate-200 leading-relaxed">${listItem}</span></li>`);
      continue;
    }
    
    // Handle numbered lists (1. 2. etc.)
    if (trimmedLine.match(/^\d+\.\s+/)) {
      if (!inList || listType !== 'ol') {
        if (inList && listType === 'ul') {
          result.push('</ul>');
        }
        result.push('<ol class="list-decimal list-inside space-y-2 my-3 text-slate-200 ml-4">');
        inList = true;
        listType = 'ol';
      }
      const listItem = trimmedLine.replace(/^\d+\.\s+/, '').trim();
      result.push(`<li class="leading-relaxed">${listItem}</li>`);
      continue;
    }
    
    // Regular paragraph or inline text
    if (inList) {
      result.push(listType === 'ol' ? '</ol>' : '</ul>');
      inList = false;
      listType = null;
    }
    
    result.push(`<p class="text-slate-200 leading-relaxed mb-3">${trimmedLine}</p>`);
  }
  
  // Close any open list
  if (inList) {
    result.push(listType === 'ol' ? '</ol>' : '</ul>');
  }
  
  return result.join('');
};

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
          {/* Header with metadata */}
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

            {/* Actionable Insight */}
            {response.actionable_insight && (
              <div className="mb-6 p-4 bg-gradient-to-r from-blue-500/10 to-purple-500/10 border border-blue-500/30 rounded-lg">
                <div className="flex items-start gap-3">
                  <Lightbulb className="w-5 h-5 text-yellow-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1">
                    <h3 className="text-base font-semibold text-white mb-2">Key Insight</h3>
                    <div 
                      className="text-slate-200 leading-relaxed"
                      dangerouslySetInnerHTML={{ 
                        __html: parseMarkdownToHTML(response.actionable_insight)
                      }}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* Key Events */}
            {response.key_events && response.key_events.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-orange-400" />
                  Key Events
                </h3>
                <ul className="space-y-2">
                  {response.key_events.map((event, idx) => (
                    <li key={idx} className="flex items-start gap-3 p-3 bg-slate-800/50 border border-slate-700/50 rounded-lg">
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-blue-400 mt-2"></span>
                      <span 
                        className="text-slate-200 leading-relaxed"
                        dangerouslySetInnerHTML={{ 
                          __html: cleanBoldMarkdown(event)
                        }}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Risk Assessment */}
            {response.risk_assessment_items && response.risk_assessment_items.length > 0 && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <h3 className="text-lg font-semibold text-red-400 mb-3 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  Risk Assessment
                </h3>
                <ul className="space-y-2">
                  {response.risk_assessment_items.map((risk, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-red-400 mt-2"></span>
                      <span 
                        className="text-red-300 leading-relaxed"
                        dangerouslySetInnerHTML={{ 
                          __html: cleanBoldMarkdown(risk)
                        }}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Fallback to old risk_assessment if new format not available */}
            {(!response.risk_assessment_items || response.risk_assessment_items.length === 0) && response.risk_assessment && (
              <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
                <h3 className="text-lg font-semibold text-red-400 mb-2 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  Risk Assessment
                </h3>
                <div 
                  className="text-red-300 leading-relaxed"
                  dangerouslySetInnerHTML={{ 
                    __html: parseMarkdownToHTML(response.risk_assessment)
                  }}
                />
              </div>
            )}

            {/* Recommendations */}
            {response.recommendations && response.recommendations.length > 0 && (
              <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-lg">
                <h3 className="text-lg font-semibold text-green-400 mb-3 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  Recommendations
                </h3>
                <ul className="space-y-2">
                  {response.recommendations.map((rec, idx) => (
                    <li key={idx} className="flex items-start gap-3">
                      <span className="flex-shrink-0 w-2 h-2 rounded-full bg-green-400 mt-2"></span>
                      <span 
                        className="text-green-300 leading-relaxed"
                        dangerouslySetInnerHTML={{ 
                          __html: cleanBoldMarkdown(rec)
                        }}
                      />
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Display answer field - always parse markdown if it exists and structured fields are empty */}
            {response.answer && 
             response.answer.trim().length > 0 &&
             (!response.key_events || response.key_events.length === 0) && 
             (!response.actionable_insight || response.actionable_insight.trim().length === 0) &&
             (!response.risk_assessment_items || response.risk_assessment_items.length === 0) &&
             (!response.recommendations || response.recommendations.length === 0) && (
              <div 
                className="prose prose-invert max-w-none"
                style={{ color: '#E5E7EB', lineHeight: '1.7' }}
                dangerouslySetInnerHTML={{ 
                  __html: parseMarkdownToHTML(response.answer)
                }}
              />
            )}
          </div>

          {/* Sources */}
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
