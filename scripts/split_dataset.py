#!/usr/bin/env python3
"""
Create project-level Train/Val/Test splits for InvoiceGuard.

Input unified datasets:
- data/unified/sroie2019/train/manifest.json
- data/unified/sroie2019/test/manifest.json
- data/unified/synthetic/manifest.json

Recommended strategy:
- Split SROIE train into train/val.
- Keep SROIE test entirely in project test.
- Split synthetic into train/val/test.

Output:
- data/splits/train_manifest.json
- data/splits/val_manifest.json
- data/splits/test_manifest.json
- data/splits/split_summary.json
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path
from typing import Dict, List, Tuple


PROJECT_ROOT_DEFAULT = "/work/bigweather/xinyanxie/invoiceguard-ai"

SROIE_TRAIN_MANIFEST_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/"
    "data/unified/sroie2019/train/manifest.json"
)

SROIE_TEST_MANIFEST_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/"
    "data/unified/sroie2019/test/manifest.json"
)

SYNTHETIC_MANIFEST_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/"
    "data/unified/synthetic/manifest.json"
)

OUTPUT_DIR_DEFAULT = (
    "/work/bigweather/xinyanxie/invoiceguard-ai/data/splits"
)


def load_manifest(path: Path) -> List[str]:
    if not path.exists():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Manifest must be a list: {path}")

    return [str(x) for x in data]


def split_list(
    items: List[str],
    train_ratio: float,
    val_ratio: float,
    test_ratio: float,
    seed: int,
) -> Tuple[List[str], List[str], List[str]]:
    """
    Split a list into train/val/test by ratio.
    """
    if abs(train_ratio + val_ratio + test_ratio - 1.0) > 1e-6:
        raise ValueError("train_ratio + val_ratio + test_ratio must equal 1.0")

    rng = random.Random(seed)
    items = list(items)
    rng.shuffle(items)

    n = len(items)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train = items[:n_train]
    val = items[n_train:n_train + n_val]
    test = items[n_train + n_val:]

    return train, val, test


def split_train_val(
    items: List[str],
    train_ratio: float,
    seed: int,
) -> Tuple[List[str], List[str]]:
    """
    Split a list into train/val only.
    """
    rng = random.Random(seed)
    items = list(items)
    rng.shuffle(items)

    n_train = int(len(items) * train_ratio)

    train = items[:n_train]
    val = items[n_train:]

    return train, val


def write_manifest(path: Path, items: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(items):>4} samples -> {path}")


def summarize_sources(items: List[str]) -> Dict[str, int]:
    summary = {
        "sroie2019_train": 0,
        "sroie2019_test": 0,
        "synthetic": 0,
        "unknown": 0,
    }

    for p in items:
        if "/sroie2019/train/" in p:
            summary["sroie2019_train"] += 1
        elif "/sroie2019/test/" in p:
            summary["sroie2019_test"] += 1
        elif "/synthetic/" in p:
            summary["synthetic"] += 1
        else:
            summary["unknown"] += 1

    return summary


def validate_no_overlap(
    train: List[str],
    val: List[str],
    test: List[str],
) -> None:
    train_set = set(train)
    val_set = set(val)
    test_set = set(test)

    overlaps = {
        "train_val": len(train_set & val_set),
        "train_test": len(train_set & test_set),
        "val_test": len(val_set & test_set),
    }

    bad = {k: v for k, v in overlaps.items() if v != 0}

    if bad:
        raise ValueError(f"Split overlap detected: {bad}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create project-level Train/Val/Test manifests."
    )

    parser.add_argument(
        "--sroie-train-manifest",
        type=str,
        default=SROIE_TRAIN_MANIFEST_DEFAULT,
    )

    parser.add_argument(
        "--sroie-test-manifest",
        type=str,
        default=SROIE_TEST_MANIFEST_DEFAULT,
    )

    parser.add_argument(
        "--synthetic-manifest",
        type=str,
        default=SYNTHETIC_MANIFEST_DEFAULT,
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR_DEFAULT,
    )

    parser.add_argument(
        "--sroie-train-ratio",
        type=float,
        default=0.85,
        help="Ratio of original SROIE train used for project train; remainder goes to val.",
    )

    parser.add_argument(
        "--synthetic-train-ratio",
        type=float,
        default=0.70,
    )

    parser.add_argument(
        "--synthetic-val-ratio",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--synthetic-test-ratio",
        type=float,
        default=0.15,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    args = parser.parse_args()

    sroie_train_manifest = Path(args.sroie_train_manifest)
    sroie_test_manifest = Path(args.sroie_test_manifest)
    synthetic_manifest = Path(args.synthetic_manifest)
    output_dir = Path(args.output_dir)

    print("Loading manifests...")
    print("SROIE train manifest:", sroie_train_manifest)
    print("SROIE test manifest: ", sroie_test_manifest)
    print("Synthetic manifest:  ", synthetic_manifest)

    sroie_train_all = load_manifest(sroie_train_manifest)
    sroie_test_all = load_manifest(sroie_test_manifest)
    synthetic_all = load_manifest(synthetic_manifest)

    print("\nInput counts:")
    print(f"  SROIE train: {len(sroie_train_all)}")
    print(f"  SROIE test:  {len(sroie_test_all)}")
    print(f"  Synthetic:   {len(synthetic_all)}")

    # 1. Split original SROIE train into project train/val.
    sroie_train, sroie_val = split_train_val(
        sroie_train_all,
        train_ratio=args.sroie_train_ratio,
        seed=args.seed,
    )

    # 2. Keep original SROIE test entirely in project test.
    sroie_test = list(sroie_test_all)

    # 3. Split synthetic into train/val/test.
    syn_train, syn_val, syn_test = split_list(
        synthetic_all,
        train_ratio=args.synthetic_train_ratio,
        val_ratio=args.synthetic_val_ratio,
        test_ratio=args.synthetic_test_ratio,
        seed=args.seed + 1,
    )

    # 4. Combine project-level splits.
    project_train = sroie_train + syn_train
    project_val = sroie_val + syn_val
    project_test = sroie_test + syn_test

    # 5. Shuffle combined splits for training convenience.
    rng = random.Random(args.seed + 2)
    rng.shuffle(project_train)
    rng.shuffle(project_val)
    rng.shuffle(project_test)

    validate_no_overlap(project_train, project_val, project_test)

    # 6. Write outputs.
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "train_manifest.json"
    val_path = output_dir / "val_manifest.json"
    test_path = output_dir / "test_manifest.json"
    summary_path = output_dir / "split_summary.json"

    write_manifest(train_path, project_train)
    write_manifest(val_path, project_val)
    write_manifest(test_path, project_test)

    summary = {
        "seed": args.seed,
        "strategy": {
            "sroie_train": (
                "split original SROIE train into project train/val"
            ),
            "sroie_test": (
                "keep original SROIE test entirely in project test"
            ),
            "synthetic": (
                "split synthetic into train/val/test"
            ),
        },
        "input_counts": {
            "sroie_train": len(sroie_train_all),
            "sroie_test": len(sroie_test_all),
            "synthetic": len(synthetic_all),
        },
        "ratios": {
            "sroie_train_ratio": args.sroie_train_ratio,
            "sroie_val_ratio": 1.0 - args.sroie_train_ratio,
            "synthetic_train_ratio": args.synthetic_train_ratio,
            "synthetic_val_ratio": args.synthetic_val_ratio,
            "synthetic_test_ratio": args.synthetic_test_ratio,
        },
        "output_counts": {
            "train": len(project_train),
            "val": len(project_val),
            "test": len(project_test),
        },
        "source_breakdown": {
            "train": summarize_sources(project_train),
            "val": summarize_sources(project_val),
            "test": summarize_sources(project_test),
        },
    }

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"Wrote summary -> {summary_path}")

    print("\n=== Split Summary ===")
    print(f"Train: {len(project_train)}")
    print(f"Val:   {len(project_val)}")
    print(f"Test:  {len(project_test)}")

    print("\nSource breakdown:")
    for split_name, items in [
        ("train", project_train),
        ("val", project_val),
        ("test", project_test),
    ]:
        print(f"  {split_name}: {summarize_sources(items)}")


if __name__ == "__main__":
    main()
