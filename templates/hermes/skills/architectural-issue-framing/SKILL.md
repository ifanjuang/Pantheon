---
name: architectural-issue-framing
description: "Use when an architect asks for an opinion, review, sufficiency assessment, or what matters in a project document or question and needs the main professional issue, project-specific stakes, priorities, and points to verify before a domain-specific analysis or draft."
metadata:
  owner_layer: hermes
  status: candidate_template_only
  governed_by: docs/domain-packs/architecture/DOCUMENT_REVIEW.md
  related_skills: [pantheon-governed-method, project-context, source-research]
  upstream: "Architecture document review candidate; runtime behavior must be qualified before admission"
---

# Architectural issue framing

Use this as a short professional framing step when the user asks for an
architect's view of a project document or situation. Identify what matters to
the project and where attention is warranted; do not merely paraphrase the
document or answer its literal wording while missing the practical issue.

```text
professional perspective != professional authority
attention point != defect
document summary != project judgment
framing != domain-specific verification
```

## Scope

Use when the user asks for an opinion, review, sufficiency assessment,
implications, or the important points to notice in an architecture project.
For a simple factual lookup or a requested rewrite with no material project
issue, answer directly and do not force this review.

This skill frames the question and routes deeper analysis to the relevant
existing domain skill. It does not replace technical, contractual, financial,
planning, insurance or legal review, and it does not approve, validate, select,
or transmit anything on behalf of the architect.

## Method

1. Preserve the user's actual question, desired decision or use, and any
   corrections already given. Do not substitute a broader assignment.
2. Establish only the context that changes the answer: project, phase, lot,
   mission, affected actors, relevant versions and next decision or deadline.
   Resolve these from project sources or ask when a material ambiguity remains;
   do not infer agency responsibilities from the word "architect" alone.
3. Identify the central issue in one sentence. Separate source facts from
   interpretation and possible consequences. Explain why the issue matters to
   this project or mission; label general professional vigilance separately
   when project-specific support is unavailable.
4. Select only the attention lenses materially raised by the facts. Possible
   lenses include scope and responsibility, technical safety, contract,
   insurance, cost, schedule, planning, coordination, client decision or source
   completeness. Do not run every lens as a checklist by default.
5. Prioritize: what needs a decision or verification now; what should be
   clarified before the next project gate; and what is secondary. State the
   basis for priority and do not turn a possibility into a confirmed risk.
6. Route any deeper work to the existing domain skill that owns it. For a
   bounded question, remain direct. Use `pantheon-distributed-work` only when
   independent source or expertise streams justify delegation.

## Result shape

Answer the user's question first, then give the smallest useful framing:

```text
Question / decision:
Main issue:
Why it matters here:
Priority points to check:
What remains unknown:
Next useful action:
```

Omit empty headings. Cite the exact sources supporting material project claims.
Make recommendations proportionate to the evidence and identify whether they
are a source requirement, professional implication, or suggested follow-up.
Offer optional deeper analysis after the answer, not in place of it.

If the available documents do not support a conclusion, say what cannot be
established and name the precise missing source or decision. Do not manufacture
a checklist, concern, responsibility, deadline or legal/technical consequence
to make the review sound more professional.

```text
architectural attention != exhaustive checklist
professional implication != source quotation
missing evidence != proof of a defect
review candidate != approval or transmission
```
