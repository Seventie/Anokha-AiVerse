// frontend/src/components/roadmap/RoadmapVisualization.tsx

import React, { useState } from 'react';
import { Image, Download, Maximize2 } from 'lucide-react';

interface RoadmapVisualizationProps {
  svgUrl: string;
  pngUrl: string;
}

const RoadmapVisualization: React.FC<RoadmapVisualizationProps> = ({ svgUrl, pngUrl }) => {
  const [imageError, setImageError] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  const handleDownload = async () => {
    try {
      const response = await fetch(pngUrl);
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'learning-roadmap.png';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Failed to download image:', error);
      alert('Failed to download diagram');
    }
  };

  if (imageError) {
    return (
      <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
        <div className="text-center text-white/40 py-12">
          <Image className="w-12 h-12 mx-auto mb-2" />
          <p>Diagram could not be loaded</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="bg-white/5 border border-white/10 rounded-[2rem] p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium text-white/90">
            📊 Visual Roadmap
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => setIsFullscreen(true)}
              className="px-3 py-2 bg-white/5 hover:bg-white/10 rounded-xl text-sm 
                       font-medium text-white/80 flex items-center gap-2 transition-all"
            >
              <Maximize2 size={16} />
              Fullscreen
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-2 bg-primary/20 hover:bg-primary/30 text-primary rounded-xl 
                       text-sm font-medium flex items-center gap-2 transition-all border border-primary/30"
            >
              <Download size={16} />
              Download
            </button>
          </div>
        </div>

        <div className="border border-white/10 rounded-xl p-4 bg-black/20 overflow-x-auto">
          <img
            src={svgUrl}
            alt="Learning Roadmap Diagram"
            onError={() => setImageError(true)}
            className="max-w-full h-auto mx-auto"
            style={{ minHeight: '400px' }}
          />
        </div>

        <p className="text-xs text-white/40 mt-2 text-center">
          Your personalized learning path from current skills to target role
        </p>
      </div>

      {/* Fullscreen Modal */}
      {isFullscreen && (
        <div
          className="fixed inset-0 bg-black/95 z-50 flex items-center justify-center p-4"
          onClick={() => setIsFullscreen(false)}
        >
          <div className="relative max-w-7xl max-h-full overflow-auto">
            <button
              onClick={() => setIsFullscreen(false)}
              className="absolute top-4 right-4 bg-white/10 text-white px-4 py-2 rounded-xl 
                       font-medium hover:bg-white/20 backdrop-blur-sm"
            >
              Close
            </button>
            <img
              src={svgUrl}
              alt="Learning Roadmap Fullscreen"
              className="max-w-full h-auto"
              onClick={(e) => e.stopPropagation()}
            />
          </div>
        </div>
      )}
    </>
  );
};

export default RoadmapVisualization;
