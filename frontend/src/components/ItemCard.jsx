import React from 'react';
import ArtworkCard from './ArtworkCard';

const ItemCard = ({ item, selectedArtwork, onSelectArtwork, onDeleteArtwork, thumbnailSize = 300, darkMode = false }) => {
  const [expanded, setExpanded] = React.useState(false);
  const [activeTab, setActiveTab] = React.useState('posters');

  const { info, artwork, total_artwork } = item;

  // Determine grid columns based on thumbnail size
  const getGridCols = () => {
    if (thumbnailSize <= 150) return 'grid-cols-3 md:grid-cols-5 lg:grid-cols-7 xl:grid-cols-9';
    if (thumbnailSize <= 250) return 'grid-cols-2 md:grid-cols-4 lg:grid-cols-6 xl:grid-cols-8';
    if (thumbnailSize <= 350) return 'grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6';
    return 'grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'; // Large thumbnails
  };

  const tabs = [
    { id: 'posters', label: 'Posters', count: artwork.posters?.length || 0 },
    { id: 'art', label: 'Art', count: artwork.art?.length || 0 },
    { id: 'backgrounds', label: 'Backgrounds', count: artwork.backgrounds?.length || 0 },
    { id: 'banners', label: 'Banners', count: artwork.banners?.length || 0 },
  ].filter((tab) => tab.count > 0);

  const currentArtwork = artwork[activeTab] || [];

  return (
    <div className={`border rounded-lg overflow-hidden shadow-sm ${
      darkMode
        ? 'border-gray-700 bg-gray-800'
        : 'border-gray-300 bg-white'
    }`}>
      {/* Header */}
      <div
        className={`p-4 border-b cursor-pointer transition-colors ${
          darkMode
            ? 'bg-gray-900 hover:bg-gray-700'
            : 'bg-gray-50 hover:bg-gray-100'
        }`}
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <h3 className={`text-lg font-semibold ${
              darkMode ? 'text-gray-100' : 'text-gray-800'
            }`}>
              {info.title}
              {info.parent_title && (
                <span className={`text-sm ml-2 ${
                  darkMode ? 'text-gray-400' : 'text-gray-600'
                }`}>
                  ({info.parent_title})
                </span>
              )}
            </h3>
            <div className={`flex items-center gap-4 mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              <span>Type: {info.type}</span>
              {info.year && <span>Year: {info.year}</span>}
              <span className={`font-medium ${
                darkMode ? 'text-blue-400' : 'text-blue-600'
              }`}>
                {total_artwork} artwork file{total_artwork !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
          <div className="ml-4">
            <svg
              className={`w-6 h-6 transition-transform ${
                darkMode ? 'text-gray-400' : 'text-gray-600'
              } ${expanded ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </div>
        </div>
      </div>

      {/* Expanded Content */}
      {expanded && (
        <div className="p-4">
          {/* Tabs */}
          <div className="flex gap-2 mb-4 border-b">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? darkMode
                      ? 'text-blue-400 border-b-2 border-blue-400'
                      : 'text-blue-600 border-b-2 border-blue-600'
                    : darkMode
                      ? 'text-gray-400 hover:text-gray-200'
                      : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          {/* Artwork Grid */}
          {currentArtwork.length > 0 ? (
            <div className={`grid ${getGridCols()} gap-4`}>
              {currentArtwork.map((art) => (
                <ArtworkCard
                  key={art.path}
                  artwork={art}
                  item={item}
                  isSelected={selectedArtwork.includes(art.path)}
                  onSelect={onSelectArtwork}
                  onDelete={onDeleteArtwork}
                  thumbnailSize={thumbnailSize}
                  darkMode={darkMode}
                />
              ))}
            </div>
          ) : (
            <p className={`text-center py-8 ${
              darkMode ? 'text-gray-500' : 'text-gray-500'
            }`}>
              No {activeTab} found for this item.
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ItemCard;
