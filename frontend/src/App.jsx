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
import { saveScanResults, loadScanResults, clearScanResults } from './utils/indexedDB';

function App() {
  const [config, setConfig] = useState(null);
  const [showConfig, setShowConfig] = useState(false);
  const [libraries, setLibraries] = useState([]);
  const [librariesLoading, setLibrariesLoading] = useState(true); // Start as true to show "Loading..." on initial render
  const [selectedLibrary, setSelectedLibrary] = useState(() => {
    const saved = localStorage.getItem('scanResults');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        return parsed.selectedLibrary || 'TV Shows';
      } catch (e) {
        return 'TV Shows';
      }
    }
    return 'TV Shows';
  });
  const [items, setItems] = useState([]);
  const [selectedArtwork, setSelectedArtwork] = useState([]);
  const [loading, setLoading] = useState(false);
  const [initialLoadComplete, setInitialLoadComplete] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchSuggestions, setSearchSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedSuggestionIndex, setSelectedSuggestionIndex] = useState(-1);
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
  const [expandedItems, setExpandedItems] = useState(new Set()); // Track which items are expanded (by rating_key)
  const [isDeleting, setIsDeleting] = useState(false); // Track deletion in progress
  const [deleteProgress, setDeleteProgress] = useState(null); // Track delete progress message

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

  // Load scan results from IndexedDB on component mount
  useEffect(() => {
    const loadSavedResults = async () => {
      try {
        const savedData = await loadScanResults();
        if (savedData && savedData.allItems && savedData.allItems.length > 0) {
          console.log('[App] Restoring scan results from IndexedDB');
          setAllItems(savedData.allItems);
          setTotalCount(savedData.totalCount || savedData.allItems.length);
          setCurrentPage(savedData.currentPage || 1);
          setScanLimit(savedData.scanLimit || 25);
          setSelectedLibrary(savedData.selectedLibrary || 'TV Shows');

          // Set initial page items - handle "All Items" case (null scanLimit)
          const limit = savedData.scanLimit;
          const savedPage = savedData.currentPage || 1;

          if (limit) {
            // Calculate correct slice for the saved page
            const startIdx = (savedPage - 1) * limit;
            const endIdx = startIdx + limit;
            const pageItems = savedData.allItems.slice(startIdx, endIdx);
            setItems(pageItems);
            console.log(`[App] Restored page ${savedPage} items (${startIdx} to ${endIdx})`);
          } else {
            // "All Items" mode - show everything
            setItems(savedData.allItems);
          }

          console.log(`[App] Restored ${savedData.allItems.length} items from IndexedDB`);
        }
      } catch (error) {
        console.error('[App] Failed to load scan results:', error);
      } finally {
        // Mark initial load as complete whether we found data or not
        setInitialLoadComplete(true);
      }
    };

    loadSavedResults();
  }, []); // Only run on mount

  // Save scan results to IndexedDB for persistence across page refreshes
  // IndexedDB has much higher storage limits (50MB-100MB+) than localStorage (5-10MB)
  useEffect(() => {
    if (allItems.length > 0) {
      const scanResults = {
        allItems,
        selectedLibrary,
        totalCount,
        currentPage,
        scanLimit
      };

      // Save to IndexedDB (async, non-blocking)
      saveScanResults(scanResults).catch(error => {
        console.error('[App] Failed to save scan results:', error);
      });

      // Also save minimal metadata to localStorage for fallback
      try {
        const metadata = {
          selectedLibrary,
          totalCount,
          currentPage,
          scanLimit,
          itemCount: allItems.length
        };
        localStorage.setItem('scanResults', JSON.stringify(metadata));
      } catch (e) {
        console.warn('[App] localStorage quota exceeded, skipping metadata save');
      }
    }
  }, [allItems, selectedLibrary, totalCount, currentPage, scanLimit]);

  // Generate autocomplete suggestions based on searchQuery
  useEffect(() => {
    if (searchQuery.trim().length > 0 && allItems.length > 0) {
      const query = searchQuery.toLowerCase().trim();
      const matches = allItems
        .filter(item => item.info.title.toLowerCase().includes(query))
        .slice(0, 10) // Limit to 10 suggestions
        .map(item => ({
          title: item.info.title,
          year: item.info.year,
          type: item.info.type,
          rating_key: item.info.rating_key
        }));

      setSearchSuggestions(matches);
      setShowSuggestions(matches.length > 0);
    } else {
      setSearchSuggestions([]);
      setShowSuggestions(false);
    }
    setSelectedSuggestionIndex(-1);
  }, [searchQuery, allItems]);

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

    // Clear previous scan results when starting a new scan
    setItems([]);
    setAllItems([]);
    setTotalCount(0);
    localStorage.removeItem('scanResults');
    clearScanResults().catch(err => console.error('[App] Failed to clear IndexedDB:', err));

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
      // ALWAYS scan ALL items (limit=null) so search works across entire library
      // scanLimit is ONLY for pagination display, not for scanning
      const response = await libraryAPI.scanLibrary(selectedLibrary, null, 0);
      const scannedItems = response.data.items;
      const totalItems = response.data.stats.total_count || scannedItems.length;

      console.log('[handleScan] Scanned ALL items:', scannedItems.length);
      console.log('[handleScan] Total items in library:', totalItems);

      // Cache all scanned items for search and pagination
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

  const handleSearch = () => {
    if (!searchQuery.trim()) {
      // Empty search - show first page of all items
      const firstPageItems = scanLimit ? allItems.slice(0, scanLimit) : allItems;
      setItems(firstPageItems);
      setCurrentPage(1);
      return;
    }

    // Search locally in cached allItems (instant, no API call needed)
    const query = searchQuery.toLowerCase().trim();
    const matchedItems = allItems.filter(item =>
      item.info.title.toLowerCase().includes(query)
    );

    console.log(`[handleSearch] Found ${matchedItems.length} matches for "${searchQuery}" in ${allItems.length} cached items`);

    // Show search results
    setItems(matchedItems);
    setCurrentPage(1);

    if (matchedItems.length === 0) {
      alert(`No results found for "${searchQuery}"`);
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

    // Calculate slice indices for client-side pagination
    const startIdx = (newPage - 1) * scanLimit;
    const endIdx = startIdx + scanLimit;

    // Check if requested page is beyond cached data
    if (startIdx >= allItems.length) {
      console.log('[handlePageChange] BLOCKED: Page beyond cached data');
      alert(`You've reached the end of the scanned items (${allItems.length} total). Please run a new scan to refresh the library.`);
      return;
    }

    // Scroll to top of page
    window.scrollTo({ top: 0, behavior: 'smooth' });

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

    // Show loading modal
    setIsDeleting(true);
    setDeleteProgress(`Deleting ${paths.length} file(s)...`);

    try {
      const response = await artworkAPI.deleteArtwork(paths, 'User deletion');

      // Update progress message with success info
      const mbFreed = response.data?.mb_freed || 0;
      setDeleteProgress(`Successfully deleted ${paths.length} file(s) (${mbFreed.toFixed(2)} MB freed)`);

      // Remove deleted artwork from current items view (without re-scanning)
      const pathSet = new Set(paths);
      const updatedItems = items.map(item => {
        const updatedArtwork = {};
        Object.keys(item.artwork).forEach(type => {
          updatedArtwork[type] = item.artwork[type].filter(art => !pathSet.has(art.path));
        });
        const newTotalArtwork = Object.values(updatedArtwork).reduce((sum, arr) => sum + arr.length, 0);
        return {
          ...item,
          artwork: updatedArtwork,
          total_artwork: newTotalArtwork
        };
      });

      // Also update allItems cache
      const updatedAllItems = allItems.map(item => {
        const updatedArtwork = {};
        Object.keys(item.artwork).forEach(type => {
          updatedArtwork[type] = item.artwork[type].filter(art => !pathSet.has(art.path));
        });
        const newTotalArtwork = Object.values(updatedArtwork).reduce((sum, arr) => sum + arr.length, 0);
        return {
          ...item,
          artwork: updatedArtwork,
          total_artwork: newTotalArtwork
        };
      });

      setAllItems(updatedAllItems);
      setItems(updatedItems); // Keep current view (don't navigate away)
      setSelectedArtwork([]);
      loadOperations();

      // Auto-close modal after 1.5 seconds
      setTimeout(() => {
        setIsDeleting(false);
        setDeleteProgress(null);
      }, 1500);
    } catch (error) {
      console.error('Error deleting artwork:', error);
      setDeleteProgress(`Error: ${error.message}`);

      // Auto-close error modal after 3 seconds
      setTimeout(() => {
        setIsDeleting(false);
        setDeleteProgress(null);
      }, 3000);
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
                onChange={(e) => {
                  const newLimit = e.target.value ? parseInt(e.target.value) : null;
                  setScanLimit(newLimit);
                  // Recalculate pagination with new items per page
                  if (newLimit && allItems.length > 0) {
                    // Use handlePageChange to properly recalculate with new limit
                    setCurrentPage(1);
                    const pageItems = allItems.slice(0, newLimit);
                    setItems(pageItems);
                  } else if (!newLimit && allItems.length > 0) {
                    // "All Items" selected - show everything
                    setCurrentPage(1);
                    setItems(allItems);
                  }
                }}
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
            <div className="lg:col-span-5 relative">
              <label className={`block text-sm font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                <Search className="w-4 h-4 inline mr-1" />
                Search
              </label>
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'ArrowDown') {
                        e.preventDefault();
                        setSelectedSuggestionIndex(prev =>
                          prev < searchSuggestions.length - 1 ? prev + 1 : prev
                        );
                      } else if (e.key === 'ArrowUp') {
                        e.preventDefault();
                        setSelectedSuggestionIndex(prev => prev > 0 ? prev - 1 : -1);
                      } else if (e.key === 'Enter') {
                        e.preventDefault();
                        if (selectedSuggestionIndex >= 0 && searchSuggestions[selectedSuggestionIndex]) {
                          setSearchQuery(searchSuggestions[selectedSuggestionIndex].title);
                          setShowSuggestions(false);
                          setSelectedSuggestionIndex(-1);
                        } else {
                          handleSearch();
                        }
                      } else if (e.key === 'Escape') {
                        setShowSuggestions(false);
                        setSelectedSuggestionIndex(-1);
                      }
                    }}
                    onBlur={() => {
                      // Delay to allow clicking on suggestions
                      setTimeout(() => setShowSuggestions(false), 200);
                    }}
                    onFocus={() => {
                      if (searchSuggestions.length > 0) {
                        setShowSuggestions(true);
                      }
                    }}
                    placeholder="Search by title..."
                    className={`w-full h-11 px-4 rounded-lg border transition-colors ${darkMode ? 'bg-gray-700 border-gray-600 text-white placeholder-gray-400' : 'bg-white border-gray-300 text-gray-900 placeholder-gray-500'} focus:outline-none focus:ring-2 focus:ring-purple-500`}
                  />

                  {/* Autocomplete Dropdown */}
                  {showSuggestions && searchSuggestions.length > 0 && (
                    <div className={`absolute z-50 w-full mt-1 rounded-lg shadow-lg border max-h-60 overflow-y-auto ${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-300'}`}>
                      {searchSuggestions.map((suggestion, index) => (
                        <div
                          key={suggestion.rating_key}
                          onClick={() => {
                            // Navigate directly to the selected show
                            setSearchQuery(suggestion.title);
                            setShowSuggestions(false);
                            setSelectedSuggestionIndex(-1);

                            // Filter to show only this specific item
                            const matchedItems = allItems.filter(item => item.info.rating_key === suggestion.rating_key);
                            setItems(matchedItems);
                            setCurrentPage(1);

                            // Scroll to top
                            window.scrollTo({ top: 0, behavior: 'smooth' });
                          }}
                          className={`px-4 py-3 cursor-pointer transition-colors border-b last:border-b-0 ${
                            index === selectedSuggestionIndex
                              ? darkMode
                                ? 'bg-purple-900 border-gray-700'
                                : 'bg-purple-100 border-gray-200'
                              : darkMode
                                ? 'hover:bg-gray-700 border-gray-700'
                                : 'hover:bg-gray-50 border-gray-200'
                          }`}
                        >
                          <div className={`font-medium ${darkMode ? 'text-gray-100' : 'text-gray-900'}`}>
                            {suggestion.title}
                          </div>
                          <div className={`text-xs flex gap-2 mt-1 ${darkMode ? 'text-gray-400' : 'text-gray-500'}`}>
                            <span className="capitalize">{suggestion.type}</span>
                            {suggestion.year && <span>• {suggestion.year}</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
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
                </div>
                <input
                  type="range"
                  min="150"
                  max="500"
                  step="1"
                  value={thumbnailSize}
                  onChange={(e) => setThumbnailSize(parseInt(e.target.value))}
                  className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
                />
              </div>
            )}

            {/* Grid View Sliders: Poster Size + Artwork Size */}
            {viewMode === 'grid' && (
              <div className="space-y-4">
                {/* Library Poster Size Slider */}
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

                {/* Artwork Size Slider */}
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <label className={`text-sm font-semibold flex items-center gap-2 ${darkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                      <SlidersHorizontal className="w-4 h-4" />
                      Artwork Size: {thumbnailSize}px
                    </label>
                  </div>
                  <input
                    type="range"
                    min="150"
                    max="500"
                    step="1"
                    value={thumbnailSize}
                    onChange={(e) => setThumbnailSize(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-300 rounded-lg appearance-none cursor-pointer slider"
                  />
                </div>
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
              <div className={`${darkMode ? 'bg-gradient-to-br from-indigo-500 via-purple-600 to-pink-700' : 'bg-gradient-to-br from-indigo-400 via-purple-500 to-pink-600'} text-white p-5 rounded-xl shadow-xl cursor-pointer transform hover:scale-105 transition-all duration-200`}>
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
          {!initialLoadComplete ? (
            // Show loading state while checking IndexedDB
            <div className={`${darkMode ? 'bg-gray-800' : 'bg-white'} rounded-xl shadow-lg p-12 text-center`}>
              <Loader className={`w-12 h-12 mx-auto mb-4 animate-spin ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
              <div className={`text-lg mb-4 ${darkMode ? 'text-gray-300' : 'text-gray-600'}`}>Loading...</div>
            </div>
          ) : loading ? (
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
                    totalPages={Math.ceil(totalCount / scanLimit)}
                    totalCount={totalCount}
                    itemsPerPage={scanLimit}
                    itemsShown={Math.min(allItems.length, totalCount)}
                    onPageChange={handlePageChange}
                    darkMode={darkMode}
                  />
                </div>
              )}

              {/* List View */}
              {viewMode === 'list' && (
                <div className="space-y-4">
                  {items.map((item, index) => {
                    const itemId = item.info.rating_key;
                    const isExpanded = expandedItems.has(itemId);

                    return (
                      <ItemCard
                        key={itemId || index}
                        item={item}
                        selectedArtwork={selectedArtwork}
                        onSelectArtwork={handleSelectArtwork}
                        onDeleteArtwork={handleDeleteArtwork}
                        thumbnailSize={thumbnailSize}
                        darkMode={darkMode}
                        initiallyExpanded={isExpanded}
                        onToggle={() => {
                          const newExpanded = new Set(expandedItems);
                          if (isExpanded) {
                            newExpanded.delete(itemId);
                          } else {
                            newExpanded.add(itemId);
                          }
                          setExpandedItems(newExpanded);
                        }}
                      />
                    );
                  })}
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
                    const itemId = item.info.rating_key;
                    const isExpanded = expandedItems.has(itemId);
                    const gridSpan = isExpanded ? 'col-span-full' : '';

                    return (
                    <div
                      key={itemId || index}
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
                            const newExpanded = new Set(expandedItems);
                            newExpanded.delete(itemId);
                            setExpandedItems(newExpanded);
                          }}
                        />
                      ) : (
                        // Collapsed view - show thumbnail card
                        <div
                          onClick={() => {
                            const newExpanded = new Set(expandedItems);
                            newExpanded.add(itemId);
                            setExpandedItems(newExpanded);
                          }}
                          style={{ cursor: 'pointer' }}
                        >
                          {/* Show first poster/artwork as thumbnail */}
                          <div className="relative">
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
                            {/* Deletable Badge Overlay */}
                            {item.has_custom_artwork && (
                              <div className="absolute top-2 right-2">
                                <span className="px-2 py-1 text-xs font-bold rounded-full bg-green-500 text-white shadow-lg">
                                  {item.custom_artwork_count}
                                </span>
                              </div>
                            )}
                          </div>
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
                    totalPages={Math.ceil(totalCount / scanLimit)}
                    totalCount={totalCount}
                    itemsPerPage={scanLimit}
                    itemsShown={Math.min(allItems.length, totalCount)}
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

      {/* Delete Progress Modal */}
      {isDeleting && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
          <div className={`${darkMode ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} rounded-xl shadow-2xl p-8 max-w-md w-full mx-4 border`}>
            <div className="flex flex-col items-center">
              {deleteProgress?.startsWith('Error') ? (
                <>
                  {/* Error Icon */}
                  <div className="w-16 h-16 rounded-full bg-red-100 dark:bg-red-900/30 flex items-center justify-center mb-4">
                    <X className="w-8 h-8 text-red-600 dark:text-red-400" />
                  </div>
                  <div className={`text-lg font-semibold mb-2 ${darkMode ? 'text-red-400' : 'text-red-600'}`}>
                    {deleteProgress}
                  </div>
                </>
              ) : deleteProgress?.startsWith('Successfully') ? (
                <>
                  {/* Success Checkmark */}
                  <div className="w-16 h-16 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mb-4">
                    <svg className="w-8 h-8 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div className={`text-lg font-semibold mb-2 text-center ${darkMode ? 'text-green-400' : 'text-green-600'}`}>
                    {deleteProgress}
                  </div>
                </>
              ) : (
                <>
                  {/* Loading Spinner */}
                  <Loader className={`w-16 h-16 mb-4 animate-spin ${darkMode ? 'text-purple-400' : 'text-purple-600'}`} />
                  <div className={`text-lg font-semibold mb-2 ${darkMode ? 'text-gray-200' : 'text-gray-800'}`}>
                    {deleteProgress}
                  </div>
                  <div className={`text-sm ${darkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                    Please wait...
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
