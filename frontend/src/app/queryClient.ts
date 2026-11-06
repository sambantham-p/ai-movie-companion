/** TanStack Query client factory and retry policy shared by the app and tests. */
import { QueryClient } from '@tanstack/react-query'

import { ApiError } from '@/lib/api/client'

/** Retry transient failures, but never retry client errors (4xx). */
export function shouldRetry(failureCount: number, error: unknown): boolean {
  if (error instanceof ApiError && error.status >= 400 && error.status < 500) return false
  return failureCount < 2
}

export function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: 30_000, retry: shouldRetry, refetchOnWindowFocus: false },
    },
  })
}
