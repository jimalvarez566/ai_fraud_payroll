import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '@/lib/api'
import type { Receipt } from '@/lib/api'
import { RiskBadge } from '@/components/RiskBadge'
import { StatusBadge } from '@/components/StatusBadge'

const STATUSES = ['', 'pending', 'flagged', 'approved', 'rejected', 'analyzed'] as const
const PAGE_SIZE = 20

function fmt(amount: number | string | null) {
  if (amount == null) return '—'
  return '$' + Number(amount).toFixed(2)
}

function fmtDate(d: string | null) {
  if (!d) return '—'
  return d
}

export function ReceiptsList() {
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()

  const page = Number(params.get('page') ?? 1)
  const status = params.get('status') ?? ''

  const [receipts, setReceipts] = useState<Receipt[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    api
      .listReceipts(page, PAGE_SIZE, status || undefined)
      .then((data) => {
        setReceipts(data.receipts)
        setTotal(data.total)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false))
  }, [page, status])

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

  const setStatus = (s: string) => {
    setParams(s ? { status: s } : {})
  }
  const setPage = (p: number) => {
    const next: Record<string, string> = { page: String(p) }
    if (status) next.status = status
    setParams(next)
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-8 py-5 border-b border-[#262626] flex items-center justify-between">
        <div>
          <h1 className="text-base font-semibold text-white">Receipts</h1>
          {!loading && <p className="text-xs text-[#737373] mt-0.5 mono">{total} total</p>}
        </div>
        <button
          onClick={() => navigate('/upload')}
          className="text-xs px-3 py-1.5 rounded border border-[#262626] text-[#e5e5e5] hover:bg-[#1a1a1a] transition-colors"
        >
          Upload
        </button>
      </div>

      {/* Filter bar */}
      <div className="px-8 py-3 border-b border-[#262626] flex gap-1.5">
        {STATUSES.map((s) => (
          <button
            key={s || 'all'}
            onClick={() => setStatus(s)}
            className={`text-xs px-3 py-1 rounded transition-colors ${
              status === s
                ? 'bg-[#1a1a1a] text-white border border-[#404040]'
                : 'text-[#737373] hover:text-[#e5e5e5] border border-transparent'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {loading ? (
          <div className="p-8 text-sm text-[#737373]">Loading…</div>
        ) : error ? (
          <div className="p-8 text-sm text-red-400">{error}</div>
        ) : receipts.length === 0 ? (
          <div className="p-8 text-sm text-[#737373]">No receipts found.</div>
        ) : (
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-[#262626] text-[#737373] text-xs">
                <th className="text-left px-8 py-2 font-normal">ID</th>
                <th className="text-left px-4 py-2 font-normal">Merchant</th>
                <th className="text-right px-4 py-2 font-normal">Amount</th>
                <th className="text-left px-4 py-2 font-normal">Date</th>
                <th className="text-left px-4 py-2 font-normal">Risk</th>
                <th className="text-left px-4 py-2 font-normal">Status</th>
                <th className="px-6 py-2" />
              </tr>
            </thead>
            <tbody>
              {receipts.map((r) => (
                <tr
                  key={r.id}
                  className="border-b border-[#1a1a1a] hover:bg-[#111111] cursor-pointer transition-colors"
                  onClick={() => navigate(`/receipts/${r.id}`)}
                >
                  <td className="px-8 py-3 mono text-[#737373] text-xs">{r.id}</td>
                  <td className="px-4 py-3 text-[#e5e5e5] max-w-48 truncate">
                    {r.merchant ?? <span className="text-[#404040]">Unknown</span>}
                  </td>
                  <td className="px-4 py-3 mono text-right text-[#e5e5e5]">{fmt(r.amount)}</td>
                  <td className="px-4 py-3 mono text-xs text-[#737373]">{fmtDate(r.transaction_date)}</td>
                  <td className="px-4 py-3">
                    <RiskBadge level={r.risk_level} score={r.fraud_score} />
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={r.status} />
                  </td>
                  <td className="px-6 py-3 text-right">
                    <span className="text-xs text-[#404040] hover:text-[#737373]">View →</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!loading && !error && totalPages > 1 && (
        <div className="px-8 py-3 border-t border-[#262626] flex items-center gap-3">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="text-xs px-3 py-1 rounded border border-[#262626] text-[#737373] disabled:opacity-30 hover:text-white hover:border-[#404040] transition-colors"
          >
            ← Prev
          </button>
          <span className="text-xs mono text-[#737373]">
            {page} / {totalPages}
          </span>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="text-xs px-3 py-1 rounded border border-[#262626] text-[#737373] disabled:opacity-30 hover:text-white hover:border-[#404040] transition-colors"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  )
}
