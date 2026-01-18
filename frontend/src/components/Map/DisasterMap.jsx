import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, CircleMarker } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getSeverityColor, formatEventTime, formatRiskScore } from '../../utils/formatters';

// Fix for default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

export const DisasterMap = ({ events, selectedEvent, onEventSelect }) => {
  const mapRef = useRef(null);

  useEffect(() => {
    if (selectedEvent && mapRef.current) {
      const { latitude, longitude } = selectedEvent;
      if (latitude && longitude) {
        mapRef.current.setView([latitude, longitude], 10);
      }
    }
  }, [selectedEvent]);

  return (
    <div className="h-full w-full relative rounded-lg overflow-hidden border border-slate-700">
      <MapContainer
        center={[20, 0]}
        zoom={2}
        style={{ height: '100%', width: '100%' }}
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {events?.map((event) => {
          const { latitude, longitude } = event;
          if (!latitude || !longitude || latitude === 0 || longitude === 0) {
            return null;
          }

          const color = getSeverityColor(event.severity);
          const isSelected = selectedEvent?.event_id === event.event_id;

          return (
            <CircleMarker
              key={event.event_id}
              center={[latitude, longitude]}
              radius={isSelected ? 12 : 8}
              pathOptions={{
                fillColor: color,
                color: '#fff',
                weight: isSelected ? 3 : 2,
                opacity: 1,
                fillOpacity: 0.8,
              }}
              eventHandlers={{
                click: () => onEventSelect?.(event),
              }}
            >
              <Popup>
                <div className="text-sm">
                  <h3 className="font-bold mb-2">{event.disaster_type}</h3>
                  <p className="text-gray-600 mb-1">
                    <strong>Severity:</strong> {event.severity}
                  </p>
                  <p className="text-gray-600 mb-1">
                    <strong>Location:</strong> {event.location}
                  </p>
                  {event.risk_score && (
                    <p className="text-gray-600 mb-1">
                      <strong>Risk:</strong> {formatRiskScore(event.risk_score)}/10
                    </p>
                  )}
                  <p className="text-gray-500 text-xs mt-2">
                    {formatEventTime(event.event_time)}
                  </p>
                </div>
              </Popup>
            </CircleMarker>
          );
        })}
      </MapContainer>

      <div className="absolute top-4 right-4 bg-slate-900/90 backdrop-blur-sm border border-slate-700 rounded-lg p-3 z-[1000]">
        <h4 className="text-sm font-semibold text-white mb-2">Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-slate-300">Red Alert</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-orange-500"></div>
            <span className="text-slate-300">Orange Alert</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-slate-300">Green Alert</span>
          </div>
        </div>
      </div>
    </div>
  );
};
