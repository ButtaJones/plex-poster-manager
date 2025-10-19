import React from 'react';

const ArtworkCard = ({ artwork, item, onSelect, isSelected, onDelete, thumbnailSize = 300, darkMode = false }) => {
  const getThumbnailUrl = (thumbUrl) => {
    // Auto-detect API base URL from environment or construct from current host
    // This allows the app to work both on localhost and over the network
    const apiBaseUrl = process.env.REACT_APP_API_URL ||
                       `${window.location.protocol}//${window.location.hostname}:5000`;
    return `${apiBaseUrl}/api/thumbnail?url=${encodeURIComponent(thumbUrl)}`;
  };

  // Calculate display size based on thumbnail size setting
  // Width is controlled by thumbnailSize, height uses aspect-ratio for proper poster proportions
  const cardStyle = {
    width: `${thumbnailSize}px`,
    margin: '0 auto' // Center cards in their grid cells
  };

  const getProviderBadgeColor = (provider) => {
    const colors = {
      'tvdb': 'bg-blue-500',
      'tmdb': 'bg-green-500',
      'gracenote': 'bg-purple-500',
      'plex': 'bg-orange-500',
      'local': 'bg-gray-500',
      'unknown': 'bg-gray-400',
    };
    return colors[provider] || colors.unknown;
  };

  const getProviderName = (provider) => {
    const names = {
      'tvdb': 'TVDB',
      'tmdb': 'TMDB',
      'gracenote': 'Gracenote',
      'plex': 'Plex',
      'local': 'Local',
      'unknown': 'Unknown',
    };
    return names[provider] || provider;
  };

  return (
    <div
      style={cardStyle}
      className={`relative border rounded-lg overflow-hidden transition-all ${
        isSelected
          ? darkMode
            ? 'ring-4 ring-blue-400 border-blue-400'
            : 'ring-4 ring-blue-500 border-blue-500'
          : darkMode
            ? 'border-gray-700 hover:border-gray-600'
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

      {/* Provider Badge */}
      <div className="absolute top-2 right-2 z-10">
        <span
          className={`${getProviderBadgeColor(
            artwork.provider
          )} text-white text-xs px-2 py-1 rounded-full font-semibold`}
        >
          {getProviderName(artwork.provider)}
        </span>
      </div>

      {/* Selected Badge */}
      {artwork.selected && (
        <div className="absolute top-2 right-2 z-20 mr-20">
          <span className="bg-green-600 text-white text-xs px-2 py-1 rounded-full font-semibold">
            ★ Active
          </span>
        </div>
      )}

      {/* Thumbnail */}
      <div className="aspect-[2/3] bg-gray-200 relative group cursor-pointer overflow-hidden">
        <img
          src={getThumbnailUrl(artwork.thumb_url)}
          alt={`${artwork.type} - ${artwork.provider}`}
          className="w-full h-full object-cover"
          loading="lazy"
          crossOrigin="anonymous"
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
      <div className={`p-3 ${darkMode ? 'bg-gray-800' : 'bg-white'}`}>
        <p className={`text-xs mb-1 capitalize ${
          darkMode ? 'text-gray-400' : 'text-gray-600'
        }`}>
          {artwork.type}
        </p>
        <div className={`flex justify-between text-xs ${
          darkMode ? 'text-gray-500' : 'text-gray-500'
        }`}>
          <span>{getProviderName(artwork.provider)}</span>
          {artwork.selected && <span className={`font-semibold ${
            darkMode ? 'text-green-400' : 'text-green-600'
          }`}>Active</span>}
        </div>
      </div>
    </div>
  );
};

export default ArtworkCard;
