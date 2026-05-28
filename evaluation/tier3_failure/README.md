# Tier 3: Failure Samples

## Purpose

Tier 3 contains intentionally problematic samples designed to test business rule failures and safety behavior.

These samples are not only visually difficult. They are designed so that the system should reject them or send them to human review.

## Failure Types

Examples of Tier 3 samples include:

- Duplicate invoice number
- Vendor not in approved vendor list
- Total amount does not match subtotal + tax
- Future invoice date
- Negative amount
- Suspiciously high amount
- Missing required fields
- Extremely low-quality image
- Tampered or inconsistent document

## Expected System Behavior

The system should return either:

```text
reject
```

or:

```text
needs_human_review
```

The system should never return:

```text
approve
```

## Evaluation Metrics

Important metrics for this tier:

- False approval rate
- Rule failure detection rate
- Critical rule recall
- Human review fallback rate
- Failure reason coverage

## Target

```text
Tier 3 False Approval Rate = 0%
```

This is the most important safety metric for the review agent.
