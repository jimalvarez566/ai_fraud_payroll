const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export interface FraudFlag {
  id: number
  flag_type: string
  severity: 'low' | 'medium' | 'high'
  description: string
  confidence_score: number
  details: Record<string, unknown> | null
  created_at: string
}

export interface Receipt {
  id: number
  employee_id: number | null
  merchant: string | null
  amount: number | null
  transaction_date: string | null
  category: string | null
  items: { line_items?: { description: string; amount: number }[]; transaction_time?: string; raw_text?: string } | null
  ocr_confidence: number | null
  fraud_score: number | null
  risk_level: 'low' | 'medium' | 'high' | null
  status: 'pending' | 'flagged' | 'approved' | 'rejected' | 'analyzed'
  image_path: string
  image_hash: string | null
  created_at: string
  analyzed_at: string | null
  reviewed_at: string | null
  fraud_flags: FraudFlag[]
}

export interface ReceiptListResponse {
  receipts: Receipt[]
  total: number
  page: number
  per_page: number
}

export interface ReviewResponse extends Receipt {
  original_receipt_id: number | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status}: ${text}`)
  }
  return res.json()
}

export const api = {
  uploadReceipt: async (file: File, employeeId?: number): Promise<Receipt> => {
    const form = new FormData()
    form.append('file', file)
    if (employeeId != null) form.append('employee_id', String(employeeId))
    const res = await fetch(`${BASE_URL}/api/v1/receipts/upload`, {
      method: 'POST',
      body: form,
    })
    if (!res.ok) {
      const text = await res.text()
      throw new Error(`${res.status}: ${text}`)
    }
    return res.json()
  },

  getReceipt: (id: number): Promise<Receipt> =>
    request(`/api/v1/receipts/${id}`),

  listReceipts: (page = 1, pageSize = 20, status?: string): Promise<ReceiptListResponse> => {
    const params = new URLSearchParams({ page: String(page), per_page: String(pageSize) })
    if (status) params.set('status', status)
    return request(`/api/v1/receipts?${params}`)
  },

  analyzeReceipt: (id: number): Promise<Receipt> =>
    request(`/api/v1/receipts/${id}/analyze`, { method: 'POST', body: '{}' }),

  reviewReceipt: (
    id: number,
    decision: 'approved' | 'rejected',
    note?: string,
  ): Promise<ReviewResponse> =>
    request(`/api/v1/receipts/${id}/review`, {
      method: 'PATCH',
      body: JSON.stringify({ decision, note }),
    }),
}
