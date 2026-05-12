/**
 * Centralised API client.
 *
 * All fetch calls to the FastAPI backend go through this module so that:
 *  - The base URL is read from one env var (VITE_API_BASE_URL)
 *  - The API key header (VITE_API_KEY) is always included
 *  - Errors are surfaced consistently
 *
 * Usage:
 *   import { apiFetch, apiUpload } from '@/lib/api';
 *   const data = await apiFetch<SnapshotData>('/snapshot');
 */

const BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_KEY = import.meta.env.VITE_API_KEY || '';

/**
 * Typed fetch wrapper for JSON endpoints.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const url = `${BASE}/api/v1${path}`;
  const res = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(API_KEY ? { 'X-API-Key': API_KEY } : {}),
      ...options.headers,
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      detail = body?.detail ?? detail;
    } catch {
      /* ignore parse error */
    }
    throw new Error(`API ${path}: ${detail}`);
  }

  return res.json() as Promise<T>;
}

/**
 * Multipart file upload using XMLHttpRequest so we get real upload progress events.
 * Returns a Promise that resolves with the parsed JSON response.
 *
 * @param file        - The File object to upload
 * @param onProgress  - Optional callback receiving 0-100 percentage
 */
export function apiUpload<T = unknown>(
  file: File,
  onProgress?: (pct: number) => void,
): Promise<T> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('file_type', file.name.endsWith('.json') ? 'json' : 'csv');
    formData.append('triggered_by', 'manual');

    const xhr = new XMLHttpRequest();
    xhr.open('POST', `${BASE}/api/v1/run`);

    if (API_KEY) {
      xhr.setRequestHeader('X-API-Key', API_KEY);
    }

    if (onProgress) {
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          onProgress(Math.round((e.loaded / e.total) * 100));
        }
      });
    }

    xhr.addEventListener('load', () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        try {
          resolve(JSON.parse(xhr.responseText) as T);
        } catch {
          reject(new Error('Invalid JSON in upload response'));
        }
      } else {
        let detail = `HTTP ${xhr.status}`;
        try {
          const body = JSON.parse(xhr.responseText);
          detail = body?.detail ?? detail;
        } catch {
          /* ignore */
        }
        reject(new Error(`Upload failed: ${detail}`));
      }
    });

    xhr.addEventListener('error', () => reject(new Error('Network error during upload')));
    xhr.addEventListener('abort', () => reject(new Error('Upload aborted')));

    xhr.send(formData);
  });
}

/**
 * Poll a run status endpoint until the run completes or fails.
 *
 * @param runId      - The pipeline run UUID returned by /run
 * @param onStatus   - Callback called with each status update
 * @param intervalMs - Polling interval (default 2000ms)
 */
export async function pollRunStatus(
  runId: string,
  onStatus: (status: string) => void,
  intervalMs = 2000,
): Promise<{ status: 'completed' | 'failed'; errorMessage?: string }> {
  return new Promise((resolve) => {
    const timer = setInterval(async () => {
      try {
        const data = await apiFetch<{ status: string; error_message?: string }>(`/runs/${runId}/status`);
        onStatus(data.status);
        if (data.status === 'completed' || data.status === 'failed') {
          clearInterval(timer);
          resolve({
            status: data.status as 'completed' | 'failed',
            errorMessage: data.error_message,
          });
        }
      } catch {
        // keep polling on transient network errors
      }
    }, intervalMs);
  });
}

/**
 * Resets all financial data, pipeline runs, and chat history.
 */
export async function resetData(): Promise<{ status: string; message: string }> {
  return apiFetch<{ status: string; message: string }>('/data/reset', {
    method: 'DELETE',
  });
}
