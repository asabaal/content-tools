# === Extracted from lyrics_timing_workbench.ipynb ===
# Source: projects/prophetic-preprint/projects/blessed-the-name/lyrics_timing_workbench.ipynb
# Last saved: 2026-07-05 13:49

#!/usr/bin/env python
# coding: utf-8

#
#
#
#



# In[1]:


import sys, json, shutil, subprocess, copy
from pathlib import Path

PIPELINE_SRC = Path('/mnt/storage/repos/content-tools/music-video-pipeline/src')
sys.path.insert(0, str(PIPELINE_SRC))

PROJECT = Path('/mnt/storage/repos/content-tools/projects/prophetic-preprint/projects/blessed-the-name')
DATA    = PROJECT / 'data'

LYRICS_TXT      = DATA / 'lyrics.txt'
SYNCED_JSON     = DATA / 'lyrics_synced.json'
SCRIPT_JSON     = DATA / 'script.json'
AUDIO_WAV       = DATA / 'BLESSED (THE NAME).wav'
LEAD_TRANS      = DATA / 'vocal_transcription_lead_vocals.json'
COMBINED_TRANS  = DATA / 'vocal_transcription_combined_vocals.json'
BACKING_TRANS   = DATA / 'vocal_transcription_backing_vocals.json'

PREVIEWS_DIR    = PROJECT / '_previews'
PREVIEWS_DIR.mkdir(exist_ok=True)

_required = {'lyrics.txt':LYRICS_TXT,'lyrics_synced.json':SYNCED_JSON,'script.json':SCRIPT_JSON,
             'audio':AUDIO_WAV,'lead':LEAD_TRANS,'combined':COMBINED_TRANS,'backing':BACKING_TRANS}
_missing = {k:p for k,p in _required.items() if not p.exists()}
print('⚠ MISSING:', _missing) if _missing else print('✓ All inputs present.')

from render.renderer import VideoRenderer
from render.encoder import VideoEncoder
print(f'Project: {PROJECT.name} | Audio: {AUDIO_WAV.stat().st_size//1024//1024} MB | Previews: {PREVIEWS_DIR}')




# In[2]:


import re

def load_canonical():
    lines, idx, section = [], 0, ''
    for raw in LYRICS_TXT.read_text(encoding='utf-8').split('\n'):
        line = raw.rstrip('\r')
        m = re.match(r'^\[(.+)\]\s*$', line)
        if m: section = m.group(1); continue
        if line.strip() == '': continue
        words = line.strip().split()
        lines.append({'idx':idx,'section':section,'word':line.strip(),
                      'words':[{'word':w,'word_index':i} for i,w in enumerate(words)]})
        idx += 1
    return lines

CANON  = load_canonical()
SYNCED = json.loads(SYNCED_JSON.read_text(encoding='utf-8'))
SCRIPT = json.loads(SCRIPT_JSON.read_text(encoding='utf-8')) if SCRIPT_JSON.exists() else {}
SCRIPT.setdefault('timing_overrides', {})

def normalize_transcription(path, source_name):
    out = []
    for seg_i, seg in enumerate(json.loads(path.read_text(encoding='utf-8')).get('segments', [])):
        ss, se = seg.get('start',0.0), seg.get('end', seg.get('start',0.0))
        st = seg.get('word','').strip()
        for w_i, w in enumerate(seg.get('words', [])):
            out.append({'source':source_name,'segment_index':seg_i,'segment_start':ss,'segment_end':se,
                        'segment_text':st,'word_index':w_i,'word_text':w.get('word',''),
                        'word_start':w.get('start',ss),'word_end':w.get('end',ss),
                        'probability':w.get('probability')})
    return out

EVIDENCE = []
for src, name in [(LEAD_TRANS,'lead'),(COMBINED_TRANS,'combined'),(BACKING_TRANS,'backing')]:
    EVIDENCE += normalize_transcription(src, name)

print(f'Canonical: {len(CANON)} | Synced: {len(SYNCED.get("lines",[]))} | Evidence: {len(EVIDENCE)} words')
print(f'Script overrides: {sum(1 for k in SCRIPT["timing_overrides"] if k!="_provenance")} lines')


#


# In[3]:


from IPython.display import HTML, display

def fmt_t(t):
    return f'{t:.2f}' if t is not None else '—'

def inspect_line(line_index, context_seconds=6.0):
    if not (0 <= line_index < len(CANON)):
        print(f'ERROR: line_index {line_index} out of range'); return
    line = CANON[line_index]
    synced_line = SYNCED.get('lines', [])[line_index]
    cur_start, cur_end = synced_line.get('start'), synced_line.get('end')
    center = cur_start if cur_start is not None else 0.0
    lo = center - context_seconds
    hi = (cur_end if cur_end is not None else center) + context_seconds
    rows = []
    sync_words = synced_line.get('words', [])
    for i, cw in enumerate(line['words']):
        sw = sync_words[i] if i < len(sync_words) else {}
        rows.append({'kind':'CANON','source':'','start':sw.get('start'),'end':sw.get('end'),
                     'word':cw['word'],'detail':f'word {i}'})
    for ev in EVIDENCE:
        if ev['word_start'] is None or ev['word_start'] < lo or ev['word_start'] > hi: continue
        rows.append({'kind':'EVIDENCE','source':ev['source'],'start':ev['word_start'],'end':ev['word_end'],
                     'word':ev['word_text'][:30],'detail':f'seg {ev["segment_index"]} w{ev["word_index"]}'})
    rows.sort(key=lambda r: r['start'] if r['start'] is not None else 1e9)
    warnings = synced_line.get('warnings', [])
    conf = synced_line.get('alignment_confidence')
    css = '<style>.wb table{border-collapse:collapse;font-family:monospace;font-size:12px}.wb td,.wb th{border:1px solid #333;padding:2px 6px}.wb .CANON{background:#1a3a5a;color:#cfe}.wb .EVIDENCE{background:#2a2a2a}.wb .src-lead{color:#f0a04c}.wb .src-combined{color:#4cf0a0}.wb .src-backing{color:#c04cf0}.wb .meta{color:#888;font-size:11px;margin-bottom:6px}</style>'
    html = [f'<div class="wb">{css}<div class="meta"><b>L{line_index}</b> [{line["section"]}] current {fmt_t(cur_start)}-{fmt_t(cur_end)} · confidence {conf} · warnings: {warnings or "none"}<br>canonical: <b>{line["word"]}</b></div>']
    html.append('<table><tr><th>kind</th><th>source</th><th>start</th><th>end</th><th>text</th><th>detail</th></tr>')
    for r in rows:
        src_cls = f'src-{r["source"]}' if r['source'] else ''
        html.append(f'<tr class="{r["kind"]}"><td>{r["kind"]}</td><td class="{src_cls}">{r["source"]}</td><td>{fmt_t(r["start"])}</td><td>{fmt_t(r["end"])}</td><td>{r["word"]}</td><td>{r["detail"]}</td></tr>')
    html.append('</table></div>')
    display(HTML('\n'.join(html)))

inspect_line(1, context_seconds=8)


#
# `SCRIPT['timing_overrides']` IS the working state. Helpers mutate it in memory; `save_script()` persists to disk.
#
# - `show_override(li)` / `get_override(li)` — inspect a line's override
# - `save_script(backup=True)` — write SCRIPT to script.json (+ .bak)
# - `reload_script()` — re-read from disk (discard in-memory edits)
# - `build_preview_sync_data()` — synced lines with overrides applied


# In[4]:


def _li_key(line_index): return str(line_index)

def get_override(line_index):
    return SCRIPT['timing_overrides'].get(_li_key(line_index))

