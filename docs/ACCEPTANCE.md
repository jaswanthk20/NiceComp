# Acceptance status

The project is a functional, inspectable **local prototype**, not a completed production deployment. The original definition of done is intentionally not claimed because several required checks depend on unavailable company information or local infrastructure.

| Requirement area | Implemented / observed | Outstanding acceptance |
| --- | --- | --- |
| Company research | 215 public pages inventoried; exact official logo; category hierarchy | Company brand/name approval and catalogue reconciliation |
| Mobile / web | Expo Router screens, responsive web, strict TypeScript | Physical Android/iPhone, native camera/permissions and Expo Go compatibility |
| Authentication | Supabase auth path; isolated development auth exercised | Real Supabase login/refresh/device session acceptance |
| Data security | Ownership tests, private files, RLS migrations, restricted API role | Execute RLS/private Supabase storage tests on running local Supabase |
| Purchases / receipts | Real persistence, private PDF rendering, synthetic E2E | Verified company export and source reconciliation |
| Warranties | Actual-date/evidence fields, status engine, admin adjustment | Approved automatic purchase-policy derivation rules |
| RAG | Ingestion, chunks/provenance, model scope, pgvector query, provider interfaces | Run pgvector/Ollama stack and evaluate company manual questions |
| Documentation | Official product-page excerpt answers correctly | Valid official manuals were not obtainable from discovered public PDF links |
| Safety | Deterministic hazard routing and whole-excerpt grounding | Technician-reviewed evaluation set; no claim of exhaustive fault detection |
| Tickets | Photo upload, idempotent creation, timeline, tracking | Native-device test and production retention policy |
| SLA | Business hours/timezone, severity, official-policy switch, internal escalation events | Approved values, holidays/split shifts and any multi-recipient escalation routing |
| Email | Actual Mailpit SMTP capture passed; durable retries | Confirmed recipient, production SMTP/domain setup; at-least-once semantics reviewed |
| Admin | Ticket status, policy, knowledge approval, mapping/import, event views | Staff workflows tested with actual roles/data |
| Odoo | Version-appropriate gated JSON-2 connector and CSV path | API plan/key/database/schema and deployment-specific relational mapping |
| Dependencies | Lockfile, tests and audit inspection | Unresolved transitive advisories must be remediated/assessed before release |

## Why the full-stack test is pending

No Docker or Ollama executable was available in the delivery environment. The Supabase CLI configuration and migrations are supplied, but a CLI without its container engine cannot start local Supabase. PostgreSQL SQL was parsed successfully; parsing is not evidence that RLS or vector queries execute correctly. The browser demonstration used SQLite, local private storage, synthetic development auth and deterministic document excerpts. These differences are visible in the app and prohibited by production configuration checks.

## Manual-based AI acceptance

The public site's two advertised PDF URLs returned HTML. The company must supply the relevant manuals, document versions and exact model applicability. Then ingest, index, review and activate them. Run the full customer-to-ticket flow with a real manual question and inspect the returned page/source references. The current product-page demonstration does not count as this manual-based acceptance.

## Release checklist

1. Start the full local Supabase/Ollama stack and execute its security/inference tests.
2. Run the same browser flow plus physical Android/iPhone review.
3. Resolve or formally assess dependency advisories; verify every deployed lockfile/container image.
4. Obtain manuals, approved policy, support recipient and brand/name approval.
5. Activate and reconcile the Odoo/CSV integration using verified data and least-privilege credentials.
6. Add company retention/deletion requirements, centralized rate limits, backup/restore monitoring and deployment controls.
7. Remove development fixtures/providers from production; verify startup rejects them.

No cloud service, store listing, production email destination or private Odoo installation was deployed or activated during this work.
