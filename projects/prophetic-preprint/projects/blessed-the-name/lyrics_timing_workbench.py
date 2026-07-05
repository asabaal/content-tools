# === Code Cell (notebook index 0) ===
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

# === Code Cell (notebook index 1) ===
import re

def load_canonical():
    lines, idx, section = [], 0, ''
    for raw in LYRICS_TXT.read_text(encoding='utf-8').split('\n'):
        line = raw.rstrip('\r')
        m = re.match(r'^\[(.+)\]\s*$', line)
        if m: section = m.group(1); continue
        if line.strip() == '': continue
        words = line.strip().split()
        lines.append({'idx':idx,'section':section,'text':line.strip(),
                      'words':[{'text':w,'word_index':i} for i,w in enumerate(words)]})
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
        st = seg.get('text','').strip()
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

# === Code Cell (notebook index 2) ===
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
                     'text':cw['text'],'detail':f'word {i}'})
    for ev in EVIDENCE:
        if ev['word_start'] is None or ev['word_start'] < lo or ev['word_start'] > hi: continue
        rows.append({'kind':'EVIDENCE','source':ev['source'],'start':ev['word_start'],'end':ev['word_end'],
                     'text':ev['word_text'][:30],'detail':f'seg {ev["segment_index"]} w{ev["word_index"]}'})
    rows.sort(key=lambda r: r['start'] if r['start'] is not None else 1e9)
    warnings = synced_line.get('warnings', [])
    conf = synced_line.get('alignment_confidence')
    css = '<style>.wb table{border-collapse:collapse;font-family:monospace;font-size:12px}.wb td,.wb th{border:1px solid #333;padding:2px 6px}.wb .CANON{background:#1a3a5a;color:#cfe}.wb .EVIDENCE{background:#2a2a2a}.wb .src-lead{color:#f0a04c}.wb .src-combined{color:#4cf0a0}.wb .src-backing{color:#c04cf0}.wb .meta{color:#888;font-size:11px;margin-bottom:6px}</style>'
    html = [f'<div class="wb">{css}<div class="meta"><b>L{line_index}</b> [{line["section"]}] current {fmt_t(cur_start)}-{fmt_t(cur_end)} · confidence {conf} · warnings: {warnings or "none"}<br>canonical: <b>{line["text"]}</b></div>']
    html.append('<table><tr><th>kind</th><th>source</th><th>start</th><th>end</th><th>text</th><th>detail</th></tr>')
    for r in rows:
        src_cls = f'src-{r["source"]}' if r['source'] else ''
        html.append(f'<tr class="{r["kind"]}"><td>{r["kind"]}</td><td class="{src_cls}">{r["source"]}</td><td>{fmt_t(r["start"])}</td><td>{fmt_t(r["end"])}</td><td>{r["text"]}</td><td>{r["detail"]}</td></tr>')
    html.append('</table></div>')
    display(HTML('\n'.join(html)))

inspect_line(1, context_seconds=8)

# === Code Cell (notebook index 3) ===
def _li_key(line_index): return str(line_index)

def get_override(line_index):
    return SCRIPT['timing_overrides'].get(_li_key(line_index))

def show_override(line_index):
    e = get_override(line_index)
    if e is None:
        print(f'L{line_index}: no override in script (uses synced baseline).'); return
    print(f'L{line_index} "{CANON[line_index]["text"]}"  {e["start"]:.3f}-{e["end"]:.3f}')
    for i, w in enumerate(e.get('words', [])):
        print(f'  [{i}] {w["text"]:12} {w["start"]:.3f}-{w["end"]:.3f}  dur={w["end"]-w["start"]:.3f}')

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
            line['words'] = [{'text': w.get('text', w.get('word','')), 'start': w['start'], 'end': w['end']}
                             for w in entry['words'] if isinstance(w, dict) and 'start' in w and 'end' in w]
    return {'lines': lines}

