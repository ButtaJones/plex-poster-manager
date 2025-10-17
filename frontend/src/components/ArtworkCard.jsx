import React from 'react';

const ArtworkCard = ({ artwork, item, onSelect, isSelected, onDelete }) => {
  const getThumbnailUrl = (path) => {
    return `http://localhost:5000/api/thumbnail?path=${encodeURIComponent(path)}`;
  };

  const formatSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  const formatDate = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  const getSourceBadgeColor = (source) => {
    const colors = {
      thetvdb: 'bg-blue-500',
      themoviedb: 'bg-green-500',
      local: 'bg-purple-500',
      unknown: 'bg-gray-500',
    };
    return colors[source] || colors.unknown;
  };

  return (
    <div
      className={`relative border rounded-lg overflow-hidden transition-all ${
        isSelected
          ? 'ring-4 ring-blue-500 border-blue-500'
          : 'border-gray-300 hover:border-gray-400'
      }`}
    >
      {/* Selection Checkbox */}
      <div className="absolute top-2 left-2 z-10">
        <input
          type="checkbox"
          checked={isSelected}
          onChange={() => onSelect(artwork.path)}
          className="w-5 h-5 cursor-pointer"
        />
      </div>

      {/* Source Badge */}
      <div className="absolute top-2 right-2 z-10">
        <span
          className={`${getSourceBadgeColor(
            artwork.source
          )} text-white text-xs px-2 py-1 rounded-full font-semibold`}
        >
          {artwork.source}
        </span>
      </div>

      {/* Thumbnail */}
      <div className="aspect-[2/3] bg-gray-200 relative group cursor-pointer">
        <img
          src={getThumbnailUrl(artwork.path)}
          alt={artwork.filename}
          className="w-full h-full object-cover"
          loading="lazy"
        />
        
        {/* Overlay on hover */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-50 transition-opacity flex items-center justify-center">
          <button
            onClick={() => onDelete([artwork.path])}
            className="opacity-0 group-hover:opacity-100 bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 transition-opacity"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Info */}
      <div className="p-3 bg-white">
        <p className="text-xs text-gray-600 mb-1 truncate" title={artwork.filename}>
          {artwork.filename}
        </p>
        <div className="flex justify-between text-xs text-gray-500">
          <span>{formatSize(artwork.size)}</span>
          <span>{formatDate(artwork.modified)}</span>
        </div>
      </div>
    </div>
  );
};

export default ArtworkCard;