def show_override(line_index):
    e = get_override(line_index)
    if e is None:
        print(f'L{line_index}: no override in script (uses synced baseline).'); return
    print(f'L{line_index} "{CANON[line_index]["word"]}"  {e["start"]:.3f}-{e["end"]:.3f}')
    for i, w in enumerate(e.get('words', [])):
        print(f'  [{i}] {w["word"]:12} {w["start"]:.3f}-{w["end"]:.3f}  dur={w["end"]-w["start"]:.3f}')

def save_script(backup=True):
    if backup and SCRIPT_JSON.exists():
        SCRIPT_JSON.with_suffix('.json.bak').write_bytes(SCRIPT_JSON.read_bytes())
    SCRIPT_JSON.write_text(json.dumps(SCRIPT, indent=2, ensure_ascii=False), encoding='utf-8')
    n = sum(1 for k in SCRIPT['timing_overrides'] if k != '_provenance')
    print(f'Saved script.json ({n} line overrides). backup: script.json.bak')

def reload_script():
    global SCRIPT
    SCRIPT = json.loads(SCRIPT_JSON.read_text(encoding='utf-8'))
    SCRIPT.setdefault('timing_overrides', {})
    n = sum(1 for k in SCRIPT['timing_overrides'] if k != '_provenance')
    print(f'Reloaded script.json from disk ({n} line overrides).')

def build_preview_sync_data():
    lines = copy.deepcopy(SYNCED.get('lines', []))
    for key, entry in SCRIPT.get('timing_overrides', {}).items():
        if key == '_provenance' or not isinstance(entry, dict): continue
        try: idx = int(key)
        except (TypeError, ValueError): continue
        if idx < 0 or idx >= len(lines): continue
        line = lines[idx]
        if 'start' in entry: line['start'] = entry['start']
        if 'end' in entry:   line['end'] = entry['end']
        if isinstance(entry.get('words'), list):
            line['words'] = [{'word': w.get('word', w.get('word','')), 'start': w['start'], 'end': w['end']}
                             for w in entry['words'] if isinstance(w, dict) and 'start' in w and 'end' in w]
    return {'lines': lines}

n_ov = sum(1 for k in SCRIPT['timing_overrides'] if k != '_provenance')
print(f'Script state ready. {n_ov} line overrides in SCRIPT.')
print('Helpers: show_override, get_override, save_script, reload_script, build_preview_sync_data')


#
#
# ```python
# SCRIPT['timing_overrides']['2'] = make_line(2, 7.34, 8.84)          # even split
# SCRIPT['timing_overrides']['2'] = seed_from_sync(2)                  # copy current synced
# e = with_word(get_override(2), 0, 7.4, 7.6); SCRIPT['timing_overrides']['2'] = e  # nudge one word
# ```
#
# ```python
# e = get_override(2)
# e = merge_words(e, sync_words(2, 1, 5, source='combined'), 1, 5)
# SCRIPT['timing_overrides']['2'] = e
# ```
#


# In[5]:


import warnings as _warnings

def _check_line(line_index):
    if not (0 <= line_index < len(CANON)): raise ValueError(f'line_index {line_index} out of range (0..{len(CANON)-1})')

def _check_range(start, end):
    if end < start: raise ValueError(f'end ({end}) < start ({start})')

def _validate(line_index, entry):
    words = entry['words']; canon = CANON[line_index]['words']; issues = []
    if len(words) != len(canon): issues.append(f'word count {len(words)} != canonical {len(canon)}')
    prev_end = None
    for i, w in enumerate(words):
        if w['end'] < w['start']: issues.append(f'w{i} "{w["word"]}": backwards')
        elif w['end'] - w['start'] < 0.02: issues.append(f'w{i} "{w["word"]}": near-zero')
        if prev_end is not None and w['start'] < prev_end - 0.001: issues.append(f'w{i} "{w["word"]}": overlap')
        prev_end = w['end']
    for iss in issues: _warnings.warn(f'L{line_index}: {iss}')
    return issues


def make_word(text, start, end):
    """Return a single word dict."""
    _check_range(start, end)
    return {'word': text, 'start': round(start, 3), 'end': round(end, 3)}

def make_line(line_index, start, end):
    """Return a full override entry: canonical words distributed evenly across [start, end]."""
    _check_line(line_index); _check_range(start, end)
    canon = CANON[line_index]['words']; n = len(canon); per = (end - start) / n
    words = [make_word(canon[i]['word'], start+i*per, start+(i+1)*per) for i in range(n)]
    entry = {'start': round(start,3), 'end': round(end,3), 'words': words}
    _validate(line_index, entry)
    return entry

def make_range(line_index, start_word, end_word, start, end):
    """Return a word list for canonical words [start_word..end_word], evenly split across [start,end]."""
    _check_line(line_index); _check_range(start, end)
    canon = CANON[line_index]['words']
    if not (0 <= start_word <= end_word < len(canon)): raise ValueError(f'word range [{start_word}..{end_word}] invalid')
    n = end_word - start_word + 1; per = (end - start) / n
    return [make_word(canon[i]['word'], start+k*per, start+(k+1)*per) for k, i in enumerate(range(start_word, end_word+1))]

def seed_from_sync(line_index):
    """Return a full override entry seeded from the current synced timing."""
    _check_line(line_index)
    sl = SYNCED.get('lines', [])[line_index]; canon = CANON[line_index]['words']; sw = sl.get('words', [])
    words = []
    for i, cw in enumerate(canon):
        s = (sw[i] if i < len(sw) else {}).get('start', sl.get('start', 0.0))
        e = (sw[i] if i < len(sw) else {}).get('end', sl.get('end', 0.0))
        words.append({'word': cw['word'], 'start': s, 'end': e})
    return {'start': sl.get('start'), 'end': sl.get('end'), 'words': words}


def merge_words(entry, new_words, word_start, word_end=None):
    """Return a NEW entry with new_words spliced into [word_start..word_end]. Does NOT mutate entry."""
    if word_end is None: word_end = word_start + len(new_words) - 1
    out = copy.deepcopy(entry); words = out['words']
    while len(words) <= word_end:
        words.append({'word': '?', 'start': out['end'], 'end': out['end']})
    for k, i in enumerate(range(word_start, word_end + 1)):
        words[i] = new_words[k]
    out['words'] = words
    out['start'] = min(w['start'] for w in words)
    out['end'] = max(w['end'] for w in words)
    return out

def with_word(entry, word_index, start, end):
    """Return a NEW entry with one word's timing replaced. Pure."""
    out = copy.deepcopy(entry)
    out['words'][word_index]['start'] = round(start, 3)
    out['words'][word_index]['end'] = round(end, 3)
    out['start'] = min(w['start'] for w in out['words'])
    out['end'] = max(w['end'] for w in out['words'])
    return out


def recompute_entry(entry):
    """Return a NEW entry with start/end recomputed from the actual word timings.
    Use after poking entry['words'][i]['start'/'end'] directly, so the line-level
    fields stay consistent with the words. Pure (does not mutate input)."""
    out = copy.deepcopy(entry)
    ws = out.get('words', [])
    if ws:
        out['start'] = min(w['start'] for w in ws)
        out['end'] = max(w['end'] for w in ws)
    return out

print('Pure edit helpers ready (return values, no mutation):')
print('  make_word, make_line, make_range, seed_from_sync, merge_words, with_word, recompute_entry')
print('  e.g. SCRIPT["timing_overrides"]["2"] = make_line(2, 7.34, 8.84)')


#
# `use_stem_range(...)` RETURNS an override entry (or word list with `as_words=True`). You assign it explicitly.


# In[6]:


