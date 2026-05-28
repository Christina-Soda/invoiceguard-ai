#!/usr/bin/env python3
"""
Preprocess SROIE2019 dataset into InvoiceGuard Agent-ready unified JSON.

Raw SROIE2019 directory structure:

data/raw/sroie/SROIE2019/
├── train/
│   ├── img/        # scanned receipt image: <doc_id>.jpg
│   ├── box/        # OCR information: <doc_id>.txt
│   └── entities/   # key information values: <doc_id>.txt
└── test/
    ├── img/
    ├── box/
    └── entities/

For each receipt:
- img/<doc_id>.jpg
- box/<doc_id>.txt
- entities/<doc_id>.txt

Output:

data/unified/sroie2019/
├── train/
│   ├── sroie_train_<doc_id>.json
│   └── manifest.json
└── test/
    ├── sroie_test_<doc_id>.json
    └── manifest.json

Each output JSON keeps:
- image_path
- ocr blocks
- raw_entities
- fields in Agent-ready format:
  {
    "value": ...,
    "evidence": ...,
    "bounding_box": ...,
    "confidence": ...
  }

Changes from original (v1 → v2):
  FIX-1  parse_ocr_line: raw_line now strips both \\n and \\r (CRLF safety).
  FIX-2  find_date_bbox: digit-only fallback now requires ≥6 digits AND the
         OCR block must match a date-like pattern, preventing phone-number
         false-positives.
  FIX-3  find_address_bbox: minimum length guard now uses the original text
         length (≥4 chars) rather than the post-punct length, and the comment
         is clarified.
  FIX-4  find_amount_bbox: y_score denominator is now derived from the actual
         maximum y-coordinate in the OCR blocks instead of a hard-coded 1000,
         making it resolution-independent.
  OPT-1  build_field_with_evidence: confidence is now assigned per match_type
         (exact_text/amount_total_context → high; multi_line_address/
         loose_text/currency_label → medium; date_digits → low) rather than
         a binary high/medium split.
  OPT-2  validate_outputs: per-field bbox-miss counts are now tracked and
         printed separately so you can see which field is hardest to locate.
  OPT-3  load_entities: UTF-8 BOM (\\ufeff) is stripped before JSON parsing
         to handle files created on Windows.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RAW_DEFAULT_ROOT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/"
    "data/raw/sroie/SROIE2019"
)

OUTPUT_DEFAULT_DIR = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/"
    "data/unified/sroie2019"
)

# OPT-1: confidence per match_type
# Tighter matches get "high"; riskier / multi-block matches get lower grades.
_CONFIDENCE_BY_MATCH_TYPE: Dict[str, str] = {
    "exact_text":           "high",
    "amount_total_context": "high",
    "multi_line_address":   "medium",
    "loose_text":           "medium",
    "currency_label":       "medium",
    "date_digits":          "low",   # digit-only match can misfire on phones
}

# FIX-2: pattern used to check whether an OCR block looks like a date
_DATE_LIKE_RE = re.compile(r"\d{1,4}[-/\.]\d{1,2}[-/\.]\d{1,4}")


# ---------------------------------------------------------------------
# Basic file loading
# ---------------------------------------------------------------------

def find_image(img_dir: Path, doc_id: str) -> Optional[Path]:
    """
    Find image file for a given receipt id.
    SROIE usually uses .jpg, but this supports common extensions.
    """
    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]:
        candidate = img_dir / f"{doc_id}{ext}"
        if candidate.exists():
            return candidate
    return None

def read_text_with_fallback(path: Path) -> str:
    """
    Read text file with multiple encoding fallbacks.

    Some SROIE .txt files may contain non-UTF-8 bytes, such as 0xa3.
    Try utf-8-sig first, then utf-8, cp1252, and latin-1.
    """
    encodings = ["utf-8-sig", "utf-8", "cp1252", "latin-1"]

    last_error = None

    for enc in encodings:
        try:
            with path.open("r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError as exc:
            last_error = exc

    # Last-resort fallback: preserve progress but replace unreadable chars.
    with path.open("r", encoding="utf-8", errors="replace") as f:
        text = f.read()

    print(f"[WARN] Used utf-8 errors='replace' for {path}: {last_error}")
    return text

def load_entities(entity_path: Path) -> Dict[str, Any]:
    """
    Load key information values from SROIE entities file.

    Although the file extension is .txt, the content is JSON, e.g.:
    {
        "company": "...",
        "date": "...",
        "address": "...",
        "total": "..."
    }

    OPT-3: Strip UTF-8 BOM (\\ufeff) before parsing. Some SROIE files
    created on Windows carry a BOM that makes json.loads() raise
    JSONDecodeError even though the content is otherwise valid.
    """
    # with entity_path.open("r", encoding="utf-8") as f:
    #     text = f.read()
    # # OPT-3: remove BOM if present, then strip surrounding whitespace
    # text = text.lstrip("\ufeff").strip()

    text = read_text_with_fallback(entity_path)
    text = text.lstrip("\ufeff").strip()

    if not text:
        return {}

    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Failed to parse entities file as JSON: {entity_path}\n{exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Entities file is not a JSON object: {entity_path}")

    return data


def parse_ocr_line(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse one line from SROIE box file.

    Expected format:
        x1,y1,x2,y2,x3,y3,x4,y4,text

    Important:
    OCR text may contain commas, so split only the first 8 commas.

    FIX-1: raw_line now strips both \\n and \\r so that files with Windows
    CRLF line endings do not leave a stray \\r in the stored raw string.
    """
    # FIX-1: strip both CR and LF from the raw copy
    raw_line = line.rstrip("\r\n")
    line = raw_line.strip()

    if not line:
        return None

    parts = line.split(",", 8)

    if len(parts) != 9:
        return None

    try:
        coords = [int(float(v)) for v in parts[:8]]
    except ValueError:
        return None

    text = parts[8].strip()

    x1, y1, x2, y2, x3, y3, x4, y4 = coords

    polygon = [
        [x1, y1],
        [x2, y2],
        [x3, y3],
        [x4, y4],
    ]

    xs = [x1, x2, x3, x4]
    ys = [y1, y2, y3, y4]

    bbox = [
        min(xs),
        min(ys),
        max(xs),
        max(ys),
    ]

    return {
        "text":    text,
        "polygon": polygon,
        "bbox":    bbox,
        "raw":     raw_line,
    }


