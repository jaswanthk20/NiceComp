# Executed validation report

Validation session: **2026-10-02, America/Toronto**. Counts refer to the final collected test cases, not repeated runs during development.

| Suite | Total | Passed | Failed | Skipped |
| --- | ---: | ---: | ---: | ---: |
| Pytest backend | 74 | 73 | 0 | 1 |
| Jest / React Native Testing Library | 8 | 8 | 0 | 0 |
| Playwright web flows | 3 | 3 | 0 | 0 |
| **Combined** | **85** | **84** | **0** | **1** |

Machine-readable evidence: [backend-results.xml](backend-results.xml), [ui-results.json](ui-results.json), [e2e-results.json](e2e-results.json).

## What ran

- Backend authentication/invalid token checks, cross-customer product/purchase/receipt/ticket/image isolation, staff endpoint protection and missing customer mapping.
- Active/expired/unknown/expiring warranties; business-hour/timezone/weekend SLA calculation; escalation idempotency; administrative warranty evidence and receipt import.
- Model-scoped retrieval, citations, unsupported specifications, inactive documents, another model's contradictory specification, fabricated model output rejection, safety escalation and persisted history.
- Ticket/photo creation, image-content validation, ticket-number generation, idempotent resubmission, timeline/status transitions, configured/unapproved SLA behavior.
- Email subject/body/recipient policy, secure image-review handling, failed-delivery retry and development recipient enforcement.
- Export validation, synchronization idempotence, missing product mapping, unverified Odoo rejection and simulated API failure.
- UI sign-in validation/error handling, development-data disclosure, authenticated API calls, offline messages and expired sessions.
- Browser flow: customer sign-in → purchase/warranty → private receipt → product → grounded answer/source → reviewed ticket handoff → actual image upload → ticket → **real Mailpit SMTP delivery** → administrator ticket visibility.
- Browser phone viewport and invalid sign-in flows. Runtime errors/text-node warnings are checked on the main browser flow. Screenshots were visually inspected; a rendering warning discovered during QA was corrected and the flow re-run.

## Other executed checks

- `npm run typecheck`: passed with strict TypeScript.
- `npm run build:web`: Expo production web export passed.
- Python Ruff checks/formatting: passed.
- PostgreSQL parser accepted both migration files. This checks SQL syntax only.
- Dependency audit executed: **60 reported affected dependencies (50 high, 10 moderate, 0 critical)**, with repeated inheritance from a smaller set of root advisories. See [dependency-audit-summary.json](dependency-audit-summary.json) and [THIRD_PARTY.md](THIRD_PARTY.md). These remain a production blocker; a passing build is not a clean audit.

## Skipped and unexecuted work

The one collected skipped test requires a running, seeded **local Supabase**. Docker was unavailable. No claim is made that PostgreSQL RLS, Supabase token refresh, Supabase private storage or pgvector execution passed runtime tests. Backend API isolation tests used SQLite and explicit ownership checks.

Ollama was unavailable; browser answers used the clearly labeled deterministic excerpt provider with the official product-page excerpt. LLM inference quality/latency and semantic retrieval remain untested. There was no verified downloadable official manual, so a manual/page-number end-to-end case remains pending.

No physical Android/iPhone or native emulator was connected. The included Maestro smoke-flow file was **not executed** and is not counted among passed tests. Native camera/library permissions and Expo Go behavior require device review. No live Odoo API or production SMTP was tested.

## Scope of the result

The **portable review flow passes**. The original full Supabase/Ollama/official-manual/mobile-device definition of done remains open. [ACCEPTANCE.md](ACCEPTANCE.md) lists the exact dependencies and remaining work.