def use_stem_range(line_index, source, segment_index, selected_start, selected_end,
                 canonical_word_start=None, canonical_word_end=None, distribution='even', as_words=False):
    """Return an override entry (or word list) assigning a trimmed stem subrange to canonical words."""
    src_file = {'lead':LEAD_TRANS,'combined':COMBINED_TRANS,'backing':BACKING_TRANS}[source]
    seg = json.loads(src_file.read_text(encoding='utf-8')).get('segments',[])[segment_index]
    canon = CANON[line_index]['words']
    if canonical_word_start is None: canonical_word_start, canonical_word_end = 0, len(canon)-1
    if canonical_word_end is None: canonical_word_end = canonical_word_start
    _check_range(selected_start, selected_end)
    n = canonical_word_end - canonical_word_start + 1
    if distribution == 'single' or n == 1:
        words = [make_word(canon[i]['word'], selected_start, selected_end) for i in range(canonical_word_start, canonical_word_end+1)]
    else:
        per = (selected_end - selected_start) / n
        words = [make_word(canon[i]['word'], selected_start+k*per, selected_start+(k+1)*per) for k, i in enumerate(range(canonical_word_start, canonical_word_end+1))]
    if as_words: return words
    entry = seed_from_sync(line_index)
    return merge_words(entry, words, canonical_word_start, canonical_word_end)

print('use_stem_range() ready (returns entry or word list).')


#
#
# - `sync_words(line_index, word_start, word_end, ...)` → word list (use with `merge_words`)
# - `sync_line(line_index, ...)` → full entry
# - `sync_line_from_stem(line_index, source)` → full entry (auto-picks nearest segment)
# - `show_onsets(start, end)` / `show_stem_words(source, start, end)` → inspection only


# In[7]:


import numpy as np
from lyrics.alignment_analyzer import _compute_onset_word_timings, _count_syllables, _group_onsets_by_gap

_ONSETS = None
def _get_onsets():
    global _ONSETS
    if _ONSETS is None:
        p = DATA / 'vocal_onsets.json'
        _ONSETS = np.array(json.loads(p.read_text(encoding='utf-8')).get('onset_times',[]), dtype=float) if p.exists() else np.array([], dtype=float)
    return _ONSETS

def show_onsets(start, end):
    """List vocal onsets in [start, end] (inspection only)."""
    ot = _get_onsets(); in_w = ot[(ot>=start)&(ot<=end)]
    if len(in_w)==0: print(f'No onsets in {start:.2f}-{end:.2f}.'); return in_w
    groups = _group_onsets_by_gap(in_w)
    print(f'Onsets in {start:.2f}-{end:.2f}: {len(in_w)} total, {len(groups)} group(s)')
    for gi,g in enumerate(groups): print(f'  group {gi}: {[round(float(x),3) for x in g]}  ({len(g)})')
    return in_w

def show_stem_words(source, start, end):
    """List a stem's transcribed words in [start, end] (inspection only)."""
    ev = [e for e in EVIDENCE if e['source']==source and e['word_start'] is not None and e['word_start']>=start-0.5 and e['word_start']<=end+0.5]
    if not ev: print(f'No {source} words in {start:.2f}-{end:.2f}.'); return ev
    print(f'{source} words in {start:.2f}-{end:.2f}: {len(ev)}')
    for e in ev:
        prob = f' p={e["probability"]:.2f}' if e['probability'] is not None else ''
        print(f'  seg{e["segment_index"]} w{e["word_index"]:2}  {e["word_start"]:.3f}-{e["word_end"]:.3f}  "{e["word_text"][:25]}"{prob}')
    return ev


def _line_end(script, line_index):
    """Effective end of line_index: derive from actual word timings when available
    (so raw edits to words[] are reflected), else the entry's line-level end, else synced."""
    if script is None or line_index is None or line_index < 0: return None
    ov = script.get('timing_overrides', {}).get(str(line_index))
    if ov:
        ws = [w for w in (ov.get('words') or []) if isinstance(w, dict) and 'end' in w]
        if ws: return max(w['end'] for w in ws)
        if 'end' in ov: return ov['end']
    lines = SYNCED.get('lines', [])
    if 0 <= line_index < len(lines):
        return lines[line_index].get('end')
    return None

def _line_start(script, line_index):
    """Effective start of line_index: derive from actual word timings when available,
    else the entry's line-level start, else synced."""
    if script is None or line_index is None: return None
    ov = script.get('timing_overrides', {}).get(str(line_index))
    if ov:
        ws = [w for w in (ov.get('words') or []) if isinstance(w, dict) and 'start' in w]
        if ws: return min(w['start'] for w in ws)
        if 'start' in ov: return ov['start']
    lines = SYNCED.get('lines', [])
    if 0 <= line_index < len(lines):
        return lines[line_index].get('start')
    return None

def _shift_to_fit(words, min_start=None, max_end=None):
    """Shift a word list later so words[0].start >= min_start, preserving internal spacing.
    If the shifted result would exceed max_end, compress proportionally to fit.
    Returns a NEW word list (does not mutate input)."""
    words = [w for w in (words or []) if isinstance(w, dict)]
    if not words: return words
    out = [dict(w) for w in words]  # shallow copy each
    if min_start is not None and out[0]['start'] < min_start:
        delta = min_start - out[0]['start']
        for w in out:
            w['start'] = round(w['start'] + delta, 3)
            w['end'] = round(w['end'] + delta, 3)
    # if now exceeds max_end, compress the whole span into [first.start, max_end]
    if max_end is not None and out[-1]['end'] > max_end and len(out) > 1:
        span_start = out[0]['start']
        orig_span = out[-1]['end'] - span_start
        target_span = max_end - span_start
        if target_span > 0 and orig_span > 0:
            scale = target_span / orig_span
            for i, w in enumerate(out):
                rel_start = (w['start'] - span_start) * scale
                rel_end = (w['end'] - span_start) * scale
                w['start'] = round(span_start + rel_start, 3)
                w['end'] = round(span_start + rel_end, 3)
    # enforce chronological + positive duration after the shift/compress
    for i in range(1, len(out)):
        if out[i]['start'] < out[i-1]['end']:
            out[i]['start'] = out[i-1]['end']
        if out[i]['end'] <= out[i]['start']:
            out[i]['end'] = round(out[i]['start'] + 0.04, 3)
    return out

import re
from difflib import SequenceMatcher


def _normalize_match_token(value):
    """Normalize a lyric/transcription token for loose matching."""
    return re.sub(r"[^a-z0-9]+", "", str(value).lower())


def _token_similarity(canonical_text, transcription_text):
    """
    Return a 0..1 rough token similarity score.

    This is used only to choose the most sensible monotonic grouping.
    The transcription remains timing evidence; canonical text remains
    the output lyric text.
    """
    canon = _normalize_match_token(canonical_text)
    stem = _normalize_match_token(transcription_text)

    if not canon or not stem:
        return 0.0

    if canon == stem:
        return 1.0

    if canon in stem or stem in canon:
        return 0.80

    return SequenceMatcher(None, canon, stem).ratio()


def _source_group_cost(canonical_word, source_group):
    """
    Cost of assigning one canonical word to one or more consecutive
    transcription words.

    Lower is better. Extra source words are allowed, but discouraged.
    This lets a five-word transcription map to a four-word lyric rather
    than throwing an error.
    """
    if not source_group:
        return float("inf")

    best_similarity = max(
        _token_similarity(canonical_word, source_word["word"])
        for source_word in source_group
    )

    extra_words = len(source_group) - 1

    # Penalize merging source words, but prefer merging a short/contiguous pair
    # over merging words separated by a large musical gap.
    if extra_words > 0:
        merged_span = source_group[-1]["end"] - source_group[0]["start"]
        internal_gaps = sum(
            max(
                0.0,
                source_group[i]["start"] - source_group[i - 1]["end"],
            )
            for i in range(1, len(source_group))
        )
    else:
        merged_span = 0.0
        internal_gaps = 0.0

    return (
        4.0 * (1.0 - best_similarity)
        + 0.35 * extra_words
        + 0.10 * merged_span
        + 0.20 * internal_gaps
    )


