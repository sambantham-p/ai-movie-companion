/** Route table. Feature pages are added here as milestones land (movies, theatres, seats...). */
import type { RouteObject } from 'react-router'

import { SystemStatus } from '@/features/system/SystemStatus'

import { AppShell } from './AppShell'
import { NotFound } from './NotFound'

export const routes: RouteObject[] = [
  {
    path: '/',
    element: <AppShell />,
    children: [
      { index: true, element: <SystemStatus /> },
      { path: '*', element: <NotFound /> },
    ],
  },
]
