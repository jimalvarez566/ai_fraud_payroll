import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app import supabase_client
from app.auth import RequestContext, get_current_context
from app.config import settings
from app.database import get_db
from app.models.receipt import Receipt
from app.schemas.receipt import ReceiptListResponse, ReceiptResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}
CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".pdf": "application/pdf",
}


@router.post("/upload", response_model=ReceiptResponse, status_code=201)
async def upload_receipt(
    file: UploadFile,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> Receipt:
    """Upload a receipt image, store it in Supabase Storage, and create a row
    scoped to the caller's active business."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{ext}' not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    contents = await file.read()
    if len(contents) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.MAX_FILE_SIZE_MB}MB",
        )

    object_path = f"{context.tenant_id}/{uuid.uuid4().hex}{ext}"
    try:
        await supabase_client.upload_object(
            object_path, contents, CONTENT_TYPES[ext]
        )
    except Exception as exc:  # storage failure — do not create a row
        logger.error("Storage upload failed for %s: %s", object_path, exc)
        raise HTTPException(status_code=502, detail="File storage failed") from exc

    receipt = Receipt(
        image_path=object_path,
        tenant_id=context.tenant_id,
        submitted_by_user_id=context.user_id,
        status="pending",
    )
    db.add(receipt)
    try:
        await db.flush()
    except Exception:
        await supabase_client.delete_object(object_path)
        raise
    await db.refresh(receipt, attribute_names=["fraud_flags"])

    logger.info(
        "Created receipt %s for tenant %s (%d bytes)",
        receipt.id, context.tenant_id, len(contents),
    )
    return receipt


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: int,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> Receipt:
    """Retrieve a receipt by ID within the caller's active business."""
    result = await db.execute(
        select(Receipt)
        .options(selectinload(Receipt.fraud_flags))
        .where(Receipt.id == receipt_id, Receipt.tenant_id == context.tenant_id)
    )
    receipt = result.scalar_one_or_none()
    if not receipt:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


@router.get("", response_model=ReceiptListResponse)
async def list_receipts(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: str | None = None,
    context: RequestContext = Depends(get_current_context),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List receipts for the caller's active business."""
    query = (
        select(Receipt)
        .options(selectinload(Receipt.fraud_flags))
        .where(Receipt.tenant_id == context.tenant_id)
    )
    count_query = select(func.count(Receipt.id)).where(
        Receipt.tenant_id == context.tenant_id
    )

    if status:
        query = query.where(Receipt.status == status)
        count_query = count_query.where(Receipt.status == status)

    total = (await db.execute(count_query)).scalar_one()
    offset = (page - 1) * per_page
    query = query.order_by(Receipt.created_at.desc()).offset(offset).limit(per_page)
    result = await db.execute(query)
    receipts = list(result.scalars().all())

    return {
        "receipts": receipts,
        "total": total,
        "page": page,
        "per_page": per_page,
    }
