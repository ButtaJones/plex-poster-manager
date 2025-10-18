import React, { useState, useEffect, useCallback } from 'react';
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

  const loadLibraries = async () => {
    try {
      const response = await libraryAPI.getLibraries();
      setLibraries(response.data.libraries);
    } catch (error) {
      console.error('Error loading libraries:', error);
    }
  };

  const loadConfig = useCallback(async () => {
    try {
      const response = await configAPI.getConfig();
      setConfig(response.data);

      // If no path configured, show config modal
      if (!response.data.plex_metadata_path) {
        setShowConfig(true);
      } else {
        loadLibraries();
      }
    } catch (error) {
      console.error('Error loading config:', error);
      setShowConfig(true);
    }
  }, []); // Empty dependency array since it only uses state setters and loadLibraries

  // Load config on mount
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
    setScanProgress({ scanning: true, current: 0, total: 0, current_item: '' });

    // Start polling for progress
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
    }, 500); // Poll every 500ms

    try {
      const response = await libraryAPI.scanLibrary(selectedLibrary);
      setItems(response.data.items);
      setStats(response.data.stats);
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
      
      // Refresh the scan
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
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-gradient-to-r from-blue-600 to-blue-800 text-white shadow-lg">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Plex Poster Manager</h1>
              <p className="text-blue-100 mt-1">Manage your Plex artwork with ease</p>
            </div>
            <button
              onClick={() => setShowConfig(true)}
              className="px-4 py-2 bg-white text-blue-600 rounded-md hover:bg-blue-50 font-medium transition-colors"
            >
              ⚙️ Settings
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Controls */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Library Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Library
              </label>
              <select
                value={selectedLibrary}
                onChange={(e) => setSelectedLibrary(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {libraries.map((lib) => (
                  <option key={lib} value={lib}>
                    {lib}
                  </option>
                ))}
              </select>
            </div>

            {/* Search */}
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Search
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search by title..."
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  onClick={handleSearch}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  🔍 Search
                </button>
              </div>
            </div>

            {/* Scan Button */}
            <div className="flex items-end">
              <button
                onClick={handleScan}
                disabled={loading}
                className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 font-medium"
              >
                {loading ? '⏳ Scanning...' : '🔄 Scan Library'}
              </button>
            </div>
          </div>

          {/* Bulk Actions */}
          {selectedArtwork.length > 0 && (
            <div className="mt-4 p-4 bg-blue-50 rounded-md border border-blue-200">
              <div className="flex items-center justify-between">
                <span className="text-blue-800 font-medium">
                  {selectedArtwork.length} artwork file(s) selected
                </span>
                <div className="flex gap-2">
                  <button
                    onClick={() => setSelectedArtwork([])}
                    className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300"
                  >
                    Clear Selection
                  </button>
                  <button
                    onClick={handleDeleteSelected}
                    className="px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
                  >
                    🗑️ Delete Selected
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Stats */}
          {stats && (
            <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 text-white p-4 rounded-lg">
                <div className="text-2xl font-bold">{stats.total_items}</div>
                <div className="text-sm opacity-90">Total Items</div>
              </div>
              <div className="bg-gradient-to-br from-green-500 to-green-600 text-white p-4 rounded-lg">
                <div className="text-2xl font-bold">{stats.total_artwork}</div>
                <div className="text-sm opacity-90">Artwork Files</div>
              </div>
              <div className="bg-gradient-to-br from-purple-500 to-purple-600 text-white p-4 rounded-lg">
                <div className="text-2xl font-bold">{items.length}</div>
                <div className="text-sm opacity-90">Items Shown</div>
              </div>
              <div className="bg-gradient-to-br from-orange-500 to-orange-600 text-white p-4 rounded-lg">
                <button
                  onClick={() => {
                    loadOperations();
                    setShowOperations(!showOperations);
                  }}
                  className="w-full text-left"
                >
                  <div className="text-2xl font-bold">{operations.length}</div>
                  <div className="text-sm opacity-90">Recent Operations</div>
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Operations Panel */}
        {showOperations && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-800">Recent Operations</h2>
              <button
                onClick={() => setShowOperations(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {operations.map((op) => (
                <div
                  key={op.id}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-md"
                >
                  <div className="flex-1">
                    <div className="font-medium text-gray-800">
                      {op.action === 'delete' ? '🗑️' : '↩️'} {op.action}
                    </div>
                    <div className="text-sm text-gray-600 truncate">
                      {op.original_path}
                    </div>
                    <div className="text-xs text-gray-500">{op.timestamp}</div>
                  </div>
                  {op.can_undo && (
                    <button
                      onClick={() => handleUndo(op.id)}
                      className="ml-4 px-3 py-1 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
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
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <div className="text-gray-500 text-lg mb-4">Scanning library...</div>
              {scanProgress && scanProgress.total > 0 && (
                <div className="max-w-md mx-auto">
                  <div className="mb-2 text-sm text-gray-600">
                    Processing {scanProgress.current} of {scanProgress.total} items
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-4 mb-2">
                    <div
                      className="bg-blue-600 h-4 rounded-full transition-all duration-300"
                      style={{ width: `${(scanProgress.current / scanProgress.total) * 100}%` }}
                    ></div>
                  </div>
                  <div className="text-xs text-gray-500 truncate">
                    {scanProgress.current_item}
                  </div>
                </div>
              )}
            </div>
          ) : items.length > 0 ? (
            items.map((item, index) => (
              <ItemCard
                key={index}
                item={item}
                selectedArtwork={selectedArtwork}
                onSelectArtwork={handleSelectArtwork}
                onDeleteArtwork={handleDeleteArtwork}
              />
            ))
          ) : (
            <div className="bg-white rounded-lg shadow-md p-12 text-center">
              <div className="text-gray-500 text-lg mb-4">
                {config?.plex_metadata_path
                  ? 'Click "Scan Library" to get started'
                  : 'Please configure your Plex path in Settings'}
              </div>
              {!config?.plex_metadata_path && (
                <button
                  onClick={() => setShowConfig(true)}
                  className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
                >
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
      />
    </div>
  );
}

export default App;
