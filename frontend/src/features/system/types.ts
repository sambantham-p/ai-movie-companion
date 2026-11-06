/** API types for the system health feature (mirror backend schemas/health.py). */

export interface Liveness {
  status: 'ok'
  service: string
  version: string
  environment: string
}

export interface DependencyCheck {
  status: 'ok' | 'error'
  latency_ms: number | null
  error: string | null
}

export interface WorkerStatus {
  online: boolean
  last_seen: string | null
}

export interface Readiness {
  status: 'ready' | 'not_ready'
  database: DependencyCheck
  redis: DependencyCheck
  workers: Record<string, WorkerStatus>
}
