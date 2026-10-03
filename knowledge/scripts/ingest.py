"""Operator CLI: python knowledge/scripts/ingest.py --help. Never auto-approves a document."""

import argparse
import hashlib
import os
from pathlib import Path
import sys
from uuid import UUID

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "services/api"))
os.chdir(ROOT)
from app.db import session_factory
from app.knowledge import download_document, create_document, extract, index_document
from app.models import ProductModel
from app.storage import storage

parser = argparse.ArgumentParser()
parser.add_argument("--url", required=True)
parser.add_argument("--title", required=True)
parser.add_argument("--version", required=True)
parser.add_argument("--family", required=True)
parser.add_argument(
    "--model",
    action="append",
    required=True,
    help="Existing product_models UUID; repeat per verified applicable model",
)
args = parser.parse_args()
ids = [str(UUID(i)) for i in args.model]
raw = download_document(args.url)
with session_factory()() as db:
    if any(not db.get(ProductModel, i) for i in ids):
        raise SystemExit("Unknown model ID")
    doc = create_document(
        db,
        args.title,
        args.url,
        args.version,
        args.family,
        ids,
        raw,
        kind="manual" if raw.startswith(b"%PDF-") else "product_page",
    )
    path = f"knowledge/{doc.id}" + (".pdf" if raw.startswith(b"%PDF-") else ".html")
    if raw.startswith(b"%PDF-"):
        storage().put(path, raw, "application/pdf")
        doc.storage_path = path
    index_document(db, doc, extract(raw))
    db.commit()
    print("Indexed inactive document:", doc.id, "Review source/model scope and activate in admin.")
