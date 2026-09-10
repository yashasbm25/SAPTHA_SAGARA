import React, { useEffect, useRef } from 'react';
import maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';

const MapComponent: React.FC = () => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);

  useEffect(() => {
    if (!mapContainer.current) return;

    map.current = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://demotiles.maplibre.org/style.json',
      center: [74.7421, 13.3386],
      zoom: 6
    });

    // Add a marker for default location (Mangalore)
    new maplibregl.Marker()
      .setLngLat([74.7421, 13.3386])
      .addTo(map.current);

    return () => {
      if (map.current) map.current.remove();
    };
  }, []);

  return <div ref={mapContainer} className="map-container" />;
};

export default MapComponent;