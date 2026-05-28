# Tier 2: Hard Samples

## Purpose

Tier 2 contains difficult samples where the system should express uncertainty instead of overconfidently approving the document.

These samples are used to test whether InvoiceGuard AI can detect low-quality or ambiguous documents and route them to human review.

## Sample Criteria

A sample can be placed in Tier 2 if it contains at least one of the following:

- Low resolution
- Blur
- Rotation or skew
- Low contrast
- Stamp or watermark over key fields
- Partial occlusion
- Non-standard layout
- Handwritten or mixed-format fields
- Key fields are visible but hard to read

## Expected System Behavior

The expected decision is:

```text
needs_human_review
```

The expected confidence range is usually:

```text
0.60 <= confidence_score <= 0.85
```

## Evaluation Metrics

Important metrics for this tier:

- Human review trigger rate
- False approval rate
- Field extraction accuracy under noisy conditions
- Missing bounding box rate
- Grounding mismatch rate

## Target

```text
Tier 2 Human Review Trigger Rate > 80%
```

That means difficult samples should usually be routed to human review instead of being automatically approved.
