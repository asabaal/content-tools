# Authoritative Source Reports - Implementation Plan

## Goal
Generate isolated authoritative source reports for verification debugging.

## Data Sources

### Tool 02 - Text Authority
- **Source**: `project['transcript']['segments']`
- **Fields**: id, original_id, original_video_id, text, start, end, words[]
- **Word fields**: text, start, end
- **Report**: Word index, text, segment index, clip assignment

### Tool 03 - Clip Selection  
- **Source**: `project['clips']`
- **Filter**: clips with `selected_segment` defined
- **Sort**: by `timeline_position`
- **Fields**: id, name, selected_segment, timeline_position
- **Report**: Clip order, clip_id, segment_idx, start, end, text preview

### Tool 04 - Assembly Timing
- **Source**: `compute_timeline_clips()` → `build_caption_events()`
- **Fields**: 
  - Event: segment_index, clip_id, output_start, output_end, words[]
  - Word: text, start, end, word_index
- **Report**: Word timing table + clip boundary table

## Output Files

```
data/output/verification/source_reports/
├── tool02_review_text_report.html
├── tool03_take_selection_report.html
├── tool04_assembly_timing_report.html
└── authoritative_sources_summary.html
```

## Cross-Reference Keys
- `clip_id` - consistent clip identifier
- `segment_index` - transcript segment reference  
- `word_index` - word position within segment/event

## Implementation

### File: tools/05b-render/source_reports.py (NEW)

```python
#!/usr/bin/env python3
"""Generate isolated authoritative source reports."""

def generate_tool02_report(project, output_dir) -> Path:
    """Text authority from transcript segments."""
    
def generate_tool03_report(project, output_dir) -> Path:
    """Clip selection authority."""
    
def generate_tool04_report(project, output_dir) -> Path:
    """Assembly timing authority."""
    
def generate_summary_report(metrics, output_dir) -> Path:
    """Cross-reference summary."""

def run_source_reports(project_root) -> Dict:
    """Main entry point."""
```

### File: tools/05b-render/verify_captions.py (EDIT)

Add argument:
```python
parser.add_argument('--source-reports', action='store_true', 
                    help='Generate source reports only')
```

Add mode in main():
```python
if args.source_reports:
    from source_reports import run_source_reports
    result = run_source_reports(root)
    sys.exit(0 if result['success'] else 1)
```

## HTML Report Structure

Each report includes:
- Header with report name and timestamp
- Summary metrics section
- Data table with sortable columns
- Cross-reference links to other reports

## Execution

```bash
python tools/05b-render/verify_captions.py --project <root> --source-reports
```

## Success Criteria

1. tool02_review_text_report.html generated with word→segment→clip mapping
2. tool03_take_selection_report.html generated with clip ordering
3. tool04_assembly_timing_report.html generated with timing data
4. authoritative_sources_summary.html with cross-reference counts
5. All reports in data/output/verification/source_reports/
