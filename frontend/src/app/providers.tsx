/** App-wide providers: server-state cache (TanStack Query). */
import { type QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { type ReactNode, useState } from 'react'

import { createQueryClient } from './queryClient'

export function AppProviders({ children, client }: { children: ReactNode; client?: QueryClient }) {
  const [queryClient] = useState(() => client ?? createQueryClient())
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}
