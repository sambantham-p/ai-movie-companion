/** Shows API, database, Redis and worker status. The first screen of the foundation build. */
import { useLiveness, useReadiness } from './api'
import type { DependencyCheck, WorkerStatus } from './types'

type Tone = 'ok' | 'bad' | 'idle'

const TONE_CLASS: Record<Tone, string> = {
  ok: 'bg-ok',
  bad: 'bg-bad',
  idle: 'bg-seat-unknown',
}

function Row({ label, tone, detail }: { label: string; tone: Tone; detail: string }) {
  return (
    <li className="flex items-center justify-between gap-4 border-b border-line py-3 last:border-0">
      <span className="flex items-center gap-3">
        <span aria-hidden className={`h-2.5 w-2.5 rounded-full ${TONE_CLASS[tone]}`} />
        <span>{label}</span>
      </span>
      <span className="text-sm text-muted">{detail}</span>
    </li>
  )
}

function dependencyDetail(check: DependencyCheck): string {
  return check.status === 'ok' ? `${check.latency_ms ?? 0} ms` : (check.error ?? 'unreachable')
}

function workerDetail(worker: WorkerStatus | undefined): string {
  if (!worker?.online || !worker.last_seen) return 'offline'
  return `seen ${new Date(worker.last_seen).toLocaleTimeString()}`
}

export function SystemStatus() {
  const liveness = useLiveness()
  const readiness = useReadiness()

  if (liveness.isError) {
    return (
      <p role="alert" className="text-bad">
        API unreachable. Start the backend with <code>make api</code>.
      </p>
    )
  }

  const ready = readiness.data
  return (
    <section
      aria-labelledby="status-heading"
      className="rounded-2xl border border-line bg-panel p-6"
    >
      <h2 id="status-heading" className="mb-1 font-display text-2xl">
        System status
      </h2>
      <p className="mb-4 text-sm text-muted">
        {liveness.data
          ? `${liveness.data.service} ${liveness.data.version} · ${liveness.data.environment}`
          : 'Checking API…'}
      </p>
      {ready ? (
        <ul>
          <Row
            label="Database"
            tone={ready.database.status === 'ok' ? 'ok' : 'bad'}
            detail={dependencyDetail(ready.database)}
          />
          <Row
            label="Redis"
            tone={ready.redis.status === 'ok' ? 'ok' : 'bad'}
            detail={dependencyDetail(ready.redis)}
          />
          <Row
            label="Jobs worker"
            tone={ready.workers.jobs?.online ? 'ok' : 'idle'}
            detail={workerDetail(ready.workers.jobs)}
          />
          <Row
            label="Browser worker"
            tone={ready.workers.browser?.online ? 'ok' : 'idle'}
            detail={workerDetail(ready.workers.browser)}
          />
        </ul>
      ) : (
        <p className="text-sm text-muted">
          {readiness.isError ? 'Readiness check failed.' : 'Checking dependencies…'}
        </p>
      )}
    </section>
  )
}
