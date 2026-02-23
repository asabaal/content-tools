#!/usr/bin/env python3
"""Verify caption completeness and timing without rendering."""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from segments import compute_timeline_clips
from captions import build_caption_events
from srt import generate_srt_content


def get_project_root() -> Path:
    return Path(__file__).parent.parent.parent


def load_project(project_path: str | Path | None = None) -> dict:
    if project_path is None:
        project_path = get_project_root() / 'data' / 'project.json'
    with open(str(project_path), 'r', encoding='utf-8') as f:
        return json.load(f)


def normalize_word(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^\w\']', '', text)
    return text


def parse_srt(srt_content: str) -> List[Dict[str, Any]]:
    blocks = []
    current_block = {}
    
    for line in srt_content.strip().split('\n'):
        line = line.strip()
        if not line:
            if current_block:
                blocks.append(current_block)
                current_block = {}
            continue
        
        if current_block.get('index') is None:
            try:
                current_block['index'] = int(line)
            except ValueError:
                if 'text' in current_block:
                    current_block['text'] += ' ' + line
                else:
                    current_block['text'] = line
        elif 'start' not in current_block:
            match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2}),(\d{3})', line)
            if match:
                h1, m1, s1, ms1, h2, m2, s2, ms2 = map(int, match.groups())
                current_block['start'] = h1 * 3600 + m1 * 60 + s1 + ms1 / 1000
                current_block['end'] = h2 * 3600 + m2 * 60 + s2 + ms2 / 1000
        else:
            if 'text' in current_block:
                current_block['text'] += ' ' + line
            else:
                current_block['text'] = line
    
    if current_block:
        blocks.append(current_block)
    
    for block in blocks:
        if 'text' in block:
            words = []
            for word in block['text'].split():
                norm = normalize_word(word)
                if norm:
                    words.append({'text': word, 'normalized': norm})
            block['words'] = words
    
    return blocks


def check_coverage(
    caption_events: List[Dict[str, Any]],
    project: dict,
    timeline_clips: List[dict]
) -> Dict[str, Any]:
    expected_words = []
    for item in timeline_clips:
        clip = item['clip']
        selected = clip.get('selected_segment', {})
        original_video_id = selected.get('original_video_id', '')
        
        for seg_start, seg_end in item['playable_segments']:
            for seg in project.get('transcript', {}).get('segments', []):
                if (seg.get('original_video_id') == original_video_id and
                    seg.get('start') <= seg_start < seg.get('end')):
                    for word in seg.get('words', []):
                        if word.get('end') > seg_start and word.get('start') < seg_end:
                            expected_words.append({
                                'text': word.get('text', ''),
                                'normalized': normalize_word(word.get('text', '')),
                                'start': word.get('start'),
                                'end': word.get('end')
                            })
                    break
    
    captioned_words = []
    for event in caption_events:
        for word in event.get('words', []):
            captioned_words.append({
                'text': word.get('text', ''),
                'normalized': normalize_word(word.get('text', '')),
                'start': word.get('start'),
                'end': word.get('end')
            })
    
    expected_normalized = [w['normalized'] for w in expected_words]
    captioned_normalized = [w['normalized'] for w in captioned_words]
    
    expected_set = set(expected_normalized)
    captioned_set = set(captioned_normalized)
    
    missing_words = list(expected_set - captioned_set)
    extra_words = list(captioned_set - expected_set)
    
    expected_counts = {}
    for w in expected_normalized:
        expected_counts[w] = expected_counts.get(w, 0) + 1
    
    captioned_counts = {}
    for w in captioned_normalized:
        captioned_counts[w] = captioned_counts.get(w, 0) + 1
    
    duplicated = []
    for word, count in captioned_counts.items():
        if count > expected_counts.get(word, 0):
            duplicated.append({'word': word, 'count': count, 'expected': expected_counts.get(word, 0)})
    
    if expected_normalized:
        coverage_pct = len([w for w in captioned_normalized if w in expected_set]) / len(expected_normalized) * 100
    else:
        coverage_pct = 0.0
    
    missing_with_times = []
    for w in expected_words:
        if w['normalized'] in missing_words:
            missing_with_times.append({
                'word': w['text'],
                'normalized': w['normalized'],
                'transcript_time': w['start']
            })
    
    return {
        'passed': coverage_pct >= 95.0 and len(missing_words) <= 5,
        'expected_word_count': len(expected_words),
        'captioned_word_count': len(captioned_words),
        'unique_expected': len(expected_set),
        'unique_captioned': len(captioned_set),
        'coverage_percentage': round(coverage_pct, 2),
        'missing_words': missing_with_times[:50],
        'missing_count': len(missing_words),
        'extra_words': extra_words[:20],
        'duplicated_words': duplicated[:20]
    }


