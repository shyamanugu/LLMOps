/**
 * Typed fetch wrapper for the LLMOps platform API.
 *
 * The base URL is read from `import.meta.env.VITE_API_BASE`. All helpers throw
 * a typed {@link ApiError} on non-2xx responses or network failures, so callers
 * (React Query hooks) can render structured error states. No `any` is used.
 */

import type { JsonValue } from './types';

/** Base URL for every request, from the Vite environment. */
export const API_BASE: string =
  (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, '') ??
  'http://localhost:8000/api/v1';

/** Structured error raised for any failed API call. */
export class ApiError extends Error {
  public readonly status: number;
  public readonly url: string;
  public readonly body: string | null;
  /** True when the failure looks like an unimplemented / missing endpoint. */
  public readonly isNotWired: boolean;

  constructor(message: string, status: number, url: string, body: string | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.url = url;
    this.body = body;
    // 0 = network/CORS failure, 404 = route missing, 501 = not implemented.
    this.isNotWired = status === 0 || status === 404 || status === 501;
  }
}

/** A payload that carries whether it came from the live API or a placeholder. */
export interface Resulted<T> {
  data: T;
  /** True when `data` is locally-generated placeholder/mock content. */
  isPlaceholder: boolean;
  /** Optional human note explaining why placeholder data is shown. */
  note?: string;
}

type QueryValue = string | number | boolean | undefined | null;

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(`${API_BASE}${path.startsWith('/') ? path : `/${path}`}`);
  if (query) {
    for (const [key, value] of Object.entries(query)) {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    }
  }
  return url.toString();
}

async function request<T>(
  method: string,
  path: string,
  options: { query?: Record<string, QueryValue>; body?: JsonValue } = {},
): Promise<T> {
  const url = buildUrl(path, options.query);
  let response: Response;
  try {
    response = await fetch(url, {
      method,
      headers: {
        Accept: 'application/json',
        ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
  } catch (cause) {
    // Network error / CORS / server down — surface as status 0.
    throw new ApiError(
      `Network request failed: ${(cause as Error).message}`,
      0,
      url,
      null,
    );
  }

  if (!response.ok) {
    let body: string | null = null;
    try {
      body = await response.text();
    } catch {
      body = null;
    }
    throw new ApiError(
      `Request failed with ${response.status} ${response.statusText}`,
      response.status,
      url,
      body,
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/** GET a JSON resource. */
export function getJson<T>(
  path: string,
  query?: Record<string, QueryValue>,
): Promise<T> {
  return request<T>('GET', path, { query });
}

/** POST a JSON body and read a JSON response. */
export function postJson<T>(path: string, body?: JsonValue): Promise<T> {
  return request<T>('POST', path, { body });
}

/**
 * Attempt a live fetch, falling back to placeholder data when the endpoint is
 * not yet wired (network error / 404 / 501). Any other error is re-thrown so it
 * can be shown as a real error state. This is how the console "never crashes"
 * on TODO endpoints (ARCHITECTURE_SPEC §4).
 */
export async function withPlaceholder<T>(
  fetcher: () => Promise<T>,
  fallback: () => T,
  note = 'Backend endpoint is not wired yet — showing placeholder data.',
): Promise<Resulted<T>> {
  try {
    const data = await fetcher();
    return { data, isPlaceholder: false };
  } catch (error) {
    if (error instanceof ApiError && error.isNotWired) {
      return { data: fallback(), isPlaceholder: true, note };
    }
    throw error;
  }
}
