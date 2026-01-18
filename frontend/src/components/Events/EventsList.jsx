import { RefreshCw, AlertCircle } from 'lucide-react';
import { EventCard } from './EventCard';
import { useDisasterEvents } from '../../hooks/useDisasterEvents';

export const EventsList = ({ filters, onEventSelect, onShowImagery }) => {
  const { data, isLoading, error, refetch } = useDisasterEvents(50, filters?.type);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-slate-400">
        <AlertCircle className="w-12 h-12 mb-4 text-red-400" />
        <p>Failed to load events. Please try again.</p>
        <button
          onClick={() => refetch()}
          className="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
        >
          Retry
        </button>
      </div>
    );
  }

  let events = data?.events || [];

  // Apply severity filter client-side
  if (filters?.severity) {
    events = events.filter((e) => e.severity === filters.severity);
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold text-white">
          Recent Events ({events.length})
        </h2>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
        >
          <RefreshCw className="w-4 h-4" />
          Refresh
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {events.length === 0 ? (
          <div className="text-center py-12 text-slate-400">
            <AlertCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>No events found matching your filters.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {events.map((event) => (
              <EventCard
                key={event.event_id}
                event={event}
                onSelect={onEventSelect}
                onShowImagery={onShowImagery}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
