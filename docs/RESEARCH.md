# Company research — observed 2026-10-02

Research preceded implementation. The main website could not be retrieved by the search tool, so its public pages were downloaded directly over HTTPS. The sitemap inventory contains **215 URLs, all returning HTTP 200 during the crawl**. A 200 response does not prove that a linked file is valid: both brochure URLs returned HTML.

## Verified public structure

The home/navigation presents reciprocating air compressors, rotary screw compressors, spare parts, air receivers and refrigerated air driers. The Odoo shop divides reciprocating products further:

| Public category | Official source |
| --- | --- |
| Single-stage reciprocating | https://www.nicecompressors.net/shop/category/single-stage-reciprocating-air-compressor-2 |
| Two-stage reciprocating | https://www.nicecompressors.net/shop/category/two-stage-reciprocating-air-compressor-1 |
| Rotary screw | https://www.nicecompressors.net/shop/category/rotary-screw-compressor-3 |
| Spare parts | https://www.nicecompressors.net/shop/category/spare-parts-4 |
| Refrigerated air drier | https://www.nicecompressors.net/shop/category/refrigerated-air-drier-5 |
| Air receiver | https://www.nicecompressors.net/shop/category/air-receiver-6 |

The catalogue contains LC single-stage models, two-stage offerings, ECO screw-compressor variants, motors, receivers, dryers and many individual spare parts. The rotary page has combined variant columns, including ECO10A/ECO10B. This is why a model filter alone is insufficient if a whole comparison table is ingested into one chunk. The supplied reviewed excerpt isolates the ECO 10A tank capacity and shared column values. Ambiguous flow/unit data and dimensions are deliberately not promoted into the demonstration knowledge.

The sitemap includes product pages, category pages, contact pages, terms/privacy, FAQs, support/helpdesk and two educational blog posts. `knowledge/research-index.json` stores URLs, titles, response status, hashes, extracted-file names, discovered PDF links and candidate images. `knowledge/research/` contains readable snapshots; none are automatically activated for retrieval.

## Branding and assets

Official home: https://www.nicecompressors.net/

Official logo endpoint: https://www.nicecompressors.net/web/image/website/1/logo

That endpoint returned an SVG containing an embedded PNG. The PNG was extracted without redrawing, recoloring or altering it, and is stored as `apps/mobile/assets/official-logo.png`. The observed logo combines blue, white, charcoal and a yellow border. UI tokens use blue/navy, white and light grey; the official logo retains its yellow accent.

Product images exist on shop pages; the inventory preserves their URLs. A verified photo for the exact ECO 10A demonstration variant was not established, so its card shows a neutral equipment icon rather than a different machine mislabeled as ECO 10A. Admin → Records supports a verified official model image URL. Company approval is still required for release branding and use of its assets.

## Contact, warranty and maintenance

- Contact page: https://www.nicecompressors.net/contact-us
- Public email addresses observed: `info@nicecompressors.net`, `nicecompressors@gmail.com`.
- Public navigation phone/WhatsApp observed: `+91 9986008433`.
- Contact hours displayed: Monday–Saturday, 9:00 AM–5:30 PM. These contact hours are not treated as an approved SLA calendar.
- Terms page: https://www.nicecompressors.net/term-condition
- FAQ page: https://www.nicecompressors.net/faq
- Help page: https://www.nicecompressors.net/help

The terms page describes a one-year manufacturer warranty with usage/handling exclusions and consumables excluded. That public statement does not supply serial-specific eligibility, commencement rules, purchase history or an approved automated warranty policy. The app therefore requires actual dates/evidence and never assigns that duration to real purchases by assumption.

The FAQ page lists topics such as oil level, air-filter cleaning, belt alignment, pressure-switch adjustment and running direction. Topic headings alone are not validated technical procedures. In particular, pressure-switch adjustments are not converted into chatbot instructions.

## Documents and limitations

The only PDF links discovered in the public sitemap crawl were:

- https://www.nicecompressors.net/pdf/LC-015A-brochure.pdf
- https://www.nicecompressors.net/pdf/LC-015B-brochure.pdf

Both returned HTML beginning with `<!DOCTYPE html>`, not PDF magic bytes. They were rejected as manuals. No valid downloadable service manual was verified. A publicly undiscovered, authenticated or unpublished document may still exist; the inventory does not prove absence. The company must provide approved manuals/catalogues and model applicability before technical-maintenance acceptance.

The current demo answer comes from https://www.nicecompressors.net/rotary-screw-compressor and is labeled as a product-page excerpt, never as a manual. Source name, version and URL are retained; there is no invented page number for HTML.

## Odoo evidence

The home HTML identifies Odoo and exposes public session metadata reporting `saas~19.3+e`. Public links also use `nice-compressors-company6.odoo.com`. This establishes website technology, not installed private business modules, API entitlement, database name or customer data access.

The official Odoo 19 documentation describes JSON-2 at `/json/2/<model>/<method>`, bearer API keys, optional database header, and database-specific model/field documentation at `/doc`. It states that external API access requires an eligible Custom plan. Source: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

See [ODOO.md](ODOO.md) for the exact activation checklist. No private customer data was requested or scraped, and no real company email was sent.
