from uuid import UUID
import secrets
from datetime import timedelta
import jwt
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from .auth import (
    current_user,
    owner_filter,
    require_customer,
    limiter,
    check_password,
    hash_password,
    issue_dev_token,
)
from .config import settings
from .db import get_db
from .models import (
    DevCredential,
    OwnedProduct,
    ProductModel,
    Product,
    Purchase,
    PurchaseItem,
    Receipt,
    Warranty,
    AuditEvent,
    utcnow,
)
from .schemas import Login
from .domain import warranty_status
from .storage import storage

router = APIRouter()
file_secret = secrets.token_urlsafe(48)
dummy_password_hash = hash_password(secrets.token_urlsafe(32))


def owned(db, user, asset_id):
    asset = db.scalar(
        owner_filter(
            select(OwnedProduct).where(OwnedProduct.id == str(asset_id)),
            OwnedProduct.customer_id,
            user,
        )
    )
    if not asset:
        raise HTTPException(404, "Product not found.")
    return asset


def product_view(db, asset):
    model = db.get(ProductModel, asset.model_id)
    product = db.get(Product, model.product_id)
    item = db.get(PurchaseItem, asset.purchase_item_id)
    purchase = db.get(Purchase, item.purchase_id)
    warranty = db.scalar(select(Warranty).where(Warranty.customer_product_id == asset.id))
    return {
        "id": asset.id,
        "model_id": model.id,
        "model": model.name,
        "name": product.name,
        "family": product.family,
        "serial": asset.serial,
        "purchased_on": purchase.purchased_on,
        "purchase_id": purchase.id,
        "image_url": product.image_url,
        "official_url": product.official_url,
        "warranty": {
            "status": warranty_status(warranty.starts_on, warranty.ends_on)
            if warranty
            else "Unknown",
            "starts_on": warranty.starts_on if warranty else None,
            "ends_on": warranty.ends_on if warranty else None,
            "basis": warranty.basis if warranty else None,
            "message": None
            if warranty and warranty.ends_on
            else "Warranty information is not currently available. Please contact Nice Compressors.",
        },
    }


@router.post("/auth/development-login")
def development_login(body: Login, request: Request, db=Depends(get_db)):
    if settings().auth_provider != "development" or settings().app_env == "production":
        raise HTTPException(404)
    limiter.check(("login", request.client.host), maximum=10, window=60)
    credential = db.scalar(select(DevCredential).where(DevCredential.email == body.email.lower()))
    valid = check_password(
        body.password, credential.password_hash if credential else dummy_password_hash
    )
    if not credential or not valid:
        raise HTTPException(401, "Email or password is incorrect.")
    return {"access_token": issue_dev_token(credential.user_id), "token_type": "bearer"}


@router.get("/config")
def config():
    cfg = settings()
    return {
        "environment": cfg.app_env,
        "auth_provider": cfg.auth_provider,
        "supabase_url": cfg.supabase_url,
        "supabase_anon_key": cfg.supabase_anon_key,
        "portable_review": cfg.embedding_provider == "development",
    }


@router.get("/me")
def me(user=Depends(current_user), db=Depends(get_db)):
    return {"id": user.id, "name": user.name, "role": user.role, "mapped": bool(user.customer_id)}


@router.get("/products")
def products(user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    # Staff portal uses admin routes to see other customers; personal portal is always scoped.
    return [
        product_view(db, a)
        for a in db.scalars(
            select(OwnedProduct).where(OwnedProduct.customer_id == user.customer_id)
        ).all()
    ]


@router.get("/products/{asset_id}")
def product(asset_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    return product_view(db, owned(db, user, asset_id))


@router.get("/purchases")
def purchases(user=Depends(current_user), db=Depends(get_db)):
    require_customer(user)
    return db.scalars(
        select(Purchase)
        .where(Purchase.customer_id == user.customer_id)
        .order_by(Purchase.purchased_on.desc())
    ).all()


@router.get("/purchases/{purchase_id}")
def purchase(purchase_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    order = db.scalar(
        owner_filter(
            select(Purchase).where(Purchase.id == str(purchase_id)), Purchase.customer_id, user
        )
    )
    if not order:
        raise HTTPException(404, "Purchase not found.")
    items = db.scalars(select(PurchaseItem).where(PurchaseItem.purchase_id == order.id)).all()
    return {
        "purchase": order,
        "items": [
            {
                "id": i.id,
                "quantity": i.quantity,
                "amount": i.amount,
                "model": db.get(ProductModel, i.model_id).name,
            }
            for i in items
        ],
        "products": [
            product_view(db, a)
            for a in db.scalars(
                select(OwnedProduct).where(OwnedProduct.purchase_item_id.in_([i.id for i in items]))
            ).all()
        ],
        "receipts": [
            {"id": r.id, "name": r.name}
            for r in db.scalars(select(Receipt).where(Receipt.purchase_id == order.id)).all()
        ],
    }


def private_link(path, content_type):
    if settings().storage_provider == "supabase":
        return {"url": storage().signed_url(path), "expires_in": 120}
    token = jwt.encode(
        {
            "path": path,
            "mime": content_type,
            "exp": utcnow() + timedelta(seconds=120),
            "aud": "private-file",
        },
        file_secret,
        algorithm="HS256",
    )
    return {"url": settings().api_base_url + "/files/" + token, "expires_in": 120}


@router.get("/receipts/{receipt_id}/url")
def receipt_url(receipt_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    receipt = db.scalar(
        owner_filter(
            select(Receipt).join(Purchase).where(Receipt.id == str(receipt_id)),
            Purchase.customer_id,
            user,
        )
    )
    if not receipt:
        raise HTTPException(404, "Receipt not found.")
    db.add(AuditEvent(actor_id=user.id, action="receipt.view", resource_id=receipt.id))
    return private_link(receipt.storage_path, "application/pdf")


@router.get("/files/{token}")
def file_content(token: str):
    if settings().storage_provider != "local" or settings().app_env == "production":
        raise HTTPException(404)
    try:
        payload = jwt.decode(token, file_secret, algorithms=["HS256"], audience="private-file")
        content = storage().get(payload["path"])
    except (jwt.PyJWTError, KeyError, ValueError, FileNotFoundError):
        raise HTTPException(404, "File link expired or unavailable.")
    return Response(
        content,
        media_type=payload["mime"],
        headers={
            "Cache-Control": "no-store",
            "Content-Disposition": "inline",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get("/receipts/{receipt_id}/pages")
def receipt_pages(receipt_id: UUID, user=Depends(current_user), db=Depends(get_db)):
    from .pdf_render import render_receipt

    receipt = db.scalar(
        owner_filter(
            select(Receipt).join(Purchase).where(Receipt.id == str(receipt_id)),
            Purchase.customer_id,
            user,
        )
    )
    if not receipt:
        raise HTTPException(404, "Receipt not found.")
    try:
        raw = storage().get(receipt.storage_path)
        pages = []
        for index, content, width, height in render_receipt(raw):
            path = f"{receipt.storage_path}.page-{index}.jpg"
            if settings().storage_provider != "local":
                path = f"{receipt.storage_path}.{secrets.token_hex(8)}.jpg"
            storage().put(path, content, "image/jpeg")
            pages.append({**private_link(path, "image/jpeg"), "width": width, "height": height})
    except Exception:
        raise HTTPException(503, "Receipt is unavailable. Please retry or contact support.")
    db.add(AuditEvent(actor_id=user.id, action="receipt.render", resource_id=receipt.id))
    return {"pages": pages}
