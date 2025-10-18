import React from 'react';

const ArtworkCard = ({ artwork, item, onSelect, isSelected, onDelete }) => {
  const getThumbnailUrl = (thumbUrl) => {
    return `http://localhost:5000/api/thumbnail?url=${encodeURIComponent(thumbUrl)}`;
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
      <div className="aspect-[2/3] bg-gray-200 relative group cursor-pointer">
        <img
          src={getThumbnailUrl(artwork.thumb_url)}
          alt={`${artwork.type} - ${artwork.provider}`}
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
        <p className="text-xs text-gray-600 mb-1 capitalize">
          {artwork.type}
        </p>
        <div className="flex justify-between text-xs text-gray-500">
          <span>{getProviderName(artwork.provider)}</span>
          {artwork.selected && <span className="text-green-600 font-semibold">Active</span>}
        </div>
      </div>
    </div>
  );
};

export default ArtworkCard;
