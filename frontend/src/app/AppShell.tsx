/** Persistent page frame: brand header, primary navigation and the routed page. */
import { NavLink, Outlet } from 'react-router'

const NAV = [{ to: '/', label: 'Status' }] as const

export function AppShell() {
  return (
    <div className="mx-auto flex min-h-screen max-w-5xl flex-col px-5 py-6">
      <header className="mb-10 flex items-center justify-between">
        <span className="font-display text-xl tracking-tight">
          Movie <span className="text-gold">Companion</span>
        </span>
        <nav aria-label="Primary">
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'text-screen' : 'text-muted hover:text-screen'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  )
}
