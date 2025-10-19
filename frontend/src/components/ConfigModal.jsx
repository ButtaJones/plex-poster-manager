import React, { useState } from 'react';

const ConfigModal = ({ isOpen, onClose, config, onSave, darkMode = false }) => {
  const [formData, setFormData] = useState({
    plex_url: config?.plex_url || 'http://localhost:32400',
    plex_token: config?.plex_token || '',
    backup_directory: config?.backup_directory || '',
    thumbnail_size: config?.thumbnail_size || [300, 450],
    default_artwork_size: config?.default_artwork_size || 300,
    default_library_size: config?.default_library_size || 200,
  });

  const [detecting, setDetecting] = useState(false);
  const [testing, setTesting] = useState(false);

  // Get current sizes from localStorage (matching App.jsx)
  const currentArtworkSize = parseInt(localStorage.getItem('thumbnailSize') || '300');
  const currentLibrarySize = parseInt(localStorage.getItem('libraryThumbnailSize') || '200');

  const handleDetectUrl = async () => {
    setDetecting(true);
    try {
      const { configAPI } = await import('../api');
      const response = await configAPI.detectPath();
      if (response.data.success) {
        setFormData({ ...formData, plex_url: response.data.url });
        alert(`Found Plex server at: ${response.data.url}`);
      } else {
        alert('Could not auto-detect Plex server. Please enter URL manually.');
      }
    } catch (error) {
      alert('Error detecting Plex server: ' + error.message);
    } finally {
      setDetecting(false);
    }
  };

  const handleTestToken = async () => {
    if (!formData.plex_token) {
      alert('Please enter a Plex token first');
      return;
    }

    setTesting(true);
    try {
      const response = await fetch('http://localhost:5000/api/test-token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: formData.plex_token })
      });
      const data = await response.json();

      if (data.success) {
        alert(`✓ Token valid! Connected to: ${data.username}`);
      } else {
        alert(`✗ Token validation failed: ${data.error}`);
      }
    } catch (error) {
      alert('Error testing token: ' + error.message);
    } finally {
      setTesting(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className={`rounded-lg shadow-xl max-w-2xl w-full mx-4 ${
        darkMode ? 'bg-gray-800' : 'bg-white'
      }`}>
        <div className={`p-6 border-b ${
          darkMode ? 'border-gray-700' : 'border-gray-200'
        }`}>
          <h2 className={`text-2xl font-bold ${
            darkMode ? 'text-gray-100' : 'text-gray-800'
          }`}>Configuration</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className={`border rounded-md p-3 mb-4 ${
            darkMode
              ? 'bg-blue-900 border-blue-700'
              : 'bg-blue-50 border-blue-200'
          }`}>
            <p className={`text-sm ${
              darkMode ? 'text-blue-200' : 'text-blue-800'
            }`}>
              <strong>API Mode:</strong> This app uses the Plex API to manage artwork. You need a Plex server URL and authentication token.
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Plex Server URL
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={formData.plex_url}
                onChange={(e) =>
                  setFormData({ ...formData, plex_url: e.target.value })
                }
                className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                  darkMode
                    ? 'bg-gray-700 border-gray-600 text-gray-100 focus:ring-blue-400'
                    : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
                }`}
                placeholder="http://localhost:32400"
                required
              />
              <button
                type="button"
                onClick={handleDetectUrl}
                disabled={detecting}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
              >
                {detecting ? 'Detecting...' : 'Auto-Detect'}
              </button>
            </div>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Usually http://localhost:32400 for local servers
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Plex Token (Required)
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={formData.plex_token}
                onChange={(e) =>
                  setFormData({ ...formData, plex_token: e.target.value })
                }
                className={`flex-1 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 font-mono text-sm ${
                  darkMode
                    ? 'bg-gray-700 border-gray-600 text-gray-100 focus:ring-blue-400'
                    : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
                }`}
                placeholder="Your Plex authentication token"
                required
              />
              <button
                type="button"
                onClick={handleTestToken}
                disabled={testing || !formData.plex_token}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50"
              >
                {testing ? 'Testing...' : 'Test'}
              </button>
            </div>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Get your token from Plex Settings → Network → Show Advanced → Manual Connections
              {' '}(<a href="https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/" target="_blank" rel="noopener noreferrer" className={darkMode ? 'text-blue-400 hover:underline' : 'text-blue-600 hover:underline'}>How to find</a>)
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Backup Directory (Optional)
            </label>
            <input
              type="text"
              value={formData.backup_directory}
              onChange={(e) =>
                setFormData({ ...formData, backup_directory: e.target.value })
              }
              className={`w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 ${
                darkMode
                  ? 'bg-gray-700 border-gray-600 text-gray-100 focus:ring-blue-400'
                  : 'bg-white border-gray-300 text-gray-900 focus:ring-blue-500'
              }`}
              placeholder="/path/to/backups"
            />
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Where deleted artwork will be backed up
            </p>
          </div>

          <div>
            <label className={`block text-sm font-medium mb-2 ${
              darkMode ? 'text-gray-300' : 'text-gray-700'
            }`}>
              Thumbnail Size: {formData.thumbnail_size[0]}x{formData.thumbnail_size[1]}px
            </label>
            <input
              type="range"
              min="150"
              max="600"
              step="50"
              value={formData.thumbnail_size[0]}
              onChange={(e) => {
                const width = parseInt(e.target.value);
                const height = Math.round(width * 1.5); // 2:3 aspect ratio
                setFormData({ ...formData, thumbnail_size: [width, height] });
              }}
              className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${
                darkMode
                  ? 'bg-gray-700 accent-blue-400'
                  : 'bg-gray-200 accent-blue-600'
              }`}
            />
            <div className={`flex justify-between text-xs mt-1 ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              <span>Small (150px)</span>
              <span>Medium (300px)</span>
              <span>Large (600px)</span>
            </div>
            <p className={`mt-1 text-sm ${
              darkMode ? 'text-gray-400' : 'text-gray-500'
            }`}>
              Adjust thumbnail display size (larger = better quality, slower loading)
            </p>
          </div>

          {/* Default Thumbnail Sizes Section */}
          <div className={`border rounded-lg p-4 space-y-4 ${
            darkMode
              ? 'bg-purple-900/20 border-purple-700'
              : 'bg-purple-50 border-purple-200'
          }`}>
            <h3 className={`font-semibold mb-3 ${
              darkMode ? 'text-gray-200' : 'text-gray-800'
            }`}>
              Default Thumbnail Sizes
            </h3>
            <p className={`text-sm mb-3 ${
              darkMode ? 'text-gray-400' : 'text-gray-600'
            }`}>
              Set your preferred default sizes. These will be applied when the page loads.
            </p>

            {/* Artwork Size (List View) */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={`text-sm font-medium ${
                  darkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Artwork Size (List View): {formData.default_artwork_size}px
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setFormData({ ...formData, default_artwork_size: currentArtworkSize });
                    alert(`Set default artwork size to ${currentArtworkSize}px`);
                  }}
                  className={`text-xs px-3 py-1 rounded-md transition-colors ${
                    darkMode
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  Set as Default ({currentArtworkSize}px)
                </button>
              </div>
              <input
                type="range"
                min="150"
                max="500"
                step="10"
                value={formData.default_artwork_size}
                onChange={(e) =>
                  setFormData({ ...formData, default_artwork_size: parseInt(e.target.value) })
                }
                className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${
                  darkMode
                    ? 'bg-gray-700 accent-purple-400'
                    : 'bg-gray-200 accent-purple-600'
                }`}
              />
              <div className={`flex justify-between text-xs mt-1 ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                <span>150px</span>
                <span>300px</span>
                <span>500px</span>
              </div>
            </div>

            {/* Library Poster Size (Grid View) */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className={`text-sm font-medium ${
                  darkMode ? 'text-gray-300' : 'text-gray-700'
                }`}>
                  Library Poster Size (Grid View): {formData.default_library_size}px
                </label>
                <button
                  type="button"
                  onClick={() => {
                    setFormData({ ...formData, default_library_size: currentLibrarySize });
                    alert(`Set default library size to ${currentLibrarySize}px`);
                  }}
                  className={`text-xs px-3 py-1 rounded-md transition-colors ${
                    darkMode
                      ? 'bg-purple-600 hover:bg-purple-700 text-white'
                      : 'bg-purple-600 hover:bg-purple-700 text-white'
                  }`}
                >
                  Set as Default ({currentLibrarySize}px)
                </button>
              </div>
              <input
                type="range"
                min="100"
                max="400"
                step="10"
                value={formData.default_library_size}
                onChange={(e) =>
                  setFormData({ ...formData, default_library_size: parseInt(e.target.value) })
                }
                className={`w-full h-2 rounded-lg appearance-none cursor-pointer ${
                  darkMode
                    ? 'bg-gray-700 accent-purple-400'
                    : 'bg-gray-200 accent-purple-600'
                }`}
              />
              <div className={`flex justify-between text-xs mt-1 ${
                darkMode ? 'text-gray-400' : 'text-gray-500'
              }`}>
                <span>100px</span>
                <span>250px</span>
                <span>400px</span>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className={`px-4 py-2 rounded-md ${
                darkMode
                  ? 'text-gray-300 bg-gray-700 hover:bg-gray-600'
                  : 'text-gray-700 bg-gray-200 hover:bg-gray-300'
              }`}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              Save Configuration
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ConfigModal;
