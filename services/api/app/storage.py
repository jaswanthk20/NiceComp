import io
from pathlib import Path
from typing import Protocol
import httpx
from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException
from .config import settings

MAX_UPLOAD = 8 * 1024 * 1024
Image.MAX_IMAGE_PIXELS = 20_000_000


class PrivateStorage(Protocol):
    def put(self, path: str, content: bytes, content_type: str): ...
    def get(self, path: str) -> bytes: ...
    def signed_url(self, path: str, expires: int = 120) -> str: ...


def clean_photo(data: bytes):
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "Photo must be smaller than 8 MB.")
    try:
        with Image.open(io.BytesIO(data)) as original:
            if original.format not in ("JPEG", "PNG", "WEBP"):
                raise ValueError()
            photo = ImageOps.exif_transpose(original).convert("RGB")
            photo.thumbnail((1920, 1920))
            buffer = io.BytesIO()
            photo.save(buffer, "JPEG", quality=85)
            return buffer.getvalue()
    except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError):
        raise HTTPException(422, "Choose a valid JPEG, PNG or WebP photo.")


class LocalPrivateStorage:
    def __init__(self):
        if settings().app_env == "production":
            raise RuntimeError("Local storage is development only")
        self.root = Path(settings().private_storage_dir).resolve()

    def path(self, path):
        target = (self.root / path).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("Invalid storage path")
        return target

    def put(self, path, content, content_type):
        target = self.path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)

    def get(self, path):
        return self.path(path).read_bytes()

    def signed_url(self, path, expires=120):
        raise NotImplementedError("Portable review streams authorized files through the API")


class SupabasePrivateStorage:
    def __init__(self):
        self.base = settings().supabase_url + "/storage/v1"
        self.headers = {"Authorization": "Bearer " + settings().supabase_service_role_key}

    def put(self, path, content, content_type):
        response = httpx.post(
            self.base + "/object/private-support/" + path,
            content=content,
            headers={**self.headers, "Content-Type": content_type},
            timeout=30,
        )
        response.raise_for_status()

    def get(self, path):
        response = httpx.get(
            self.base + "/object/private-support/" + path, headers=self.headers, timeout=30
        )
        response.raise_for_status()
        return response.content

    def signed_url(self, path, expires=120):
        response = httpx.post(
            self.base + "/object/sign/private-support/" + path,
            json={"expiresIn": expires},
            headers=self.headers,
            timeout=10,
        )
        response.raise_for_status()
        return self.base + response.json()["signedURL"]


def storage() -> PrivateStorage:
    return (
        LocalPrivateStorage()
        if settings().storage_provider == "local"
        else SupabasePrivateStorage()
    )
