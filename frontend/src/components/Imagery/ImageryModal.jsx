import { useState, useEffect } from 'react';
import { X, ZoomIn, ZoomOut, Sparkles, ExternalLink, Loader2 } from 'lucide-react';
import { analyzeImagery } from '../../services/api';
import { useImageryAnalysis } from '../../hooks/useImagery';

export const ImageryModal = ({ isOpen, onClose, imageUrl, eventId, eventContext }) => {
  const [analysis, setAnalysis] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [zoom, setZoom] = useState(1);

  useEffect(() => {
    if (!isOpen) {
      setAnalysis(null);
      setZoom(1);
    }
  }, [isOpen]);

  const handleAnalyze = async () => {
    if (!imageUrl) return;

    setIsAnalyzing(true);
    try {
      const result = await analyzeImagery(imageUrl, eventContext);
      setAnalysis(result.analysis);
    } catch (error) {
      console.error('Analysis error:', error);
      setAnalysis({ error: 'Failed to analyze image' });
    } finally {
      setIsAnalyzing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 backdrop-blur-sm">
      <div className="relative w-full h-full max-w-7xl max-h-[90vh] m-4 bg-slate-900 border border-slate-700 rounded-lg flex flex-col">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-white transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="flex-1 flex items-center justify-center p-6 overflow-hidden">
          <div className="relative max-w-full max-h-full">
            <img
              src={imageUrl}
              alt="Disaster imagery"
              className="max-w-full max-h-[70vh] object-contain rounded-lg"
              style={{ transform: `scale(${zoom})` }}
            />
          </div>
        </div>

        <div className="p-4 border-t border-slate-700 bg-slate-800">
          <div className="flex items-center gap-3 mb-4">
            <button
              onClick={() => setZoom(Math.max(0.5, zoom - 0.25))}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white"
              disabled={zoom <= 0.5}
            >
              <ZoomOut className="w-5 h-5" />
            </button>
            <button
              onClick={() => setZoom(Math.min(3, zoom + 0.25))}
              className="p-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-white"
              disabled={zoom >= 3}
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            <span className="text-sm text-slate-400">Zoom: {Math.round(zoom * 100)}%</span>

            <div className="flex-1" />

            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing}
              className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 disabled:bg-slate-700 text-white rounded-lg transition-colors"
            >
              {isAnalyzing ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <Sparkles className="w-5 h-5" />
              )}
              Analyze with AI
            </button>

            <a
              href={imageUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition-colors"
            >
              <ExternalLink className="w-5 h-5" />
              Open in Tab
            </a>
          </div>

          {analysis && (
            <div className="mt-4 p-4 bg-slate-900 rounded-lg border border-slate-700">
              <h4 className="text-sm font-semibold text-blue-400 mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />
                AI Image Analysis
              </h4>
              {analysis.error ? (
                <p className="text-red-400 text-sm">{analysis.error}</p>
              ) : (
                <div className="space-y-2 text-sm text-slate-300">
                  <p>{analysis.analysis}</p>
                  {analysis.severity_indicators && analysis.severity_indicators.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {analysis.severity_indicators.map((indicator, idx) => (
                        <span
                          key={idx}
                          className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded text-xs"
                        >
                          {indicator}
                        </span>
                      ))}
                    </div>
                  )}
                  {analysis.key_observations && analysis.key_observations.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-slate-400 mb-1">Key Observations:</p>
                      <ul className="list-disc list-inside text-xs space-y-1">
                        {analysis.key_observations.map((obs, idx) => (
                          <li key={idx}>{obs}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