def load_ocr_blocks(box_path: Path) -> List[Dict[str, Any]]:
    """
    Load OCR text blocks from a SROIE box file.
    """
    blocks: List[Dict[str, Any]] = []

    if not box_path.exists():
        return blocks

    text = read_text_with_fallback(box_path)
    
    for line_idx, line in enumerate(text.splitlines()):
        parsed = parse_ocr_line(line)

        if parsed is None:
            continue

        parsed["line_id"] = line_idx
        blocks.append(parsed)

    # with box_path.open("r", encoding="utf-8") as f:
    #     for line_idx, line in enumerate(f):
    #         parsed = parse_ocr_line(line)

    #         if parsed is None:
    #             continue
    #         parsed["line_id"] = line_idx
    #         blocks.append(parsed)

    return blocks


# ---------------------------------------------------------------------
# Text normalization and bbox helpers
# ---------------------------------------------------------------------

def normalize_text(text: Any) -> str:
    """
    Normalize text for loose matching.
    """
    if text is None:
        return ""

    text = str(text).upper()
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def normalize_text_no_punct(text: Any) -> str:
    """
    Normalize text and remove most punctuation for more tolerant matching.
    """
    text = normalize_text(text)
    text = re.sub(r"[^A-Z0-9]+", "", text)
    return text


def normalize_amount(text: Any) -> str:
    """
    Normalize amount strings like RM12.00, 12.00, 12,00.
    """
    if text is None:
        return ""

    text = str(text).strip()
    text = text.replace(",", "")
    text = re.sub(r"[^0-9.]", "", text)

    if not text:
        return ""

    try:
        return f"{float(text):.2f}"
    except ValueError:
        return text


def merge_bboxes(bboxes: List[List[int]]) -> Optional[List[int]]:
    """
    Merge multiple [x1, y1, x2, y2] boxes into one enclosing box.
    """
    if not bboxes:
        return None

    return [
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    ]