def check_timing_monotonicity(caption_events: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues = []
    
    for event_idx, event in enumerate(caption_events):
        words = event.get('words', [])
        if not words:
            continue
        
        sorted_words = sorted(words, key=lambda w: w.get('start', 0))
        
        for i, word in enumerate(sorted_words):
            start = word.get('start', 0)
            end = word.get('end', 0)
            
            if end <= start:
                issues.append({
                    'type': 'zero_or_negative_duration',
                    'event_index': event_idx,
                    'word': word.get('text'),
                    'start': start,
                    'end': end
                })
            
            if i > 0:
                prev_end = sorted_words[i-1].get('end', 0)
                if start < prev_end - 0.1:
                    issues.append({
                        'type': 'word_overlap',
                        'event_index': event_idx,
                        'word': word.get('text'),
                        'prev_word': sorted_words[i-1].get('text'),
                        'gap': start - prev_end
                    })
    
    all_word_times = []
    for event_idx, event in enumerate(caption_events):
        output_start = event.get('output_start', 0)
        original_start = event.get('original_start', 0)
        
        for word in event.get('words', []):
            word_rel_start = word.get('start', 0) - original_start
            word_rel_end = word.get('end', 0) - original_start
            
            all_word_times.append({
                'event_index': event_idx,
                'word': word.get('text'),
                'output_start': output_start + word_rel_start,
                'output_end': output_start + word_rel_end
            })
    
    for i in range(1, len(all_word_times)):
        curr = all_word_times[i]
        prev = all_word_times[i-1]
        
        if curr['output_start'] < prev['output_start'] - 0.1:
            issues.append({
                'type': 'non_monotonic_output_time',
                'event_index': curr['event_index'],
                'word': curr['word'],
                'output_start': curr['output_start'],
                'prev_word': prev['word'],
                'prev_output_start': prev['output_start']
            })
    
    hard_failures = [i for i in issues if i['type'] in ('zero_or_negative_duration', 'non_monotonic_output_time')]
    
    return {
        'passed': len(hard_failures) == 0,
        'total_issues': len(issues),
        'hard_failures': len(hard_failures),
        'issues': issues[:50]
    }


def check_segment_mapping(
    timeline_clips: List[dict],
    caption_events: List[Dict[str, Any]]
) -> Dict[str, Any]:
    timeline_order = []
    for item in timeline_clips:
        clip = item['clip']
        timeline_position = clip.get('timeline_position', 0)
        for seg_start, seg_end in item['playable_segments']:
            timeline_order.append({
                'timeline_position': timeline_position,
                'segment_start': seg_start,
                'segment_end': seg_end
            })
    
    event_order = []
    for event in caption_events:
        event_order.append({
            'output_start': event.get('output_start', 0),
            'original_start': event.get('original_start', 0)
        })
    
    reorderings = []
    for i in range(1, len(event_order)):
        if event_order[i]['output_start'] < event_order[i-1]['output_start']:
            reorderings.append({
                'index': i,
                'current_output_start': event_order[i]['output_start'],
                'prev_output_start': event_order[i-1]['output_start']
            })
    
    return {
        'passed': len(reorderings) == 0,
        'timeline_clip_count': len(timeline_order),
        'event_count': len(event_order),
        'reorderings': reorderings[:5]
    }


def check_line_completeness(
    caption_events: List[Dict[str, Any]],
    srt_blocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    issues = []
    
    for event_idx, event in enumerate(caption_events):
        words = event.get('words', [])
        
        if not words:
            issues.append({
                'type': 'empty_event',
                'event_index': event_idx,
                'output_start': event.get('output_start'),
                'output_end': event.get('output_end')
            })
    
    event_texts = []
    for event in caption_events:
        text = ' '.join(w.get('text', '') for w in event.get('words', []))
        event_texts.append(normalize_word(text))
    
    srt_texts = []
    for block in srt_blocks:
        text = ' '.join(w.get('text', '') for w in block.get('words', []))
        srt_texts.append(normalize_word(text))
    
    full_event_text = ' '.join(event_texts)
    full_srt_text = ' '.join(srt_texts)
    
    event_words = set(full_event_text.split())
    srt_words = set(full_srt_text.split())
    
    missing_in_srt = event_words - srt_words
    extra_in_srt = srt_words - event_words
    
    return {
        'passed': len([i for i in issues if i['type'] == 'empty_event']) == 0,
        'total_events': len(caption_events),
        'events_with_words': sum(1 for e in caption_events if e.get('words')),
        'events_without_words': sum(1 for e in caption_events if not e.get('words')),
        'srt_block_count': len(srt_blocks),
        'issues': issues[:50],
        'words_missing_in_srt': list(missing_in_srt)[:20],
        'words_extra_in_srt': list(extra_in_srt)[:20]
    }


def generate_html_report(
    caption_events: List[Dict[str, Any]],
    coverage_result: Dict[str, Any],
    timing_result: Dict[str, Any],
    segment_result: Dict[str, Any],
    completeness_result: Dict[str, Any],
    output_path: Path
) -> None:
    all_passed = (
        coverage_result['passed'] and
        timing_result['passed'] and
        segment_result['passed'] and
        completeness_result['passed']
    )
    
    status_class = 'pass' if all_passed else 'fail'
    status_text = 'ALL CHECKS PASSED' if all_passed else 'SOME CHECKS FAILED'
    
    html_parts = [
        '<!DOCTYPE html>',
        '<html lang="en">',
        '<head>',
        '<meta charset="UTF-8">',
        '<title>Caption Verification Report</title>',
        '<style>',
        'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 40px; background: #f5f5f5; }',
        '.container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }',
        'h1 { color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }',
        'h2 { color: #555; margin-top: 30px; }',
        '.status { padding: 15px 20px; border-radius: 4px; font-weight: bold; font-size: 18px; margin-bottom: 20px; }',
        '.status.pass { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }',
        '.status.fail { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }',
        '.check { margin-bottom: 25px; padding: 15px; background: #f9f9f9; border-radius: 4px; }',
        '.check h3 { margin-top: 0; }',
        '.check.pass { border-left: 4px solid #4CAF50; }',
        '.check.fail { border-left: 4px solid #f44336; }',
        'table { width: 100%; border-collapse: collapse; margin-top: 15px; }',
        'th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }',
        'th { background: #4CAF50; color: white; }',
        'tr:nth-child(even) { background: #f9f9f9; }',
        'tr:hover { background: #f1f1f1; }',
        '.flag { background: #fff3cd; padding: 2px 6px; border-radius: 3px; font-size: 12px; }',
        '.missing-word { background: #f8d7da; padding: 4px 8px; margin: 2px; display: inline-block; border-radius: 3px; }',
        '.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-bottom: 20px; }',
        '.stat { background: #e9ecef; padding: 15px; border-radius: 4px; text-align: center; }',
        '.stat-value { font-size: 24px; font-weight: bold; color: #333; }',
        '.stat-label { font-size: 12px; color: #666; text-transform: uppercase; }',
        '</style>',
        '</head>',
        '<body>',
        '<div class="container">',
        f'<h1>Caption Verification Report</h1>',
        f'<p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>',
        f'<div class="status {status_class}">{status_text}</div>',
    ]
    
    html_parts.append('<div class="stats">')
    html_parts.append(f'<div class="stat"><div class="stat-value">{coverage_result["coverage_percentage"]:.1f}%</div><div class="stat-label">Coverage</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{coverage_result["captioned_word_count"]}</div><div class="stat-label">Captioned Words</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{completeness_result["total_events"]}</div><div class="stat-label">Caption Events</div></div>')
    html_parts.append(f'<div class="stat"><div class="stat-value">{timing_result["total_issues"]}</div><div class="stat-label">Timing Issues</div></div>')
    html_parts.append('</div>')
    
    check_class = 'pass' if coverage_result['passed'] else 'fail'
    html_parts.append(f'<div class="check {check_class}">')
    html_parts.append(f'<h3>A. Coverage Check: {"PASS" if coverage_result["passed"] else "FAIL"}</h3>')
    html_parts.append(f'<p>Expected: {coverage_result["expected_word_count"]} words, Captioned: {coverage_result["captioned_word_count"]} words</p>')
    html_parts.append(f'<p>Coverage: {coverage_result["coverage_percentage"]:.2f}%</p>')
    
    if coverage_result['missing_words']:
        html_parts.append('<h4>Missing Words:</h4>')
        html_parts.append('<div style="max-height: 200px; overflow-y: auto;">')
        for mw in coverage_result['missing_words'][:30]:
            html_parts.append(f'<span class="missing-word">{mw["word"]} ({mw["transcript_time"]:.2f}s)</span>')
        html_parts.append('</div>')
    
    if coverage_result['duplicated_words']:
        html_parts.append('<h4>Duplicated Words:</h4>')
        for dw in coverage_result['duplicated_words'][:10]:
            html_parts.append(f'<span class="flag">{dw["word"]}: {dw["count"]} (expected {dw["expected"]})</span> ')
    
    html_parts.append('</div>')
    
    check_class = 'pass' if timing_result['passed'] else 'fail'
    html_parts.append(f'<div class="check {check_class}">')
    html_parts.append(f'<h3>B. Timing Monotonicity Check: {"PASS" if timing_result["passed"] else "FAIL"}</h3>')
    html_parts.append(f'<p>Total issues: {timing_result["total_issues"]}, Hard failures: {timing_result["hard_failures"]}</p>')
    
    if timing_result['issues']:
        html_parts.append('<table><tr><th>Type</th><th>Event</th><th>Word</th><th>Details</th></tr>')
        for issue in timing_result['issues'][:20]:
            details = {k: v for k, v in issue.items() if k not in ('type', 'event_index', 'word')}
            html_parts.append(f'<tr><td>{issue["type"]}</td><td>{issue.get("event_index", "-")}</td><td>{issue.get("word", "-")}</td><td>{json.dumps(details)}</td></tr>')
        html_parts.append('</table>')
    
    html_parts.append('</div>')
    
    check_class = 'pass' if segment_result['passed'] else 'fail'
    html_parts.append(f'<div class="check {check_class}">')
    html_parts.append(f'<h3>C. Segment Mapping Check: {"PASS" if segment_result["passed"] else "FAIL"}</h3>')
    html_parts.append(f'<p>Timeline clips: {segment_result["timeline_clip_count"]}, Events: {segment_result["event_count"]}</p>')
    
    if segment_result['reorderings']:
        html_parts.append('<h4>Reorderings Detected:</h4>')
        html_parts.append('<table><tr><th>Index</th><th>Current Start</th><th>Previous Start</th></tr>')
        for r in segment_result['reorderings']:
            html_parts.append(f'<tr><td>{r["index"]}</td><td>{r["current_output_start"]:.3f}</td><td>{r["prev_output_start"]:.3f}</td></tr>')
        html_parts.append('</table>')
    
    html_parts.append('</div>')
    
    check_class = 'pass' if completeness_result['passed'] else 'fail'
    html_parts.append(f'<div class="check {check_class}">')
    html_parts.append(f'<h3>D. Line Completeness Check: {"PASS" if completeness_result["passed"] else "FAIL"}</h3>')
    html_parts.append(f'<p>Events with words: {completeness_result["events_with_words"]}/{completeness_result["total_events"]}</p>')
    html_parts.append(f'<p>SRT blocks: {completeness_result["srt_block_count"]}</p>')
    
    if completeness_result['issues']:
        html_parts.append('<h4>Issues:</h4>')
        for issue in completeness_result['issues'][:10]:
            html_parts.append(f'<span class="flag">{issue["type"]}: event {issue["event_index"]}</span> ')
    
    html_parts.append('</div>')
    
    html_parts.append('<h2>Caption Events Detail</h2>')
    html_parts.append('<table><tr><th>#</th><th>Output Start</th><th>Output End</th><th>Text</th><th>Words</th><th>Flags</th></tr>')
    
    for event_idx, event in enumerate(caption_events):
        words = event.get('words', [])
        text = ' '.join(w.get('text', '') for w in words[:5])
        if len(words) > 5:
            text += '...'
        
        flags = []
        if not words:
            flags.append('EMPTY')
        
        flag_html = ' '.join(f'<span class="flag">{f}</span>' for f in flags) if flags else '-'
        
        html_parts.append(f'<tr><td>{event_idx}</td><td>{event.get("output_start", 0):.3f}</td><td>{event.get("output_end", 0):.3f}</td><td>{text}</td><td>{len(words)}</td><td>{flag_html}</td></tr>')
    
    html_parts.append('</table>')
    
    html_parts.extend([
        '</div>',
        '</body>',
        '</html>'
    ])
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(html_parts))


def main():
    parser = argparse.ArgumentParser(description='Verify caption completeness and timing')
    parser.add_argument('--project', '-p', type=str, help='Path to project.json or project root')
    parser.add_argument('--data-dir', '-d', type=str, help='Path to data directory')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    args = parser.parse_args()
    
    root = get_project_root()
    
    if args.project:
        project_arg = Path(args.project)
        if project_arg.is_dir():
            project_path = project_arg / 'data' / 'project.json'
            data_dir = project_arg / 'data'
        else:
            project_path = project_arg
            data_dir = project_arg.parent
    else:
        project_path = root / 'data' / 'project.json'
        data_dir = root / 'data'
    
    if args.data_dir:
        data_dir = Path(args.data_dir)
    
    output_dir = data_dir / 'output'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading project: {project_path}")
    project = load_project(str(project_path))
    
    print("Computing timeline clips...")
    timeline_clips = compute_timeline_clips(project)
    
    print("Building caption events...")
    caption_events = build_caption_events(project, timeline_clips)
    print(f"  Found {len(caption_events)} caption events")
    
    srt_path = output_dir / 'captions.srt'
    if srt_path.exists():
        print(f"Loading existing SRT: {srt_path}")
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
    else:
        print("Generating SRT content...")
        srt_content = generate_srt_content(caption_events)
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        print(f"  Saved SRT to: {srt_path}")
    
    srt_blocks = parse_srt(srt_content)
    print(f"  Parsed {len(srt_blocks)} SRT blocks")
    
    print("\nRunning verification checks...")
    
    print("  A. Coverage check...")
    coverage_result = check_coverage(caption_events, project, timeline_clips)
    if args.verbose:
        print(f"     Coverage: {coverage_result['coverage_percentage']:.2f}%")
        print(f"     Missing: {coverage_result['missing_count']} words")
    
    print("  B. Timing monotonicity check...")
    timing_result = check_timing_monotonicity(caption_events)
    if args.verbose:
        print(f"     Issues: {timing_result['total_issues']}, Hard failures: {timing_result['hard_failures']}")
    
    print("  C. Segment mapping check...")
    segment_result = check_segment_mapping(timeline_clips, caption_events)
    if args.verbose:
        print(f"     Reorderings: {len(segment_result['reorderings'])}")
    
    print("  D. Line completeness check...")
    completeness_result = check_line_completeness(caption_events, srt_blocks)
    if args.verbose:
        print(f"     Empty events: {completeness_result['events_without_words']}")
    
    summary = {
        'timestamp': datetime.now().isoformat(),
        'project_path': str(project_path),
        'checks': {
            'coverage': coverage_result,
            'timing_monotonicity': timing_result,
            'segment_mapping': segment_result,
            'line_completeness': completeness_result
        },
        'passed': (
            coverage_result['passed'] and
            timing_result['passed'] and
            segment_result['passed'] and
            completeness_result['passed']
        )
    }
    
    summary_path = output_dir / 'captions_verification_summary.json'
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
    print(f"\nSummary saved to: {summary_path}")
    
    report_path = output_dir / 'captions_verification_report.html'
    generate_html_report(
        caption_events,
        coverage_result,
        timing_result,
        segment_result,
        completeness_result,
        report_path
    )
    print(f"Report saved to: {report_path}")
    
    print("\n" + "=" * 50)
    if summary['passed']:
        print("RESULT: ALL CHECKS PASSED")
        print("=" * 50)
        sys.exit(0)
    else:
        print("RESULT: SOME CHECKS FAILED")
        print("=" * 50)
        
        if not coverage_result['passed']:
            print(f"  - Coverage: {coverage_result['coverage_percentage']:.2f}% (threshold: 95%)")
            print(f"    Missing words: {coverage_result['missing_count']}")
        
        if not timing_result['passed']:
            print(f"  - Timing: {timing_result['hard_failures']} hard failures")
        
        if not segment_result['passed']:
            print(f"  - Segment mapping: {len(segment_result['reorderings'])} reorderings")
        
        if not completeness_result['passed']:
            print(f"  - Completeness: {completeness_result['events_without_words']} empty events")
        
        sys.exit(2)


if __name__ == '__main__':
    main()