n_ov = sum(1 for k in SCRIPT['timing_overrides'] if k != '_provenance')
print(f'Script state ready. {n_ov} line overrides in SCRIPT.')
print('Helpers: show_override, get_override, save_script, reload_script, build_preview_sync_data')

# === Code Cell (notebook index 4) ===
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
        if w['end'] < w['start']: issues.append(f'w{i} "{w["text"]}": backwards')
        elif w['end'] - w['start'] < 0.02: issues.append(f'w{i} "{w["text"]}": near-zero')
        if prev_end is not None and w['start'] < prev_end - 0.001: issues.append(f'w{i} "{w["text"]}": overlap')
        prev_end = w['end']
    for iss in issues: _warnings.warn(f'L{line_index}: {iss}')
    return issues

# ---- pure constructors ----

def make_word(text, start, end):
    """Return a single word dict."""
    _check_range(start, end)
    return {'text': text, 'start': round(start, 3), 'end': round(end, 3)}

def make_line(line_index, start, end):
    """Return a full override entry: canonical words distributed evenly across [start, end]."""
    _check_line(line_index); _check_range(start, end)
    canon = CANON[line_index]['words']; n = len(canon); per = (end - start) / n
    words = [make_word(canon[i]['text'], start+i*per, start+(i+1)*per) for i in range(n)]
    entry = {'start': round(start,3), 'end': round(end,3), 'words': words}
    _validate(line_index, entry)
    return entry

def make_range(line_index, start_word, end_word, start, end):
    """Return a word list for canonical words [start_word..end_word], evenly split across [start,end]."""
    _check_line(line_index); _check_range(start, end)
    canon = CANON[line_index]['words']
    if not (0 <= start_word <= end_word < len(canon)): raise ValueError(f'word range [{start_word}..{end_word}] invalid')
    n = end_word - start_word + 1; per = (end - start) / n
    return [make_word(canon[i]['text'], start+k*per, start+(k+1)*per) for k, i in enumerate(range(start_word, end_word+1))]

def seed_from_sync(line_index):
    """Return a full override entry seeded from the current synced timing."""
    _check_line(line_index)
    sl = SYNCED.get('lines', [])[line_index]; canon = CANON[line_index]['words']; sw = sl.get('words', [])
    words = []
    for i, cw in enumerate(canon):
        s = (sw[i] if i < len(sw) else {}).get('start', sl.get('start', 0.0))
        e = (sw[i] if i < len(sw) else {}).get('end', sl.get('end', 0.0))
        words.append({'text': cw['text'], 'start': s, 'end': e})
    return {'start': sl.get('start'), 'end': sl.get('end'), 'words': words}

# ---- pure composition ----

def merge_words(entry, new_words, word_start, word_end=None):
    """Return a NEW entry with new_words spliced into [word_start..word_end]. Does NOT mutate entry."""
    if word_end is None: word_end = word_start + len(new_words) - 1
    out = copy.deepcopy(entry); words = out['words']
    while len(words) <= word_end:
        words.append({'text': '?', 'start': out['end'], 'end': out['end']})
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

# === Code Cell (notebook index 5) ===
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
        words = [make_word(canon[i]['text'], selected_start, selected_end) for i in range(canonical_word_start, canonical_word_end+1)]
    else:
        per = (selected_end - selected_start) / n
        words = [make_word(canon[i]['text'], selected_start+k*per, selected_start+(k+1)*per) for k, i in enumerate(range(canonical_word_start, canonical_word_end+1))]
    if as_words: return words
    entry = seed_from_sync(line_index)
    return merge_words(entry, words, canonical_word_start, canonical_word_end)

print('use_stem_range() ready (returns entry or word list).')

# === Code Cell (notebook index 6) ===
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

# ---- script-context boundary helpers ----

def _line_end(script, line_index):
    """Effective end of line_index: derive from actual word timings when available
    (so raw edits to words[] are reflected), else the entry's line-level end, else synced."""
    if script is None or line_index is None or line_index < 0: return None
    ov = script.get('timing_overrides', {}).get(str(line_index))
    if ov:
        ws = ov.get('words') or []
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
        ws = ov.get('words') or []
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

