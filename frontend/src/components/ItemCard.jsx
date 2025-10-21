import React from 'react';
import ArtworkCard from './ArtworkCard';

const ItemCard = React.memo(({ item, selectedArtwork, onSelectArtwork, onDeleteArtwork, thumbnailSize = 300, darkMode = false, initiallyExpanded = false, onCollapse, onToggle }) => {
  const [expanded, setExpanded] = React.useState(initiallyExpanded);
  const [activeTab, setActiveTab] = React.useState('posters');

  const { info, artwork, total_artwork, has_custom_artwork, custom_artwork_count } = item;

  // Sync expanded state with prop changes
  React.useEffect(() => {
    setExpanded(initiallyExpanded);
  }, [initiallyExpanded]);

  // Handle toggle - use parent's onToggle if provided, otherwise manage locally
  const handleToggle = () => {
    if (onToggle) {
      onToggle();
    } else if (expanded && onCollapse) {
      onCollapse();
    } else {
      setExpanded(!expanded);
    }
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
        onClick={handleToggle}
      >
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2">
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
              {/* Custom Artwork Badge */}
              {has_custom_artwork ? (
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200 whitespace-nowrap">
                  {custom_artwork_count} Deletable
                </span>
              ) : (
                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 whitespace-nowrap">
                  Agent Only
                </span>
              )}
            </div>
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
          {/* Warning for items without custom artwork */}
          {!has_custom_artwork && (
            <div className={`p-4 mb-4 rounded-lg border ${
              darkMode
                ? 'bg-yellow-900/20 border-yellow-700 text-yellow-300'
                : 'bg-yellow-50 border-yellow-200 text-yellow-800'
            }`}>
              <div className="flex items-start gap-2">
                <svg className="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                <div>
                  <div className="font-semibold">No Custom Artwork to Delete</div>
                  <div className="text-sm mt-1">This item only has agent-provided artwork (from TMDB/TVDB). These cannot be deleted as they are automatically managed by Plex.</div>
                </div>
              </div>
            </div>
          )}

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
            <div
              className="grid gap-4"
              style={{
                gridTemplateColumns: `repeat(auto-fill, minmax(${thumbnailSize}px, 1fr))`
              }}
            >
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
});

export default ItemCard;
