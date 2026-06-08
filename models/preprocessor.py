# models/preprocessor.py

from __future__ import annotations

from pathlib import Path
import cv2
import fitz  # PyMuPDF
import numpy as np


SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def load_document(file_path: str | Path, dpi: int = 300) -> list[np.ndarray]:
    """
    Load a PDF/image into a list of RGB numpy images.

    PDF: render each page at `dpi`.
    Image: load as RGB.
    """
    path = Path(file_path).expanduser()
    suffix = path.suffix.lower()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if suffix == ".pdf":
        doc = fitz.open(str(path))
        pages: list[np.ndarray] = []

        try:
            for page in doc:
                mat = fitz.Matrix(dpi / 72, dpi / 72)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                img = np.frombuffer(pix.samples, dtype=np.uint8)
                img = img.reshape(pix.height, pix.width, pix.n)

                if pix.n == 1:
                    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
                elif pix.n == 4:
                    img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
                elif pix.n != 3:
                    raise ValueError(f"Unsupported PDF pixel channel count: {pix.n}")

                pages.append(img)
        finally:
            doc.close()

        if not pages:
            raise ValueError(f"PDF has no pages: {path}")
        return pages

    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        img_bgr = cv2.imread(str(path), cv2.IMREAD_COLOR)
        if img_bgr is None:
            raise ValueError(f"OpenCV failed to read image: {path}")
        return [cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)]

    raise ValueError(f"Unsupported file type: {suffix}. Expected PDF or image.")


def deskew_image(img_rgb: np.ndarray) -> np.ndarray:
    """
    Estimate a small skew angle using Hough lines.
    Only correct if angle is within +/- 15 degrees.
    """
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)

    lines = cv2.HoughLines(edges, 1, np.pi / 180, 200)
    if lines is None:
        return img_rgb

    angles: list[float] = []
    for _rho, theta in lines[:30, 0]:
        angle = (theta - np.pi / 2) * 180 / np.pi
        if abs(angle) < 15:
            angles.append(float(angle))

    if not angles:
        return img_rgb

    median_angle = float(np.median(angles))
    if abs(median_angle) < 0.5:
        return img_rgb

    h, w = img_rgb.shape[:2]
    matrix = cv2.getRotationMatrix2D((w // 2, h // 2), median_angle, 1.0)
    return cv2.warpAffine(
        img_rgb,
        matrix,
        (w, h),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def enhance_contrast(img_rgb: np.ndarray) -> np.ndarray:
    """CLAHE contrast enhancement on the L channel."""
    lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)

    enhanced_lab = cv2.merge([enhanced_l, a_channel, b_channel])
    return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2RGB)


def preprocess_image(img_rgb: np.ndarray, enable_denoise: bool = True) -> np.ndarray:
    """Document preprocessing: denoise -> deskew -> contrast enhancement."""
    if img_rgb is None or img_rgb.size == 0:
        raise ValueError("Empty image passed to preprocess_image")

    if enable_denoise:
        img_rgb = cv2.fastNlMeansDenoisingColored(
            img_rgb,
            None,
            h=10,
            hColor=10,
            templateWindowSize=7,
            searchWindowSize=21,
        )

    return enhance_contrast(deskew_image(img_rgb))


def save_page_image(img_rgb: np.ndarray, output_path: str | Path) -> str:
    """Save an RGB numpy image. OpenCV expects BGR, so convert first."""
    out_path = Path(output_path).expanduser()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    success = cv2.imwrite(str(out_path), img_bgr)
    if not success:
        raise RuntimeError(f"Failed to save image to {out_path}")
    return str(out_path)