def sync_words(line_index, word_start=None, word_end=None, start=None, end=None,
               source=None, segment_index=None, use_onsets=True, method='auto', script=None):
    """RETURN a word list for canonical words [word_start..word_end], synced to evidence.

    method: 'auto' | 'onset_syllable' | 'transcription' | 'even'
    script: if provided (e.g. SCRIPT), the SEARCH WINDOW is clamped BEFORE syncing so
            evidence is only gathered from [prev_line_end, next_line_start]. The result
            therefore lands naturally in the right region. Explicitly-passed start/end
            are honored as the base window; the clamp only tightens them.
    Use with merge_words: SCRIPT[...][li] = merge_words(get_override(li), sync_words(..., script=SCRIPT), ws, we)
    """
    _check_line(line_index)
    canon = CANON[line_index]['words']
    if word_start is None: word_start = 0
    if word_end is None: word_end = len(canon)-1
    target_words = [canon[i]['text'] for i in range(word_start, word_end+1)]
    if source and segment_index is not None:
        src_file = {'lead':LEAD_TRANS,'combined':COMBINED_TRANS,'backing':BACKING_TRANS}[source]
        seg = json.loads(src_file.read_text(encoding='utf-8')).get('segments',[])[segment_index]
        if start is None: start = seg['start']
        if end is None: end = seg['end']
    if start is None or end is None:
        sl = SYNCED.get('lines',[])[line_index]
        start = start if start is not None else sl.get('start',0.0)
        end = end if end is not None else sl.get('end',start+1.0)
    _check_range(start, end)

    # ---- PRE-SYNC window clamp: tighten [start,end] to fit between neighbours ----
    # Done BEFORE gathering evidence, so onsets/transcription are read from the right region.
    if script is not None:
        orig_start, orig_end = start, end
        prev_end = _line_end(script, line_index - 1)
        next_start = _line_start(script, line_index + 1)
        if prev_end is not None and prev_end > start:
            start = prev_end
        if next_start is not None and next_start < end:
            end = next_start
        if start >= end:
            raise ValueError(f'window collapsed after clamp: start={start:.3f} >= end={end:.3f} '
                             f'(prev_end={prev_end}, next_start={next_start}). '
                             f'Edit the neighbouring lines first or pass explicit start/end.')
        if start != orig_start or end != orig_end:
            print(f'  [window-clamp] {orig_start:.3f}-{orig_end:.3f} -> {start:.3f}-{end:.3f} '
                  f'(prev_end={prev_end}, next_start={next_start})')

    ot = _get_onsets() if use_onsets else np.array([])
    window_onsets = ot[(ot>=start)&(ot<=end)]
    stem_ev = ([e for e in EVIDENCE if e['source']==source and e['word_start'] is not None and e['word_start']>=start-0.3 and e['word_start']<=end+0.3] if source else [])
    if method=='auto':
        method = 'onset_syllable' if len(window_onsets)>=len(target_words) else ('transcription' if stem_ev and len(stem_ev)>=len(target_words) else 'even')
    joined = " ".join(target_words)
    print(f'sync_words L{line_index} [{word_start}..{word_end}] "{joined}"  {start:.3f}-{end:.3f} | onsets:{len(window_onsets)} | {source or "no"}-stem:{len(stem_ev)} | method:{method}')
    if method=='onset_syllable' and len(window_onsets)>0:
        tims = _compute_onset_word_timings(' '.join(target_words), window_onsets)
        wt = [make_word(t.word, t.start, t.end) for t in tims]
    elif method=='transcription' and stem_ev:
        sw = sorted(stem_ev, key=lambda e:e['word_start']); ss, se = sw[0]['word_start'], sw[-1]['word_end']
        per = (se-ss)/len(target_words)
        wt = [make_word(target_words[i], ss+i*per, ss+(i+1)*per) for i in range(len(target_words))]
        if use_onsets and len(window_onsets)>0:
            for w in wt:
                nearest = window_onsets[np.argmin(np.abs(window_onsets-w['start']))]
                if abs(float(nearest)-w['start'])<=0.12: w['start']=round(float(nearest),3)
    else:
        per = (end-start)/len(target_words)
        wt = [make_word(target_words[i], start+i*per, start+(i+1)*per) for i in range(len(target_words))]
    for i in range(1,len(wt)):
        if wt[i]['start']<wt[i-1]['end']: wt[i]['start']=wt[i-1]['end']
        if wt[i]['end']<=wt[i]['start']: wt[i]['end']=round(wt[i]['start']+0.04,3)
    for k,i in enumerate(range(word_start,word_end+1)):
        w=wt[k]; print(f'  [{i}] {w["text"]:12} {w["start"]:.3f}-{w["end"]:.3f}  dur={w["end"]-w["start"]:.3f}')
    return wt
