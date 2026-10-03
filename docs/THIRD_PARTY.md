# Assets and dependency notes

- The NICE COMP logo remains Nice Compressors' asset. Its unchanged embedded PNG was recovered from the official website logo endpoint for this requested internal prototype. Release/distribution permission must be confirmed with the company.
- Public product text snapshots are research material with their original URLs recorded. They are not an approved complete technical knowledge base and do not grant rights to redistribute company manuals.
- Icons are from Expo's Ionicons integration; dependency licenses remain with their respective packages.
- PDF rendering uses pypdfium2/PDFium; preserve the package's license and bundled third-party notices when redistributing its binary. PDF text extraction uses pypdf.
- The source archive excludes dependency binaries, secrets, private storage, generated databases and installed runtimes. Reproduce dependencies from the lockfile and requirements file.

## Dependency audit at development time

The npm audit reported multiple inherited advisories, primarily rooted in `braces`, `node-forge`, `decode-uri-component` and an older transitive `uuid`. Many reported packages are affected through the same build/test dependency chain. The latest versions queried for `braces` (3.0.3) and `node-forge` (1.4.0) were still within the reported vulnerable ranges. npm's suggested forced fix included downgrading Expo to SDK 44, which would break the chosen current Expo stack; that downgrade was not applied.

Do not interpret passing application tests as a clean security audit. The final dependency summary is retained in `docs/dependency-audit-summary.json`. Resolve upstream updates or explicitly evaluate/package replacements before production. In particular, keep Metro and development servers on a trusted local network. A full production security review is outstanding.
