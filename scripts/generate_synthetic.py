#!/usr/bin/env python3
"""
Generate synthetic invoice images and Agent-ready unified JSON files.

Output format matches SROIE unified JSON produced by preprocess_sroie.py:

{
  "doc_id": "...",
  "source": "synthetic",
  "document_type": "invoice",
  "image_path": "...",
  "fields": {
    "vendor_name": {
      "value": "...",
      "evidence": "...",
      "bounding_box": [...],
      "confidence": "high"
    },
    ...
  },
  "line_items": [...],
  "ocr": {
    "source": "synthetic_rendered_text",
    "blocks": [...]
  },
  "raw_entities": {...},
  "tier": "tier1_clean"
}

This script intentionally creates clean synthetic invoices suitable for:
- baseline pipeline testing
- rule engine testing
- VLM extraction evaluation
- later fine-tuning data preparation
"""

from __future__ import annotations

import argparse
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont


PROJECT_ROOT_DEFAULT = "/work/bigweather/xinyanxie/invoiceguard-ai"

SYNTHETIC_IMAGE_DIR_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/data/synthetic/img"
)

UNIFIED_OUTPUT_DIR_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/data/unified/synthetic"
)

VENDOR_FILE_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/data/synthetic/vendors.json"
)


# ---------------------------------------------------------------------
# Static synthetic pools
# ---------------------------------------------------------------------

VENDOR_NAMES = [
    "ABC Medical Supply LLC",
    "Lincoln Office Solutions",
    "Prairie Lab Equipment",
    "Midwest Data Services",
    "Great Plains Stationery",
    "Nebraska Clinical Supplies",
    "Cornhusker Tech Parts",
    "Horizon Imaging Center",
    "Summit Facility Services",
    "Red Oak Scientific",
    "Blue River Consulting",
    "North Star Logistics",
    "Capital City Hardware",
    "Greenfield Bio Labs",
    "Union Campus Bookstore",
    "Pioneer Safety Products",
    "Silverline Diagnostics",
    "Evergreen Maintenance",
    "Maple Leaf Instruments",
    "Central Plains Printing",
]

STREET_NAMES = [
    "O Street",
    "P Street",
    "Holdrege Street",
    "Vine Street",
    "Normal Blvd",
    "Superior Street",
    "Yankee Hill Road",
    "Fletcher Avenue",
    "South 48th Street",
    "North 27th Street",
]

ITEM_DESCRIPTIONS = [
    "Disposable nitrile gloves",
    "Thermal receipt paper rolls",
    "Printer toner cartridge",
    "Laboratory test kit",
    "Office chair replacement parts",
    "Barcode scanner cable",
    "Sterile sample containers",
    "Shipping labels",
    "Network adapter",
    "Cleaning solution",
    "Document storage boxes",
    "Safety goggles",
    "USB-C docking station",
    "Calibration service",
    "Maintenance labor",
    "Packaging tape",
]


# ---------------------------------------------------------------------
# Geometry / OCR helpers
# ---------------------------------------------------------------------

def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """
    Load a commonly available font if possible.
    Falls back to PIL default font.
    """
    candidates = []

    if bold:
        candidates.extend([
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ])
    else:
        candidates.extend([
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ])

    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)

    return ImageFont.load_default()


def bbox_to_polygon(bbox: List[int]) -> List[List[int]]:
    x1, y1, x2, y2 = bbox
    return [
        [x1, y1],
        [x2, y1],
        [x2, y2],
        [x1, y2],
    ]


def merge_bboxes(bboxes: List[List[int]]) -> Optional[List[int]]:
    if not bboxes:
        return None

    return [
        min(b[0] for b in bboxes),
        min(b[1] for b in bboxes),
        max(b[2] for b in bboxes),
        max(b[3] for b in bboxes),
    ]


