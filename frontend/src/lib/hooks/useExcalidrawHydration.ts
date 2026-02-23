/**
 * Excalidraw Hydration Hook
 *
 * Handles loading images from URLs into Excalidraw's binary file store.
 * The backend stores external URLs in files[id].dataURL, but Excalidraw
 * needs actual base64 data. This hook fetches the images via a proxy
 * and converts them to base64.
 */

import { useCallback, useRef } from 'react';

// Use generic types to avoid Excalidraw type import issues
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ExcalidrawAPI = any;

interface BinaryFileData {
  id: string;
  mimeType: string;
  dataURL: string;
  created: number;
}

interface OriginalFile {
  id: string;
  mimeType?: string;
  dataURL?: string;
  created?: number;
}

interface HydrationState {
  isHydrating: boolean;
  hydratedFileIds: Set<string>;
  pendingUrls: Map<string, Promise<BinaryFileData | null>>;
  originalFiles: Record<string, OriginalFile>;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
type ExcalidrawElement = any;

/**
 * Check if a dataURL looks like an external URL (not a base64 data URL)
 */
function isExternalUrl(dataUrl: string | undefined): boolean {
  if (!dataUrl) return false;
  return dataUrl.startsWith('http://') || dataUrl.startsWith('https://');
}

/**
 * Convert an image URL to a DataURL via the proxy
 */
async function fetchImageAsDataUrl(imageUrl: string): Promise<{ dataUrl: string; mimeType: string } | null> {
  try {
    // Use our proxy to avoid CORS issues
    const proxyUrl = `/api/image-proxy?url=${encodeURIComponent(imageUrl)}`;

    const response = await fetch(proxyUrl);

    if (!response.ok) {
      console.warn(`[Hydration] Failed to fetch image: ${response.status} for ${imageUrl}`);
      return null;
    }

    const blob = await response.blob();
    const mimeType = blob.type || 'image/jpeg';

    // Convert blob to DataURL
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        resolve({
          dataUrl: reader.result as string,
          mimeType,
        });
      };
      reader.onerror = () => {
        console.warn(`[Hydration] Failed to read blob for ${imageUrl}`);
        resolve(null);
      };
      reader.readAsDataURL(blob);
    });
  } catch (error) {
    console.warn(`[Hydration] Error fetching image ${imageUrl}:`, error);
    return null;
  }
}

/**
 * Hook to hydrate Excalidraw images from URLs
 */
export function useExcalidrawHydration() {
  const stateRef = useRef<HydrationState>({
    isHydrating: false,
    hydratedFileIds: new Set(),
    pendingUrls: new Map(),
    originalFiles: {},
  });

  const excalidrawApiRef = useRef<ExcalidrawAPI | null>(null);

  /**
   * Set the Excalidraw API reference
   */
  const setExcalidrawApi = useCallback((api: ExcalidrawAPI | null) => {
    excalidrawApiRef.current = api;
  }, []);

  /**
   * Set the original files from the backend (with URLs)
   */
  const setOriginalFiles = useCallback((files: Record<string, unknown>) => {
    stateRef.current.originalFiles = files as Record<string, OriginalFile>;
    console.log('[Hydration] Received original files:', Object.keys(files).length);
  }, []);

  /**
   * Hydrate all URL-based images in the current scene
   */
  const hydrateImages = useCallback(async () => {
    const api = excalidrawApiRef.current;
    if (!api) {
      console.warn('[Hydration] No Excalidraw API available');
      return;
    }

    const state = stateRef.current;
    if (state.isHydrating) {
      console.log('[Hydration] Already hydrating, skipping...');
      return;
    }

    state.isHydrating = true;
    console.log('[Hydration] Starting image hydration...');

    try {
      const elements = api.getSceneElements();
      // Use the original files from backend, not api.getFiles() which may have rejected them
      const originalFiles = state.originalFiles;

      console.log('[Hydration] Elements:', elements.length, 'Original files:', Object.keys(originalFiles).length);

      // Find image elements that reference files with external URLs
      const imageElements = elements.filter(
        (el: ExcalidrawElement) => {
          if (el.type !== 'image' || !('fileId' in el) || !el.fileId) {
            return false;
          }

          // Already hydrated?
          if (state.hydratedFileIds.has(el.fileId)) {
            return false;
          }

          // Check if we have this file in our original files from backend
          const file = originalFiles[el.fileId];
          if (!file) {
            console.log(`[Hydration] File ${el.fileId} not found in original files`);
            return false;
          }

          // Check if dataURL is an external URL (not a base64 data URL)
          const hasExternalUrl = isExternalUrl(file.dataURL);
          if (hasExternalUrl) {
            console.log(`[Hydration] Found external URL for ${el.fileId}: ${file.dataURL?.substring(0, 60)}...`);
          }

          return hasExternalUrl;
        }
      );

      if (imageElements.length === 0) {
        console.log('[Hydration] No images to hydrate');
        state.isHydrating = false;
        return;
      }

      console.log(`[Hydration] Found ${imageElements.length} images to hydrate`);

      // Process images in parallel (with limit)
      const BATCH_SIZE = 5;
      const filesToAdd: BinaryFileData[] = [];

      for (let i = 0; i < imageElements.length; i += BATCH_SIZE) {
        const batch = imageElements.slice(i, i + BATCH_SIZE);

        await Promise.all(
          batch.map(async (element: ExcalidrawElement) => {
            const fileId = (element as any).fileId as string;
            // Use original files from backend, not Excalidraw's files
            const file = originalFiles[fileId];
            const imageUrl = file?.dataURL;

            if (!imageUrl) {
              console.warn(`[Hydration] No URL found for file ${fileId}`);
              return;
            }

            // Check if we're already fetching this URL
            let fetchPromise = state.pendingUrls.get(fileId);

            if (!fetchPromise) {
              fetchPromise = (async () => {
                console.log(`[Hydration] Fetching image: ${imageUrl.substring(0, 60)}...`);
                const result = await fetchImageAsDataUrl(imageUrl);

                if (result) {
                  // Update the existing file with the base64 data
                  const fileData: BinaryFileData = {
                    id: fileId as any,
                    mimeType: result.mimeType as any,
                    dataURL: result.dataUrl as any,
                    created: Date.now(),
                  };
                  return fileData;
                }
                return null;
              })();

              state.pendingUrls.set(fileId, fetchPromise);
            }

            const fileData = await fetchPromise;

            if (fileData) {
              filesToAdd.push(fileData);
              state.hydratedFileIds.add(fileId);
            }

            state.pendingUrls.delete(fileId);
          })
        );
      }

      // Add the files to Excalidraw with base64 data
      if (filesToAdd.length > 0) {
        console.log(`[Hydration] Adding ${filesToAdd.length} files to Excalidraw`);
        api.addFiles(filesToAdd);
        console.log('[Hydration] Files added with base64 data');
      }

    } catch (error) {
      console.error('[Hydration] Error during hydration:', error);
    } finally {
      state.isHydrating = false;
    }
  }, []);

  /**
   * Check if hydration is in progress
   */
  const isHydrating = useCallback(() => {
    return stateRef.current.isHydrating;
  }, []);

  /**
   * Clear hydration cache (useful when loading a new board)
   */
  const clearCache = useCallback(() => {
    stateRef.current.hydratedFileIds.clear();
    stateRef.current.pendingUrls.clear();
    stateRef.current.originalFiles = {};
  }, []);

  return {
    setExcalidrawApi,
    setOriginalFiles,
    hydrateImages,
    isHydrating,
    clearCache,
  };
}

export default useExcalidrawHydration;
