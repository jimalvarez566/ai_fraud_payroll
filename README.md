# AI-Powered Expense Fraud Detection

Senior capstone project (CPSC 490/491) — an intelligent system that analyzes employee expense receipts to identify fraudulent submissions using computer vision, NLP, and machine learning.

## Stack

- **Backend:** FastAPI (Python 3.11+), SQLAlchemy async, PostgreSQL
- **AI/ML (planned):** Tesseract OCR, Claude API, Gemini Vision, scikit-learn
- **Frontend (planned):** React 18, TypeScript, Tailwind CSS

## What's Built

### Backend foundation (`backend/`)
- FastAPI project structure with async/await throughout
- PostgreSQL database with 4 core tables: `employees`, `receipts`, `fraud_flags`, `policy_rules`
- Alembic migrations for schema management
- Pydantic v2 schemas for request/response validation
- Environment-based configuration with feature flags

### Tesseract OCR Service (`backend/app/services/ocr.py`)
Automatically runs on every receipt upload and extracts:
- **Merchant name** — detected by finding the largest-font line using Tesseract's internal line hierarchy (`image_to_data` level-4 bounding boxes), with boilerplate filtering (URLs, "thank you", payment info) and a receipt zone limit (top 60% of image)
- **Transaction date and time** — regex patterns covering MM/DD/YYYY, YYYY-MM-DD, and month-name formats
- **Total amount** — keyword-anchored search (`total`, `amount due`, `grand total`), falling back to the largest dollar amount on the page
- **Line items** — regex per line, stops at the first footer keyword (`subtotal`, `tax`, `total`) so payment and card info are never included; handles trailing taxability indicators (e.g. Walmart's `X`)

Image preprocessing pipeline applied before all OCR calls:
1. Grayscale conversion
2. Upscale to minimum 1000px width (improves Tesseract accuracy on phone photos)
3. Auto-contrast histogram stretch
4. Sharpening (2×)
5. Binarization (pure black/white threshold)

### API Endpoints (`/api/v1/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/receipts/upload` | Upload receipt → auto-runs OCR → stores extracted data |
| `GET` | `/api/v1/receipts/{id}` | Get a receipt with fraud flags and OCR results |
| `GET` | `/api/v1/receipts` | List receipts (paginated, filterable by status) |

Interactive docs available at `http://localhost:8000/docs` when running locally.

## Local Setup

**Prerequisites:** Python 3.11+, PostgreSQL 15

```bash
# 1. Create database
createdb fraud_detection

# 2. Install dependencies
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env with your database credentials

# 4. Run migrations
alembic upgrade head

# 5. Start server
uvicorn app.main:app --reload
```

## What's Next

- [ ] Duplicate detection — perceptual hashing (pHash)
- [ ] Policy validator — configurable rule checks
- [ ] Fraud scorer — combine signals into a 0–100 risk score
- [ ] React frontend — upload form and results display
- [ ] Unit + integration tests

## Project Docs

- [`PROJECT.md`](PROJECT.md) — goals, tech stack, success metrics
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — architecture and technical decisions
- [`TODO.md`](TODO.md) — full task breakdown by semester