def draw_text_block(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: Tuple[int, int],
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str = "black",
    line_id: int = 0,
) -> Dict[str, Any]:
    """
    Draw text and return an OCR block compatible with SROIE OCR block format.
    """
    x, y = xy
    draw.text((x, y), text, fill=fill, font=font)

    # textbbox returns (left, top, right, bottom)
    bbox_tuple = draw.textbbox((x, y), text, font=font)
    bbox = [int(v) for v in bbox_tuple]

    return {
        "line_id": line_id,
        "text": text,
        "polygon": bbox_to_polygon(bbox),
        "bbox": bbox,
        "raw": f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[1]},{bbox[2]},{bbox[3]},{bbox[0]},{bbox[3]},{text}",
    }


def field_with_evidence(
    value: Any,
    evidence: Optional[str],
    bbox: Optional[List[int]],
    confidence: Optional[str] = "high",
) -> Dict[str, Any]:
    if value in [None, ""]:
        return {
            "value": None,
            "evidence": None,
            "bounding_box": None,
            "confidence": None,
        }

    return {
        "value": value,
        "evidence": evidence,
        "bounding_box": bbox,
        "confidence": confidence,
    }


def money(value: float) -> str:
    return f"{value:.2f}"


def random_date_this_year() -> str:
    start = date(date.today().year, 1, 1)
    delta = random.randint(0, max(1, (date.today() - start).days))
    return (start + timedelta(days=delta)).strftime("%Y-%m-%d")


def generate_address() -> str:
    number = random.randint(100, 9999)
    street = random.choice(STREET_NAMES)
    city = random.choice(["Lincoln", "Omaha", "Grand Island", "Kearney"])
    state = "NE"
    zip_code = random.randint(68000, 68999)
    return f"{number} {street}, {city}, {state} {zip_code}"


def split_address_for_rendering(address: str) -> List[str]:
    """
    Render address in 2 lines to create realistic multi-line OCR blocks.
    """
    parts = address.split(", ")
    if len(parts) >= 3:
        return [
            parts[0],
            ", ".join(parts[1:]),
        ]

    mid = len(address) // 2
    return [address[:mid].strip(), address[mid:].strip()]


# ---------------------------------------------------------------------
# Single synthetic invoice generation
# ---------------------------------------------------------------------

def generate_invoice_record(idx: int) -> Dict[str, Any]:
    vendor_name = random.choice(VENDOR_NAMES)
    vendor_address = generate_address()

    invoice_number = f"INV-{date.today().year}-{idx:06d}"
    invoice_date = random_date_this_year()

    n_items = random.randint(3, 7)
    items = []

    for _ in range(n_items):
        desc = random.choice(ITEM_DESCRIPTIONS)
        qty = random.randint(1, 12)
        unit_price = round(random.uniform(5.0, 350.0), 2)
        amount = round(qty * unit_price, 2)

        items.append({
            "description": desc,
            "quantity": qty,
            "unit_price": unit_price,
            "amount": amount,
        })

    subtotal = round(sum(item["amount"] for item in items), 2)
    tax_rate = random.choice([0.055, 0.06, 0.07, 0.08])
    tax = round(subtotal * tax_rate, 2)
    total = round(subtotal + tax, 2)

    return {
        "vendor_name": vendor_name,
        "vendor_address": vendor_address,
        "invoice_number": invoice_number,
        "invoice_date": invoice_date,
        "subtotal": subtotal,
        "tax": tax,
        "tax_rate": tax_rate,
        "total": total,
        "currency": "USD",
        "line_items": items,
    }