def _canonical_group_cost(source_word, canonical_group):
    """
    Cost of assigning one transcription word to multiple canonical words.

    Used when the transcription has fewer words than the canonical lyric.
    The source timing interval will be divided across the assigned canonical
    words rather than rejected.
    """
    if not canonical_group:
        return float("inf")

    best_similarity = max(
        _token_similarity(canonical_word, source_word["word"])
        for canonical_word in canonical_group
    )

    extra_words = len(canonical_group) - 1

    return (
        4.0 * (1.0 - best_similarity)
        + 0.35 * extra_words
    )


def _map_more_source_words_to_canonical(target_words, source_words):
    """
    Map m source words onto n canonical words where m >= n.

    Every canonical word receives one or more consecutive source words.
    Extra source words are grouped with the closest-compatible canonical word.
    """
    n_targets = len(target_words)
    n_sources = len(source_words)

    dp = [
        [float("inf")] * (n_sources + 1)
        for _ in range(n_targets + 1)
    ]
    back = [
        [None] * (n_sources + 1)
        for _ in range(n_targets + 1)
    ]

    dp[0][0] = 0.0

    for target_count in range(1, n_targets + 1):
        for source_count in range(target_count, n_sources + 1):
            max_group_size = source_count - (target_count - 1)

            for group_size in range(1, max_group_size + 1):
                prior_source_count = source_count - group_size

                previous_cost = dp[target_count - 1][prior_source_count]
                if previous_cost == float("inf"):
                    continue

                source_group = source_words[
                    prior_source_count:source_count
                ]

                candidate_cost = (
                    previous_cost
                    + _source_group_cost(
                        target_words[target_count - 1],
                        source_group,
                    )
                )

                if candidate_cost < dp[target_count][source_count]:
                    dp[target_count][source_count] = candidate_cost
                    back[target_count][source_count] = (
                        prior_source_count,
                        source_group,
                    )

    if dp[n_targets][n_sources] == float("inf"):
        raise RuntimeError(
            "Could not construct a monotonic source-to-canonical mapping."
        )

    groups = []
    target_count = n_targets
    source_count = n_sources

    while target_count > 0:
        previous_source_count, source_group = back[
            target_count
        ][source_count]

        groups.append(source_group)

        source_count = previous_source_count
        target_count -= 1

    groups.reverse()
    return groups


def _map_more_canonical_words_to_source(target_words, source_words):
    """
    Map n canonical words onto m source words where n > m.

    Every source word gets one or more consecutive canonical words.
    Its source interval is split across those canonical words.
    """
    n_targets = len(target_words)
    n_sources = len(source_words)

    dp = [
        [float("inf")] * (n_targets + 1)
        for _ in range(n_sources + 1)
    ]
    back = [
        [None] * (n_targets + 1)
        for _ in range(n_sources + 1)
    ]

    dp[0][0] = 0.0

    for source_count in range(1, n_sources + 1):
        for target_count in range(source_count, n_targets + 1):
            max_group_size = target_count - (source_count - 1)

            for group_size in range(1, max_group_size + 1):
                prior_target_count = target_count - group_size

                previous_cost = dp[source_count - 1][prior_target_count]
                if previous_cost == float("inf"):
                    continue

                canonical_group = target_words[
                    prior_target_count:target_count
                ]

                candidate_cost = (
                    previous_cost
                    + _canonical_group_cost(
                        source_words[source_count - 1],
                        canonical_group,
                    )
                )

                if candidate_cost < dp[source_count][target_count]:
                    dp[source_count][target_count] = candidate_cost
                    back[source_count][target_count] = (
                        prior_target_count,
                        canonical_group,
                    )

    if dp[n_sources][n_targets] == float("inf"):
        raise RuntimeError(
            "Could not construct a monotonic canonical-to-source mapping."
        )

    groups = []
    source_count = n_sources
    target_count = n_targets

    while source_count > 0:
        previous_target_count, canonical_group = back[
            source_count
        ][target_count]

        groups.append(canonical_group)

        target_count = previous_target_count
        source_count -= 1

    groups.reverse()
    return groups


def _map_transcription_to_canonical(target_words, source_words):
    """
    Return canonical word timing dicts by mapping source transcription timing
    as closely as possible onto canonical words.

    Handles unequal word counts without discarding timing evidence.
    """
    if not target_words:
        return []

    if not source_words:
        raise ValueError(
            "No usable source words were available for transcription mapping."
        )

    n_targets = len(target_words)
    n_sources = len(source_words)

    # Exact one-to-one mapping: preserve source boundaries directly.
    if n_sources == n_targets:
        mapped = [
            make_word(
                target_words[i],
                source_words[i]["start"],
                source_words[i]["end"],
            )
            for i in range(n_targets)
        ]

        #print("  [transcription mapping] exact 1:1 word mapping")

        return mapped

    # More source words than canonical words:
    # group consecutive source words into canonical words.
    if n_sources > n_targets:
        source_groups = _map_more_source_words_to_canonical(
            target_words,
            source_words,
        )

        mapped = []

        #print(
        #    f"  [transcription mapping] "
        #    f"{n_sources} source words -> {n_targets} canonical words"
        #)

        for canonical_word, source_group in zip(
            target_words,
            source_groups,
        ):
            mapped.append(
                make_word(
                    canonical_word,
                    source_group[0]["start"],
                    source_group[-1]["end"],
                )
            )

            group_text = " ".join(
                source_word["word"]
                for source_word in source_group
            )

            #print(
            #    f'    {canonical_word!r} <- {group_text!r} '
            #    f'{source_group[0]["start"]:.3f}-'
            #    f'{source_group[-1]["end"]:.3f}'
            #)

        return mapped

    # Fewer source words than canonical words:
    # split each source interval across its assigned canonical-word group.
    canonical_groups = _map_more_canonical_words_to_source(
        target_words,
        source_words,
    )

    mapped = []

    #print(
    #    f"  [transcription mapping] "
    #    f"{n_sources} source words -> {n_targets} canonical words "
    #    f"(source intervals split)"
    #)

    for source_word, canonical_group in zip(
        source_words,
        canonical_groups,
    ):
        group_size = len(canonical_group)
        source_start = source_word["start"]
        source_end = source_word["end"]
        duration_per_word = (source_end - source_start) / group_size

        for index, canonical_word in enumerate(canonical_group):
            mapped.append(
                make_word(
                    canonical_word,
                    source_start + index * duration_per_word,
                    source_start + (index + 1) * duration_per_word,
                )
            )

        #print(
        #    f'    {source_word["word"]!r} '
        #    f'{source_start:.3f}-{source_end:.3f} -> '
        #    f"{canonical_group!r}"
        #)

    return mapped


