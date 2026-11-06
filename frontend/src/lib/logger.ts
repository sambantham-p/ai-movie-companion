/**
 * Centralized frontend logger. Use `createLogger('feature/module')` instead of console.*.
 * Lines carry an ISO timestamp, level and scope, and secrets are redacted before printing.
 */
import { config } from './config'

export type LogLevel = 'debug' | 'info' | 'warn' | 'error'

const ORDER: Record<LogLevel, number> = { debug: 10, info: 20, warn: 30, error: 40 }
const SECRET_PATTERN =
  /(token|password|otp|secret|api[_-]?key|authorization|cookie|upi|cvv)(["']?\s*[:=]\s*["']?)([^\s"',;&}]+)/gi
const BEARER_PATTERN = /(bearer\s+)[\w.~+/=-]+/gi

/** Mask secrets in a log string. */
export function redact(text: string): string {
  return text.replace(BEARER_PATTERN, '$1***').replace(SECRET_PATTERN, '$1$2***')
}

function format(value: unknown): string {
  if (value instanceof Error) return `${value.name}: ${value.message}`
  if (typeof value === 'string') return value
  try {
    return JSON.stringify(value)
  } catch {
    return String(value)
  }
}

export interface Logger {
  debug(message: string, ...details: unknown[]): void
  info(message: string, ...details: unknown[]): void
  warn(message: string, ...details: unknown[]): void
  error(message: string, ...details: unknown[]): void
}

/** Create a scoped logger that respects the configured minimum level. */
export function createLogger(scope: string, minLevel: LogLevel = config.logLevel): Logger {
  const emit = (level: LogLevel, message: string, details: unknown[]) => {
    if (ORDER[level] < ORDER[minLevel]) return
    const line = [message, ...details.map(format)].join(' ')
    console[level](
      `${new Date().toISOString()} | ${level.toUpperCase()} | ${scope} | ${redact(line)}`,
    )
  }
  return {
    debug: (m, ...d) => emit('debug', m, d),
    info: (m, ...d) => emit('info', m, d),
    warn: (m, ...d) => emit('warn', m, d),
    error: (m, ...d) => emit('error', m, d),
  }
}
