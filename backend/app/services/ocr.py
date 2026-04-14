import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps

logger = logging.getLogger(__name__)

# Date formats to try when parsing extracted date strings
_DATE_FORMATS = [
    "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
    "%Y-%m-%d",
    "%B %d, %Y", "%b %d, %Y",
    "%B %d %Y", "%b %d %Y",
]

# Keywords that signal a total line (excluded from line items)
_TOTAL_KEYWORDS = re.compile(
    r"\b(total|subtotal|tax|tip|gratuity|balance|amount\s*due|grand\s*total)\b",
    re.IGNORECASE,
)

# Patterns that indicate a line is boilerplate, not a merchant name
_BOILERPLATE = re.compile(
    r"www\.|\.com|\.net|\.org|@"           # URLs / email
    r"|\bthank\s*you\b|\bwelcome\b|\bplease\b|\breceipt\b"
    r"|\bfeedback\b|\bsurvey\b|\bcashier\b|\bregister\b|\bterminal\b"
    r"|\bapproved\b|\bchange\b|\bdebit\b|\bcredit\b|\bvisa\b|\bmastercard\b"
    r"|\b\d{4,}\b",                         # long number sequences (IDs, phone)
    re.IGNORECASE,
)


@dataclass
class OCRResult:
    merchant: str | None = None
    transaction_date: date | None = None
    transaction_time: str | None = None
    total_amount: Decimal | None = None
    line_items: list[dict] = field(default_factory=list)
    raw_text: str = ""
    confidence: Decimal = Decimal("0")


def _preprocess(img: Image.Image) -> Image.Image:
    """Improve image quality before OCR to reduce recognition errors.

    Steps applied in order:
    1. Grayscale   — colour is irrelevant for text; reduces noise channels.
    2. Upscale     — Tesseract accuracy drops below ~200 DPI. Receipts are
                     narrow, so photos are often under-resolved. We target a
                     minimum width of 1000 px as a safe proxy for ~300 DPI.
    3. Autocontrast — stretches the histogram so faint ink becomes darker
                      and background becomes whiter, without manual tuning.
    4. Sharpen     — counteracts blur from phone camera photos.
    5. Binarize    — converts to pure black/white. Eliminates grey gradients
                     that confuse Tesseract's edge detector.
    """
    img = img.convert("L")

    if img.width < 1000:
        scale = 1000 / img.width
        img = img.resize(
            (int(img.width * scale), int(img.height * scale)),
            Image.LANCZOS,
        )
        logger.debug("Upscaled image to %dx%d", img.width, img.height)

    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Sharpness(img).enhance(2.0)
    img = img.point(lambda x: 255 if x > 128 else 0)

    return img


def _load_images(file_path: Path) -> list[Image.Image]:
    """Return a list of PIL Images for the file (one per page for PDFs)."""
    if file_path.suffix.lower() == ".pdf":
        try:
            from pdf2image import convert_from_path
            return convert_from_path(str(file_path))
        except ImportError:
            logger.warning("pdf2image not available; cannot process PDF %s", file_path)
            return []
    return [Image.open(file_path)]


def _parse_merchant_by_font_size(img: Image.Image) -> str | None:
    """Identify the merchant name using Tesseract's line hierarchy + filtering.

    Three signals combined:
    1. Line height  — merchant logos are printed in the largest font on the receipt.
    2. Boilerplate filter — strips URLs, payment info, "thank you" lines, etc.
                           before scoring, so junk lines never win the height contest.
    3. Receipt zone — merchant names appear in the top 60 % of the receipt;
                      footer content (totals, card info, barcodes) is excluded.

    image_to_data level meanings: 1=page 2=block 3=paragraph 4=line 5=word
    Level-4 bounding boxes span the full line, giving reliable height comparisons.
    """
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    n = len(data["text"])
    img_height = img.height

    # Pass 1: build a map of line key -> {height, top} from level-4 entries
    line_info: dict[tuple, dict] = {}
    for i in range(n):
        if data["level"][i] == 4 and data["height"][i] > 0:
            key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
            line_info[key] = {"height": data["height"][i], "top": data["top"][i]}

    if not line_info:
        return None

    # Pass 2: collect words (level=5) for each line
    line_words: dict[tuple, list[dict]] = {}
    for i in range(n):
        if data["level"][i] != 5:
            continue
        key = (data["block_num"][i], data["par_num"][i], data["line_num"][i])
        if key not in line_info:
            continue
        text = data["text"][i].strip()
        # conf == -1 are non-word structural elements; keep everything else
        if not text or int(data["conf"][i]) < 0:
            continue
        line_words.setdefault(key, []).append(
            {"text": text, "left": data["left"][i]}
        )

    # Pass 3: score each line — filter boilerplate and footer zone, rank by height
    candidates = []
    for key, info in line_info.items():
        words = line_words.get(key)
        if not words:
            continue

        line_text = " ".join(
            w["text"] for w in sorted(words, key=lambda w: w["left"])
        )

        if _BOILERPLATE.search(line_text):
            continue

        # Ignore anything in the bottom 40 % of the receipt
        if info["top"] > img_height * 0.60:
            continue

        candidates.append({
            "key": key,
            "height": info["height"],
            "top": info["top"],
            "text": line_text,
        })

    if not candidates:
        return None

    max_height = max(c["height"] for c in candidates)

    # Among lines within 15 % of the tallest, pick the topmost
    tall = [c for c in candidates if c["height"] >= max_height * 0.85]
    best = min(tall, key=lambda c: c["top"])

    return _clean_merchant_text(best["text"])