def sync_words(
    line_index,
    word_start=None,
    word_end=None,
    start=None,
    end=None,
    source=None,
    segment_index=None,
    use_onsets=True,
    method="auto",
    script=None,
    anchor_start=None,
    anchor_end=None,
):
    """
    Return timing dicts for canonical words [word_start..word_end].

    start/end:
        Evidence window. These determine which stem/onset data is considered.

    anchor_start / anchor_end:
        Final line-boundary constraints.

        - anchor_start only:
            Shift all generated timing so the first word starts exactly there.

        - anchor_end only:
            Shift all generated timing so the last word ends exactly there.

        - both:
            Proportionally scale all generated timing so the entire result
            fits exactly inside [anchor_start, anchor_end].

    method:
        "auto" | "onset_syllable" | "transcription" | "even"

    Important:
        Exact transcription timing is used as evidence. Canonical lyric word
        remains the rendered lyric word.
    """
    _check_line(line_index)

    valid_methods = {
        "auto",
        "onset_syllable",
        "transcription",
        "even",
    }

    if method not in valid_methods:
        raise ValueError(
            f"Unknown method {method!r}. "
            f"Expected one of: {sorted(valid_methods)}"
        )

    source_paths = {
        "lead": LEAD_TRANS,
        "combined": COMBINED_TRANS,
        "backing": BACKING_TRANS,
    }

    if source is not None and source not in source_paths:
        raise ValueError(
            f"Unknown source {source!r}. "
            f"Expected one of: {sorted(source_paths)}"
        )

    if anchor_start is not None:
        anchor_start = float(anchor_start)

    if anchor_end is not None:
        anchor_end = float(anchor_end)

    if (
        anchor_start is not None
        and anchor_end is not None
        and anchor_end <= anchor_start
    ):
        raise ValueError(
            f"anchor_end ({anchor_end:.3f}) must be after "
            f"anchor_start ({anchor_start:.3f})."
        )

    canon_words = CANON[line_index]["words"]

    if word_start is None:
        word_start = 0

    if word_end is None:
        word_end = len(canon_words) - 1

    if not (0 <= word_start <= word_end < len(canon_words)):
        raise ValueError(
            f"Invalid canonical word range [{word_start}..{word_end}] "
            f"for L{line_index}, which has {len(canon_words)} words."
        )

    target_words = [
        canon_words[i]["word"]
        for i in range(word_start, word_end + 1)
    ]

    selected_segment = None
    raw_source_words = []

    # Load the explicitly selected transcription segment.
    if source is not None and segment_index is not None:
        source_data = json.loads(
            source_paths[source].read_text(encoding="utf-8")
        )

        segments = source_data.get("segments", [])

        if not (0 <= segment_index < len(segments)):
            raise ValueError(
                f"{source} segment {segment_index} is out of range "
                f"(0..{len(segments) - 1})."
            )

        selected_segment = segments[segment_index]

        if start is None:
            start = float(selected_segment.get("start", 0.0))

        if end is None:
            end = float(
                selected_segment.get(
                    "end",
                    selected_segment.get("start", 0.0),
                )
            )

        for source_word in selected_segment.get("words", []):
            source_start = source_word.get(
                "start",
                selected_segment.get("start", 0.0),
            )
            source_end = source_word.get(
                "end",
                source_start,
            )

            if source_start is None or source_end is None:
                continue

            source_start = float(source_start)
            source_end = float(source_end)

            if source_end < source_start:
                print(
                    f'  [skip invalid source word] '
                    f'{source_word.get("word", "")!r} '
                    f"{source_start:.3f}-{source_end:.3f}"
                )
                continue

            raw_source_words.append(
                {
                    "word": source_word.get("word", ""),
                    "start": source_start,
                    "end": source_end,
                }
            )

        raw_source_words.sort(key=lambda item: item["start"])

    # If no source segment supplied a working window, use the synced baseline.
    if start is None or end is None:
        synced_line = SYNCED["lines"][line_index]

        if start is None:
            start = float(synced_line.get("start", 0.0))

        if end is None:
            end = float(synced_line.get("end", start + 1.0))

    start = float(start)
    end = float(end)
    _check_range(start, end)

    # Source words must overlap the requested evidence window.
    # We clip only at the evidence-window edges; we do not silently clamp
    # around neighboring lines here, because explicit anchors should remain
    # under your control.
    source_words = []

    for source_word in raw_source_words:
        clipped_start = max(source_word["start"], start)
        clipped_end = min(source_word["end"], end)

        if clipped_end <= clipped_start:
            continue

        source_words.append(
            {
                "word": source_word["word"],
                "start": clipped_start,
                "end": clipped_end,
            }
        )

    onset_times = _get_onsets() if use_onsets else np.array([])

    window_onsets = onset_times[
        (onset_times >= start) & (onset_times <= end)
    ]

    if method == "auto":
        if len(window_onsets) >= len(target_words):
            method = "onset_syllable"
        elif source_words:
            method = "transcription"
        else:
            method = "even"

    source_label = (
        f"{source} segment {segment_index}"
        if selected_segment is not None
        else "no selected segment"
    )

    anchor_label = []

    if anchor_start is not None:
        anchor_label.append(f"start={anchor_start:.3f}")

    if anchor_end is not None:
        anchor_label.append(f"end={anchor_end:.3f}")

    anchors_text = ", ".join(anchor_label) if anchor_label else "none"

    print(
        f'sync_words L{line_index} [{word_start}..{word_end}] '
        f'"{" ".join(target_words)}" '
        f"{start:.3f}-{end:.3f} | "
        f"onsets:{len(window_onsets)} | "
        f"source-words:{len(source_words)} | "
        f"{source_label} | "
        f"method:{method} | "
        f"anchors:{anchors_text}"
    )

    # ---- Generate timing from the chosen evidence source ----

    if method == "onset_syllable":
        if len(window_onsets) == 0:
            raise ValueError(
                'method="onset_syllable" was requested, but no onsets '
                f"exist in {start:.3f}-{end:.3f}."
            )

        generated = _compute_onset_word_timings(
            " ".join(target_words),
            window_onsets,
        )

        word_timings = [
            make_word(item.word, item.start, item.end)
            for item in generated
        ]

    elif method == "transcription":
        if selected_segment is None:
            raise ValueError(
                'method="transcription" requires source and segment_index.'
            )

        if not source_words:
            raise ValueError(
                f"No usable source words remain in {source} segment "
                f"{segment_index} after applying the evidence window "
                f"{start:.3f}-{end:.3f}."
            )

        print(
            f"  [source segment word] "
            f'{selected_segment.get("word", "").strip()!r}'
        )

        # Uses flexible monotonic mapping:
        # - exact 1:1 when counts match;
        # - groups source words when source has extras;
        # - splits source intervals when canonical lyrics have extras.
        word_timings = _map_transcription_to_canonical(
            target_words,
            source_words,
        )

    elif method == "even":
        duration_per_word = (end - start) / len(target_words)

        word_timings = [
            make_word(
                target_words[i],
                start + i * duration_per_word,
                start + (i + 1) * duration_per_word,
            )
            for i in range(len(target_words))
        ]

    else:
        raise RuntimeError(f"Unexpected resolved method {method!r}.")

    if not word_timings:
        raise ValueError("Syncing produced no word timings.")

    # ---- Apply final anchors after evidence-based timing is generated ----

    generated_start = min(word["start"] for word in word_timings)
    generated_end = max(word["end"] for word in word_timings)

    if anchor_start is not None and anchor_end is not None:
        generated_span = generated_end - generated_start
        anchor_span = anchor_end - anchor_start

        if generated_span <= 0:
            # Degenerate source timing: use the final anchored span rather
            # than preserving a zero-length result.
            duration_per_word = anchor_span / len(word_timings)

            word_timings = [
                make_word(
                    target_words[i],
                    anchor_start + i * duration_per_word,
                    anchor_start + (i + 1) * duration_per_word,
                )
                for i in range(len(target_words))
            ]

            print(
                "  [anchor transform] source span was zero; "
                "used even timing across anchored line window"
            )

        else:
            scale = anchor_span / generated_span

            transformed = []

            for word in word_timings:
                new_start = (
                    anchor_start
                    + (word["start"] - generated_start) * scale
                )
                new_end = (
                    anchor_start
                    + (word["end"] - generated_start) * scale
                )

                transformed.append(
                    make_word(
                        word["word"],
                        new_start,
                        new_end,
                    )
                )

            # Guarantee exact outer boundaries despite rounding.
            transformed[0]["start"] = round(anchor_start, 3)
            transformed[-1]["end"] = round(anchor_end, 3)

            word_timings = transformed

            print(
                f"  [anchor transform] scaled "
                f"{generated_start:.3f}-{generated_end:.3f} -> "
                f"{anchor_start:.3f}-{anchor_end:.3f} "
                f"(scale={scale:.4f})"
            )

    elif anchor_start is not None:
        delta = anchor_start - generated_start

        word_timings = [
            make_word(
                word["word"],
                word["start"] + delta,
                word["end"] + delta,
            )
            for word in word_timings
        ]

        word_timings[0]["start"] = round(anchor_start, 3)

        print(
            f"  [anchor transform] shifted "
            f"{generated_start:.3f} -> {anchor_start:.3f} "
            f"(delta={delta:+.3f})"
        )

    elif anchor_end is not None:
        delta = anchor_end - generated_end

        word_timings = [
            make_word(
                word["word"],
                word["start"] + delta,
                word["end"] + delta,
            )
            for word in word_timings
        ]

        word_timings[-1]["end"] = round(anchor_end, 3)

        print(
            f"  [anchor transform] shifted "
            f"{generated_end:.3f} -> {anchor_end:.3f} "
            f"(delta={delta:+.3f})"
        )

    # ---- Diagnostics only: do not silently override your anchors ----

    if script is not None:
        previous_end = _line_end(script, line_index - 1)
        next_start = _line_start(script, line_index + 1)

        final_start = min(word["start"] for word in word_timings)
        final_end = max(word["end"] for word in word_timings)

        if (
            previous_end is not None
            and final_start < previous_end - 0.001
        ):
            print(
                f"  [warning] L{line_index} starts at {final_start:.3f}, "
                f"before L{line_index - 1} ends at {previous_end:.3f}"
            )

        if (
            next_start is not None
            and final_end > next_start + 0.001
        ):
            print(
                f"  [warning] L{line_index} ends at {final_end:.3f}, "
                f"after L{line_index + 1} starts at {next_start:.3f}"
            )

    # Final validation and display.
    for i, word in enumerate(word_timings):
        if word["end"] < word["start"]:
            raise ValueError(
                f'Generated backwards timing for {word["word"]!r}: '
                f'{word["start"]:.3f}-{word["end"]:.3f}'
            )

        if i > 0:
            previous = word_timings[i - 1]

            if word["start"] < previous["end"] - 0.001:
                print(
                    f'  [warning] overlap: '
                    f'{previous["word"]!r} ends {previous["end"]:.3f}; '
                    f'{word["word"]!r} starts {word["start"]:.3f}'
                )

    for local_i, canonical_i in enumerate(
        range(word_start, word_end + 1)
    ):
        word = word_timings[local_i]

        print(
            f'  [{canonical_i}] {word["word"]:12} '
            f'{word["start"]:.3f}-{word["end"]:.3f} '
            f'dur={word["end"] - word["start"]:.3f}'
        )

    return word_timings


