/** API calls and query hooks for backend health. */
import { useQuery } from '@tanstack/react-query'

import { apiRequest } from '@/lib/api/client'

import type { Liveness, Readiness } from './types'

export const systemKeys = {
  liveness: ['system', 'liveness'] as const,
  readiness: ['system', 'readiness'] as const,
}

export function fetchLiveness(signal?: AbortSignal): Promise<Liveness> {
  return apiRequest<Liveness>('/api/v1/health', { signal })
}

/** Readiness returns 503 with a body when a dependency is down; treat that as data. */
export function fetchReadiness(signal?: AbortSignal): Promise<Readiness> {
  return apiRequest<Readiness>('/api/v1/health/ready', { signal, acceptStatuses: [503] })
}

export function useLiveness() {
  return useQuery({ queryKey: systemKeys.liveness, queryFn: ({ signal }) => fetchLiveness(signal) })
}

export function useReadiness() {
  return useQuery({
    queryKey: systemKeys.readiness,
    queryFn: ({ signal }) => fetchReadiness(signal),
    refetchInterval: 30_000,
  })
}
