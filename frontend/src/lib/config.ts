/** Frontend runtime configuration read from Vite env vars (VITE_*), with safe defaults. */

export interface AppConfig {
  /** Base URL for API calls. Empty means same origin (dev proxy or reverse proxy). */
  apiBaseUrl: string
  /** Minimum level the logger prints. */
  logLevel: 'debug' | 'info' | 'warn' | 'error'
}

const LEVELS = ['debug', 'info', 'warn', 'error'] as const

/** Build config from an env object; exported separately so it can be unit-tested. */
export function readConfig(env: Record<string, string | undefined>): AppConfig {
  const level = env.VITE_LOG_LEVEL as AppConfig['logLevel'] | undefined
  return {
    apiBaseUrl: (env.VITE_API_BASE_URL ?? '').replace(/\/$/, ''),
    logLevel: level && LEVELS.includes(level) ? level : env.DEV ? 'debug' : 'warn',
  }
}

export const config: AppConfig = readConfig(import.meta.env as Record<string, string | undefined>)
