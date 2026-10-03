# Implementation phases

| Phase | Deliverable | Status |
| --- | --- | --- |
| 1 Research | Public sitemap crawl, product hierarchy, logo, API/version/document findings | Implemented; source limitations documented |
| 2 Architecture | Relational model, API/provider boundaries, schema/RLS/pgvector migrations | Implemented; PostgreSQL runtime acceptance pending |
| 3 Infrastructure | Supabase config, Compose, portable review mode, startup scripts | Portable services exercised; container stack unavailable here |
| 4 Auth / portal | Email sign-in, identity mapping, dashboard, role separation | Portable path exercised; Supabase path pending |
| 5 Purchases | Purchase detail, private receipts, warranty status/adjustment, connector/import path | Synthetic flow exercised; company source unconnected |
| 6 Knowledge | Official-source validation, PDF extraction, chunks, versions/approval | Product excerpt indexed; valid company PDF still needed |
| 7 RAG | Scoped retrieval, exact-excerpt validator, safety escalation, citations/history | Portable retrieval tested; Ollama/pgvector run pending |
| 8 Tickets / SLA | Reviewed chat handoff, photos, category/severity, deadlines, events | Exercised in API and browser tests |
| 9 Email | Transactional outbox, Mailpit/SMTP providers, retry tracking | Real local Mailpit delivery exercised |
| 10 Admin | Ticket review/status, SLA, knowledge, mapping/import/events/records | Browser admin ticket review exercised |
| 11 Automated tests | Pytest and Jest / React Native Testing Library | Executed; report distinguishes skipped integration |
| 12 E2E | Browser receipt → source answer → image ticket → email → admin | Passed in portable mode; native/full-stack pending |
| 13 UI | Official brand asset, touch targets, responsive layout, screenshot inspection | Web desktop/mobile viewport inspected |
| 14 Handover | README, local demo, integration/acceptance docs, test evidence | Delivered with explicit completion limits |
