import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Receipt } from '@/lib/api'

interface Stats {
  total: number
  high: number
  medium: number
  low: number
  pending: number
  flagged: number
  approved: number
  rejected: number
}

function computeStats(receipts: Receipt[]): Stats {
  const stats: Stats = { total: 0, high: 0, medium: 0, low: 0, pending: 0, flagged: 0, approved: 0, rejected: 0 }
  stats.total = receipts.length
  for (const r of receipts) {
    if (r.risk_level === 'high') stats.high++
    else if (r.risk_level === 'medium') stats.medium++
    else if (r.risk_level === 'low') stats.low++
    if (r.status === 'pending') stats.pending++
    else if (r.status === 'flagged') stats.flagged++
    else if (r.status === 'approved') stats.approved++
    else if (r.status === 'rejected') stats.rejected++
  }
  return stats
}

export function Dashboard() {
  const navigate = useNavigate()
  const [stats, setStats] = useState<Stats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Fetch up to 100 receipts for aggregation — sufficient for the prototype
    api
      .listReceipts(1, 100)
      .then((data) => setStats(computeStats(data.receipts)))
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="p-8">
      <div className="mb-6">
        <h1 className="text-base font-semibold text-white">Dashboard</h1>
        <p className="text-xs text-[#737373] mt-0.5">Overview of submitted receipts</p>
      </div>

      {loading ? (
        <p className="text-sm text-[#737373]">Loading…</p>
      ) : error ? (
        <p className="text-sm text-red-400">{error}</p>
      ) : stats ? (
        <div className="space-y-6">
          {/* Volume */}
          <div>
            <p className="text-xs text-[#404040] uppercase tracking-wider mb-2">Volume</p>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
              <Card
                label="Total"
                value={stats.total}
                onClick={() => navigate('/receipts')}
              />
              <Card
                label="Pending review"
                value={stats.pending + stats.flagged}
                onClick={() => navigate('/receipts?status=flagged')}
              />
              <Card label="Approved" value={stats.approved} onClick={() => navigate('/receipts?status=approved')} />
              <Card label="Rejected" value={stats.rejected} onClick={() => navigate('/receipts?status=rejected')} />
            </div>
          </div>

          {/* Risk breakdown */}
          <div>
            <p className="text-xs text-[#404040] uppercase tracking-wider mb-2">Risk Levels</p>
            <div className="grid grid-cols-3 gap-3">
              <Card
                label="High risk"
                value={stats.high}
                accent="red"
                onClick={() => navigate('/receipts')}
              />
              <Card
                label="Medium risk"
                value={stats.medium}
                accent="yellow"
                onClick={() => navigate('/receipts')}
              />
              <Card
                label="Low risk"
                value={stats.low}
                accent="green"
                onClick={() => navigate('/receipts')}
              />
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}

function Card({
  label,
  value,
  accent,
  onClick,
}: {
  label: string
  value: number
  accent?: 'red' | 'yellow' | 'green'
  onClick?: () => void
}) {
  const accentStyle =
    accent === 'red'
      ? 'text-red-400'
      : accent === 'yellow'
        ? 'text-yellow-400'
        : accent === 'green'
          ? 'text-green-400'
          : 'text-white'

  return (
    <button
      onClick={onClick}
      className="text-left border border-[#262626] rounded p-4 bg-[#111111] hover:bg-[#161616] hover:border-[#404040] transition-colors w-full"
    >
      <p className={`mono text-2xl font-semibold ${accentStyle}`}>{value}</p>
      <p className="text-xs text-[#737373] mt-1">{label}</p>
    </button>
  )
}
