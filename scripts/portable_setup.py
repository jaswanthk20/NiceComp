"""No-Docker review option. Explicitly different from Supabase/Ollama acceptance testing."""

from pathlib import Path
import secrets
import sys

root = Path(__file__).resolve().parents[1]
config = root / ".env"
if config.exists():
    raise SystemExit(
        ".env already exists. Preserve it; use the documented manual portable settings if needed."
    )
(root / ".local").mkdir(exist_ok=True)
config.write_text(
    f"""APP_ENV=development
DATABASE_URL=sqlite:///{(root / ".local/review.db").as_posix()}
AUTH_PROVIDER=development
STORAGE_PROVIDER=local
PRIVATE_STORAGE_DIR={(root / ".local/private").as_posix()}
DEV_TOKEN_SECRET={secrets.token_urlsafe(48)}
API_BASE_URL=http://127.0.0.1:8000
EMBEDDING_PROVIDER=development
CHAT_PROVIDER=extractive
EMAIL_PROVIDER=mailpit
SMTP_HOST=127.0.0.1
SMTP_PORT=1025
CORS_ORIGINS=http://localhost:8081,http://127.0.0.1:8081
""",
    encoding="utf-8",
)
print("Portable review configured. This does not validate Supabase RLS or local LLM inference.")
