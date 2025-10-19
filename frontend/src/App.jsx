import React, { useState, useEffect, useCallback } from 'react';
import {
  Settings, RefreshCw, Search, Trash2, X, Moon, Sun,
  Film, Image, Eye, History, ChevronDown, Loader, SlidersHorizontal,
  LayoutGrid, List
} from 'lucide-react';
import ConfigModal from './components/ConfigModal';
import ItemCard from './components/ItemCard';
import Pagination from './components/Pagination';
import { configAPI, libraryAPI, artworkAPI, operationsAPI } from './api';

function App() {
  const [config, setConfig] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [libraries, setLibraries] = useState([]);
  const [librariesLoading, setLibrariesLoading] = useState(true); // Start as true to show "Loading..." on initial render
  const [selectedLibrary, setSelectedLibrary] = useState('TV Shows');
  const [items, setItems] = useState([]);
  const [selectedArtwork, setSelectedArtwork] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [stats, setStats] = useState(null);
  const [operations, setOperations] = useState([]);
  const [showOperations, setShowOperations] = useState(false);
  const [scanProgress, setScanProgress] = useState(null);
  const [scanLimit, setScanLimit] = useState(25); // Default to 25 items
  const [totalCount, setTotalCount] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [allItems, setAllItems] = useState([]); // Cache all scanned items for pagination

  // New UI state
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });
  const [thumbnailSize, setThumbnailSize] = useState(() => {
    const saved = localStorage.getItem('thumbnailSize');
    if (saved) return parseInt(saved);
    // Try to load from config defaults, fallback to 300
    const configDefaults = localStorage.getItem('config');
    if (configDefaults) {
      try {
        const parsed = JSON.parse(configDefaults);
        return parsed.default_artwork_size || 300;
      } catch (e) {
        return 300;
      }
    }
    return 300;
  });
  const [showSizeSlider, setShowSizeSlider] = useState(false);
  const [viewMode, setViewMode] = useState(() => {
    const saved = localStorage.getItem('viewMode');
    return saved || 'list'; // 'list' or 'grid'
  });
  const [libraryThumbnailSize, setLibraryThumbnailSize] = useState(() => {
    const saved = localStorage.getItem('libraryThumbnailSize');
    if (saved) return parseInt(saved);
    // Try to load from config defaults, fallback to 200
    const configDefaults = localStorage.getItem('config');
    if (configDefaults) {
      try {
        const parsed = JSON.parse(configDefaults);
        return parsed.default_library_size || 200;
      } catch (e) {
        return 200;
      }
    }
    return 200;
  });
  const [expandedGridItems, setExpandedGridItems] = useState(new Set()); // Track which grid items are expanded

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

  // Save view mode preference
  useEffect(() => {
    localStorage.setItem('viewMode', viewMode);
  }, [viewMode]);

  // Save library thumbnail size preference
  useEffect(() => {
    localStorage.setItem('libraryThumbnailSize', libraryThumbnailSize.toString());
  }, [libraryThumbnailSize]);

  // Note: localStorage persistence removed - fresh start on each browser open

  const loadLibraries = useCallback(async () => {
    setLibrariesLoading(true);
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
    } finally {
      setLibrariesLoading(false);
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

      // Save config to localStorage so defaults can be loaded on page refresh
      localStorage.setItem('config', JSON.stringify(newConfig));

      // If defaults were changed, update current sizes to match
      if (newConfig.default_artwork_size) {
        setThumbnailSize(newConfig.default_artwork_size);
        localStorage.setItem('thumbnailSize', newConfig.default_artwork_size.toString());
      }
      if (newConfig.default_library_size) {
        setLibraryThumbnailSize(newConfig.default_library_size);
        localStorage.setItem('libraryThumbnailSize', newConfig.default_library_size.toString());
      }

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
    setCurrentPage(1);
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
      // Scan a larger batch for caching (10x the page size, or 250 items minimum)
      // This gives us enough items for multiple pages without scanning everything
      const batchSize = scanLimit ? Math.max(scanLimit * 10, 250) : null;
      const response = await libraryAPI.scanLibrary(selectedLibrary, batchSize, 0);
      const scannedItems = response.data.items;
      const totalItems = response.data.stats.total_count || 0;

      console.log('[handleScan] Scanned items:', scannedItems.length);
      console.log('[handleScan] Total items:', totalItems);
      console.log('[handleScan] Batch size:', batchSize);

      // Cache all scanned items
      setAllItems(scannedItems);
      setTotalCount(totalItems);
      setStats(response.data.stats);

      // Show first page from cached data
      const firstPageItems = scanLimit ? scannedItems.slice(0, scanLimit) : scannedItems;
      console.log('[handleScan] Showing first page:', firstPageItems.length, 'items');
      setItems(firstPageItems);

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

  const handlePageChange = (newPage) => {
    console.log('[handlePageChange] Page:', newPage);
    console.log('[handlePageChange] scanLimit:', scanLimit);
    console.log('[handlePageChange] allItems.length:', allItems.length);

    if (!scanLimit || allItems.length === 0) {
      console.log('[handlePageChange] BLOCKED: scanLimit or allItems empty');
      return;
    }

    // Scroll to top of page
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Calculate slice indices for client-side pagination
    const startIdx = (newPage - 1) * scanLimit;
    const endIdx = startIdx + scanLimit;

    console.log('[handlePageChange] Slice range:', startIdx, '-', endIdx);

    // Slice from cached items (no API call needed!)
    const pageItems = allItems.slice(startIdx, endIdx);
    console.log('[handlePageChange] Page items:', pageItems.length);
    setItems(pageItems);
    setCurrentPage(newPage);
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
              <div className="relative">
                <select
                  value={selectedLibrary}
                  onChange={(e) => setSelectedLibrary(e.target.value)}
                  className={`w-full h-11 px-4 pr-10 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                  disabled={librariesLoading || libraries.length === 0}
                >
                  {librariesLoading ? (
                    <option value="">Loading libraries...</option>
                  ) : libraries.length === 0 ? (
                    <option value="">No libraries found</option>
                  ) : (
                  libraries.map((lib) => {
                    // Handle both old format (string) and new format (object with name/count)
                    const libName = typeof lib === 'string' ? lib : lib.name;
                    const libCount = typeof lib === 'object' && lib.count !== undefined ? lib.count : null;
                    const displayText = libCount !== null
                      ? `${libName} (${libCount.toLocaleString()} items)`
                      : libName;

                    return (
                      <option key={libName} value={libName}>
                        {displayText}
                      </option>
                    );
                  })
                )}
                </select>
                {/* Spinning loader icon when loading libraries */}
                {librariesLoading && (
                  <div className="absolute right-10 top-1/2 transform -translate-y-1/2 pointer-events-none">
                    <Loader className={`w-5 h-5 animate-spin ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                  </div>
                )}
              </div>
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
                className={`w-full h-11 px-4 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white' : 'bg-white border-gray-300 text-gray-900'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
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
                  className={`flex-1 h-11 px-4 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                />
                <button
                  onClick={handleSearch}
                  className={`h-11 px-4 rounded-lg font-medium transition-all flex items-center gap-2 ${darkMode ? 'bg-purple-600 hover:bg-purple-700' : 'bg-gray-700 hover:bg-gray-800'} text-white`}
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
                className={`w-full h-11 px-4 rounded-lg font-medium transition-all flex items-center justify-center gap-2 leading-none ${darkMode ? 'bg-indigo-600 hover:bg-indigo-700' : 'bg-purple-600 hover:bg-purple-700'} text-white disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span className="leading-none">{loading ? 'Scanning...' : 'Scan Library'}</span>
              </button>
            </div>
          </div>

          {/* View Mode Toggle & Thumbnail Size Controls */}
          <div className={`p-4 rounded-lg mb-4 ${darkMode ? 'bg-gray-700/50' : 'bg-purple-50'}`}>
            {/* View Mode Toggle */}
            <div className="flex items-center justify-between mb-4">
              <label className={`text-sm font-semibold flex items-center gap-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <Eye className="w-4 h-4" />
                View Mode
              </label>
              <div className="flex gap-2">
                <button
                  onClick={() => setViewMode('list')}
                  className={`px-3 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${viewMode === 'list' ? (darkMode ? 'bg-purple-600 text-white' : 'bg-purple-600 text-white') : (darkMode ? 'bg-gray-600 text-gray-300 hover:bg-gray-500' : 'bg-purple-200 text-purple-800 hover:bg-purple-300')}`}
                >
                  <List className="w-4 h-4" />
                  <span className="hidden sm:inline">List</span>
                </button>
                <button
                  onClick={() => setViewMode('grid')}
                  className={`px-3 py-2 rounded-lg font-medium transition-all flex items-center gap-2 ${viewMode === 'grid' ? (darkMode ? 'bg-purple-600 text-white' : 'bg-purple-600 text-white') : (darkMode ? 'bg-gray-600 text-gray-300 hover:bg-gray-500' : 'bg-purple-200 text-purple-800 hover:bg-purple-300')}`}
                >
                  <LayoutGrid className="w-4 h-4" />
                  <span className="hidden sm:inline">Grid</span>
                </button>
              </div>
            </div>

            {/* Artwork Thumbnail Size Slider (List View Only) */}
            {viewMode === 'list' && (
              <div className="mb-4">
                <div className="flex items-center justify-between mb-3">
                  <label className={`text-sm font-semibold flex items-center gap-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    <SlidersHorizontal className="w-4 h-4" />
                    Artwork Size: {thumbnailSize}px
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
                    step="1"
                    value={thumbnailSize}
                    onChange={(e) => setThumbnailSize(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
                  />
                )}
              </div>
            )}

            {/* Library Thumbnail Size Slider (only in grid mode) */}
            {viewMode === 'grid' && (
              <div>
                <div className="flex items-center justify-between mb-3">
                  <label className={`text-sm font-semibold flex items-center gap-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                    <LayoutGrid className="w-4 h-4" />
                    Library Poster Size: {libraryThumbnailSize}px
                  </label>
                </div>
                <input
                  type="range"
                  min="100"
                  max="400"
                  step="1"
                  value={libraryThumbnailSize}
                  onChange={(e) => setLibraryThumbnailSize(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>
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
              <div className={`${darkMode ? 'bg-gradient-to-br from-blue-500 via-blue-600 to-indigo-700' : 'bg-gradient-to-br from-blue-400 via-blue-500 to-indigo-600'} text-white p-5 rounded-xl shadow-xl transform hover:scale-105 transition-transform duration-200`}>
                <div className="text-4xl font-bold drop-shadow-lg">{stats.total_items}</div>
                <div className="text-sm font-medium opacity-95 mt-2">Total Items</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-emerald-500 via-green-600 to-teal-700' : 'bg-gradient-to-br from-emerald-400 via-green-500 to-teal-600'} text-white p-5 rounded-xl shadow-xl transform hover:scale-105 transition-transform duration-200`}>
                <div className="text-4xl font-bold drop-shadow-lg">{stats.total_artwork}</div>
                <div className="text-sm font-medium opacity-95 mt-2">Artwork Files</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-purple-500 via-violet-600 to-fuchsia-700' : 'bg-gradient-to-br from-purple-400 via-violet-500 to-fuchsia-600'} text-white p-5 rounded-xl shadow-xl transform hover:scale-105 transition-transform duration-200`}>
                <div className="text-4xl font-bold drop-shadow-lg">{items.length}</div>
                <div className="text-sm font-medium opacity-95 mt-2">Items Shown</div>
              </div>
              <div className={`${darkMode ? 'bg-gradient-to-br from-orange-500 via-amber-600 to-yellow-700' : 'bg-gradient-to-br from-orange-400 via-amber-500 to-yellow-600'} text-white p-5 rounded-xl shadow-xl cursor-pointer transform hover:scale-105 transition-all duration-200`}>
                <button
                  onClick={() => {
                    loadOperations();
                    setShowOperations(!showOperations);
                  }}
                  className="w-full text-left"
                >
                  <div className="text-4xl font-bold drop-shadow-lg flex items-center gap-2">
                    {operations.length}
                    <ChevronDown className={`w-6 h-6 transition-transform duration-200 ${showOperations ? 'rotate-180' : ''}`} />
                  </div>
                  <div className="text-sm font-medium opacity-95 mt-2">Recent Operations</div>
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

        {/* Items List/Grid */}
        <div className={viewMode === 'list' ? 'space-y-4' : ''}>
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
              {/* Top Pagination */}
              {totalCount > 0 && scanLimit && allItems.length > 0 && (
                <div className="mb-4">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={Math.ceil(allItems.length / scanLimit)}
                    totalCount={totalCount}
                    itemsPerPage={scanLimit}
                    itemsShown={Math.min(currentPage * scanLimit, allItems.length)}
                    onPageChange={handlePageChange}
                    darkMode={darkMode}
                  />
                </div>
              )}

              {/* List View */}
              {viewMode === 'list' && (
                <div className="space-y-4">
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
                </div>
              )}

              {/* Grid View */}
              {viewMode === 'grid' && (
                <div
                  className="grid gap-4 mb-4"
                  style={{
                    gridTemplateColumns: `repeat(auto-fill, minmax(${libraryThumbnailSize}px, 1fr))`
                  }}
                >
                  {items.map((item, index) => {
                    const isExpanded = expandedGridItems.has(index);
                    const gridSpan = isExpanded ? 'col-span-full' : '';

                    return (
                    <div
                      key={index}
                      className={`rounded-xl overflow-hidden shadow-lg transition-all duration-200 ${!isExpanded ? 'hover:scale-105' : ''} ${gridSpan} ${darkMode ? 'bg-gray-800 border border-gray-700' : 'bg-white border border-gray-200'}`}
                      style={!isExpanded ? {
                        width: `${libraryThumbnailSize}px`,
                        justifySelf: 'center',
                        cursor: 'pointer'
                      } : undefined}
                    >
                      {isExpanded ? (
                        // Expanded view - show full ItemCard
                        <ItemCard
                          item={item}
                          selectedArtwork={selectedArtwork}
                          onSelectArtwork={handleSelectArtwork}
                          onDeleteArtwork={handleDeleteArtwork}
                          thumbnailSize={thumbnailSize}
                          darkMode={darkMode}
                          initiallyExpanded={true}
                          onCollapse={() => {
                            const newExpanded = new Set(expandedGridItems);
                            newExpanded.delete(index);
                            setExpandedGridItems(newExpanded);
                          }}
                        />
                      ) : (
                        // Collapsed view - show thumbnail card
                        <div
                          onClick={() => {
                            const newExpanded = new Set(expandedGridItems);
                            newExpanded.add(index);
                            setExpandedGridItems(newExpanded);
                          }}
                          style={{ cursor: 'pointer' }}
                        >
                          {/* Show first poster/artwork as thumbnail */}
                          {(() => {
                            // Get first available poster (try posters, then art, then backgrounds, then banners)
                            const firstPoster = item.artwork?.posters?.[0] ||
                                              item.artwork?.art?.[0] ||
                                              item.artwork?.backgrounds?.[0] ||
                                              item.artwork?.banners?.[0];

                            return firstPoster ? (
                              <img
                                src={firstPoster.thumb_url}
                                alt={item.info.title}
                                className="w-full aspect-[2/3] object-cover"
                                loading="lazy"
                              />
                            ) : (
                              <div className={`w-full aspect-[2/3] flex items-center justify-center ${darkMode ? 'bg-gray-700' : 'bg-gray-200'}`}>
                                <Image className={`w-12 h-12 ${darkMode ? 'text-gray-600' : 'text-gray-400'}`} />
                              </div>
                            );
                          })()}
                          <div className="p-3">
                            <h3 className={`font-semibold text-sm truncate ${darkMode ? 'text-white' : 'text-gray-800'}`}>
                              {item.info.title}
                            </h3>
                            <p className={`text-xs mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                              {item.total_artwork || 0} artwork files
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                    );
                  })}
                </div>
              )}

              {/* Bottom Pagination */}
              {totalCount > 0 && scanLimit && allItems.length > 0 && (
                <div className="mt-4">
                  <Pagination
                    currentPage={currentPage}
                    totalPages={Math.ceil(allItems.length / scanLimit)}
                    totalCount={totalCount}
                    itemsPerPage={scanLimit}
                    itemsShown={Math.min(currentPage * scanLimit, allItems.length)}
                    onPageChange={handlePageChange}
                    darkMode={darkMode}
                  />
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
