import { NavLink, Outlet } from 'react-router-dom'
import { ErrorBoundary } from '@/components/ErrorBoundary'

const links = [
  { to: '/', label: 'Dashboard', exact: true },
  { to: '/receipts', label: 'Receipts', exact: false },
  { to: '/upload', label: 'Upload', exact: false },
]

export function Layout() {
  return (
    <div className="flex h-screen bg-[#0a0a0a] text-[#e5e5e5]">
      {/* Sidebar */}
      <aside className="w-52 shrink-0 border-r border-[#262626] flex flex-col">
        <div className="px-4 py-5 border-b border-[#262626]">
          <span className="text-sm font-semibold tracking-tight text-white">FraudDetect</span>
        </div>
        <nav className="flex flex-col gap-0.5 p-2 flex-1">
          {links.map(({ to, label, exact }) => (
            <NavLink
              key={to}
              to={to}
              end={exact}
              className={({ isActive }) =>
                `px-3 py-2 rounded text-sm transition-colors ${
                  isActive
                    ? 'bg-[#1a1a1a] text-white'
                    : 'text-[#737373] hover:text-[#e5e5e5] hover:bg-[#111111]'
                }`
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="px-4 py-3 border-t border-[#262626]">
          <p className="text-xs text-[#404040]">CPSC 490 · v1.0</p>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <ErrorBoundary>
          <Outlet />
        </ErrorBoundary>
      </main>
    </div>
  )
}