def render_invoice(
    record: Dict[str, Any],
    image_path: Path,
    doc_id: str,
) -> Dict[str, Any]:
    """
    Render invoice image and return OCR blocks + field bboxes.
    """
    width, height = 1000, 1400
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)

    font_title = load_font(34, bold=True)
    font_header = load_font(22, bold=True)
    font_normal = load_font(20, bold=False)
    font_small = load_font(18, bold=False)
    font_bold = load_font(20, bold=True)

    ocr_blocks: List[Dict[str, Any]] = []
    line_id = 0

    def add_text(text: str, x: int, y: int, font, fill: str = "black") -> Dict[str, Any]:
        nonlocal line_id
        block = draw_text_block(
            draw=draw,
            text=text,
            xy=(x, y),
            font=font,
            fill=fill,
            line_id=line_id,
        )
        ocr_blocks.append(block)
        line_id += 1
        return block

    # Outer border
    draw.rectangle([40, 40, width - 40, height - 40], outline="black", width=2)

    # Header
    invoice_title_block = add_text("INVOICE", 760, 70, font_title)

    vendor_block = add_text(record["vendor_name"], 70, 70, font_header)
    address_lines = split_address_for_rendering(record["vendor_address"])

    address_blocks = []
    y = 110
    for line in address_lines:
        address_blocks.append(add_text(line, 70, y, font_small))
        y += 26

    # Invoice metadata
    inv_no_label = add_text("Invoice No:", 650, 150, font_bold)
    inv_no_value = add_text(record["invoice_number"], 790, 150, font_normal)

    date_label = add_text("Date:", 650, 185, font_bold)
    date_value = add_text(record["invoice_date"], 790, 185, font_normal)

    currency_label = add_text("Currency:", 650, 220, font_bold)
    currency_value = add_text(record["currency"], 790, 220, font_normal)

    # Divider
    draw.line([70, 285, 930, 285], fill="black", width=2)

    # Table header
    table_top = 330
    add_text("Description", 80, table_top, font_bold)
    add_text("Qty", 540, table_top, font_bold)
    add_text("Unit Price", 640, table_top, font_bold)
    add_text("Amount", 820, table_top, font_bold)

    draw.line([70, table_top + 35, 930, table_top + 35], fill="black", width=1)

    # Table rows
    line_items_output = []

    y = table_top + 60

    for item in record["line_items"]:
        desc_block = add_text(item["description"][:42], 80, y, font_normal)
        qty_block = add_text(str(item["quantity"]), 550, y, font_normal)
        unit_block = add_text(money(item["unit_price"]), 660, y, font_normal)
        amount_block = add_text(money(item["amount"]), 840, y, font_normal)

        row_bbox = merge_bboxes([
            desc_block["bbox"],
            qty_block["bbox"],
            unit_block["bbox"],
            amount_block["bbox"],
        ])

        line_items_output.append({
            "description": item["description"],
            "quantity": item["quantity"],
            "unit_price": money(item["unit_price"]),
            "amount": money(item["amount"]),
            "evidence": "synthetic rendered line item row",
            "bounding_box": row_bbox,
            "confidence": "high",
        })

        y += 38

    # Totals area
    totals_y = max(y + 40, 900)

    draw.line([600, totals_y - 20, 930, totals_y - 20], fill="black", width=1)

    subtotal_label = add_text("Subtotal:", 640, totals_y, font_bold)
    subtotal_value = add_text(money(record["subtotal"]), 840, totals_y, font_normal)

    tax_label = add_text(f"Tax ({record['tax_rate'] * 100:.1f}%):", 640, totals_y + 38, font_bold)
    tax_value = add_text(money(record["tax"]), 840, totals_y + 38, font_normal)

    total_label = add_text("TOTAL:", 640, totals_y + 86, font_header)
    total_value = add_text(money(record["total"]), 840, totals_y + 86, font_header)

    draw.line([640, totals_y + 125, 930, totals_y + 125], fill="black", width=2)

    # Footer
    add_text("Thank you for your business.", 70, height - 110, font_small)
    add_text(f"Document ID: {doc_id}", 70, height - 80, font_small)

    image_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(image_path, quality=95)

    address_bbox = merge_bboxes([b["bbox"] for b in address_blocks])

    fields = {
        "vendor_name": field_with_evidence(
            value=record["vendor_name"],
            evidence="synthetic rendered vendor name in invoice header",
            bbox=vendor_block["bbox"],
            confidence="high",
        ),
        "vendor_address": field_with_evidence(
            value=record["vendor_address"],
            evidence="synthetic rendered vendor address below vendor name",
            bbox=address_bbox,
            confidence="high",
        ),
        "invoice_number": field_with_evidence(
            value=record["invoice_number"],
            evidence="synthetic rendered value to the right of 'Invoice No:' label",
            bbox=inv_no_value["bbox"],
            confidence="high",
        ),
        "invoice_date": field_with_evidence(
            value=record["invoice_date"],
            evidence="synthetic rendered value to the right of 'Date:' label",
            bbox=date_value["bbox"],
            confidence="high",
        ),
        "subtotal": field_with_evidence(
            value=money(record["subtotal"]),
            evidence="synthetic rendered amount to the right of 'Subtotal:' label",
            bbox=subtotal_value["bbox"],
            confidence="high",
        ),
        "tax": field_with_evidence(
            value=money(record["tax"]),
            evidence="synthetic rendered amount to the right of tax label",
            bbox=tax_value["bbox"],
            confidence="high",
        ),
        "total": field_with_evidence(
            value=money(record["total"]),
            evidence="synthetic rendered amount to the right of 'TOTAL:' label",
            bbox=total_value["bbox"],
            confidence="high",
        ),
        "currency": field_with_evidence(
            value=record["currency"],
            evidence="synthetic rendered value to the right of 'Currency:' label",
            bbox=currency_value["bbox"],
            confidence="high",
        ),
    }

    raw_entities = {
        "company": record["vendor_name"],
        "date": record["invoice_date"],
        "address": record["vendor_address"],
        "total": money(record["total"]),
        "invoice_number": record["invoice_number"],
        "subtotal": money(record["subtotal"]),
        "tax": money(record["tax"]),
        "currency": record["currency"],
    }

    return {
        "fields": fields,
        "line_items": line_items_output,
        "ocr_blocks": ocr_blocks,
        "raw_entities": raw_entities,
    }


