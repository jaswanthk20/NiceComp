# Local demonstration

This is a management-review prototype. All login accounts, purchases, serials, receipts and warranty dates below are synthetic. The ECO 10A product excerpt is from the official product page. No service manual or official SLA is invented.

## Already running on the delivery laptop

- App: [http://127.0.0.1:8081](http://127.0.0.1:8081)
- Captured email: [http://127.0.0.1:8025](http://127.0.0.1:8025)
- API reference: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

These local services were started for this review and must be restarted after the laptop/session stops. The prepared `.env` uses **portable mode** because Docker and Ollama were unavailable. It uses SQLite, development authentication, private local files and deterministic document excerpts. It does not demonstrate Supabase RLS or LLM inference.

| Role | Email | Development-only password |
| --- | --- | --- |
| Customer | `customer@nicecomp.test` | `Review-Only-2026!` |
| Administrator | `admin@nicecomp.test` | `Review-Only-2026!` |
| Isolation-test customer | `other@nicecomp.test` | `Review-Only-2026!` |

## Fresh portable setup (without Docker)

Install Node.js 22.13+ and Python 3.12+. Download the [Mailpit release for your platform](https://github.com/axllent/mailpit/releases). The tested Windows capture binary was v1.31.3. From the source folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r services/api/requirements.txt
npm ci
.\.venv\Scripts\python.exe scripts/portable_setup.py
.\.venv\Scripts\python.exe scripts/seed.py
```

`portable_setup.py` creates a random local auth secret and refuses to overwrite an existing `.env`. It does not enable production mode. If using the already prepared folder, preserve its `.env` and skip that step.

On Windows, the optional `scripts/install-mailpit.ps1` downloads the pinned v1.31.3 executable into `.local/mailpit` and verifies its SHA-256 before extraction. Start that local copy in a terminal:

```powershell
.\.local\mailpit\mailpit.exe --listen 127.0.0.1:8025 --smtp 127.0.0.1:1025
```

Start the remaining services from the project root:

```powershell
npm run dev
```

For the full Supabase + Ollama stack instead, follow the installation section in [README.md](README.md). Do not mix the portable `.env` with the full-stack settings. Migrate/reseed explicitly when switching; no automatic production data migration is performed.

## Laptop review walkthrough

1. Open the app and sign in as the test customer.
2. Home displays the test equipment, warranty count and open tickets.
3. Open **My purchases → View purchase details → View receipt**. The synthetic receipt renders inside the app.
4. Open **Products → View product**. Check model, test serial, purchase date and clearly synthetic warranty information.
5. Select **Ask NICE AI**. Ask **“What is the tank capacity?”**. The answer uses the scoped official product-table excerpt and retains its source link.
6. Ask **“What oil should I use?”**. There is no verified oil specification in the available material, so the system declines to invent one and offers support.
7. Choose **Issue unresolved? Create ticket**. The last question is carried into an editable description. Chat context is shared only if the customer explicitly enables the review toggle.
8. Describe the issue, choose category/severity, select **Choose photo**, attach a safe diagnostic image and submit. No machine intervention is needed for a demonstration. On mobile, **Take photo** is also available.
9. The ticket page shows its number, state, image and timeline. Test SLA deadlines are calculated internally but the customer sees that official response targets await company configuration.
10. Open Mailpit. Find the message addressed to `support@nicecomp.test`, with the ticket number and priority in its subject. No message is sent to Nice Compressors.
11. Sign out and sign in as the test administrator. Open **Admin → Tickets**, find the ticket, inspect its private images and acknowledge it with a timeline note.
12. Review **SLA rules**, **Knowledge**, **Integrations** and **Records**. Leave sample rules unapproved. Do not activate a document without checking its actual model applicability.

## Android phone

1. Install Expo Go and connect phone/laptop to the same private Wi-Fi.
2. Find the laptop LAN IPv4 address with `ipconfig`.
3. In `apps/mobile/.env`, set `EXPO_PUBLIC_API_BASE_URL=http://LAPTOP-IP:8000`.
4. In root `.env`, set `API_BASE_URL=http://LAPTOP-IP:8000` so temporary file URLs are reachable. Set `WEB_BASE_URL=http://LAPTOP-IP:8081`. For browser review over LAN also add that origin to `CORS_ORIGINS`.
5. Restart the API/Expo. `npm run dev` binds the API to `0.0.0.0`; permit private-network access to ports 8000/8081 when Windows asks. Do not expose the services on a public network.
6. Run `npm run mobile` if Expo is not already running, and scan its QR code in Expo Go. Use the same test login.

For an Android emulator, use `http://10.0.2.2:8000` instead of the LAN address. Expo Go must support SDK 57; check the installed version. A native development build is the fallback if it does not.

## iPhone

Use the same LAN configuration, install compatible Expo Go, and scan the Expo QR code with the iPhone camera. No App Store publication is required. The laptop cannot run an iOS simulator on Windows. Camera/library permissions and the full flow remain unverified on a physical iPhone in this delivery.

## Full-stack acceptance still required

Repeat this exact flow using Supabase authentication/PostgreSQL/private storage and Ollama embeddings/chat after starting Docker and downloading the models. Obtain a verified official manual from the company, associate it with the exact model, ingest/approve it, and repeat a manual-based question. The current demonstration uses a product page, so it does not satisfy the requested **official-manual** step of the final definition of done.

## Stop and restart

For services started by `npm run dev`, press Ctrl+C in that terminal; stop Mailpit in its terminal. Docker services stop with `docker compose stop`; Supabase stops with `npx supabase stop`. Synthetic local records remain in `.local/` until explicitly removed. Do not reuse portable credentials or `.env` in production.
