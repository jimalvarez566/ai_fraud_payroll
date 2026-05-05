type Status = 'pending' | 'flagged' | 'approved' | 'rejected' | 'analyzed'

export function StatusBadge({ status }: { status: Status }) {
  const color =
    status === 'flagged'
      ? 'text-red-400 border-red-400/30 bg-red-400/10'
      : status === 'approved'
        ? 'text-green-400 border-green-400/30 bg-green-400/10'
        : status === 'rejected'
          ? 'text-neutral-500 border-neutral-700 bg-neutral-800'
          : status === 'analyzed'
            ? 'text-blue-400 border-blue-400/30 bg-blue-400/10'
            : 'text-neutral-400 border-neutral-700 bg-neutral-800'

  return (
    <span className={`inline-flex px-2 py-0.5 rounded border text-xs mono ${color}`}>
      {status}
    </span>
  )
}
