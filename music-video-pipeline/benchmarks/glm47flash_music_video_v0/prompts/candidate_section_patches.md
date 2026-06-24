You are a music video scripting assistant. Your task is to propose three section-level candidate patches using ONLY fields and values proven to exist in the current scripting surface.

## Evidence

The following files comprise the evidence bundle manifest paths:
{{EVIDENCE_MANIFEST}}

## Fixture Data (AI Psalm 9 project)

{{FIXTURE_DATA}}

## Creative Briefs

### Brief 1: Restrained Testimony (restrained_testimony)
Dense lyrics, intimate vocal delivery, low visual activity. Visual clarity prioritized over spectacle. Use subdued colors, minimal motion, clear typography.

### Brief 2: Escalating Hook (escalating_hook)
Percussion and energy rise sharply. The brief requires an actual change in geometry or motion behavior if the system supports one — not merely a palette shift. Use the script surface to increase visual energy.

### Brief 3: Spoken-Word Resolution (spoken_word_resolution)
Sparse final lines, deliberate pacing, lyric legibility, no clutter, clear ending posture.

## Instructions

1. Each patch must be an isolated JSON fragment — NOT a full-song rewrite.
2. Use ONLY fields and values that have code evidence proving they work.
3. Do NOT claim a new geometry family exists unless code evidence supports it.
4. Do NOT modify the fixture script.
5. If no schema/validator exists, validate against the confirmed-field inventory.
6. Be explicit about which visual outcomes cannot be guaranteed.
7. List any changes that would require renderer modifications.

## Required Response Format

Return ONLY valid JSON with this exact structure:

```json
{
  "candidate_patches": [
    {
      "brief_id": "restrained_testimony|escalating_hook|spoken_word_resolution",
      "patch": {},
      "field_rationales": [
        {
          "field": "string",
          "rationale": "string",
          "source_evidence": [
            {
              "path": "string",
              "symbol_or_line_range": "string"
            }
          ]
        }
      ],
      "visual_outcomes_that_cannot_be_guaranteed": ["string"],
      "requires_renderer_change_for": ["string"]
    }
  ]
}
```
