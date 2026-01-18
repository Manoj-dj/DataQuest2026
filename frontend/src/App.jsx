import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from './components/Header/Header';
import { Sidebar } from './components/Sidebar/Sidebar';
import { DisasterMap } from './components/Map/DisasterMap';
import { QueryPanel } from './components/Query/QueryPanel';
import { EventsList } from './components/Events/EventsList';
import { StatsDashboard } from './components/Dashboard/StatsDashboard';
import { ImageryModal } from './components/Imagery/ImageryModal';
import { useDisasterEvents } from './hooks/useDisasterEvents';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function AppContent() {
  const [activeView, setActiveView] = useState('dashboard');
  const [filters, setFilters] = useState({ type: '', severity: '' });
  const [selectedEvent, setSelectedEvent] = useState(null);
  const [imageryModal, setImageryModal] = useState({ isOpen: false, imageUrl: null, eventId: null, eventContext: null });
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { data: eventsData } = useDisasterEvents(50, filters.type);
  const events = eventsData?.events || [];

  const handleEventSelect = (event) => {
    setSelectedEvent(event);
    setActiveView('map');
  };

  const handleShowImagery = (event) => {
    const imageUrl = event.imagery_urls && event.imagery_urls.length > 0 
      ? (Array.isArray(event.imagery_urls) ? event.imagery_urls[0] : JSON.parse(event.imagery_urls)[0])
      : null;
    
    if (imageUrl) {
      setImageryModal({
        isOpen: true,
        imageUrl,
        eventId: event.event_id,
        eventContext: `${event.disaster_type} event at ${event.location}`,
      });
    }
  };

  const handleImageClick = (imageUrl, event) => {
    setImageryModal({
      isOpen: true,
      imageUrl,
      eventId: event?.event_id || null,
      eventContext: event ? `${event.disaster_type} event at ${event.location}` : null,
    });
  };

  return (
    <div className="h-screen flex flex-col bg-slate-950">
      <Header />

      <div className="flex-1 flex overflow-hidden">
        <Sidebar
          activeView={activeView}
          onViewChange={setActiveView}
          filters={filters}
          onFiltersChange={setFilters}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
        />

        <main className="flex-1 overflow-y-auto bg-slate-950">
          {activeView === 'dashboard' && <StatsDashboard />}
          {activeView === 'events' && (
            <div className="p-6">
              <EventsList
                filters={filters}
                onEventSelect={handleEventSelect}
                onShowImagery={handleShowImagery}
              />
            </div>
          )}
          {activeView === 'map' && (
            <div className="p-6 h-[calc(100vh-73px)]">
              <DisasterMap
                events={events}
                selectedEvent={selectedEvent}
                onEventSelect={handleEventSelect}
              />
            </div>
          )}
          {activeView === 'query' && (
            <div className="h-[calc(100vh-73px)]">
              <QueryPanel />
            </div>
          )}
          {activeView === 'settings' && (
            <div className="p-6">
              <h2 className="text-2xl font-bold text-white mb-4">Settings</h2>
              <div className="bg-slate-800 border border-slate-700 rounded-lg p-6">
                <p className="text-slate-400">Settings panel coming soon...</p>
              </div>
            </div>
          )}
        </main>
      </div>

      {imageryModal.isOpen && (
        <ImageryModal
          isOpen={imageryModal.isOpen}
          onClose={() => setImageryModal({ isOpen: false, imageUrl: null, eventId: null, eventContext: null })}
          imageUrl={imageryModal.imageUrl}
          eventId={imageryModal.eventId}
          eventContext={imageryModal.eventContext}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AppContent />
    </QueryClientProvider>
  );
}

export default App;
