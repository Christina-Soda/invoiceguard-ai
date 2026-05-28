# Tier 1: Clean Samples

## Purpose

Tier 1 contains clean and standard receipt/invoice samples that the system should process automatically.

These samples are used to evaluate whether InvoiceGuard AI can correctly extract fields and approve low-risk documents without unnecessary human review.

## Sample Criteria

A sample can be placed in Tier 1 if it satisfies most of the following:

- High-quality scanned image
- Text is clear and readable
- No heavy blur or rotation
- No stamp or watermark covering key fields
- Required fields are visible:
  - vendor_name
  - invoice_date
  - vendor_address
  - total
- Amount values are consistent
- Vendor is expected to be valid or low risk

## Expected System Behavior

The expected decision is:

```text
approve
```

The expected confidence should usually be high:

```text
confidence_score > 0.90
```

## Evaluation Metrics

Important metrics for this tier:

- Field exact match
- Field-level F1
- Average normalized string similarity
- Average bounding box availability
- False rejection rate

## Target

```text
Tier 1 False Rejection Rate < 5%
```

That means clean samples should rarely be rejected or sent to human review.