def _max_y_in_blocks(ocr_blocks: List[Dict[str, Any]]) -> float:
    """
    Return the largest y2 value seen across all OCR blocks.
    Used by find_amount_bbox as a resolution-independent normaliser.
    Falls back to 1000 when the block list is empty.
    """
    ys = [b["bbox"][3] for b in ocr_blocks if b.get("bbox")]
    return float(max(ys)) if ys else 1000.0


# ---------------------------------------------------------------------
# OCR matching functions
# ---------------------------------------------------------------------

def find_exact_text_bbox(
    value: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Find OCR block whose text exactly matches the field value after
    normalization.  Good for company names and short date strings.
    """
    target = normalize_text(value)

    if not target:
        return None

    for block in ocr_blocks:
        block_text = normalize_text(block.get("text"))

        if block_text == target:
            return {
                "bbox":          block.get("bbox"),
                "matched_text":  block.get("text"),
                "matched_blocks": [block],
                "match_type":    "exact_text",
            }

    return None


def find_loose_text_bbox(
    value: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Looser text matching using punctuation-insensitive comparison.
    """
    target = normalize_text_no_punct(value)

    if not target:
        return None

    for block in ocr_blocks:
        block_text = normalize_text_no_punct(block.get("text"))

        if not block_text:
            continue

        if target == block_text or target in block_text or block_text in target:
            return {
                "bbox":           block.get("bbox"),
                "matched_text":   block.get("text"),
                "matched_blocks": [block],
                "match_type":     "loose_text",
            }

    return None


def find_date_bbox(
    value: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Find date bbox.

    Strategy (in order):
    1. Exact normalized text match — block must also look like a date.
    2. Loose (punctuation-insensitive) text match — same date-pattern guard.
    3. Digit-only fallback — FIX-2 applies here.

    FIX-2: All three matching stages now require the candidate OCR block to
    match _DATE_LIKE_RE (i.e. contain a separator between digit groups).
    This prevents phone numbers ("2503-2018"), years ("2018"), and other
    digit-heavy tokens from being returned as dates.

    Specifically the digit-only fallback additionally requires:
      a) The digit sequences are the same length (prevents subset matches).
      b) The OCR block text looks like a date (matches _DATE_LIKE_RE).
      c) The digit sequence has at least 6 characters (a bare year "2018"
         has only 4 and is too ambiguous to match safely this way).
    """
    target_digits = re.sub(r"[^0-9]", "", str(value or ""))

    # Stage 1: exact normalized text, but only if the block looks like a date
    target_norm = normalize_text(value)
    if target_norm:
        for block in ocr_blocks:
            block_text = block.get("text", "")
            if normalize_text(block_text) == target_norm:
                # FIX-2: also require date-like pattern on the raw block text
                if _DATE_LIKE_RE.search(block_text):
                    return {
                        "bbox":           block.get("bbox"),
                        "matched_text":   block_text,
                        "matched_blocks": [block],
                        "match_type":     "exact_text",
                    }

    # Stage 2: loose (punct-insensitive) match, also gated on date pattern
    target_np = normalize_text_no_punct(value)
    if target_np:
        for block in ocr_blocks:
            block_text = block.get("text", "")
            block_np   = normalize_text_no_punct(block_text)
            if not block_np:
                continue
            if target_np == block_np or target_np in block_np or block_np in target_np:
                # FIX-2: reject matches whose block text is not date-shaped
                if _DATE_LIKE_RE.search(block_text):
                    return {
                        "bbox":           block.get("bbox"),
                        "matched_text":   block_text,
                        "matched_blocks": [block],
                        "match_type":     "loose_text",
                    }

    # Stage 3: digit-only fallback
    # FIX-2a: require at least 6 digits to proceed
    if len(target_digits) < 6:
        return None

    for block in ocr_blocks:
        block_text   = block.get("text", "")
        block_digits = re.sub(r"[^0-9]", "", block_text)

        # FIX-2b: lengths must match exactly (no subset matching)
        if len(block_digits) != len(target_digits):
            continue

        if block_digits != target_digits:
            continue

        # FIX-2c: the block must look like a date (separator present)
        if not _DATE_LIKE_RE.search(block_text):
            continue

        return {
            "bbox":           block.get("bbox"),
            "matched_text":   block_text,
            "matched_blocks": [block],
            "match_type":     "date_digits",
        }

    return None


def find_amount_bbox(
    value: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Find amount bbox.

    There can be multiple identical amounts, e.g. several "12.00" values.
    For SROIE total, prefer the amount that appears near words such as:
    TOTAL, PAYABLE, AMT, INCL.

    Fallback: choose the lower occurrence on the receipt.

    FIX-4: y_score previously divided y_center by a hard-coded 1000, which
    over-weighted position for high-resolution scans (>1000 px tall) and
    under-weighted it for small ones.  The denominator is now the actual
    maximum y2 across all OCR blocks, so y_score is always in [0, 1].
    """
    target = normalize_amount(value)

    if not target:
        return None

    candidates = []

    for idx, block in enumerate(ocr_blocks):
        block_amount = normalize_amount(block.get("text"))

        if block_amount == target and block.get("bbox"):
            candidates.append((idx, block))

    if not candidates:
        return None

    total_keywords = ["TOTAL", "PAYABLE", "AMT", "INCL", "AMOUNT"]

    # FIX-4: resolution-independent normaliser
    max_y = _max_y_in_blocks(ocr_blocks)

    scored = []

    for idx, block in candidates:
        bbox = block["bbox"]
        y_center = (bbox[1] + bbox[3]) / 2.0

        nearby_texts = []

        for j, other in enumerate(ocr_blocks):
            if j == idx:
                continue

            other_bbox = other.get("bbox")
            if not other_bbox:
                continue

            other_y_center = (other_bbox[1] + other_bbox[3]) / 2.0

            # Same row or nearby row.
            if abs(other_y_center - y_center) <= 30:
                nearby_texts.append(normalize_text(other.get("text")))

        nearby_joined = " ".join(nearby_texts)

        keyword_score = sum(1 for kw in total_keywords if kw in nearby_joined)

        # FIX-4: y_score is now in [0, 1] regardless of image resolution.
        # Higher y means lower on the receipt (closer to the total line).
        y_score = y_center / max_y

        final_score = keyword_score * 10.0 + y_score

        scored.append((final_score, idx, block, nearby_joined))

    scored.sort(key=lambda x: x[0], reverse=True)
    _, _, best_block, nearby_joined = scored[0]

    return {
        "bbox":           best_block.get("bbox"),
        "matched_text":   best_block.get("text"),
        "matched_blocks": [best_block],
        "match_type":     "amount_total_context",
        "context":        nearby_joined,
    }


