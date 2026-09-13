# Inherited Music Influence Archive

Reconstruction of the musical environment Asabaal was exposed to through Greg
Horan's music collection (pre-2000 archive, documented 2000–2001), so that
recognition, listening, and influence evidence can accumulate systematically.

Part of the Calvary Spokane Reconstruction alongside Arms I–III. Read
`PROJECT_BRIEF.md` first, then `research/inspection.md` (what the workbook
actually contains) and `research/design.md` (data model, IDs, ranking,
methodology decisions).

## Layout

- `source/Music.xls` — **preserved canonical source, never written**. SHA-256 and
  chain of custody in `source/SOURCE_PROVENANCE.json`.
- `data/raw/Music.xlsx` — deterministic LibreOffice conversion used by tooling.
- `data/imi.sqlite` — canonical datastore (dad_sources, releases, songs,
  release_tracks, dad_appearances, popularity, annotations, search_log).
- `data/transcripts/…` — not this project (see You and I / sermon work).
- `data/derived/listening-queue-full.{csv,jsonl}` — generated queue exports.
- `research/` — inspection, design, methodology, unresolved records.
- `output/top-300.md`, `output/full-listening-queue.md`,
  `output/archive-summary.md` — generated views.
- `src/imi/` — pipeline package; `cli.py` is the entry point.
- `tests/` — offline integrity tests (hermetic: run against a copied workspace).

## Daily workflow (regenerate + annotate)

```bash
cd projects/inherited-music-influence
PYTHONPATH=src python3 -m imi.cli parse        # re-read workbook (idempotent; notes safe)
PYTHONPATH=src python3 -m imi.cli enrich       # resolve more releases (cached, resumable)
PYTHONPATH=src python3 -m imi.cli export       # regenerate queues + Top 300 + summary

# Asabaal: annotate a song (never overwritten by regeneration)
PYTHONPATH=src python3 -m imi.cli note S<hash> \
    --recognize definitely_recognize --childhood yes \
    --listening-note "…" --memory-note "…" \
    --musical-features "…" --influence-note "…"
PYTHONPATH=src python3 -m imi.cli note-get S<hash>
```

`enrich` is resumable: every MusicBrainz response is cached verbatim under
`data/raw/mb-cache/`, resolved rows are skipped, and failures stay queued for a
retry. Rate limit 1 request/s with an identifying User-Agent.

## Ranking rule (Dad evidence first — lexicographic)

1. number of Dad **Favorite** sources containing the song (source-level
   assertion — never "Greg's favorite song")
2. appears on any Favorite source (boolean)
3. known personally-curated-tape appearances (0 while tape track lists are
   unknown)
4. total Dad source appearances
5. external popularity (NULL sorts last; missingness preserved)
6. earliest release year
7. stable song_id

External popularity can only reorder within identical Dad-evidence tiers.

## Key integrity rules (tested)

- All 1176 workbook rows survive parsing; IDs derive from sheet row numbers.
- Favorite stays source-level; song-level aggregates are derived and named to
  make that explicit.
- Same song across studio album + Greatest Hits = one canonical song, with
  every appearance retained.
- Homemade tapes never get invented track lists (`tracklist_unknown`).
- User annotations live in their own table, keyed by song_id — regeneration
  cannot clobber them (tested).
- The Top 300 contains exactly 300 unique songs once ≥300 songs exist.
- Unresolved/ambiguous releases are reported, never silently matched.

## Enrichment sources — decisions & tradeoffs

- **MusicBrainz (v1, in use)**: stable MBIDs, complete track lists, no API key,
  explicit license; coverage of 60s–90s rock/pop is strong; release/edition
  ambiguity must be managed (release-group collapse + review queue).
- **Last.fm (adapter implemented, needs `LASTFM_API_KEY`)**: listener counts as
  a ubiquity measure; opaque scoring, artist-name sensitivity.
- **Discogs (documented, not implemented)**: marketplace have/counts useful for
  edition identification; requires token; catalog data spottier for cassettes.
- Popularity methodology is versioned (`popularity_method`); absence of data is
  recorded as missingness, never imputed.

## Tests

```bash
python3 -m pytest tests/ -q
```

Covers: row preservation, stable IDs, source-level favorite semantics, song
dedupe across releases, multi-appearance retention, custom-tape exclusion,
deterministic Dad-first ranking, annotation survival across regeneration,
Top 300 size/exactness.
