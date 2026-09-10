import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Layout } from '@/components/Layout'
import { Upload } from '@/pages/Upload'
import { ReceiptsList } from '@/pages/ReceiptsList'
import { ReceiptDetail } from '@/pages/ReceiptDetail'
import { Dashboard } from '@/pages/Dashboard'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Dashboard />} />
          <Route path="/receipts" element={<ReceiptsList />} />
          <Route path="/receipts/:id" element={<ReceiptDetail />} />
          <Route path="/upload" element={<Upload />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
