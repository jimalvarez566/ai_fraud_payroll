# TODO

## Today (Getting Started)
- [ ] Set up FastAPI project structure
- [ ] Create database models (Employee, Receipt, FraudFlag)
- [ ] Set up PostgreSQL locally
- [ ] Create initial Alembic migration
- [ ] Build basic receipt upload endpoint
- [ ] Test file upload with sample receipt image

## This Week (Core MVP)
- [ ] Implement Tesseract OCR service
- [ ] Build receipt text parsing (extract merchant, amount, date)
- [ ] Create perceptual hashing for duplicate detection
- [ ] Implement basic policy validator (2-3 simple rules)
- [ ] Build fraud scoring logic
- [ ] Create analyze endpoint that combines all detectors
- [ ] Write unit tests for fraud detectors

## Next 2 Weeks (MVP Polish)
- [ ] Add proper error handling to API endpoints
- [ ] Implement caching for analysis results
- [ ] Create simple React upload form
- [ ] Build results display page (show fraud flags)
- [ ] Add loading states to frontend
- [ ] Deploy backend to Render
- [ ] Deploy frontend to Vercel
- [ ] Test end-to-end with 20 sample receipts

## Semester 1 Completion (CPSC 490)
- [ ] Document API endpoints in API.md
- [ ] Create test dataset (100 legitimate, 50 fraudulent receipts)
- [ ] Measure and document accuracy metrics
- [ ] Write final report for CPSC 490
- [ ] Prepare demo for presentation
- [ ] Tag release as v1.0-mvp

## Semester 2 - Phase 2 Features (CPSC 491)

### Month 1: Advanced Detection
- [ ] Integrate Gemini Vision API for image analysis
- [ ] Build AI analyzer service (Claude API integration)
- [ ] Implement Isolation Forest anomaly detector
- [ ] Add expense categorization validation
- [ ] Enhance risk scoring with weighted signals
- [ ] Test improved accuracy vs MVP

### Month 2: Analytics Dashboard
- [ ] Create employee statistics aggregation
- [ ] Implement K-means clustering for risk profiles
- [ ] Build time series analysis for fraud trends
- [ ] Create analytics API endpoints
- [ ] Build React analytics dashboard components
- [ ] Add data visualization (charts, heatmaps)

### Month 3: Production Features
- [ ] Add user authentication (JWT)
- [ ] Build fraud review workflow UI
- [ ] Implement export functionality (CSV, PDF)
- [ ] Add API rate limiting
- [ ] Optimize database queries with indexes
- [ ] Set up monitoring and logging

### Month 4: Final Polish
- [ ] Comprehensive testing (unit, integration, e2e)
- [ ] Performance optimization
- [ ] Security audit
- [ ] Final documentation
- [ ] Create demo video
- [ ] Write CPSC 491 final report
- [ ] Tag release as v2.0-production

## Ideas for Future (Post-Graduation)
- [ ] Mobile app (React Native)
- [ ] Integration with Expensify/Concur APIs
- [ ] Multi-tenant support (company accounts)
- [ ] Real-time fraud alerts (email/Slack)
- [ ] Custom ML model training on company data
- [ ] Notion/Linear export integration

## Next (Phase 2 hardening of multi-tenancy)
- [ ] Add Row-Level Security policies on tenant tables (defense-in-depth)
- [ ] Enforce roles (admin vs member) on tenant + policy_rule endpoints
- [ ] Invitation tokens + emails for users without a Supabase account yet
- [ ] Serve receipt images to the frontend via short-lived signed URLs
- [ ] Handle GoTrue admin-list pagination in lookup_user_id_by_email

## Done ✅
- [x] Created PROJECT.md
- [x] Created IMPLEMENTATION.md
- [x] Created TODO.md
- [x] Defined database schema
- [x] Chose tech stack
- [x] Supabase-backed multi-tenant auth foundation (tenants, memberships, JWT verification, Storage)