# OCR Candidate Evaluation: MiniCPM and Qwen

Date: 2026-10-27  
Status: small comparative trial; not a production qualification

## Scope

Three pages from a scanned construction-reception form were used to compare
MiniCPM OCR output with the local Qwen vision fallback. The sample contained
printed French text, checkboxes, and a small amount of handwriting. Project,
client, and source-location details are intentionally omitted. The temporary
images, model files, and OCR outputs were removed after this note was written.

The trial covered MiniCPM-OCR-1.0 and MiniCPM-OCR-Jev GGUF, Qwen 3.8 27B, and
the Jev consistency decision on Qwen-produced text. It was a visual review, not
a benchmark against a manually transcribed ground truth.

## Observations

- Qwen transcribed the reviewed printed text more accurately overall than Jev
  on this three-page sample. On page 2 it retained words and handwritten dates
  that Jev mistyped or omitted. On page 3 it avoided several visible Jev
  misspellings in the contractual instructions.
- Both systems had weaknesses. Handwriting and the handwritten company name on
  page 1 remained uncertain; checkboxes, signatures, and page furniture also
  need visual review. OCR text must not be treated as verified source content.
- Jev's consistency decision marked reviewed Qwen output as inconsistent even
  though visual inspection did not support that conclusion. This is a false
  alarm for this sample and makes Jev unsuitable as an automatic acceptance
  gate without a better calibrated evaluation.
- Observed processing times were roughly 50–63 seconds per page for Qwen and
  about 69–71 seconds for two Jev pages. These are single-run observations, not
  controlled throughput measurements.
- A comparable Docling result was not obtained in this trial: the MCP
  conversion attempt failed, and the direct CLI path could not load its missing
  OCR weights in the isolated environment. This says nothing conclusive about
  Docling's OCR quality.

## Decision for the current pipeline

Keep Docling as the preferred structural document-processing path and Qwen as
the existing image-based fallback. Do not add MiniCPM-OCR-Jev or Jev's
consistency decision to the production route on the evidence from this trial.
This is a narrow decision about one three-page sample, not a general claim that
MiniCPM or Jev performs poorly.

## Limits and next evaluation

The test did not use ground-truth transcription, a representative document
corpus, repeated timing runs, or a directly comparable Docling extraction. A
future qualification should score character/word error rates, field accuracy,
table and checkbox fidelity, handwritten fields, page completeness, and review
time on a consented, de-identified sample with manually checked ground truth.