def find_address_bbox(
    address: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Match address across multiple OCR lines.

    SROIE address is usually one long string in entities, while OCR blocks
    split it into multiple lines. We select OCR blocks whose normalized text
    appears inside the full address string.

    FIX-3: The minimum-length guard now checks the original (pre-punct-strip)
    block text length (≥4 chars) rather than the post-punct length.  Using
    the post-punct length could silently pass through very short tokens whose
    visible text is longer (e.g. "1A." has 3 visible chars but only 2 after
    stripping punctuation, so it would have been filtered by the old ≥5
    post-punct guard — that is fine — but the intent is clearer when expressed
    on the original text).
    """
    target         = normalize_text(address)
    target_no_punct = normalize_text_no_punct(address)

    if not target:
        return None

    matched_blocks = []

    for block in ocr_blocks:
        block_text     = normalize_text(block.get("text"))
        block_no_punct = normalize_text_no_punct(block.get("text"))

        # FIX-3: guard on original text length (≥4), not post-punct length
        if not block_text or len(block_text.strip()) < 4:
            continue

        # Skip common header labels that appear in many receipts and could
        # accidentally match parts of addresses.
        if block_text in {"TAX INVOICE", "GST SUMMARY"}:
            continue

        if block_text in target or block_no_punct in target_no_punct:
            matched_blocks.append(block)

    if not matched_blocks:
        return None

    # Sort visually top-to-bottom, then left-to-right.
    matched_blocks.sort(key=lambda b: (b["bbox"][1], b["bbox"][0]))

    bboxes      = [b["bbox"] for b in matched_blocks if b.get("bbox")]
    merged_bbox = merge_bboxes(bboxes)

    return {
        "bbox":           merged_bbox,
        "matched_text":   " | ".join(b.get("text", "") for b in matched_blocks),
        "matched_blocks": matched_blocks,
        "match_type":     "multi_line_address",
    }


def find_currency_bbox(
    ocr_blocks: List[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Try to find currency label. For Malaysian receipts, RM is common.
    """
    currency_candidates = {"RM", "MYR"}

    for block in ocr_blocks:
        text = normalize_text(block.get("text"))

        if text in currency_candidates and block.get("bbox"):
            return {
                "bbox":           block.get("bbox"),
                "matched_text":   block.get("text"),
                "matched_blocks": [block],
                "match_type":     "currency_label",
            }

    return None


# ---------------------------------------------------------------------
# Field construction
# ---------------------------------------------------------------------

def normalize_sroie_fields(raw_entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert SROIE key names to InvoiceGuard unified field names.

    SROIE:
        company
        date
        address
        total

    InvoiceGuard:
        vendor_name
        invoice_date
        vendor_address
        total
    """
    return {
        "vendor_name":    raw_entities.get("company"),
        "invoice_date":   raw_entities.get("date"),
        "vendor_address": raw_entities.get("address"),
        "total":          raw_entities.get("total"),

        # SROIE does not directly provide these fields.
        "invoice_number": None,
        "subtotal":       None,
        "tax":            None,

        # Try to infer this from OCR blocks later.
        "currency":       None,
    }


def build_null_field() -> Dict[str, Any]:
    return {
        "value":        None,
        "evidence":     None,
        "bounding_box": None,
        "confidence":   None,
    }


def build_field_with_evidence(
    field_name: str,
    value: Any,
    ocr_blocks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Build one Agent-ready field:
    {
        "value": ...,
        "evidence": ...,
        "bounding_box": ...,
        "confidence": ...
    }

    OPT-1: confidence is now derived from the match_type via
    _CONFIDENCE_BY_MATCH_TYPE instead of a binary high/medium split.
    This lets callers and the downstream confidence scorer know that a
    "date_digits" bbox is less certain than an "exact_text" bbox.
    """
    if value in [None, ""]:
        return build_null_field()

    match: Optional[Dict[str, Any]] = None

    if field_name == "vendor_name":
        match = (
            find_exact_text_bbox(value, ocr_blocks)
            or find_loose_text_bbox(value, ocr_blocks)
        )

    elif field_name == "invoice_date":
        match = find_date_bbox(value, ocr_blocks)

    elif field_name == "vendor_address":
        match = find_address_bbox(value, ocr_blocks)

    elif field_name == "total":
        match = find_amount_bbox(value, ocr_blocks)

    else:
        match = (
            find_exact_text_bbox(value, ocr_blocks)
            or find_loose_text_bbox(value, ocr_blocks)
        )

    if match and match.get("bbox"):
        # OPT-1: look up confidence from match_type; default to "medium"
        match_type = match.get("match_type", "")
        confidence = _CONFIDENCE_BY_MATCH_TYPE.get(match_type, "medium")

        return {
            "value":        value,
            "evidence":     (
                f"matched OCR text: {match.get('matched_text')} "
                f"({match_type})"
            ),
            "bounding_box": match.get("bbox"),
            "confidence":   confidence,
        }

    return {
        "value":        value,
        "evidence":     (
            "ground truth value from SROIE entities; "
            "no matching OCR bounding box found"
        ),
        "bounding_box": None,
        "confidence":   "medium",
    }


def build_currency_field(ocr_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Currency is not provided in SROIE entities. Try to infer from OCR.
    """
    match = find_currency_bbox(ocr_blocks)

    if not match:
        return build_null_field()

    text = normalize_text(match.get("matched_text"))

    if text == "RM":
        value = "RM"
    elif text == "MYR":
        value = "MYR"
    else:
        value = text

    return {
        "value":        value,
        "evidence":     (
            f"matched OCR currency label: {match.get('matched_text')} "
            f"({match.get('match_type')})"
        ),
        "bounding_box": match.get("bbox"),
        "confidence":   _CONFIDENCE_BY_MATCH_TYPE.get(
            match.get("match_type", ""), "medium"
        ),
    }


def build_fields_with_evidence(
    normalized_fields: Dict[str, Any],
    ocr_blocks: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Build all fields in Agent-ready FieldWithEvidence format.
    """
    output: Dict[str, Dict[str, Any]] = {}

    for field_name, value in normalized_fields.items():
        if field_name == "currency" and value in [None, ""]:
            output[field_name] = build_currency_field(ocr_blocks)
        else:
            output[field_name] = build_field_with_evidence(
                field_name=field_name,
                value=value,
                ocr_blocks=ocr_blocks,
            )

    return output


# ---------------------------------------------------------------------
# Conversion
# ---------------------------------------------------------------------

def convert_one_receipt(
    split_name: str,
    doc_id: str,
    image_path: Path,
    box_path: Path,
    entity_path: Path,
    output_split_dir: Path,
) -> Optional[Path]:
    """
    Convert one SROIE receipt sample into unified JSON.
    """
    raw_entities  = load_entities(entity_path)
    ocr_blocks    = load_ocr_blocks(box_path)

    normalized_fields    = normalize_sroie_fields(raw_entities)
    fields_with_evidence = build_fields_with_evidence(
        normalized_fields=normalized_fields,
        ocr_blocks=ocr_blocks,
    )

    unified = {
        "doc_id":          f"sroie_{split_name}_{doc_id}",
        "original_doc_id": doc_id,

        "source":          "sroie2019",
        "split":           split_name,
        "document_type":   "receipt",

        "image_path":      str(image_path),
        "ocr_path":        str(box_path) if box_path.exists() else None,
        "entity_path":     str(entity_path),

        "fields":          fields_with_evidence,
        "line_items":      [],

        "ocr": {
            "source": "sroie_box",
            "blocks": ocr_blocks,
        },

        "raw_entities": raw_entities,

        # Later: tier1_clean / tier2_hard / tier3_failure
        "tier": None,
    }

    output_split_dir.mkdir(parents=True, exist_ok=True)

    out_path = output_split_dir / f"sroie_{split_name}_{doc_id}.json"

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(unified, f, indent=2, ensure_ascii=False)

    return out_path


def convert_split(
    sroie_root: Path,
    split_name: str,
    output_dir: Path,
) -> List[Path]:
    """
    Convert one split: train or test.
    """
    split_dir    = sroie_root / split_name
    img_dir      = split_dir / "img"
    box_dir      = split_dir / "box"
    entities_dir = split_dir / "entities"

    if not split_dir.exists():
        raise FileNotFoundError(f"Split directory not found: {split_dir}")
    if not img_dir.exists():
        raise FileNotFoundError(f"Image directory not found: {img_dir}")
    if not box_dir.exists():
        raise FileNotFoundError(f"OCR box directory not found: {box_dir}")
    if not entities_dir.exists():
        raise FileNotFoundError(f"Entities directory not found: {entities_dir}")

    entity_files     = sorted(entities_dir.glob("*.txt"))
    output_split_dir = output_dir / split_name
    converted_files: List[Path] = []

    print(f"\n=== Converting split: {split_name} ===")
    print(f"Images:   {img_dir}")
    print(f"OCR box:  {box_dir}")
    print(f"Entities: {entities_dir}")
    print(f"Found entity files: {len(entity_files)}")

    missing_images = 0
    missing_boxes  = 0
    failed         = 0

    for entity_path in entity_files:
        doc_id     = entity_path.stem
        image_path = find_image(img_dir, doc_id)
        box_path   = box_dir / f"{doc_id}.txt"

        if image_path is None:
            print(f"[SKIP]  Missing image for doc_id={doc_id}")
            missing_images += 1
            continue

        if not box_path.exists():
            print(f"[WARN]  Missing OCR box file for doc_id={doc_id}: {box_path}")
            missing_boxes += 1

        try:
            out_path = convert_one_receipt(
                split_name=split_name,
                doc_id=doc_id,
                image_path=image_path,
                box_path=box_path,
                entity_path=entity_path,
                output_split_dir=output_split_dir,
            )
        except Exception as exc:
            print(f"[FAILED] doc_id={doc_id}: {exc}")
            failed += 1
            continue

        if out_path is not None:
            converted_files.append(out_path)

    print(f"Converted:       {len(converted_files)}")
    print(f"Missing images:  {missing_images}")
    print(f"Missing boxes:   {missing_boxes}")
    print(f"Failed:          {failed}")

    return converted_files


def write_manifest(
    output_dir: Path,
    split_name: str,
    json_files: List[Path],
) -> Path:
    """
    Write one manifest file per split.
    The manifest stores unified JSON paths, not image paths.
    """
    split_dir = output_dir / split_name
    split_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = split_dir / "manifest.json"

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump([str(p) for p in json_files], f, indent=2, ensure_ascii=False)

    print(f"Manifest written: {manifest_path}")
    return manifest_path


# ---------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------

def unwrap_field_value(field: Any) -> Any:
    if isinstance(field, dict) and "value" in field:
        return field.get("value")
    return field


def validate_outputs(json_files: List[Path]) -> Dict[str, Any]:
    """
    Validate generated unified JSON files.

    OPT-2: Per-field bbox-miss counts are now tracked in addition to the
    aggregate flag so you can see which field is most often unlocatable.
    The return type is Dict[str, Any] (was Dict[str, int]) to accommodate
    the nested per_field_missing_bbox dict.
    """
    required_fields = [
        "vendor_name",
        "invoice_date",
        "vendor_address",
        "total",
    ]

    stats: Dict[str, Any] = {
        "total":                    0,
        "missing_image_path":       0,
        "missing_required_values":  0,
        "empty_ocr_blocks":         0,
        "missing_required_bboxes":  0,          # aggregate (≥1 field missing)
        # OPT-2: per-field bbox miss counter
        "per_field_missing_bbox":   {f: 0 for f in required_fields},
    }

    for json_path in json_files:
        stats["total"] += 1

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        image_path = Path(data["image_path"])
        if not image_path.exists():
            stats["missing_image_path"] += 1

        ocr_blocks = data.get("ocr", {}).get("blocks", [])
        if not ocr_blocks:
            stats["empty_ocr_blocks"] += 1

        fields = data.get("fields", {})

        has_missing_value = False
        has_missing_bbox  = False

        for field_name in required_fields:
            field = fields.get(field_name, {})
            value = unwrap_field_value(field)

            if value in [None, ""]:
                has_missing_value = True

            if isinstance(field, dict):
                if field.get("bounding_box") in [None, []]:
                    has_missing_bbox = True
                    # OPT-2: increment per-field counter
                    stats["per_field_missing_bbox"][field_name] += 1

        if has_missing_value:
            stats["missing_required_values"] += 1

        if has_missing_bbox:
            stats["missing_required_bboxes"] += 1

    return stats


# ---------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Convert SROIE2019 train/test files into "
            "InvoiceGuard Agent-ready unified JSON format."
        )
    )

    parser.add_argument(
        "--sroie-root",
        type=str,
        default=RAW_DEFAULT_ROOT,
        help="Root directory of SROIE2019 containing train/ and test/.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DEFAULT_DIR,
        help="Output directory for unified JSON files.",
    )

    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "test"],
        choices=["train", "test"],
        help="Splits to convert.",
    )

    args = parser.parse_args()

    sroie_root = Path(args.sroie_root)
    output_dir = Path(args.output_dir)

    print("SROIE root:", sroie_root)
    print("Output dir:", output_dir)
    print("Splits:",     args.splits)

    if not sroie_root.exists():
        raise FileNotFoundError(f"SROIE root does not exist: {sroie_root}")

    output_dir.mkdir(parents=True, exist_ok=True)

    all_converted: List[Path] = []

    for split_name in args.splits:
        converted = convert_split(
            sroie_root=sroie_root,
            split_name=split_name,
            output_dir=output_dir,
        )

        write_manifest(output_dir, split_name, converted)
        all_converted.extend(converted)

    stats = validate_outputs(all_converted)

    print("\n=== Final Summary ===")
    print(f"Total converted JSON files:        {stats['total']}")
    print(f"Missing image paths:               {stats['missing_image_path']}")
    print(f"Samples with empty OCR blocks:     {stats['empty_ocr_blocks']}")
    print(f"Samples missing required values:   {stats['missing_required_values']}")
    print(f"Samples missing required bboxes:   {stats['missing_required_bboxes']}")
    # OPT-2: per-field breakdown
    print("Per-field missing bbox counts:")
    for field, count in stats["per_field_missing_bbox"].items():
        pct = count / stats["total"] * 100 if stats["total"] else 0
        print(f"  {field:<20} {count:>4}  ({pct:.1f}%)")
    print(f"Output directory:                  {output_dir}")


if __name__ == "__main__":
    main()