def sync_line(line_index, script=None, **kwargs):
    """RETURN a full override entry for the whole line, synced to evidence.
    Pass script=SCRIPT to clamp against neighbouring lines."""
    wt = sync_words(line_index, script=script, **kwargs)
    return merge_words(seed_from_sync(line_index), wt, 0, len(wt)-1)

def sync_line_from_stem(
    line_index,
    source,
    segment_index=None,
    use_onsets=True,
    script=None,
    **kwargs,
):
    """
    Return a full line override using a selected or auto-selected stem segment.

    If anchor_start and/or anchor_end are passed, they are used when choosing
    the nearest stem segment as well as passed into sync_words().
    """
    _check_line(line_index)

    source_paths = {
        "lead": LEAD_TRANS,
        "combined": COMBINED_TRANS,
        "backing": BACKING_TRANS,
    }

    if source not in source_paths:
        raise ValueError(
            f"Unknown source {source!r}. "
            f"Expected one of: {sorted(source_paths)}"
        )

    anchor_start = kwargs.get("anchor_start")
    anchor_end = kwargs.get("anchor_end")

    synced_line = SYNCED["lines"][line_index]

    baseline_start = float(synced_line.get("start", 0.0))
    baseline_end = float(
        synced_line.get("end", baseline_start + 1.0)
    )

    if anchor_start is not None:
        anchor_start = float(anchor_start)

    if anchor_end is not None:
        anchor_end = float(anchor_end)

    # Build a target region for segment selection.
    if anchor_start is not None and anchor_end is not None:
        target_start = anchor_start
        target_end = anchor_end

    elif anchor_start is not None:
        baseline_duration = max(0.01, baseline_end - baseline_start)
        target_start = anchor_start
        target_end = anchor_start + baseline_duration

    elif anchor_end is not None:
        baseline_duration = max(0.01, baseline_end - baseline_start)
        target_start = anchor_end - baseline_duration
        target_end = anchor_end

    else:
        target_start = baseline_start
        target_end = baseline_end

    target_center = (target_start + target_end) / 2.0

    if segment_index is None:
        source_data = json.loads(
            source_paths[source].read_text(encoding="utf-8")
        )

        segments = source_data.get("segments", [])

        if not segments:
            raise ValueError(f"No segments found in {source} transcription.")

        best_index = None
        best_score = None

        for i, segment in enumerate(segments):
            segment_start = float(segment.get("start", 0.0))
            segment_end = float(
                segment.get("end", segment_start)
            )
            segment_center = (segment_start + segment_end) / 2.0

            # Primary score: temporal distance from desired target region.
            if segment_end < target_start:
                region_distance = target_start - segment_end
            elif segment_start > target_end:
                region_distance = segment_start - target_end
            else:
                region_distance = 0.0

            # Tie-breaker: midpoint closeness.
            center_distance = abs(segment_center - target_center)

            score = (region_distance, center_distance)

            if best_score is None or score < best_score:
                best_score = score
                best_index = i

        segment_index = best_index

        print(
            f"Auto-selected {source} segment {segment_index} "
            f"for target region {target_start:.3f}-{target_end:.3f}"
        )

    return sync_line(
        line_index,
        source=source,
        segment_index=segment_index,
        use_onsets=use_onsets,
        script=script,
        **kwargs,
    )

print('Pure sync helpers ready (return values, no mutation).')
print('  Pass script=SCRIPT to clamp a line against its neighbours:')
print('    e = sync_line_from_stem(1, "combined", script=SCRIPT)')
print('    SCRIPT["timing_overrides"]["1"] = e')


#


# In[8]:


def apply_overrides_to_renderer(renderer, script=None, overrides=None):
    """Push timing overrides onto a VideoRenderer (idempotent deep-overwrite).

    script:   base script dict (default: global SCRIPT). Its timing_overrides are applied.
    overrides: optional dict {line_idx_str: entry} layered ON TOP of the script's
              timing_overrides — use this to preview a candidate entry before committing.
              Pure: deep-copies, does not mutate script or overrides.
    """
    base = script if script is not None else SCRIPT
    merged = copy.deepcopy(base.get('timing_overrides', {}))
    if overrides:
        for k, v in overrides.items():
            merged[k] = copy.deepcopy(v)
    renderer.script['timing_overrides'] = merged
    renderer._apply_timing_overrides()

_test_r = VideoRenderer(PROJECT, width=480, height=270, fps=15)
_test_r.load()
apply_overrides_to_renderer(_test_r)
print(f'Renderer ready. {sum(1 for k in SCRIPT["timing_overrides"] if k!="_provenance")} overrides applied.')
print('apply_overrides_to_renderer(renderer, script=, overrides=) — preview candidates before committing.')
del _test_r