def build_unified_json(
    idx: int,
    image_path: Path,
    rendered: Dict[str, Any],
) -> Dict[str, Any]:
    doc_id = f"synthetic_{idx:06d}"

    unified = {
        "doc_id": doc_id,
        "original_doc_id": doc_id,

        "source": "synthetic",
        "split": "synthetic",
        "document_type": "invoice",

        "image_path": str(image_path),
        "ocr_path": None,
        "entity_path": None,

        "fields": rendered["fields"],
        "line_items": rendered["line_items"],

        "ocr": {
            "source": "synthetic_rendered_text",
            "blocks": rendered["ocr_blocks"],
        },

        "raw_entities": rendered["raw_entities"],

        # Synthetic clean invoices are tier1 by default.
        "tier": "tier1_clean",
    }

    return unified


# ---------------------------------------------------------------------
# Dataset generation
# ---------------------------------------------------------------------

def write_vendors_file(vendor_file: Path) -> None:
    vendor_file.parent.mkdir(parents=True, exist_ok=True)

    vendors = [
        {
            "name": name,
            "status": "approved",
            "risk_level": "low",
            "risk_reason": "",
        }
        for name in VENDOR_NAMES
    ]

    with vendor_file.open("w", encoding="utf-8") as f:
        json.dump(vendors, f, indent=2, ensure_ascii=False)

    print(f"Vendor file written: {vendor_file}")


