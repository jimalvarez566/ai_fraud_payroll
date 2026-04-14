import asyncio
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models.receipt import Receipt
from app.schemas.receipt import ReceiptListResponse, ReceiptResponse
from app.services.ocr import extract_receipt_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/receipts", tags=["receipts"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf"}


@router.post("/upload", response_model=ReceiptResponse, status_code=201)
async def upload_receipt(
    file: UploadFile,
    employee_id: int | None = None,
    db: AsyncSession = Depends(get_db),
) -> Receipt:
    """Upload a receipt image and create a database record.

    Accepts PNG, JPG, or PDF files up to the configured size limit.
    The file is saved to the uploads directory with a unique filename.
    """
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

    # Save file with unique name to prevent collisions
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.upload_path / unique_name
    file_path.write_bytes(contents)

    logger.info("Saved receipt image: %s (%d bytes)", unique_name, len(contents))

    receipt = Receipt(
        image_path=str(file_path),
        employee_id=employee_id,
        status="pending",
    )
    db.add(receipt)
    await db.flush()

    # Run Tesseract OCR in a thread pool so it doesn't block the event loop
    loop = asyncio.get_event_loop()
    ocr = await loop.run_in_executor(None, extract_receipt_data, str(file_path))

    receipt.merchant = ocr.merchant
    receipt.amount = ocr.total_amount
    receipt.transaction_date = ocr.transaction_date
    receipt.items = {
        "line_items": ocr.line_items,
        "transaction_time": ocr.transaction_time,
        "raw_text": ocr.raw_text,
    }
    receipt.ocr_confidence = ocr.confidence
    receipt.ocr_method = "tesseract"
    receipt.analyzed_at = datetime.utcnow()
    receipt.status = "analyzed"

    await db.refresh(receipt, attribute_names=["fraud_flags"])

    return receipt


@router.get("/{receipt_id}", response_model=ReceiptResponse)
async def get_receipt(
    receipt_id: int,
    db: AsyncSession = Depends(get_db),
) -> Receipt:
    """Retrieve a single receipt by ID, including any fraud flags."""
    result = await db.execute(
        select(Receipt)
        .options(selectinload(Receipt.fraud_flags))
        .where(Receipt.id == receipt_id)
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
    db: AsyncSession = Depends(get_db),
) -> dict:
    """List receipts with pagination and optional status filter."""
    query = select(Receipt).options(selectinload(Receipt.fraud_flags))
    count_query = select(func.count(Receipt.id))

    if status:
        query = query.where(Receipt.status == status)
        count_query = count_query.where(Receipt.status == status)

    # Get total count
    total = (await db.execute(count_query)).scalar_one()

    # Get paginated results
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
