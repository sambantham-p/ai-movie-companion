/**
 * Typed HTTP client for the Movie Companion API.
 * Adds the owner bearer token and a request ID, and turns the backend's error envelope
 * ({ error: { code, message, request_id } }) into `ApiError`.
 */
import { config } from '../config'
import { createLogger } from '../logger'

const log = createLogger('api/client')

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId?: string

  constructor(status: number, code: string, message: string, requestId?: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.requestId = requestId
  }
}

let ownerToken: string | null = null

/** Set (or clear) the owner API token sent as a bearer token. */
export function setOwnerToken(token: string | null): void {
  ownerToken = token
}

function newRequestId(): string {
  return crypto.randomUUID().replace(/-/g, '').slice(0, 16)
}

async function toApiError(response: Response, requestId: string): Promise<ApiError> {
  try {
    const body = (await response.json()) as { error?: { code?: string; message?: string } }
    if (body.error?.code) {
      return new ApiError(response.status, body.error.code, body.error.message ?? '', requestId)
    }
  } catch {
    // Non-JSON error body: fall through to a generic error.
  }
  return new ApiError(
    response.status,
    'http_error',
    response.statusText || 'Request failed',
    requestId,
  )
}

export interface RequestOptions {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  signal?: AbortSignal
  /** Statuses that still return a parsed body (e.g. 503 from readiness). */
  acceptStatuses?: number[]
}

/** Call `path` (e.g. '/api/v1/health') and return the parsed JSON body. */
export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const requestId = newRequestId()
  const headers: Record<string, string> = { Accept: 'application/json', 'X-Request-ID': requestId }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'
  if (ownerToken) headers.Authorization = `Bearer ${ownerToken}`

  let response: Response
  try {
    response = await fetch(`${config.apiBaseUrl}${path}`, {
      method: options.method ?? 'GET',
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body),
      signal: options.signal,
    })
  } catch (cause) {
    // Caller-initiated cancellation (unmount, superseded query) is not a failure: rethrow as-is
    // so TanStack Query recognises it, and keep it out of the error log.
    if (options.signal?.aborted) {
      log.debug(`Request cancelled: ${path}`)
      throw cause
    }
    log.error(`Network error on ${path}`, cause)
    throw new ApiError(0, 'network_error', 'Could not reach the server', requestId)
  }

  if (!response.ok && !options.acceptStatuses?.includes(response.status)) {
    const error = await toApiError(response, requestId)
    log.warn(`${options.method ?? 'GET'} ${path} -> ${response.status} ${error.code}`)
    throw error
  }
  return (await response.json()) as T
}
