import { Component } from 'react'
import type { ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  reset = () => this.setState({ error: null })

  render() {
    const { error } = this.state
    if (error) {
      return (
        <div className="p-8">
          <p className="text-sm text-red-400 mb-2">Something went wrong.</p>
          <p className="text-xs text-[#737373] mono mb-4">{error.message}</p>
          <button
            onClick={this.reset}
            className="text-xs px-3 py-1.5 rounded border border-[#262626] text-[#e5e5e5] hover:bg-[#1a1a1a] transition-colors"
          >
            Retry
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
