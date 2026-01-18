import { MapPin, Clock, ExternalLink, Image as ImageIcon } from 'lucide-react';
import { formatEventTime, getSeverityBadgeClass, formatRiskScore, capitalizeFirst } from '../../utils/formatters';

export const EventCard = ({ event, onSelect, onShowImagery }) => {
  const severityClass = getSeverityBadgeClass(event.severity);
  const hasImagery = event.imagery_urls && event.imagery_urls.length > 0;

  return (
    <div
      onClick={() => onSelect?.(event)}
      className="bg-slate-800 border border-slate-700 rounded-lg p-4 hover:border-blue-500/50 hover:shadow-lg transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-blue-400 transition-colors">
            {capitalizeFirst(event.disaster_type || 'Unknown')}
          </h3>
          <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${severityClass}`}>
            {event.severity || 'Unknown'}
          </span>
        </div>
        {hasImagery && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onShowImagery?.(event);
            }}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
            title="View imagery"
          >
            <ImageIcon className="w-5 h-5 text-blue-400" />
          </button>
        )}
      </div>

      <div className="space-y-2 text-sm text-slate-300">
        <div className="flex items-center gap-2">
          <MapPin className="w-4 h-4 text-slate-400" />
          <span>{event.location || 'Unknown Location'}</span>
        </div>

        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-slate-400" />
          <span>{formatEventTime(event.event_time)}</span>
        </div>

        {event.risk_score && (
          <div className="flex items-center justify-between pt-2 border-t border-slate-700">
            <span className="text-slate-400">Risk Score:</span>
            <span className="font-semibold text-orange-400">
              {formatRiskScore(event.risk_score)}/10
            </span>
          </div>
        )}

        {event.source && (
          <div className="text-xs text-slate-500">
            Source: {event.source}
          </div>
        )}

        {event.url && (
          <a
            href={event.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => e.stopPropagation()}
            className="inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 text-xs"
          >
            View Source <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>
    </div>
  );
};
