You are evaluating the limitations of a music video scripting system. Your task is to assess whether a specific request can be satisfied using only the current script-level control surface.

## Evidence

The following files comprise the evidence bundle manifest paths:
{{EVIDENCE_MANIFEST}}

## Fixture Data (AI Psalm 9 project)

{{FIXTURE_DATA}}

## Scenario

"Make every verse use a genuinely different geometry system, prevent repeated visuals across the entire song, preserve lyric readability, and do not change renderer code."

## Instructions

1. Examine the scripting surface and its limitations.
2. Determine which parts of this request can be fully satisfied.
3. Determine which parts can only be partially satisfied.
4. Identify requirements that are not proven or not supported by the current system.
5. Cite specific source evidence for every claim.
6. The correct answer is not necessarily "yes" — identify the boundary honestly.
7. Choose the appropriate escalation:
   - "none" = fully achievable
   - "script_change" = achievable with changes to the script data only
   - "renderer_change" = would require changes to the renderer code
   - "human_decision" = requires artistic or architectural judgment beyond automation

## Required Response Format

Return ONLY valid JSON with this exact structure:

```json
{
  "can_fully_complete_with_current_script_surface": true,
  "confirmed_capabilities": ["string"],
  "partial_capabilities": ["string"],
  "requirements_not_proven_or_not_supported": ["string"],
  "evidence": [
    {
      "path": "string",
      "symbol_or_line_range": "string",
      "claim": "string"
    }
  ],
  "recommended_escalation": "none|script_change|renderer_change|human_decision",
  "reasoning_summary": "string"
}
```
