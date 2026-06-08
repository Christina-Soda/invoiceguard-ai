# models/qwen_vl_extractor.py

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import torch
from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
from qwen_vl_utils import process_vision_info


MODEL_ID = os.getenv("INVOICEGUARD_VLM_MODEL", "Qwen/Qwen2.5-VL-7B-Instruct")
MODEL_CACHE_DIR = Path(os.getenv("INVOICEGUARD_MODEL_CACHE", "archs"))
MAX_PIXELS = int(os.getenv("INVOICEGUARD_MAX_PIXELS", str(960 * 28 * 28)))
MIN_PIXELS = int(os.getenv("INVOICEGUARD_MIN_PIXELS", str(256 * 256)))

_model = None
_processor = None


def get_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


INVOICE_EXTRACTION_PROMPT = """
You are a document AI extraction system specialized in invoices and receipts.

Extract fields from this document image.

For EACH field, return:
1. value: extracted value, or null if not found
2. evidence: where/how you see it in the image
3. bounding_box: [x1, y1, x2, y2] pixel coordinates, or null if not visible
4. confidence: "high", "medium", or "low"

Return ONLY valid JSON. Do not use markdown. Do not add explanation.

Required JSON schema:
{
  "fields": {
    "vendor_name": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "vendor_address": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "invoice_number": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "invoice_date": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "due_date": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "subtotal": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "tax": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "shipping": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "discount": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "total": {"value": null, "evidence": null, "bounding_box": null, "confidence": null},
    "currency": {"value": null, "evidence": null, "bounding_box": null, "confidence": null}
  },
  "line_items": [
    {"description": null, "quantity": null, "unit_price": null, "amount": null, "evidence": null}
  ],
  "overall_confidence": 0.0,
  "missing_fields": [],
  "document_quality_issues": []
}
""".strip()


def get_model():
    """Global singleton model loader."""
    global _model, _processor

    if _model is not None and _processor is not None:
        return _model, _processor

    device = get_device()
    if device == "cpu":
        print(
            "WARNING: No GPU detected. Qwen2.5-VL-7B on CPU will be very slow "
            "and may run out of memory. Please run this on a GPU node."
        )

    MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Loading model: {MODEL_ID}")
    print(f"Model cache dir: {MODEL_CACHE_DIR.resolve()}")
    print(f"Image pixels: min={MIN_PIXELS}, max={MAX_PIXELS}")

    _processor = AutoProcessor.from_pretrained(
        MODEL_ID,
        cache_dir=str(MODEL_CACHE_DIR),
        min_pixels=MIN_PIXELS,
        max_pixels=MAX_PIXELS,
    )

    _model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        MODEL_ID,
        cache_dir=str(MODEL_CACHE_DIR),
        torch_dtype=torch.bfloat16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )

    if device == "cpu":
        _model = _model.to("cpu")

    _model.eval()
    print("Model loaded.")
    return _model, _processor


def safe_parse_json(text: str) -> dict[str, Any]:
    """
    Parse model output into JSON robustly.

    Returns a normalized extraction dict with:
    - _parse_success: bool
    - _parse_error: str | None
    - _raw_model_output: original model text
    """
    if not text:
        return empty_extraction(
            reason="EMPTY_OUTPUT",
            raw_text=text,
            parse_error="empty output",
        )

    cleaned = text.strip()

    # Remove common markdown fences.
    cleaned = re.sub(r"^```json\s*", "", cleaned)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    # First attempt: parse whole cleaned text.
    try:
        parsed = json.loads(cleaned)
        return ensure_extraction_shape(
            parsed,
            parse_success=True,
            raw_text=text,
            parse_error=None,
        )
    except json.JSONDecodeError as exc:
        first_error = str(exc)

    # Second attempt: extract first JSON object from surrounding text.
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            return ensure_extraction_shape(
                parsed,
                parse_success=True,
                raw_text=text,
                parse_error=None,
            )
        except json.JSONDecodeError as exc:
            return empty_extraction(
                reason="JSON_PARSE_ERROR",
                raw_text=text,
                parse_error=str(exc),
            )

    return empty_extraction(
        reason="JSON_PARSE_ERROR",
        raw_text=text,
        parse_error=first_error,
    )


def ensure_extraction_shape(
    data: dict[str, Any],
    parse_success: bool,
    raw_text: str | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    """
    Ensure the parsed model output has the expected top-level keys.

    This does not guarantee that every field is correct. It only normalizes
    the output shape for downstream scripts.
    """
    if not isinstance(data, dict):
        return empty_extraction(
            reason="OUTPUT_NOT_OBJECT",
            raw_text=str(data),
            parse_error="parsed JSON is not an object",
        )

    data.setdefault("fields", {})
    data.setdefault("line_items", [])
    data.setdefault("overall_confidence", 0.5)
    data.setdefault("missing_fields", [])
    data.setdefault("document_quality_issues", [])

    data["_parse_success"] = parse_success
    data["_parse_error"] = parse_error
    data["_raw_model_output"] = raw_text

    return data


def empty_extraction(
    reason: str,
    raw_text: str | None = None,
    parse_error: str | None = None,
) -> dict[str, Any]:
    """
    Return a safe empty extraction object when model output is empty or invalid.
    """
    return {
        "fields": {},
        "line_items": [],
        "overall_confidence": 0.0,
        "missing_fields": ["PARSE_ERROR"],
        "document_quality_issues": [reason],
        "_parse_success": False,
        "_parse_error": parse_error,
        "_raw_model_output": raw_text,
    }

def load_prompt(prompt_path: str | Path | None = None) -> str:
    """
    Load a prompt from file. If prompt_path is None, use the built-in prompt.
    """
    if prompt_path is None:
        return INVOICE_EXTRACTION_PROMPT

    prompt_path = Path(prompt_path).expanduser()

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8").strip()


def extract_fields(
    image_path: str | Path,
    prompt_path: str | Path | None = None,
    prompt_text: str | None = None,
) -> dict[str, Any]:
    """
    Input a receipt/invoice image path and output structured JSON.

    Args:
        image_path:
            Path to the image file.
        prompt_path:
            Optional path to a prompt txt file.
        prompt_text:
            Optional direct prompt string. If provided, it overrides prompt_path.

    Returns:
        Parsed extraction dict with _parse_success and _raw_model_output.
    """
    image_path = Path(image_path).expanduser()

    if not image_path.exists():
        return empty_extraction(
            reason="IMAGE_NOT_FOUND",
            raw_text=None,
            parse_error=f"image not found: {image_path}",
        )

    model, processor = get_model()

    if prompt_text is None:
        prompt = load_prompt(prompt_path)
    else:
        prompt = prompt_text.strip()

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "image": str(image_path),
                    "min_pixels": MIN_PIXELS,
                    "max_pixels": MAX_PIXELS,
                },
                {
                    "type": "text",
                    "text": prompt,
                },
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    image_inputs, video_inputs = process_vision_info(messages)
    device = get_device()

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=int(os.getenv("INVOICEGUARD_MAX_NEW_TOKENS", "2048")),
            do_sample=False,
        )

    generated_trimmed = generated_ids[:, inputs.input_ids.shape[1]:]

    output_text = processor.batch_decode(
        generated_trimmed,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )[0]

    return safe_parse_json(output_text)