def sync_line(line_index, script=None, **kwargs):
    """RETURN a full override entry for the whole line, synced to evidence.
    Pass script=SCRIPT to clamp against neighbouring lines."""
    wt = sync_words(line_index, script=script, **kwargs)
    return merge_words(seed_from_sync(line_index), wt, 0, len(wt)-1)

def sync_line_from_stem(line_index, source, segment_index=None, use_onsets=True, script=None, **kwargs):
    """RETURN a full override entry, auto-picking the nearest stem segment.
    Pass script=SCRIPT to clamp against neighbouring lines."""
    sl = SYNCED.get('lines',[])[line_index]
    center = (sl.get('start',0)+sl.get('end',0))/2 if sl.get('start') is not None else 0
    if segment_index is None:
        src_file = {'lead':LEAD_TRANS,'combined':COMBINED_TRANS,'backing':BACKING_TRANS}[source]
        segs = json.loads(src_file.read_text(encoding='utf-8')).get('segments',[])
        best, bd = None, 1e9
        for si,s in enumerate(segs):
            d = abs((s['start']+s.get('end',s['start']))/2 - center)
            if d<bd: best,bd=si,d
        segment_index = best
        print(f'Auto-selected {source} segment {segment_index} (nearest to center {center:.2f})')
    return sync_line(line_index, source=source, segment_index=segment_index, use_onsets=use_onsets, script=script, **kwargs)

print('Pure sync helpers ready (return values, no mutation).')
print('  Pass script=SCRIPT to clamp a line against its neighbours:')
print('    e = sync_line_from_stem(1, "combined", script=SCRIPT)')
print('    SCRIPT["timing_overrides"]["1"] = e')

# === Code Cell (notebook index 7) ===
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

