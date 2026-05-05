# Frontend Implementation

## Overview
React 18 + TypeScript frontend for the AI-powered expense fraud detection system.
Connects to the FastAPI backend at the URL defined in `VITE_API_URL`.
This is a prototype — pages should be functional and clean, not feature-complete.

## Tech Stack
- React 18 with TypeScript
- Vite
- Tailwind CSS
- shadcn/ui for components
- React Router for navigation

## Design Direction
Fintech SaaS tool. Reference: Stripe, Vercel, Linear.
This is used by someone doing a job, not a marketing page.

Rules:
- Dark neutral background (#0a0a0a or similar), light text
- Clean sans-serif typography, monospace for all numbers, amounts, scores, and IDs
- Risk indicators are the only place color is used prominently: red (high), yellow (medium), green (low)
- No gradients, no hero sections, no decorative illustrations
- Borders over shadows
- Dense and informative, not spacious and decorative
- Sidebar navigation, not top navbar

## Pages

### Dashboard `/`
- Summary cards: total receipts, high risk count, medium risk count, low risk count
- Keep it minimal, just enough to orient the user
- Data from `GET /api/v1/receipts` aggregated on the frontend for now

### Receipts List `/receipts`
- Table pulling from `GET /api/v1/receipts`
- Columns: ID, merchant, amount, date, risk score, status badge, view button
- Amounts and scores in monospace
- Status badges: pending (neutral), flagged (red), approved (green), rejected (gray)
- Paginated using the API's built-in pagination
- Filterable by status

### Receipt Detail `/receipts/:id`
- Data from `GET /api/v1/receipts/:id`
- Top section: fraud score displayed large in monospace, colored by risk level
- OCR fields: merchant, amount, date, line items in a clean structured layout
- Fraud flags section: each flag shows type, severity, description, confidence score
- If receipt has a duplicate flag, surface original_receipt_id as a clickable link
- Approve / Reject buttons calling `PATCH /api/v1/receipts/:id/review`
- Re-analyze button calling `POST /api/v1/receipts/:id/analyze`

### Upload `/upload`
- Clean file drop zone
- Accepted formats: PNG, JPG, PDF
- Calls `POST /api/v1/receipts/upload`
- Show loading state while pipeline runs (OCR takes a few seconds)
- On success, redirect to `/receipts/:id` for the new receipt
- No animations beyond a functional spinner

## API
Base URL stored in `.env` as `VITE_API_URL=http://localhost:8000`
All calls use fetch with async/await.
Handle loading and error states on every page.

## Conventions
- One component per file
- Pages live in `src/pages/`, shared components in `src/components/`
- No component libraries beyond shadcn/ui
- No features or pages beyond what is listed above
- Keep it prototype-quality: functional and clean, not polished