def _clean_merchant_text(text: str) -> str | None:
    """Strip symbol noise and short garbage tokens from the extracted merchant line.

    Two rules, applied per token:
    1. No alphabetic characters at all → drop.
       Removes pure symbols ("=", "#") and standalone numbers ("12345").
       Edge case: "Big 5" loses the "5" — acceptable tradeoff.
    2. 1-2 characters that are all lowercase → drop.
       Removes OCR noise fragments like "id", "it", "or" that appear next to logos.
       Keeps legitimate short names: "BP" (uppercase), "Coca-Cola" (hyphen+letters),
       "7-Eleven" (contains alpha), "H&M" (uppercase), "AT&T" (uppercase).
    """
    clean_words = []
    for token in text.split():
        if not re.search(r"[a-zA-Z]", token):
            continue
        if len(token) <= 2 and token == token.lower():
            continue
        clean_words.append(token)
    return " ".join(clean_words) or None


def _parse_date_time(text: str) -> tuple[date | None, str | None]:
    """Extract the first recognisable date and time from the receipt text."""
    found_date: date | None = None
    found_time: str | None = None

    date_patterns = [
        r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}",
        r"\d{4}-\d{2}-\d{2}",
        r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}",
    ]
    for pattern in date_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        date_str = match.group(0).strip().rstrip(",")
        for fmt in _DATE_FORMATS:
            try:
                found_date = datetime.strptime(date_str, fmt).date()
                break
            except ValueError:
                continue
        if found_date:
            break

    time_match = re.search(
        r"\b(\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?)\b", text
    )
    if time_match:
        found_time = time_match.group(1).strip()

    return found_date, found_time


def _parse_total(text: str) -> Decimal | None:
    """Find the grand total amount on the receipt."""
    # Prefer an explicit total keyword
    total_match = re.search(
        r"(?:total|amount\s*due|grand\s*total|balance\s*due|total\s*due)"
        r"\s*[:\-]?\s*\$?\s*(\d[\d,]*\.\d{2})",
        text,
        re.IGNORECASE,
    )
    if total_match:
        try:
            return Decimal(total_match.group(1).replace(",", ""))
        except InvalidOperation:
            pass

    # Fallback: largest dollar amount in the document (often the total)
    amounts = re.findall(r"\$?\s*(\d[\d,]*\.\d{2})", text)
    if amounts:
        try:
            return max(Decimal(a.replace(",", "")) for a in amounts)
        except InvalidOperation:
            pass

    return None


def _parse_line_items(lines: list[str]) -> list[dict]:
    """Extract individual purchased items, stopping at the receipt footer.

    The footer begins at the first line that contains a total/subtotal/tax
    keyword. Everything from that line onward (payment method, change due,
    card info, barcodes) is ignored.

    The regex allows an optional single trailing character after the price,
    which handles per-item indicators common on retail receipts:
      - "X" on Walmart receipts marks taxable items
      - "N" marks non-taxable items
    """
    items: list[dict] = []
    # Trailing \w? captures optional single-char indicators (X, N, F, etc.)
    item_pattern = re.compile(r"^(.+?)\s+\$?\s*(\d[\d,]*\.\d{2})\s*\w?\s*$")

    for line in lines:
        line = line.strip()

        # Hit the footer — stop here, do not parse any further lines
        if _TOTAL_KEYWORDS.search(line):
            break

        match = item_pattern.match(line)
        if not match:
            continue

        description = match.group(1).strip()
        try:
            items.append({
                "description": description,
                "amount": float(Decimal(match.group(2).replace(",", ""))),
            })
        except InvalidOperation:
            continue

    return items


def extract_receipt_data(file_path: str) -> OCRResult:
    """Run Tesseract on a receipt file and return structured extracted data.

    Populates:
    - merchant: store / restaurant name
    - transaction_date: date of purchase
    - transaction_time: time of purchase (string, e.g. "2:34 PM")
    - total_amount: grand total as Decimal
    - line_items: list of {"description": str, "amount": float}
    - raw_text: full Tesseract output (stored for debugging / future use)
    - confidence: rough 0-100 score based on how many fields were extracted
    """
    result = OCRResult()

    try:
        path = Path(file_path)
        images = _load_images(path)
        if not images:
            return result

        images = [_preprocess(img) for img in images]

        # Raw text from all pages (used for date / total / items parsing)
        raw_text = "\n".join(pytesseract.image_to_string(img) for img in images)
        result.raw_text = raw_text

        lines = [l for l in raw_text.splitlines() if l.strip()]

        # Merchant: use font-size detection on the first page (where the logo lives)
        result.merchant = _parse_merchant_by_font_size(images[0])
        result.transaction_date, result.transaction_time = _parse_date_time(raw_text)
        result.total_amount = _parse_total(raw_text)
        result.line_items = _parse_line_items(lines)

        # Confidence: 25 points per successfully extracted field (max 100)
        fields_found = sum([
            result.merchant is not None,
            result.transaction_date is not None,
            result.total_amount is not None,
            len(result.line_items) > 0,
        ])
        result.confidence = Decimal(str(fields_found * 25))

        logger.info(
            "OCR complete — merchant=%r date=%s total=%s items=%d confidence=%s",
            result.merchant,
            result.transaction_date,
            result.total_amount,
            len(result.line_items),
            result.confidence,
        )

    except Exception:
        logger.exception("OCR extraction failed for %s", file_path)

    return result
