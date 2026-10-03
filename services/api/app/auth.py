import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID
import httpx
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .config import settings
from .db import get_db, apply_identity
from .models import Profile, utcnow

bearer = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex()
    return salt + ":" + digest


def check_password(password: str, stored: str) -> bool:
    salt, digest = stored.split(":")
    return hmac.compare_digest(
        hashlib.scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1).hex(), digest
    )


@dataclass
class Identity:
    id: str
    customer_id: str | None
    name: str
    role: str


def current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer), db=Depends(get_db)
):
    if not credentials:
        raise HTTPException(401, "Please sign in.")
    cfg = settings()
    try:
        if cfg.auth_provider == "development":
            payload = jwt.decode(
                credentials.credentials,
                cfg.dev_token_secret,
                algorithms=["HS256"],
                audience="nicecomp-dev",
                issuer="nicecomp-dev",
                options={"require": ["sub", "exp", "iat"]},
            )
            user_id = str(UUID(payload["sub"]))
        else:
            response = httpx.get(
                cfg.supabase_url + "/auth/v1/user",
                headers={
                    "apikey": cfg.supabase_anon_key,
                    "Authorization": "Bearer " + credentials.credentials,
                },
                timeout=10,
            )
            if response.status_code != 200:
                raise ValueError("Invalid session")
            user_id = str(UUID(response.json()["id"]))
    except (jwt.PyJWTError, ValueError, KeyError):
        raise HTTPException(401, "Your session has expired. Please sign in again.")
    except httpx.HTTPError:
        raise HTTPException(503, "Sign-in service is unavailable. Please retry.")
    apply_identity(db, user_id)
    profile = db.get(Profile, user_id)
    if not profile:
        raise HTTPException(403, "Your account is awaiting customer association. Contact support.")
    return Identity(profile.id, profile.customer_id, profile.display_name, profile.role)


def staff(user=Depends(current_user)):
    if user.role not in ("admin", "support"):
        raise HTTPException(403, "Support access required.")
    return user


def admin(user=Depends(current_user)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator access required.")
    return user


def owner_filter(query, column, user):
    return query if user.role in ("admin", "support") else query.where(column == user.customer_id)


def require_customer(user):
    if not user.customer_id:
        raise HTTPException(403, "Your account needs a verified customer association.")


def issue_dev_token(user_id):
    now = utcnow()
    return jwt.encode(
        {
            "sub": user_id,
            "iat": now,
            "exp": now + timedelta(hours=2),
            "aud": "nicecomp-dev",
            "iss": "nicecomp-dev",
        },
        settings().dev_token_secret,
        algorithm="HS256",
    )


class RateLimiter:
    """Per-process protection; deploy one worker or add gateway-wide limits."""

    def __init__(self):
        self.hits = {}

    def check(self, key, maximum=20, window=60):
        now = time.monotonic()
        self.hits = {
            k: [t for t in v if now - t < window]
            for k, v in self.hits.items()
            if v and now - v[-1] < window
        }
        hits = self.hits.setdefault(key, [])
        if len(hits) >= maximum:
            raise HTTPException(429, "Too many requests. Please wait and retry.")
        hits.append(now)


limiter = RateLimiter()
