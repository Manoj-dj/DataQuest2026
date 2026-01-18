import { useState } from 'react';
import { Image as ImageIcon, ZoomIn, X } from 'lucide-react';

export const ImageGallery = ({ images, onImageClick }) => {
  if (!images || images.length === 0) {
    return null;
  }

  return (
    <div className="grid grid-cols-3 gap-2">
      {images.slice(0, 3).map((url, idx) => (
        <div
          key={idx}
          onClick={() => onImageClick?.(url, idx)}
          className="relative aspect-square rounded-lg overflow-hidden bg-slate-800 border border-slate-700 cursor-pointer group hover:border-blue-500 transition-all"
        >
          <img
            src={url}
            alt={`Disaster imagery ${idx + 1}`}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <ZoomIn className="w-6 h-6 text-white" />
          </div>
        </div>
      ))}
    </div>
  );
};
