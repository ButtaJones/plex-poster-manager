import React, { useState } from 'react';

const ConfigModal = ({ isOpen, onClose, config, onSave }) => {
  const [formData, setFormData] = useState({
    plex_metadata_path: config?.plex_metadata_path || '',
    backup_directory: config?.backup_directory || '',
    thumbnail_size: config?.thumbnail_size || [300, 450],
  });

  const [detecting, setDetecting] = useState(false);

  const handleDetectPath = async () => {
    setDetecting(true);
    try {
      const { configAPI } = await import('../api');
      const response = await configAPI.detectPath();
      if (response.data.success) {
        setFormData({ ...formData, plex_metadata_path: response.data.path });
      } else {
        alert('Could not auto-detect Plex path. Please enter it manually.');
      }
    } catch (error) {
      alert('Error detecting Plex path: ' + error.message);
    } finally {
      setDetecting(false);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(formData);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
        <div className="p-6 border-b">
          <h2 className="text-2xl font-bold text-gray-800">Configuration</h2>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Plex Metadata Path
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={formData.plex_metadata_path}
                onChange={(e) =>
                  setFormData({ ...formData, plex_metadata_path: e.target.value })
                }
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="/path/to/Plex Media Server/Metadata"
                required
              />
              <button
                type="button"
                onClick={handleDetectPath}
                disabled={detecting}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 disabled:opacity-50"
              >
                {detecting ? 'Detecting...' : 'Auto-Detect'}
              </button>
            </div>
            <p className="mt-1 text-sm text-gray-500">
              Path to your Plex Media Server's Metadata folder
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Backup Directory
            </label>
            <input
              type="text"
              value={formData.backup_directory}
              onChange={(e) =>
                setFormData({ ...formData, backup_directory: e.target.value })
              }
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="/path/to/backups"
            />
            <p className="mt-1 text-sm text-gray-500">
              Where deleted artwork will be backed up (optional)
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Common Plex Paths
            </label>
            <div className="space-y-2 text-sm text-gray-600 bg-gray-50 p-3 rounded-md">
              <div>
                <strong>Windows:</strong>{' '}
                <code className="text-xs bg-gray-200 px-2 py-1 rounded">
                  %LOCALAPPDATA%\Plex Media Server\Metadata
                </code>
              </div>
              <div>
                <strong>macOS:</strong>{' '}
                <code className="text-xs bg-gray-200 px-2 py-1 rounded">
                  ~/Library/Application Support/Plex Media Server/Metadata
                </code>
              </div>
              <div>
                <strong>Linux:</strong>{' '}
                <code className="text-xs bg-gray-200 px-2 py-1 rounded">
                  /var/lib/plexmediaserver/Library/Application Support/Plex Media
                  Server/Metadata
                </code>
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
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
