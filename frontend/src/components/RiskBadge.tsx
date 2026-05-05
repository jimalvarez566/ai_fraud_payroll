interface RiskBadgeProps {
  level: 'low' | 'medium' | 'high' | null
  score?: number | null
}

export function RiskBadge({ level, score }: RiskBadgeProps) {
  const color =
    level === 'high'
      ? 'text-red-400 border-red-400/30 bg-red-400/10'
      : level === 'medium'
        ? 'text-yellow-400 border-yellow-400/30 bg-yellow-400/10'
        : level === 'low'
          ? 'text-green-400 border-green-400/30 bg-green-400/10'
          : 'text-neutral-400 border-neutral-700 bg-neutral-800'

  return (
    <span className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded border text-xs mono ${color}`}>
      {score != null && <span>{score}</span>}
      {level ?? '—'}
    </span>
  )
}