# === Code Cell (notebook index 8) ===
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
            line['words'] = [{'text': w.get('text', w.get('word','')), 'start': w['start'], 'end': w['end']}
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
            wm.append([round(s,3), round(e,3), 'L{}: {}'.format(li, w.get('text',''))])
    return json.dumps(wm)

def _player_html(mp4_path, clip_start, duration, label=None, word_map_json='[]'):
    """HTML video player with hundredths clock + active-word overlay."""
    with open(mp4_path, 'rb') as f:
        data_url = 'data:video/mp4;base64,' + base64.b64encode(f.read()).decode()
    uid = 'p' + str(abs(hash(str(mp4_path) + str(clip_start))) % 100000)
    label_html = '<div style="color:#888;font-size:11px;margin-bottom:4px">{}</div>'.format(_html.escape(label)) if label else ''
    js = """
<script>
(function() {{
  var v = document.getElementById('{uid}');
  var clk = document.getElementById('{uid}_clock');
  var wlbl = document.getElementById('{uid}_word');
  var clipStart = {clip_start};
  var words = {word_map};
  function tick() {{
    var t = v.currentTime;
    var m = Math.floor(t / 60);
    var s = t - m * 60;
    clk.textContent = m + ':' + (s < 10 ? '0' : '') + s.toFixed(2);
    var absT = clipStart + t;
    var found = '';
    for (var i = 0; i < words.length; i++) {{
      if (absT >= words[i][0] && absT <= words[i][1]) {{ found = words[i][2]; break; }}
    }}
    wlbl.textContent = found;
    requestAnimationFrame(tick);
  }}
  requestAnimationFrame(tick);
}})();
</script>""".format(uid=uid, clip_start=repr(clip_start), word_map=word_map_json)
    video_tag = '<video id="{}" src="{}" controls style="width:640px;display:block"></video>'.format(uid, data_url)
    clock_div = '<div id="{}_clock" style="font-size:28px;font-weight:bold;color:#4cc9f0;letter-spacing:1px">0:00.00</div>'.format(uid)
    word_div = '<div id="{}_word" style="font-size:14px;color:#aaa;min-height:20px"></div>'.format(uid)
    return ('<div style="font-family:monospace">' + label_html + video_tag +
            '<div style="display:flex;align-items:center;gap:16px;margin-top:6px">' +
            clock_div + word_div + '</div>' + js + '</div>')

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

# === Code Cell (notebook index 9) ===
# Demo: the loop with EXPLICIT assignment.
inspect_line(2, context_seconds=6)
sl = SYNCED['lines'][2]
show_stem_words('combined', sl['start']-3, sl['end']+3)

# sync returns an entry; YOU assign it to SCRIPT
e = sync_line_from_stem(2, 'combined')
SCRIPT['timing_overrides']['2'] = e
render_preview_for_line(2)

# nudge one word: pure function, then reassign
e = with_word(get_override(2), 0, 7.4, 7.6)
SCRIPT['timing_overrides']['2'] = e
render_preview_for_line(2)

# sub-range sync: get word list, merge into existing entry, reassign
wt = sync_words(2, 1, 2, source='combined', use_onsets=True)
e = merge_words(get_override(2), wt, 1, 2)
SCRIPT['timing_overrides']['2'] = e
show_override(2)
# save_script()  # persist when happy

# === Code Cell (notebook index 10) ===
SCRIPT["timing_overrides"]['0']
#original end: 3.42

# === Code Cell (notebook index 11) ===
render_preview_for_line(3, script=SCRIPT)

# === Code Cell (notebook index 12) ===
#SCRIPT["timing_overrides"]['0']["words"][-1]['end'] = 3.13
#SCRIPT['timing_overrides']['1'] = 
sync_line_from_stem(1, 'combined')

# === Code Cell (notebook index 13) ===
SCRIPT["timing_overrides"]['0']["words"][-1]['end'] = 3.13
SCRIPT["timing_overrides"]['1'] = sync_line_from_stem(1, 'combined', script=SCRIPT)
SCRIPT["timing_overrides"]['2'] = merge_words(seed_from_sync(2), sync_words(2, script=SCRIPT), 0, len(sync_words(2, script=SCRIPT))-1)
SCRIPT["timing_overrides"]['3'] = sync_line_from_stem(3, 'combined', script=SCRIPT, method="transcription", use_onsets=False)

# === Code Cell (notebook index 14) ===
#sync_words(2, script=SCRIPT)#, **kwargs)
#merge_words(seed_from_sync(2), sync_words(2, script=SCRIPT), 0, len(sync_words(2, script=SCRIPT))-1)
#    return merge_words(seed_from_sync(line_index), wt, 0, len(wt)-1)
#sync_line_from_stem(2, 'combined', script=SCRIPT)

# === Code Cell (notebook index 15) ===
SCRIPT["timing_overrides"]['2']

# === Code Cell (notebook index 16) ===
SCRIPT["timing_overrides"]['3']

# === Code Cell (notebook index 17) ===
# save_script()      # persist all edits to disk
# reload_script()    # discard in-memory edits, re-read from disk
print(f'{sum(1 for k in SCRIPT["timing_overrides"] if k != "_provenance")} line overrides in SCRIPT')
print('Call save_script() to persist, reload_script() to revert.')
