import { useRef, useState } from 'react'
import type { DragEvent, ChangeEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '@/lib/api'

type UploadState = 'idle' | 'dragging' | 'loading' | 'error'

const ACCEPTED = ['image/png', 'image/jpeg', 'application/pdf']

export function Upload() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [state, setState] = useState<UploadState>('idle')
  const [error, setError] = useState<string | null>(null)
  const [fileName, setFileName] = useState<string | null>(null)

  const submit = async (file: File) => {
    if (!ACCEPTED.includes(file.type)) {
      setError(`Unsupported file type: ${file.type}. Use PNG, JPG, or PDF.`)
      setState('error')
      return
    }
    setFileName(file.name)
    setError(null)
    setState('loading')
    try {
      const receipt = await api.uploadReceipt(file)
      navigate(`/receipts/${receipt.id}`)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
      setState('error')
    }
  }

  const onDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    setState('idle')
    const file = e.dataTransfer.files[0]
    if (file) submit(file)
  }

  const onChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) submit(file)
  }

  const isLoading = state === 'loading'

  return (
    <div className="p-8 max-w-xl">
      <h1 className="text-base font-semibold text-white mb-1">Upload Receipt</h1>
      <p className="text-sm text-[#737373] mb-6">
        PNG, JPG, or PDF. OCR and fraud analysis run automatically.
      </p>

      <div
        onClick={() => !isLoading && inputRef.current?.click()}
        onDragOver={(e) => { e.preventDefault(); if (!isLoading) setState('dragging') }}
        onDragLeave={() => setState('idle')}
        onDrop={onDrop}
        className={`
          relative border rounded flex flex-col items-center justify-center gap-3
          py-16 px-8 cursor-pointer select-none transition-colors
          ${isLoading ? 'cursor-not-allowed opacity-60' : ''}
          ${state === 'dragging'
            ? 'border-[#404040] bg-[#1a1a1a]'
            : state === 'error'
              ? 'border-red-400/40 bg-red-400/5'
              : 'border-[#262626] bg-[#111111] hover:border-[#404040] hover:bg-[#161616]'
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".png,.jpg,.jpeg,.pdf"
          className="hidden"
          onChange={onChange}
          disabled={isLoading}
        />

        {isLoading ? (
          <>
            <Spinner />
            <p className="text-sm text-[#737373]">
              Uploading <span className="text-white mono">{fileName}</span>…
            </p>
            <p className="text-xs text-[#404040]">OCR and fraud analysis in progress</p>
          </>
        ) : (
          <>
            <UploadIcon />
            <div className="text-center">
              <p className="text-sm text-[#e5e5e5]">Drop file here or click to browse</p>
              <p className="text-xs text-[#737373] mt-1">PNG · JPG · PDF</p>
            </div>
          </>
        )}
      </div>

      {state === 'error' && error && (
        <p className="mt-3 text-sm text-red-400">{error}</p>
      )}

      {state === 'error' && (
        <button
          onClick={() => { setState('idle'); setError(null) }}
          className="mt-4 text-xs text-[#737373] underline underline-offset-2 hover:text-white"
        >
          Try again
        </button>
      )}
    </div>
  )
}

function UploadIcon() {
  return (
    <svg className="w-8 h-8 text-[#404040]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
    </svg>
  )
}

function Spinner() {
  return (
    <svg className="w-8 h-8 text-[#404040] animate-spin" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
  )
}