def generate_dataset(
    num_samples: int,
    image_dir: Path,
    output_dir: Path,
    vendor_file: Path,
    seed: int,
) -> List[Path]:
    random.seed(seed)

    image_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)

    write_vendors_file(vendor_file)

    json_files: List[Path] = []

    for idx in range(num_samples):
        doc_id = f"synthetic_{idx:06d}"
        image_path = image_dir / f"{doc_id}.jpg"
        json_path = output_dir / f"{doc_id}.json"

        record = generate_invoice_record(idx)
        rendered = render_invoice(
            record=record,
            image_path=image_path,
            doc_id=doc_id,
        )

        unified = build_unified_json(
            idx=idx,
            image_path=image_path,
            rendered=rendered,
        )

        with json_path.open("w", encoding="utf-8") as f:
            json.dump(unified, f, indent=2, ensure_ascii=False)

        json_files.append(json_path)

        if (idx + 1) % 50 == 0 or idx == 0:
            print(f"Generated {idx + 1}/{num_samples}")

    manifest_path = output_dir / "manifest.json"

    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump([str(p) for p in json_files], f, indent=2, ensure_ascii=False)

    print(f"Manifest written: {manifest_path}")

    return json_files


def validate_outputs(json_files: List[Path]) -> Dict[str, int]:
    required_fields = [
        "vendor_name",
        "vendor_address",
        "invoice_number",
        "invoice_date",
        "subtotal",
        "tax",
        "total",
        "currency",
    ]

    stats = {
        "total": 0,
        "missing_image_path": 0,
        "missing_required_values": 0,
        "missing_required_bboxes": 0,
        "empty_ocr_blocks": 0,
        "empty_line_items": 0,
    }

    for json_path in json_files:
        stats["total"] += 1

        with json_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        if not Path(data["image_path"]).exists():
            stats["missing_image_path"] += 1

        if not data.get("ocr", {}).get("blocks"):
            stats["empty_ocr_blocks"] += 1

        if not data.get("line_items"):
            stats["empty_line_items"] += 1

        fields = data.get("fields", {})

        missing_value = False
        missing_bbox = False

        for field_name in required_fields:
            field = fields.get(field_name, {})

            if field.get("value") in [None, ""]:
                missing_value = True

            if field.get("bounding_box") in [None, []]:
                missing_bbox = True

        if missing_value:
            stats["missing_required_values"] += 1

        if missing_bbox:
            stats["missing_required_bboxes"] += 1

    return stats


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic invoice data in Agent-ready unified JSON format."
    )

    parser.add_argument(
        "--num-samples",
        type=int,
        default=500,
        help="Number of synthetic invoices to generate.",
    )

    parser.add_argument(
        "--image-dir",
        type=str,
        default=SYNTHETIC_IMAGE_DIR_DEFAULT,
        help="Directory for generated synthetic invoice images.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=UNIFIED_OUTPUT_DIR_DEFAULT,
        help="Directory for generated unified JSON files.",
    )

    parser.add_argument(
        "--vendor-file",
        type=str,
        default=VENDOR_FILE_DEFAULT,
        help="Path to write synthetic vendor database seed file.",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility.",
    )

    args = parser.parse_args()

    image_dir = Path(args.image_dir)
    output_dir = Path(args.output_dir)
    vendor_file = Path(args.vendor_file)

    print("Synthetic image dir:", image_dir)
    print("Unified output dir: ", output_dir)
    print("Vendor file:        ", vendor_file)
    print("Num samples:        ", args.num_samples)
    print("Seed:               ", args.seed)

    json_files = generate_dataset(
        num_samples=args.num_samples,
        image_dir=image_dir,
        output_dir=output_dir,
        vendor_file=vendor_file,
        seed=args.seed,
    )

    stats = validate_outputs(json_files)

    print("\n=== Final Summary ===")
    print(f"Total synthetic JSON files:        {stats['total']}")
    print(f"Missing image paths:               {stats['missing_image_path']}")
    print(f"Samples with empty OCR blocks:     {stats['empty_ocr_blocks']}")
    print(f"Samples with empty line_items:     {stats['empty_line_items']}")
    print(f"Samples missing required values:   {stats['missing_required_values']}")
    print(f"Samples missing required bboxes:   {stats['missing_required_bboxes']}")
    print(f"Output directory:                  {output_dir}")


if __name__ == "__main__":
    main()