#
#
#


# In[9]:


from IPython.display import HTML, Video as IPythonVideo, display
import base64, html as _html

_PREVIEW_RENDERER = None

def _get_preview_renderer(width=960, height=540, fps=15, script=None, overrides=None):
    global _PREVIEW_RENDERER
    if _PREVIEW_RENDERER is None:
        _PREVIEW_RENDERER = VideoRenderer(PROJECT, width=width, height=height, fps=fps)
        _PREVIEW_RENDERER.load()
    apply_overrides_to_renderer(_PREVIEW_RENDERER, script=script, overrides=overrides)
    return _PREVIEW_RENDERER

def _slice_audio(start, duration, out_aac):
    if not AUDIO_WAV.exists(): return None
    cmd = ['ffmpeg','-y','-loglevel','error','-ss',f'{start:.3f}','-t',f'{duration:.3f}','-i',str(AUDIO_WAV),'-vn','-acodec','aac','-b:a','128k',str(out_aac)]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return out_aac if out_aac.exists() else None
    except Exception: return None

def _effective_lines(script=None, overrides=None):
    """Return synced lines with script+overrides applied (deep-copy). Used for the
    active-word overlay so it reflects the candidate being previewed."""
    base = script if script is not None else SCRIPT
    lines = copy.deepcopy(SYNCED.get('lines', []))
    merged = copy.deepcopy(base.get('timing_overrides', {}))
    if overrides:
        for k, v in overrides.items():
            merged[k] = copy.deepcopy(v)
    for key, entry in merged.items():
        if key == '_provenance' or not isinstance(entry, dict): continue
        try: idx = int(key)
        except (TypeError, ValueError): continue
        if idx < 0 or idx >= len(lines): continue
        line = lines[idx]
        if 'start' in entry: line['start'] = entry['start']
        if 'end' in entry:   line['end'] = entry['end']
        if isinstance(entry.get('words'), list):
            line['words'] = [{'word': w.get('word', w.get('word','')), 'start': w['start'], 'end': w['end']}
                             for w in entry['words'] if isinstance(w, dict) and 'start' in w and 'end' in w]
    return lines

def _word_map_for_clip(clip_start, clip_end, script=None, overrides=None):
    """Build [[abs_start, abs_end, 'Lli: word'], ...] for words overlapping the clip window,
    using the effective (script+overrides) timings so the overlay matches what's rendered."""
    lines = _effective_lines(script=script, overrides=overrides)
    wm = []
    lo, hi = clip_start - 0.5, clip_end + 0.5
    for li, line in enumerate(lines):
        for w in line.get('words', []):
            s, e = w.get('start'), w.get('end')
            if s is None or e is None: continue
            if s > hi or e < lo: continue
            wm.append([round(s,3), round(e,3), 'L{}: {}'.format(li, w.get('word',''))])
    return json.dumps(wm)

def _player_html(mp4_path, clip_start, duration, label=None, word_map_json='[]'):
    """HTML video player with absolute-song-time clock + active-word overlay."""
    with open(mp4_path, 'rb') as f:
        data_url = (
            'data:video/mp4;base64,'
            + base64.b64encode(f.read()).decode()
        )

    uid = 'p' + str(abs(hash(str(mp4_path) + str(clip_start))) % 100000)

    label_html = (
        '<div style="color:#888;font-size:11px;margin-bottom:4px">'
        f'{_html.escape(label)}'
        f' · song time {clip_start:.2f}–{clip_start + duration:.2f}'
        '</div>'
        if label
        else ''
    )

    js = """
<script>
(function() {{
  var v = document.getElementById('{uid}');
  var clk = document.getElementById('{uid}_clock');
  var localClk = document.getElementById('{uid}_local_clock');
  var wlbl = document.getElementById('{uid}_word');

  var clipStart = {clip_start};
  var words = {word_map};

  function formatClock(seconds) {{
    var m = Math.floor(seconds / 60);
    var s = seconds - m * 60;
    return m + ':' + (s < 10 ? '0' : '') + s.toFixed(2);
  }}

  function tick() {{
    var localT = Number.isFinite(v.currentTime) ? v.currentTime : 0;
    var absT = clipStart + localT;

    // Main counter: absolute position in the full song.
    clk.textContent = formatClock(absT);

    // Smaller counter: local elapsed time inside this preview clip.
    localClk.textContent = '+' + formatClock(localT);

    var found = '';
    for (var i = 0; i < words.length; i++) {{
      if (absT >= words[i][0] && absT <= words[i][1]) {{
        found = words[i][2];
        break;
      }}
    }}

    wlbl.textContent = found;
    requestAnimationFrame(tick);
  }}

  requestAnimationFrame(tick);
}})();
</script>
""".format(
        uid=uid,
        clip_start=repr(clip_start),
        word_map=word_map_json,
    )

    video_tag = (
        '<video id="{}" src="{}" controls '
        'style="width:640px;display:block"></video>'
    ).format(uid, data_url)

    clock_div = (
        '<div id="{}_clock" '
        'style="font-size:28px;font-weight:bold;color:#4cc9f0;'
        'letter-spacing:1px">0:00.00</div>'
    ).format(uid)

    local_clock_div = (
        '<div id="{}_local_clock" '
        'style="font-size:13px;color:#888;white-space:nowrap">+0:00.00</div>'
    ).format(uid)

    word_div = (
        '<div id="{}_word" '
        'style="font-size:14px;color:#aaa;min-height:20px"></div>'
    ).format(uid)

    return (
        '<div style="font-family:monospace">'
        + label_html
        + video_tag
        + '<div style="display:flex;align-items:center;gap:16px;margin-top:6px">'
        + clock_div
        + local_clock_div
        + word_div
        + '</div>'
        + js
        + '</div>'
    )

def render_preview(start, end, padding_before=0, padding_after=0,
                   width=960, height=540, fps=15, label=None, player='custom',
                   script=None, overrides=None):
    """Render [start-pad, end+pad] to a short MP4 and display it inline.

    script:   base script for the renderer's timing_overrides (default: global SCRIPT).
    overrides: {line_idx_str: entry} layered on top — preview a candidate before committing.
    player: 'custom' (M:SS.cc hundredths + word overlay) | 'native' (whole seconds)
    """
    clip_start, clip_end = max(0.0, start-padding_before), end+padding_after
    duration = clip_end - clip_start
    if duration <= 0: raise ValueError('clip duration <= 0')
    renderer = _get_preview_renderer(width, height, fps, script=script, overrides=overrides)
    audio_clip = _slice_audio(clip_start, duration, PREVIEWS_DIR / f'_audio_{clip_start:.2f}_{duration:.2f}.aac')
    out_mp4 = PREVIEWS_DIR / f'preview_{clip_start:.2f}_{clip_end:.2f}.mp4'
    total_frames = int(duration*fps)+1
    with VideoEncoder(out_mp4, width, height, fps, audio_path=audio_clip) as enc:
        for fi in range(total_frames):
            img = renderer.render_frame(clip_start + fi/fps)
            enc.write_frame(img.tobytes())
    if audio_clip is not None and audio_clip.exists():
        try: audio_clip.unlink()
        except Exception: pass
    if label: print(f'{label}: {clip_start:.2f}-{clip_end:.2f} ({duration:.2f}s, {total_frames} frames)')
    if player == 'native':
        display(IPythonVideo(str(out_mp4), embed=True, width=640))
    else:
        wm = _word_map_for_clip(clip_start, clip_end, script=script, overrides=overrides)
        display(HTML(_player_html(out_mp4, clip_start, duration, label, wm)))
    return out_mp4

