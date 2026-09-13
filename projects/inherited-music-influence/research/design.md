# Inherited Music Influence Archive — Design

## Data model (SQLite: `data/imi.sqlite`)

### `dad_sources` — one row per original workbook row
`dad_source_id` = `D` + zero-padded **sheet row number** (stable: sheet rows never
reorder; the workbook's own `num` column has a duplicate "1" and must not be an ID).

Raw-preserving: artist_raw, band_name_raw, various_misc_raw, title_raw,
edition_qualifier_raw, year_raw, media_raw, tape1, tape2, tape_order, special,
misc_flag, favorite_raw (0/1). Plus derived: row_kind (`commercial` |
`custom_tape`), source_group (tape series name), artist_search / title_search
(normalized for resolution), resolution_status
(`unresolved` → `probable` / `resolved` / `ambiguous` / `non_commercial`),
release_id (FK after resolution).

Row-kind rule: `custom_tape` when MEDIA = Tape and normalized artist ≈ normalized
title (FM Rock 1, Party Tape 15, …); else `commercial`. Commercial rows with
tape-series-like titles that don't self-match stay commercial and surface in the
unresolved report if resolution fails.

### `releases` — resolved commercial releases
`release_id` = `R` + MusicBrainz release MBID (dedupes across dad rows).
title/artist/date/country/labels from MusicBrainz, plus provenance columns
(source_provider, source_url, retrieved_at, match_score, candidates_json).
`dad_sources.release_id` links dad rows to the single canonical release.

### `songs` — canonical songs (work = artist+title identity)
`song_id` = `S` + first 10 hex of SHA-1 of `norm_artist || '||' || norm_title`.
The same recording on a studio album and a Greatest Hits compilation maps to one
song. `recording_variant` retains version info when known.

### `release_tracks` — (release_id, disc, track_no) → song_id, printed title

### `dad_appearances` — song ↔ dad source join
Includes `appears_on_dad_favorite_source` (derived **source-level** favorite),
`certainty`. A song on three Greg albums yields three appearance rows plus one
consolidated stat row set on `songs`.

### `songs` Dad-evidence columns (computed, transparent)
`dad_source_count`, `dad_favorite_source_count`, `appears_on_dad_favorite_source`,
`dad_format_count`, `curated_tape_known_count` (always 0 while named tapes are
`tracklist_unknown`).

### `popularity` — (song_id, provider) keyed evidence rows
provider, score, rank, listeners, payload_json, retrieved_at.
**v1 methodology (`popularity_method = v1`)**: no external popularity source is
fetched by default. Candidate sources documented with tradeoffs
(`research/popularity-methodology.md`); a Last.fm adapter is implemented behind
`LASTFM_API_KEY` (not present in this environment). Songs without enrichment have
`popularity_score = NULL` — missingness is represented, never imputed.

### `annotations` — Asabaal's layer (regeneration never touches it)
song_id PK; recognition_status (`unreviewed` default), childhood_association,
listened, first_reviewed_at, last_listened_at, listening_note, memory_note,
musical_features, possible_influence_note, influence_confidence, updated_at.
Only the `note` CLI writes here. `parse`/`enrich`/`rank`/`export` never do.

## Ranking (Dad-first, lexicographic)

```
ORDER BY
  dad_favorite_source_count DESC,      -- explicit Favorite albums containing the song
  appears_on_dad_favorite_source DESC, -- same signal, boolean form
  curated_tape_known_count DESC,       -- known-tracklist curated tape appearances
  dad_source_count DESC,               -- total Greg archive appearances
  popularity_score DESC NULLS LAST,    -- external popularity (NULL = not enriched)
  first_release_year ASC NULLS LAST,   -- earlier release = earlier in environment
  song_id ASC                          -- total order
```

External popularity can therefore only reorder *within* identical Dad-evidence
tiers; it can never outrank stronger Greg evidence.

## Release resolution (v1)

Provider: **MusicBrainz** (stable IDs, free, no key, explicit licensing; documented
tradeoffs vs Discogs/Last.fm in `research/sources.md`). Per commercial dad row:

1. search `release` with `artist:"…" AND release:"…"` (+ year hint);
2. score candidates (normalized title/artist similarity + year proximity);
3. best score ≥ 0.82 → `resolved` (fetch full track list with recordings);
   0.60–0.82 or tie → `probable` (track list fetched, flagged) or `ambiguous`
   (candidates stored, no pick); no candidate → `unresolved`.

All HTTP responses cached verbatim under `data/raw/mb-cache/` (resumable; re-running
never re-fetches). Rate limit 1 request/s with identifying User-Agent.

## Popularity adapters

`LASTFM_API_KEY` env → Last.fm `track.getInfo`/`artist.getTopTracks` listeners as
ubiquity evidence. Absent the key, popularity stays unpopulated (explicit
missingness). Discogs (community have/want counts) documented as alternative.

## Regeneration

`imi parse | enrich | apply-enrichment | rank | export` are all idempotent and
keyed by stable IDs. `imi note` is the only writer of `annotations`. Tests assert
notes survive a full regenerate.
