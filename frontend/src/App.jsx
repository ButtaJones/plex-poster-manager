import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings, RefreshCw, Search, Trash2, X, Moon, Sun,
  Film, Image, Eye, History, ChevronDown, Loader, SlidersHorizontal
} from 'lucide-react';
import ConfigModal from './components/ConfigModal';
import ItemCard from './components/ItemCard';
import { configAPI, libraryAPI, artworkAPI, operationsAPI } from './api';

function App() {
  const [config, setConfig] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [libraries, setLibraries] = useState([]);
  const [selectedLibrary, setSelectedLibrary] = useState('TV Shows');
  const [items, setItems] = useState([]);
  const [selectedArtwork, setSelectedArtwork] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState(null);
  const [operations, setOperations] = useState([]);
  const [showOperations, setShowOperations] = useState(false);
  const [scanProgress, setScanProgress] = useState(null);
  const [scanLimit, setScanLimit] = useState(null); // null = scan all
  const [offset, setOffset] = useState(0);
  const [totalCount, setTotalCount] = useState(0);

  // New UI state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [thumbnailSize, setThumbnailSize] = useState(() => {
    const saved = localStorage.getItem('thumbnailSize');
    return saved ? parseInt(saved) : 300;
  });
  const [showSizeSlider, setShowSizeSlider] = useState(false);

  // Save dark mode preference
  useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Save thumbnail size preference
  useEffect(() => {
    localStorage.setItem('thumbnailSize', thumbnailSize.toString());
  }, [thumbnailSize]);

  const loadLibraries = useCallback(async () => {
    try {
      const response = await libraryAPI.getLibraries();
      const libs = response.data.libraries || [];
      console.log('[Frontend] Loaded libraries:', libs);
      setLibraries(libs);

      if (libs.length > 0 && !selectedLibrary) {
        setSelectedLibrary(libs[0]);
        console.log('[Frontend] Set default library to:', libs[0]);
      }
    } catch (error) {
      console.error('Error loading libraries:', error);
    }
  }, [selectedLibrary]);

  const loadConfig = useCallback(async () => {
    try {
      const response = await configAPI.getConfig();
      setConfig(response.data);

      if (!response.data.plex_url) {
        setShowConfig(true);
      } else {
        loadLibraries();
      }
    } catch (error) {
      console.error('Error loading config:', error);
      setShowConfig(true);
    }
  }, [loadLibraries]);

  useEffect(() => {
    loadConfig();
  }, [loadConfig]);

  const handleSaveConfig = async (newConfig) => {
    try {
      await configAPI.updateConfig(newConfig);
      setConfig(newConfig);
      setShowConfig(false);
      loadLibraries();
      alert('Configuration saved successfully!');
    } catch (error) {
      console.error('Error saving config:', error);
      alert('Error saving configuration: ' + error.message);
    }
  };

  const handleScan = async () => {
    if (!selectedLibrary) return;

    setLoading(true);
    setOffset(0);
    setScanProgress({ scanning: true, current: 0, total: 0, current_item: '' });

    const progressInterval = setInterval(async () => {
      try {
        const progressResponse = await libraryAPI.getScanProgress();
        setScanProgress(progressResponse.data);

        if (!progressResponse.data.scanning) {
          clearInterval(progressInterval);
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
      }
    }, 500);

    try {
      const response = await libraryAPI.scanLibrary(selectedLibrary, scanLimit, 0);
      setItems(response.data.items);
      setStats(response.data.stats);
      setTotalCount(response.data.stats.total_count || 0);
      setOffset(scanLimit || 0);
      clearInterval(progressInterval);
      setScanProgress(null);
    } catch (error) {
      console.error('Error scanning library:', error);
      alert('Error scanning library: ' + error.message);
      clearInterval(progressInterval);
      setScanProgress(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      handleScan();
      return;
    }

    setLoading(true);
    try {
      const response = await libraryAPI.searchItems(searchQuery, selectedLibrary);
      setItems(response.data.items);
    } catch (error) {
      console.error('Error searching:', error);
      alert('Error searching: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = async () => {
    if (!selectedLibrary || !scanLimit) return;

    setLoading(true);
    setScanProgress({ scanning: true, current: 0, total: 0, current_item: '' });

    const progressInterval = setInterval(async () => {
      try {
        const progressResponse = await libraryAPI.getScanProgress();
        setScanProgress(progressResponse.data);

        if (!progressResponse.data.scanning) {
          clearInterval(progressInterval);
        }
      } catch (error) {
        console.error('Error fetching progress:', error);
      }
    }, 500);

    try {
      const response = await libraryAPI.scanLibrary(selectedLibrary, scanLimit, offset);
      setItems((prevItems) => [...prevItems, ...response.data.items]);
      setStats(response.data.stats);
      setOffset((prevOffset) => prevOffset + scanLimit);
      clearInterval(progressInterval);
      setScanProgress(null);
    } catch (error) {
      console.error('Error loading more:', error);
      alert('Error loading more: ' + error.message);
      clearInterval(progressInterval);
      setScanProgress(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectArtwork = (path) => {
    setSelectedArtwork((prev) =>
      prev.includes(path)
        ? prev.filter((p) => p !== path)
        : [...prev, path]
    );
  };

  const handleDeleteArtwork = async (paths) => {
    if (!window.confirm(`Are you sure you want to delete ${paths.length} artwork file(s)? They will be moved to backup.`)) {
      return;
    }

    try {
      await artworkAPI.deleteArtwork(paths, 'User deletion');
      alert(`Successfully deleted ${paths.length} file(s)`);

      handleScan();
      setSelectedArtwork([]);
      loadOperations();
    } catch (error) {
      console.error('Error deleting artwork:', error);
      alert('Error deleting artwork: ' + error.message);
    }
  };

  const handleDeleteSelected = () => {
    if (selectedArtwork.length === 0) {
      alert('Please select artwork to delete');
      return;
    }
    handleDeleteArtwork(selectedArtwork);
  };

  const loadOperations = async () => {
    try {
      const response = await operationsAPI.getOperations(20);
      setOperations(response.data.operations);
    } catch (error) {
      console.error('Error loading operations:', error);
    }
  };

  const handleUndo = async (operationId) => {
    try {
      await operationsAPI.undoOperation(operationId);
      alert('Operation undone successfully');
      handleScan();
      loadOperations();
    } catch (error) {
      console.error('Error undoing operation:', error);
      alert('Error undoing operation: ' + error.message);
    }
  };

  return (
    <div className={`min-h-screen transition-colors duration-200 ${darkMode ? 'dark bg-gray-900' : 'bg-gray-50'}`}>
      {/* Modern Header */}
      <header className={`${darkMode ? 'bg-gradient-to-r from-gray-800 to-gray-900 border-b border-gray-700' : 'bg-gradient-to-r from-indigo-600 via-purple-600 to-pink-600'} shadow-xl`}>
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-3">
              <Film className="w-10 h-10 text-white" />
              <div>
                <h1 className="text-3xl font-bold text-white">Plex Poster Manager</h1>
                <p className="text-white/80 text-sm mt-1">Manage your Plex artwork with style</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {/* Dark Mode Toggle */}
              <button
                onClick={() => setDarkMode(!darkMode)}
                className={`p-3 rounded-lg transition-all ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-yellow-400' : 'bg-white/20 hover:bg-white/30 text-white'}`}
                title={darkMode ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
              >
                {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
              </button>

              {/* Settings Button */}
              <button
                onClick={() => setShowConfig(true)}
                className={`flex items-center gap-2 px-4 py-3 rounded-lg font-medium transition-all ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-white' : 'bg-white hover:bg-gray-50 text-purple-600'}`}
              >
                <Settings className="w-5 h-5" />
                <span className="hidden sm:inline">Settings</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Controls Panel */}
        <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'} rounded-xl shadow-lg p-6 mb-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
          {/* Top Row: Library, Items Per Page, Search, Scan */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 mb-6">
            {/* Library Selection */}
            <div className="lg:col-span-3">
              <label className={`block text-sm font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <Film className="w-4 h-4 inline mr-1" />
                Library
              </label>
              <select
                value={selectedLibrary}
                onChange={(e) => setSelectedLibrary(e.target.value)}
                className={`w-full px-4 py-2.5 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                disabled={libraries.length === 0}
              >
                {libraries.length === 0 ? (
                  <option value="">No libraries found</option>
                ) : (
                  libraries.map((lib) => (
                    <option key={lib} value={lib}>
                      {lib}
                    </option>
                  ))
                )}
              </select>
            </div>

            {/* Items Per Page */}
            <div className="lg:col-span-2">
              <label className={`block text-sm font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <Eye className="w-4 h-4 inline mr-1" />
                Items Per Page
              </label>
              <select
                value={scanLimit || ''}
                onChange={(e) => setScanLimit(e.target.value ? parseInt(e.target.value) : null)}
                className={`w-full px-4 py-2.5 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
              >
                <option value="">All Items</option>
                <option value="25">25 items</option>
                <option value="50">50 items</option>
                <option value="75">75 items</option>
                <option value="100">100 items</option>
              </select>
            </div>

            {/* Search */}
            <div className="lg:col-span-5">
              <label className={`block text-sm font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <Search className="w-4 h-4 inline mr-1" />
                Search
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search by title..."
                  className={`flex-1 px-4 py-2.5 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                />
                <button
                  onClick={handleSearch}
                  className={`px-4 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 ${darkMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-gray-700 hover:bg-gray-800'} text-white`}
                >
                  <Search className="w-4 h-4" />
                  <span className="hidden sm:inline">Search</span>
                </button>
              </div>
            </div>

            {/* Scan Button */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-semibold mb-2 opacity-0">Scan</label>
              <button
                onClick={handleScan}
                disabled={loading}
                className={`w-full px-4 py-2.5 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${darkMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-purple-600 hover:bg-purple-700'} text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                {loading ? 'Scanning...' : 'Scan Library'}
              </button>
            </div>
          </div>

          {/* Thumbnail Size Slider */}
          <div className={`p-4 rounded-lg mb-4 ${darkMode ? 'bg-gray-700/50' : 'bg-purple-50'}`}>
            <div className="flex items-center justify-between mb-3">
              <label className={`text-sm font-semibold flex items-center gap-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <SlidersHorizontal className="w-4 h-4" />
                Thumbnail Size: {thumbnailSize}px
              </label>
              <button
                onClick={() => setShowSizeSlider(!showSizeSlider)}
                className={`text-xs px-3 py-1 rounded-md ${darkMode ? 'bg-gray-600 hover:bg-gray-500 text-gray-200' : 'bg-purple-200 hover:bg-purple-300 text-purple-800'} transition-colors`}
              >
                {showSizeSlider ? 'Hide' : 'Show'} Slider
              </button>
            </div>
            {showSizeSlider && (
              <input
                type="range"
                min="150"
                max="500"
                step="10"
                value={thumbnailSize}
                onChange={(e) => setThumbnailSize(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
              />
            )}
          </div>

          {/* Bulk Actions */}
          {selectedArtwork.length > 0 && (
            <div className={`p-4 rounded-lg border ${darkMode ? 'bg-red-900/20 border-red-700' : 'bg-red-50 border-red-200'}`}>
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <span className={`font-semibold flex items-center gap-2 ${darkMode ? 'text-red-300' : 'text-red-800'}`}>
                  <Image className="w-4 h-4" />
                  {selectedArtwork.length} artwork file(s) selected
                </span>
                <div className="flex gap-2 w-full sm:w-auto">
                  <button
                    onClick={() => setSelectedArtwork([])}
                    className={`flex-1 sm:flex-none px-4 py-2 rounded-lg font-medium transition-all flex items-center justify-center gap-2 ${darkMode ? 'bg-gray-700 hover:bg-gray-600 text-gray-200' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'}`}
                  >
                    <X className="w-4 h-4" />
                    Clear
                  </button>
                  <button
                    onClick={handleDeleteSelected}
                    className="flex-1 sm:flex-none px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg font-medium transition-all flex items-center justify-center gap-2"
                  >
                    <Trash2 className="w-4 h-4" />
                    Delete
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Stats Cards */}
          {stats && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mt-6">
              <div className={`${darkMode ? 'bg-gradient-to-br from-blue-600 to-blue-700' : 'bg-gradient-to-br from-blue-500 to-blue-600'} text-white p-4 rounded-xl shadow-lg`}>
                <div className="text-3xl font-bold">{stats.total_items}</div>
                <div className="text-sm opacity-90 mt-1">Total Items</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-green-600 to-green-700' : 'bg-gradient-to-br from-green-500 to-green-600'} text-white p-4 rounded-xl shadow-lg`}>
                <div className="text-3xl font-bold">{stats.total_artwork}</div>
                <div className="text-sm opacity-90 mt-1">Artwork Files</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-purple-600 to-purple-700' : 'bg-gradient-to-br from-purple-500 to-purple-600'} text-white p-4 rounded-xl shadow-lg`}>
                <div className="text-3xl font-bold">{items.length}</div>
                <div className="text-sm opacity-90 mt-1">Items Shown</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-orange-600 to-orange-700' : 'bg-gradient-to-br from-orange-500 to-orange-600'} text-white p-4 rounded-xl shadow-lg cursor-pointer hover:opacity-90 transition-opacity`}>
                <button
                  onClick={() => {
                    loadOperations();
                    setShowOperations(!showOperations);
                  }}
                  className="w-full text-left"
                >
                  <div className="text-3xl font-bold flex items-center gap-2">
                    {operations.length}
                    <ChevronDown className={`w-5 h-5 transition-transform ${showOperations ? 'rotate-180' : ''}`} />
                  </div>
                  <div className="text-sm opacity-90 mt-1">Recent Operations</div>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Operations Panel */}
        {showOperations && (
          <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white'} rounded-xl shadow-lg p-6 mb-6 border ${darkMode ? 'border-gray-700' : 'border-gray-200'}`}>
            <div className="flex items-center justify-between mb-4">
              <h2 className={`text-xl font-bold flex items-center gap-2 ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                <History className="w-5 h-5" />
                Recent Operations
              </h2>
              <button
                onClick={() => setShowOperations(false)}
                className={`p-2 rounded-lg transition-colors ${darkMode ? 'hover:bg-gray-700 text-gray-400' : 'hover:bg-gray-100 text-gray-600'}`}
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {operations.map((op) => (
                <div
                  key={op.id}
                  className={`flex flex-col sm:flex-row items-start sm:items-center justify-between p-4 rounded-lg ${darkMode ? 'bg-gray-700' : 'bg-gray-50'} gap-3`}
                >
                  <div className="flex-1 min-w-0">
                    <div className={`font-medium ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                      {op.action === 'delete' ? <Trash2 className="w-4 h-4 inline mr-1" /> : '↩️'} {op.action}
                    </div>
                    <div className={`text-sm truncate ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                      {op.original_path}
                    </div>
                    <div className={`text-xs ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>{op.timestamp}</div>
                  </div>
                  {op.can_undo && (
                    <button
                      onClick={() => handleUndo(op.id)}
                      className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-lg transition-colors whitespace-nowrap"
                    >
                      Undo
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Items List */}
        <div className="space-y-4">
          {loading ? (
            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl shadow-lg p-12 text-center`}>
              <Loader className={`w-12 h-12 mx-auto mb-4 animate-spin ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
              <div className={`text-lg mb-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Scanning library...</div>
              {scanProgress && scanProgress.total > 0 && (
                <div className="max-w-md mx-auto">
                  <div className={`mb-2 text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    Processing {scanProgress.current} of {scanProgress.total} items
                  </div>
                  <div className={`w-full rounded-full h-4 mb-2 ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                    <div
                      className="bg-gradient-to-r from-purple-500 to-pink-500 h-4 rounded-full transition-all duration-300"
                      style={{ width: `${(scanProgress.current / scanProgress.total) * 100}%` }}
                    ></div>
                  </div>
                  <div className={`text-xs truncate ${darkMode ? 'text-gray-500' : 'text-gray-500'}`}>
                    {scanProgress.current_item}
                  </div>
                </div>
              )}
            </div>
          ) : items.length > 0 ? (
            <>
              {/* Pagination Info */}
              {totalCount > 0 && scanLimit && (
                <div className={`${darkMode ? 'bg-blue-900/30 border-blue-700' : 'bg-blue-50 border-blue-200'} border rounded-xl p-4 mb-4`}>
                  <div className={`text-center font-medium ${darkMode ? 'text-blue-300' : 'text-blue-800'}`}>
                    Showing {items.length} of {totalCount} items in library
                    {offset < totalCount && ` (${Math.ceil((totalCount - offset) / scanLimit)} more page${Math.ceil((totalCount - offset) / scanLimit) === 1 ? '' : 's'} available)`}
                  </div>
                </div>
              )}

              {items.map((item, index) => (
                <ItemCard
                  key={index}
                  item={item}
                  selectedArtwork={selectedArtwork}
                  onSelectArtwork={handleSelectArtwork}
                  onDeleteArtwork={handleDeleteArtwork}
                  thumbnailSize={thumbnailSize}
                  darkMode={darkMode}
                />
              ))}

              {/* Load More Button */}
              {scanLimit && offset < totalCount && (
                <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl shadow-lg p-6 text-center`}>
                  <button
                    onClick={handleLoadMore}
                    disabled={loading}
                    className={`px-6 py-3 rounded-lg font-medium transition-all inline-flex items-center gap-2 ${darkMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-purple-600 hover:bg-purple-700'} text-white disabled:opacity-50 disabled:cursor-not-allowed`}
                  >
                    <ChevronDown className="w-5 h-5" />
                    {loading ? 'Loading...' : `Load More (${Math.min(scanLimit, totalCount - offset)} more items)`}
                  </button>
                </div>
              )}
            </>
          ) : (
            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl shadow-lg p-12 text-center`}>
              <Film className={`w-16 h-16 mx-auto mb-4 ${darkMode ? 'text-gray-600' : 'text-gray-300'}`} />
              <div className={`text-lg mb-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                {config?.plex_url
                  ? 'Click "Scan Library" to get started'
                  : 'Please configure your Plex settings'}
              </div>
              {!config?.plex_url && (
                <button
                  onClick={() => setShowConfig(true)}
                  className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg font-medium transition-all inline-flex items-center gap-2"
                >
                  <Settings className="w-5 h-5" />
                  Open Settings
                </button>
              )}
            </div>
          )}
        </div>
      </main>

      {/* Config Modal */}
      <ConfigModal
        isOpen={showConfig}
        onClose={() => setShowConfig(false)}
        config={config}
        onSave={handleSaveConfig}
        darkMode={darkMode}
      />
    </div>
  );
}

export default App;
