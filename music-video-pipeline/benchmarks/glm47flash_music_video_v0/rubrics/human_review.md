# GLM-4.7-Flash Music Video Scripting Benchmark v0 — Human Review Rubric

## Scoring Guide

Each category is scored 0–2.

| Score | Meaning |
|-------|---------|
| **0** | Missing, incorrect, or hallucinated. The model fails this criterion. |
| **1** | Partially correct or ambiguous. Some evidence present, but gaps or errors exist. |
| **2** | Fully correct and well-grounded in evidence. No hallucination or unsupported claim. |

---

## Categories

### 1. Architecture Grounding
Does the model correctly map the pipeline from inputs to rendered output?

- **0**: Invented stages, wrong artifact names, no source citations.
- **1**: Mostly correct pipeline but missing stages or citing irrelevant evidence.
- **2**: Accurate pipeline stages, correct input/output artifacts, properly cited source evidence for each stage.

### 2. Feature Grounding
Does the model correctly identify script-level features and their renderer support?

- **0**: Claims features that don't exist; cites template examples as renderer proof; no code evidence.
- **1**: Identifies real features but mislabels some as "confirmed" without renderer evidence or misses key interactions.
- **2**: Every feature mapped to actual code consumption; status values are appropriate; interactions documented.

### 3. Unsupported Claims / Hallucinations
Does the model invent files, symbols, fields, or behavior?

- **0**: Multiple invented files, fields, or behavior that don't exist in the codebase.
- **1**: One or two minor fabrications but generally grounded.
- **2**: Zero inventions. Every claim is traceable to the evidence bundle.

### 4. Patch Validity (candidate_section_patches only)
Are the proposed patches structurally valid and constrained to proven fields?

- **0**: Patch uses fields not in confirmed inventory; full-song rewrite instead of fragment; references unsupported values.
- **1**: Mostly valid patches but one or two questionable field choices or values.
- **2**: All patches use only confirmed fields and values; structure is correct; limitations honestly stated.

### 5. Scope Discipline
Does the model stay within the defined task scope?

- **0**: Proposes renderer changes, new features, or external dependencies when explicitly prohibited.
- **1**: Mostly stays in scope but makes one out-of-scope suggestion.
- **2**: Respects all scope constraints. Does not propose renderer changes or new features.

### 6. Boundary Awareness (safe_boundary only)
Does the model accurately identify what the scripting surface can and cannot do?

- **0**: Answers "yes" when the system clearly lacks the capability; no evidence cited.
- **1**: Acknowledges some limitations but underestimates the gap between request and capability.
- **2**: Honest assessment with clear distinction between confirmed, partial, and unsupported capabilities; appropriate escalation recommendation.

### 7. Creative Usefulness
Is the response practically useful for a human editor?

- **0**: Schema-valid but useless — e.g., empty patches, trivial changes, irrelevant analysis.
- **1**: Some useful elements but mixed with noise or irrelevant detail.
- **2**: Provides actionable insight, clear rationale, and honest limitations; a human editor would find it helpful.

---

## Overall Assessment

| Score Range | Rating |
|-------------|--------|
| 12–14 | Excellent — model is reliable for this task |
| 8–11 | Acceptable — usable with human verification |
| 4–7 | Marginal — significant gaps; route to stronger model |
| 0–3 | Unacceptable — do not route to Flash for this task |

---

## Notes for Reviewer

- Review the raw response alongside the evidence manifest.
- Check each source citation manually: does the cited line actually support the claim?
- For candidate patches, verify that patch fields exist in the confirmed-field inventory.
- Rate limits and API availability are NOT part of this scoring.
- This rubric assesses the model's response quality, NOT the visual output quality.
- "Recommended escalation" for safe_boundary should match the assessment; flag contradictions.
