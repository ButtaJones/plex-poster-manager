/**
 * IndexedDB utility for storing large scan results
 *
 * IndexedDB has MUCH higher storage limits than localStorage:
 * - localStorage: 5-10MB
 * - IndexedDB: 50MB-100MB+ (varies by browser)
 *
 * This allows us to persist full scan results across page refreshes
 * without hitting quota exceeded errors.
 */

const DB_NAME = 'PlexPosterManager';
const DB_VERSION = 1;
const STORE_NAME = 'scanResults';

/**
 * Open/create IndexedDB database
 */
function openDB() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = event.target.result;

      // Create object store if it doesn't exist
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME);
      }
    };
  });
}

/**
 * Save scan results to IndexedDB
 * @param {Object} data - Scan results data to save
 */
export async function saveScanResults(data) {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);

    // Store with key 'current' to always have latest scan
    store.put(data, 'current');

    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log('[IndexedDB] Scan results saved successfully');
        resolve();
      };
      transaction.onerror = () => reject(transaction.error);
    });
  } catch (error) {
    console.error('[IndexedDB] Failed to save scan results:', error);
    throw error;
  }
}

/**
 * Load scan results from IndexedDB
 * @returns {Object|null} - Scan results or null if not found
 */
export async function loadScanResults() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get('current');

    return new Promise((resolve, reject) => {
      request.onsuccess = () => {
        if (request.result) {
          console.log('[IndexedDB] Scan results loaded successfully');
          resolve(request.result);
        } else {
          console.log('[IndexedDB] No saved scan results found');
          resolve(null);
        }
      };
      request.onerror = () => reject(request.error);
    });
  } catch (error) {
    console.error('[IndexedDB] Failed to load scan results:', error);
    return null;
  }
}

/**
 * Clear scan results from IndexedDB
 */
export async function clearScanResults() {
  try {
    const db = await openDB();
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    store.delete('current');

    return new Promise((resolve, reject) => {
      transaction.oncomplete = () => {
        console.log('[IndexedDB] Scan results cleared successfully');
        resolve();
      };
      transaction.onerror = () => reject(transaction.error);
    });
  } catch (error) {
    console.error('[IndexedDB] Failed to clear scan results:', error);
    throw error;
  }
}
