You are analyzing a music video scripting pipeline. Your task is to map the actual pipeline from inputs to rendered output using the provided evidence.

## Evidence

The following files comprise the evidence bundle manifest paths:
{{EVIDENCE_MANIFEST}}

## Fixture Data (AI Psalm 9 project)

{{FIXTURE_DATA}}

## Instructions

1. Examine the source code and fixture data provided above.
2. Identify the pipeline stages from input ingestion through rendered output.
3. For each stage, list the input and output artifacts.
4. Cite specific source evidence (file path + symbol name or line range) for every claim.
5. If you cannot find code evidence for a claim, label its status as "inference" or "unknown" rather than guessing.
6. Do NOT invent files, symbols, fields, or behavior that are not present in the evidence.

## Required Response Format

Return ONLY valid JSON with this exact structure:

```json
{
  "pipeline_stages": [
    {
      "stage": "string",
      "input_artifacts": ["string"],
      "output_artifacts": ["string"],
      "source_evidence": [
        {
          "path": "string",
          "symbol_or_line_range": "string",
          "claim": "string"
        }
      ],
      "status": "confirmed|inference|unknown"
    }
  ],
  "unresolved_questions": ["string"]
}
```
