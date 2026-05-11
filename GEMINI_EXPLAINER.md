# GEMINI_EXPLAINER.md

## Overview
This document covers the "Why this score?" AI explanation feature built on top of
the existing fraud detection pipeline. Read IMPLEMENTATION.md and README.md first
for full system context before implementing anything here.

## What This Feature Does
On the Receipt Detail page, a button labeled "Why this score?" appears for any
receipt that has at least one fraud flag. Clicking it calls the backend which
sends the receipt's fraud data to Gemini 2.5 Flash and returns a 2-3 sentence
plain English explanation of why the receipt received that risk score. The result
is cached so Gemini is only called once per receipt.

## Model
Gemini 2.5 Flash — gemini-2.5-flash

## Backend

### New endpoint
POST /api/v1/receipts/{id}/explain

- Checks if explanation is already cached on the receipt record
- If cached, returns it immediately without calling Gemini
- If not cached, builds prompt from receipt fields and fraud flags,
  calls Gemini, stores result, returns it
- Rate limited to 5 requests per day globally using SlowAPI
  (no auth yet so limit is per-IP for now, switches to per-user in Phase 2)
- Only callable on receipts that have at least one fraud flag
- Returns 400 if receipt has no flags (nothing to explain)

### Database change
Add explanation TEXT column to receipts table.
Add a new Alembic migration — do not modify existing migrations.

Receipt model addition:
  explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

### Prompt structure
Build the prompt from structured data, not raw OCR text.
Include: merchant, amount, date, risk score, risk level, and each flag's
type, severity, and description. Ask for 2-3 sentences in plain English
written for a non-technical reviewer. Do not use bullet points in the response.

Example prompt shape:
  "A receipt from [merchant] for $[amount] on [date] received a fraud risk
  score of [score]/100 ([risk_level]). The following issues were detected:
  [flag descriptions]. In 2-3 sentences, explain to a non-technical reviewer
  why this receipt was flagged and what specifically looks suspicious."

### Rate limiting
Use SlowAPI
Limit the explain endpoint specifically: 5 requests per day per IP.
All other endpoints keep existing behavior — do not add rate limiting
to upload, list, or detail endpoints at this stage.

Add to requirements.txt: slowapi

### Gemini API key
Add to .env and .env.example:
  GEMINI_API_KEY=your-key-here

Add to config.py as an optional setting so the server starts without it
and returns a clear error if the endpoint is called without a key configured.

### Error handling
- No GEMINI_API_KEY configured → 503 with clear message
- Receipt has no fraud flags → 400
- Gemini call fails → 502, do not cache failed responses
- Rate limit exceeded → 429

## Frontend
The explain button lives on the Receipt Detail page only.
See FRONTEND.md for the page layout context.

Button behavior:
- Label: "Why this score?" when explanation is not yet loaded
- Only rendered if the receipt has at least one fraud flag
- On click: calls POST /api/v1/receipts/{id}/explain
- Show a loading spinner inline while waiting (Gemini can take 2-3 seconds)
- On success: render the explanation text below the fraud flags section
  in a clean bordered box, styled like a callout, no special colors
- Button label changes to "Hide explanation" after loading
- Subsequent clicks toggle visibility without re-fetching
  (explanation is stored in component state after first load)
- On error: show a small inline error message, do not crash the page
- If explanation already exists on the receipt object from the initial
  GET /api/v1/receipts/{id} response, render it pre-loaded and skip the fetch

## Caching strategy
- First call: Gemini is called, result stored in receipts.explanation column
- All subsequent calls: backend returns cached value instantly
- No expiration for now — explanations are stable for a given set of flags
- If receipt is re-analyzed (POST /{id}/analyze), clear the cached explanation
  so it regenerates on next request against the new flags

## What not to build
- Do not auto-generate explanations on upload or analyze
- Do not add explanation to the receipts list table
- Do not add any streaming — wait for the full response
- Do not add this to the Dashboard page
- Do not add per-user rate limiting until Phase 2 auth is added