import axios from 'axios';

// Auto-detect API base URL to work both locally and over network
// Uses env var if set, otherwise constructs URL from current hostname
const API_BASE_URL = process.env.REACT_APP_API_URL ||
                     `${window.location.protocol}//${window.location.hostname}:5000`;

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const configAPI = {
  getConfig: () => api.get('/config'),
  updateConfig: (config) => api.post('/config', config),
  detectPath: () => api.get('/detect-path'),
};

export const libraryAPI = {
  getLibraries: () => api.get('/libraries'),
  scanLibrary: (library, limit = null, offset = 0) => api.post('/scan', { library, limit, offset }),
  getScanProgress: () => api.get('/scan-progress'),
  searchItems: (query, library) => api.post('/search', { query, library }),
};

export const artworkAPI = {
  getThumbnail: (path) => `${API_BASE_URL}/api/thumbnail?path=${encodeURIComponent(path)}`,
  deleteArtwork: (files, reason) => api.post('/delete', { files, reason }),
  findDuplicates: (library) => api.post('/duplicates', { library }),
};

export const operationsAPI = {
  getOperations: (limit = 50) => api.get('/operations', { params: { limit } }),
  undoOperation: (operationId) => api.post('/undo', { operation_id: operationId }),
};

export const backupAPI = {
  getBackupInfo: () => api.get('/backup-info'),
  cleanBackups: (days) => api.post('/clean-backups', { days }),
};

export const healthAPI = {
  check: () => api.get('/health'),
};

export default api;