def render_preview_for_line(line_index, padding_before=0, padding_after=0,
                            width=960, height=540, fps=15, player='custom',
                            script=None, overrides=None):
    """Render a preview around a line's current timing.

    The line's window is resolved from: overrides[line_index] if present, else the
    script's override, else the synced baseline — so previewing a candidate shows
    the candidate's own time span.
    """
    base = script if script is not None else SCRIPT
    key = _li_key(line_index)
    src = overrides if overrides and key in overrides else base.get('timing_overrides', {})
    if key in src:
        e = src[key]
        # Derive the window from ACTUAL word timings, not the (possibly stale)
        # line-level e['start']/e['end'] — so raw edits to words[] are reflected.
        ws = e.get('words') or []
        if ws:
            s, e_end = min(w['start'] for w in ws), max(w['end'] for w in ws)
        else:
            s, e_end = e.get('start', 0), e.get('end', 0)
    else:
        sl = SYNCED.get('lines',[])[line_index]; s, e_end = sl.get('start',0), sl.get('end',0)
    return render_preview(s, e_end, padding_before, padding_after, width, height, fps,
                          label=f'L{line_index}', player=player, script=script, overrides=overrides)

print('render_preview() and render_preview_for_line() ready.')
print('  Preview a candidate WITHOUT assigning: render_preview_for_line(1, overrides={"1": e})')
print('  Default player shows M:SS.cc (hundredths) + active-word overlay.')

def _resolved_line_window(line_index, script=None, overrides=None):
    """
    Return the effective [start, end] timing window for one canonical line,
    using synced data plus script overrides plus optional candidate overrides.

    Prefers actual word timing boundaries over stale line-level start/end fields.
    """
    try:
        line_index = int(line_index)
    except (TypeError, ValueError):
        raise ValueError(f"line_index must be an integer, got {line_index!r}")

    effective_lines = _effective_lines(
        script=script,
        overrides=overrides,
    )

    if not (0 <= line_index < len(effective_lines)):
        raise ValueError(
            f"line_index {line_index} is out of range "
            f"(0..{len(effective_lines) - 1})"
        )

    line = effective_lines[line_index]
    valid_words = []

    for word in line.get("words", []):
        word_start = word.get("start")
        word_end = word.get("end")

        if word_start is None or word_end is None:
            continue

        try:
            word_start = float(word_start)
            word_end = float(word_end)
        except (TypeError, ValueError):
            continue

        if word_end < word_start:
            print(
                f'  [warning] L{line_index} has backwards word timing: '
                f'{word.get("word", "")!r} '
                f"{word_start:.3f}-{word_end:.3f}"
            )
            continue

        valid_words.append((word_start, word_end))

    if valid_words:
        return (
            min(word_start for word_start, _ in valid_words),
            max(word_end for _, word_end in valid_words),
        )

    line_start = line.get("start")
    line_end = line.get("end")

    if line_start is None or line_end is None:
        raise ValueError(
            f"L{line_index} has neither usable word timing nor a "
            "line-level start/end window."
        )

    line_start = float(line_start)
    line_end = float(line_end)

    if line_end < line_start:
        raise ValueError(
            f"L{line_index} has backwards line timing: "
            f"{line_start:.3f}-{line_end:.3f}"
        )

    return line_start, line_end


def render_preview_selection(
    *,
    line=None,
    lines=None,
    line_start=None,
    line_end=None,
    start=None,
    end=None,
    padding_before=0.0,
    padding_after=0.0,
    width=960,
    height=540,
    fps=15,
    player="custom",
    label=None,
    script=None,
    overrides=None,
):
    """
    Render and display an inline preview for exactly one selection mode.

    Selection modes:

      One line:
        render_preview_selection(line=4)

      Explicit line list:
        render_preview_selection(lines=[4, 5, 6])

      Inclusive consecutive line range:
        render_preview_selection(line_start=4, line_end=8)

      Absolute song-time range:
        render_preview_selection(start=13.72, end=17.54)

    Candidate overrides can be previewed without assigning them to SCRIPT:

        render_preview_selection(
            line=4,
            overrides={"4": candidate4},
        )
    """
    has_line = line is not None
    has_lines = lines is not None
    has_line_range = line_start is not None or line_end is not None
    has_time_range = start is not None or end is not None

    mode_count = sum([
        has_line,
        has_lines,
        has_line_range,
        has_time_range,
    ])

    if mode_count != 1:
        raise ValueError(
            "Choose exactly one selection mode: "
            "line=, lines=, line_start=/line_end=, or start=/end=."
        )

    selected_lines = None

    if has_line:
        selected_lines = [int(line)]
        selection_label = f"L{selected_lines[0]}"

    elif has_lines:
        if isinstance(lines, int):
            selected_lines = [lines]
        else:
            try:
                selected_lines = [int(item) for item in lines]
            except TypeError:
                raise ValueError(
                    "lines= must be an integer or an iterable of line indexes."
                )

        if not selected_lines:
            raise ValueError("lines= cannot be empty.")

        selected_lines = sorted(set(selected_lines))

        if len(selected_lines) == 1:
            selection_label = f"L{selected_lines[0]}"
        elif selected_lines == list(
            range(selected_lines[0], selected_lines[-1] + 1)
        ):
            selection_label = (
                f"lines L{selected_lines[0]}–L{selected_lines[-1]}"
            )
        else:
            selection_label = (
                "selected lines "
                + ", ".join(f"L{i}" for i in selected_lines)
            )

    elif has_line_range:
        if line_start is None or line_end is None:
            raise ValueError(
                "line_start= and line_end= must be supplied together."
            )

        line_start = int(line_start)
        line_end = int(line_end)

        if line_end < line_start:
            raise ValueError(
                f"line_end ({line_end}) is before line_start ({line_start})."
            )

        selected_lines = list(range(line_start, line_end + 1))
        selection_label = f"lines L{line_start}–L{line_end}"

    else:
        if start is None or end is None:
            raise ValueError(
                "start= and end= must be supplied together."
            )

        start = float(start)
        end = float(end)

        if end <= start:
            raise ValueError(
                f"end ({end:.3f}) must be later than start ({start:.3f})."
            )

        preview_label = label or f"time range {start:.2f}–{end:.2f}"

        return render_preview(
            start,
            end,
            padding_before=padding_before,
            padding_after=padding_after,
            width=width,
            height=height,
            fps=fps,
            label=preview_label,
            player=player,
            script=script,
            overrides=overrides,
        )

    # Resolve line selection into one continuous absolute-song-time window.
    line_windows = []

    for selected_line in selected_lines:
        window_start, window_end = _resolved_line_window(
            selected_line,
            script=script,
            overrides=overrides,
        )
        line_windows.append((selected_line, window_start, window_end))

    preview_start = min(window_start for _, window_start, _ in line_windows)
    preview_end = max(window_end for _, _, window_end in line_windows)

    print(f"{selection_label}:")
    for selected_line, window_start, window_end in line_windows:
        print(
            f"  L{selected_line}: "
            f"{window_start:.3f}–{window_end:.3f}"
        )

    preview_label = label or (
        f"{selection_label} · "
        f"song time {preview_start:.2f}–{preview_end:.2f}"
    )

    return render_preview(
        preview_start,
        preview_end,
        padding_before=padding_before,
        padding_after=padding_after,
        width=width,
        height=height,
        fps=fps,
        label=preview_label,
        player=player,
        script=script,
        overrides=overrides,
    )


print("render_preview_selection() ready.")
print("Examples:")
print("  render_preview_selection(line=4)")
print("  render_preview_selection(lines=[4, 5, 6])")
print("  render_preview_selection(line_start=4, line_end=8)")
print("  render_preview_selection(start=13.72, end=17.54)")
