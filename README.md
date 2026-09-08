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

### API Endpoints (`/api/v1/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/receipts/upload` | Upload a receipt image (PNG, JPG, PDF) |
| `GET` | `/api/v1/receipts/{id}` | Get a receipt with fraud flags |
| `GET` | `/api/v1/receipts` | List receipts (paginated, filterable by status) |
| `GET` | `/api/v1/auth/me` | Current user + business memberships |
| `POST` | `/api/v1/tenants` | Create a business |
| `GET` | `/api/v1/tenants` | List your businesses |
| `GET` | `/api/v1/tenants/{id}/members` | List members of a business |
| `POST` | `/api/v1/tenants/{id}/members` | Add a member by email |
| `DELETE` | `/api/v1/tenants/{id}/members/{user_id}` | Remove a member |

### Auth & multi-tenancy

- Authentication is handled by Supabase Auth (GoTrue). The frontend logs in
  against Supabase and sends the resulting JWT as `Authorization: Bearer <token>`
  on every request.
- Data requests also carry `X-Tenant-ID: <id>` to select the active business.
  FastAPI verifies the JWT, checks the caller's membership in that business, and
  scopes every query by that tenant. `POST /api/v1/tenants` and
  `GET /api/v1/tenants` are the exceptions — they need only the JWT.
- Create a business with `POST /api/v1/tenants` (you become its owner). Add
  teammates with `POST /api/v1/tenants/{id}/members` — they must already have a
  Supabase account.
- Receipt images are stored in a Supabase Storage bucket named `receipts`, keyed
  by `{tenant_id}/{uuid}.{ext}`.
- Row-Level Security is not yet enabled; tenant isolation is enforced in the
  application layer. Adding RLS as defense-in-depth is a Phase 2 task.

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

### Environment

Copy `backend/.env.example` to `backend/.env` and fill in, from your Supabase
project dashboard:

- `DATABASE_URL` — the **pooled** connection string (port 6543), for the app
- `DATABASE_URL_DIRECT` — the **direct** connection string (port 5432), for Alembic
- `SUPABASE_URL`, `SUPABASE_JWT_SECRET`, `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_STORAGE_BUCKET` (default `receipts` — create this bucket, not public)

Run `cd backend && alembic upgrade head` to apply migrations.

## What's Next

- [ ] Tesseract OCR service — extract text from receipt images
- [ ] Receipt parser — pull out merchant, amount, date
- [ ] Duplicate detection — perceptual hashing (pHash)
- [ ] Policy validator — configurable rule checks
- [ ] Fraud scorer — combine signals into a 0–100 risk score
- [ ] React frontend — upload form and results display
- [ ] Unit + integration tests

## Project Docs

- [`PROJECT.md`](PROJECT.md) — goals, tech stack, success metrics
- [`IMPLEMENTATION.md`](IMPLEMENTATION.md) — architecture and technical decisions
- [`TODO.md`](TODO.md) — full task breakdown by semester
