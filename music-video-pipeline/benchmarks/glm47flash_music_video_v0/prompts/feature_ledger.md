You are auditing a music video scripting system. Your task is to identify every script-level feature and verify where each is actually interpreted in the renderer or canvas pipeline.

## Evidence

The following files comprise the evidence bundle manifest paths:
{{EVIDENCE_MANIFEST}}

## Fixture Data (AI Psalm 9 project)

{{FIXTURE_DATA}}

## Instructions

1. Scan the script.json structure for every field and concept.
2. For each field, find where it is actually read/consumed in the renderer, canvas, or effect code.
3. A template example alone does NOT prove renderer support.
4. A field name alone does NOT prove a visual effect.
5. Label each feature's status:
   - "confirmed" = code evidence proves it produces a visible/behavioral effect in the rendered output
   - "inference" = plausible but not fully proven by code evidence
   - "unknown" = no code evidence found
6. Document interactions, override conditions, and which fields override which.
7. Collect unsupported or unproven claims separately.

## Required Response Format

Return ONLY valid JSON with this exact structure:

```json
{
  "features": [
    {
      "script_field_or_concept": "string",
      "supported_values_or_shape": "string",
      "source_evidence": [
        {
          "path": "string",
          "symbol_or_line_range": "string"
        }
      ],
      "confirmed_renderer_or_canvas_effect": "string",
      "interactions_or_override_conditions": ["string"],
      "status": "confirmed|inference|unknown",
      "notes": "string"
    }
  ],
  "unsupported_or_unproven_claims": ["string"]
}
```
