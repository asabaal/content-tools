# Calvary Spokane Historical Sermon Archiver

A resumable, provenance-preserving Python application for inventorying and downloading the publicly accessible Calvary Spokane sermon archive for historical and theological research.

The default historical window is inclusive:

- Start: `2004-06-01`
- End: `2010-08-31`

SQLite is the canonical inventory. CSV, JSON, and Markdown files are generated views of that database.

## Responsible use

This tool retrieves only resources already exposed through Calvary Spokane's public website, public Subsplash interface, public legacy media indexes, and Internet Archive's public Wayback interface. It does not bypass authentication, CAPTCHAs, paywalls, or access controls. Metadata requests are serialized, delayed, retried with backoff, and recorded. Media downloads default to one at a time.

Public accessibility does not grant redistribution rights. Keep downloaded sermon media private unless you separately establish permission to redistribute it.

## What the application discovers

The visible Calvary site is Squarespace, but Squarespace does not contain the complete sermon record set. Its sermon pages embed a Subsplash library.

The crawler begins with all four public pages:

- `https://www.calvaryspokane.com/sermon-archive`
- `https://www.calvaryspokane.com/sermons`
- `https://www.calvaryspokane.com/old-testament`
- `https://www.calvaryspokane.com/new-testament`

It scans HTML, links, iframe values, and scripts for Subsplash app and Builder-list shortcodes. During development, those public pages resolved to app shortcode `qq9m`, app key `JGX9N6`, and organization key `45B9GCHD`; these values are **not hardcoded as the sole source of truth**.

A public Subsplash library page contains a short-lived `shoebox-tokens` API token. The crawler extracts that public token at runtime, redacts it before saving HTML, and refreshes it on `401`. It then uses public structured endpoints under `https://core.subsplash.com`:

- `accounts/v1/apps` to resolve the discovered app shortcode;
- `builder/v1/lists` and `builder/v1/list-rows` to audit visible archive/Old Testament/New Testament list structure, including nested lists;
- `media/v1/media-series` to inventory all published series and their advertised item counts;
- app-wide `media/v1/media-items` pagination as the authoritative inventory of what Subsplash currently publishes.

The app-wide item crawl is important because a series-only crawl omits published seriesless sermons. Subsplash does not allow a server-side historical-date filter on this endpoint, so every metadata page is retained and the actual sermon `date` is filtered locally. `created_at` and `published_at` are never substituted for the sermon date.

Subsplash is not historically complete by itself. The supplemental legacy adapter also discovers:

- the church's 2011 Wayback-captured `/sermon/archive/` database, including source item, series, MP3, notes, and historical video URLs;
- the public `https://media.calvaryspokane.com/C.Mp3/prophecy/` index;
- explicitly dated New Year's Eve files, with `ffprobe` used only to read public embedded metadata;
- current HTTP availability separately from historical availability.

Cross-source evidence is stored in `sermon_sources`. A dead historical `.m4v` link remains auditable there but does not set `has_video` on the canonical sermon. No Playwright fallback is currently required because these public HTML and structured endpoints expose the archive. Source-specific code is isolated in `src/calvary_archive/discovery.py` and `src/calvary_archive/legacy.py`.

## Archive layout

The default workspace is `/mnt/storage/data/calvary-spokane`. Override it with `--root` after a command or with the `CALVARY_ARCHIVE_ROOT` environment variable.

```text
/mnt/storage/data/calvary-spokane/
├── data/
│   ├── sermons.sqlite       # canonical inventory
│   ├── sermons.csv          # flat, inspectable export
│   ├── sermons.json         # rich canonical sermon export
│   ├── sermon_sources.json  # cross-source provenance and availability checks
│   └── raw/
│       └── RUN_ID/          # redacted bodies plus URL/status/time/hash manifest
├── downloads/
│   └── YYYY/
│       └── YYYY-MM-DD__speaker__series__title__ITEMID.ext
├── logs/
│   └── archive.jsonl
└── reports/
    ├── summary.md
    ├── completeness.csv
    ├── provenance.csv
    └── needs_date_review.csv
```

The program creates these directories as needed. Existing verified media is never overwritten.

## Architecture

- `archive_sermons.py`: source-tree executable.
- `src/calvary_archive/cli.py`: CLI orchestration and JSONL operation logging.
- `src/calvary_archive/discovery.py`: Squarespace/Subsplash discovery, pagination, raw capture, and normalization.
- `src/calvary_archive/legacy.py`: Wayback listing parsing, legacy media-index discovery, availability checks, and supplemental import.
- `src/calvary_archive/models.py`: normalized inventory model and lifecycle states.
- `src/calvary_archive/database.py`: SQLite schema, canonical sermon/source-provenance separation, conservative duplicate handling, metadata upserts, transitions, and verification facts.
- `src/calvary_archive/downloader.py`: video-first backend selection, HTTP range resume, `yt-dlp`, HLS/`ffmpeg`, checksums, and verification.
- `src/calvary_archive/reports.py`: deterministic CSV/JSON exports and completeness/date-review reports.
- `tests/fixtures/`: sanitized representative Subsplash and legacy-listing payloads for offline parser tests.

### Lifecycle states

Each inventory row has one of:

- `discovered`
- `metadata_complete`
- `queued`
- `downloading`
- `downloaded`
- `verified`
- `audio_only`
- `no_media`
- `failed`
- `needs_review`

Transitions are validated and recorded in `status_events`. `audio_only` describes public source availability; it does **not** by itself mean that audio was downloaded. A real download is indicated by `local_media_path`, `filesize`, `sha256`, and `downloaded_at`. Metadata refreshes recover newly dated/newly available records while preserving existing local paths, hashes, retry state, and verification timestamps.

### Duplicate policy

The primary key is the public platform item identifier (a Subsplash UUID for current records or a stable generated legacy ID). Conservative fallback matching uses, in order:

1. platform + item identifier;
2. canonical source URL;
3. exact sermon date + title + speaker;
4. exact media URL.

Title-only matching is not used. Two different nonempty item IDs from the same platform are always retained separately, even if they share a media URL; this prevents source metadata defects from collapsing distinct sermons. Fallback reconciliation is reserved for cross-platform or ID-less records.

## Dependencies and setup

Requirements:

- Python 3.11 or newer;
- `httpx`;
- `yt-dlp` for provider pages;
- `ffmpeg` and `ffprobe` on `PATH` for HLS and media validation.

Create an isolated environment:

```bash
cd /mnt/storage/repos/content-tools/public_retrieval/calvary_spokane
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
ffmpeg -version
ffprobe -version
yt-dlp --version
```

On Debian/Ubuntu, install the system media tools with your normal package-management process if they are absent:

```bash
sudo apt-get install ffmpeg
```

## Metadata-only crawl

Preferred command:

```bash
python archive_sermons.py discover \
  --start-date 2004-06-01 \
  --end-date 2010-08-31
```

The original command concept is also supported:

```bash
python archive_sermons.py \
  --start-date 2004-06-01 \
  --end-date 2010-08-31 \
  --metadata-only
```

`discover` never downloads media. It crawls the public list structure, all published series, and the app-wide Subsplash item collection before generating the inventory and reports.

Run the supplemental legacy crawl after Subsplash discovery:

```bash
python archive_sermons.py discover-legacy \
  --start-date 2004-06-01 \
  --end-date 2010-08-31
```

This command retrieves metadata and performs lightweight HEAD/`ffprobe` availability checks; it does not download full sermon media. A preserved audit can be re-imported without refetching the Wayback listing pages:

```bash
python archive_sermons.py discover-legacy \
  --cache-dir /mnt/storage/data/calvary-spokane/data/raw/wayback-legacy-2011-audit-20260818
```

For a partial integration test:

```bash
python archive_sermons.py discover --limit 10
```

A limited crawl is intentionally incomplete and should not be used as the final historical inventory. It is persisted as a `partial` crawl, and reports continue to use the most recent completed crawl for overall completeness metrics.

A network-only dry run that does not upsert sermon or series metadata:

```bash
python archive_sermons.py discover --limit 5 --dry-run
```

## Inspecting the inventory

Regenerate all exports from canonical SQLite:

```bash
python archive_sermons.py report
```

Inspect with SQLite:

```bash
sqlite3 /mnt/storage/data/calvary-spokane/data/sermons.sqlite
```

Useful SQL:

```sql
.headers on
.mode column
SELECT sermon_date, title, speaker, series, has_video, has_audio, download_status
FROM sermons
ORDER BY sermon_date, title;

SELECT speaker, COUNT(*) AS sermons
FROM sermons
GROUP BY speaker
ORDER BY sermons DESC;

SELECT series, COUNT(*) AS sermons
FROM sermons
GROUP BY series
ORDER BY sermons DESC;
```

`data/sermons.csv` begins with every requested normalized field. `data/sermons.json` also embeds the canonical source item metadata. `data/sermon_sources.json` and `reports/provenance.csv` retain alternate listing/media URLs, archived URLs, raw metadata, retrieval/check timestamps, and tri-state media availability. Missing dates remain in SQLite and appear in `reports/needs_date_review.csv` rather than being silently excluded.

## Testing media selection before downloading

Preview one video target without changing state or writing media:

```bash
python archive_sermons.py download --video --limit 1 --dry-run
```

Filter test selections by exact source metadata:

```bash
python archive_sermons.py download --video --speaker "Ken Ortize" --year 2006 --limit 3 --dry-run
python archive_sermons.py download --video --series "Acts" --limit 3 --dry-run
```

## Downloading media

Video is always the primary target. Downloads are date-scoped to `2004-06-01` through `2010-08-31` by default, even if the same SQLite database later accumulates broader discovery data:

```bash
python archive_sermons.py download --video
```

Use explicit bounds only when intentionally changing that scope:

```bash
python archive_sermons.py download --video --start-date 2004-06-01 --end-date 2010-08-31
```

In the reconciled live snapshot from August 2026, the inventory contains 445 dated target-period records. None has a currently reachable public video. The legacy archive documents 51 historical `.m4v` links, but all return 404 and none is preserved as a media capture in Wayback. A video-only command therefore selects zero target files rather than treating historical evidence as a downloadable video.

Download audio only when no public video exists:

```bash
python archive_sermons.py download --video --audio-if-no-video
```

Backend selection is automatic:

- ordinary `.mp4`, `.mp3`, and other direct media URLs use resumable HTTP;
- provider/web pages use `yt-dlp`;
- `.m3u8` HLS URLs use `ffmpeg`.

Direct HTTP writes to `.part`, resumes with `Range`, and safely restarts when a server ignores or rejects the requested range. `yt-dlp` uses its native continuation support. HLS cannot generally resume a partially muxed container, so an interrupted HLS item restarts that item's `.part` file.

Successful files are hashed with SHA-256 and validated with `ffprobe`, including an audio/video stream and positive duration check, before video rows become `verified`. Verification fails closed if `ffprobe` is unavailable. `--no-ffprobe` is an explicit opt-out that leaves only size/hash checks. Audio-only downloads remain visibly `audio_only` while also retaining their local path, download/verification timestamps, size, and hash.

`yt-dlp` and `ffmpeg` subprocesses are bounded to six hours per item by default; adjust with `--process-timeout` when a legitimate long item needs more time.

## Resume and retry

Re-running `download` is safe:

- verified files are skipped;
- existing files are checked rather than overwritten;
- direct `.part` files resume;
- completed local facts survive metadata refreshes;
- source-only `audio_only` records remain eligible for a later `--audio-if-no-video` run;
- failed items retain errors and attempt counts;
- default start/end bounds prevent records outside the historical scope from being selected.

Retry only eligible failed records:

```bash
python archive_sermons.py retry-failed --video --audio-if-no-video
```

Restrict retries for testing:

```bash
python archive_sermons.py retry-failed --limit 3 --dry-run
```

## Verification

Re-hash and validate every known local file:

```bash
python archive_sermons.py verify
```

Filter or preview:

```bash
python archive_sermons.py verify --year 2009 --limit 5
python archive_sermons.py verify --dry-run
```

A missing or checksum-mismatched file is moved to `needs_review`; it is not silently replaced.

## Completeness auditing

`reports/summary.md` includes counts by:

- year;
- month;
- speaker;
- series;
- Bible book;
- media type;
- lifecycle/download status.

`reports/completeness.csv` includes overall, crawl, series, and listing rows for:

- series discovered;
- items advertised by structured/listing metadata;
- items/API pages observed;
- records in the historical inventory;
- video, audio-only, and no-media records;
- successful downloads;
- failures;
- manual-review records.

The known historical series—Genesis, Mark, Acts, 1 John, 2 John, and 3 John—are useful checks, not discovery seeds or completeness boundaries. The app-wide crawl also retains topical, guest, holiday, special-service, seriesless, and no-media records when they fall in the date range.

`reports/provenance.csv` audits every supplemental source URL and distinguishes untested, reachable, and unavailable historical media.

### Reconciling legacy media candidates

The recursive media-index audit deliberately does not turn every listed MP3 into a sermon. After reviewing its candidate evidence, run the conservative reconciliation step:

```bash
python archive_sermons.py reconcile-media-candidates \
  --start-date 2004-06-01 \
  --end-date 2010-08-31
```

This command:

- imports sermon-length guest files when a trusted source-title date lands on a normal Sunday or Thursday;
- keeps year-only, sequence-bounded, or conflicting-date files as undated `needs_review` records;
- ignores arbitrary XMP production timestamps and short promotional files;
- corrects a canonical remote-media assignment only when a unique exact source match conflicts with the existing legacy filename;
- writes `reports/missing-sermons.md` and `reports/missing-sermons.csv`.

Use `--dry-run` to preview the decisions or `--run-id` to reconcile a specific completed media-index crawl. Re-running the command is idempotent.

## Current historical audit snapshot

As of the August 2026 metadata audit before the final guest-media reconciliation:

- 445 dated records fell in the inclusive target window: 241 Sunday records and 204 Thursday records;
- a later recursive media-index pass recovered live replacement paths for all 8 formerly unavailable MP3s;
- 80 Thursday teachings from 2008–2010 were recovered from the 2011 archived sermon catalog;
- three public 2009 New Year's Eve prophecy sessions were recovered from the legacy media index;
- the previously no-media Subsplash record `The Liar` (`2009-08-23`) was reconnected to a live legacy MP3;
- a subsequent candidate reconciliation identified 14 exact-dated guest recordings plus additional year-only and date-ambiguous historical sessions; current counts are generated in `reports/missing-sermons.md` rather than duplicated here;
- 51 historical video URLs are documented, but zero are currently reachable or captured by Wayback;
- the official YouTube channel's oldest currently listed material is from 2017;
- the current official podcast feed begins in 2015, so neither source supplied additional 2004–2010 records;
- Facebook and Instagram exposed no pre-2010 public content without login, and no access control was bypassed.

The third 2009 NYE file has no artist tag. Its speaker remains blank in normalized metadata, while the first two raw files identify `Ken Orize`; that known legacy typo is normalized to `Ken Ortize` and retained verbatim in raw metadata.

## Transcription

Transcribe the locally archived audio into derivative transcript artifacts with `faster-whisper`:

```bash
# from the project venv (python3 -m venv .venv && .venv/bin/pip install faster-whisper onnxruntime)
.venv/bin/python -m calvary_archive transcribe --dry-run
.venv/bin/python -m calvary_archive transcribe                     # resumable full run
.venv/bin/python -m calvary_archive transcribe --retry-failed      # re-queue failures
.venv/bin/python -m calvary_archive transcribe --year 2006 --limit 2
```

- Writes `transcripts/<year>/<audio-stem>.json` (machine-readable: full provenance, segments, word timestamps, quality metrics) and `.txt` (readable, `[m:ss]` markers).
- Canonical run configuration: `large-v3`, CUDA `float16`, batched pipeline (batch 16), beam 5, VAD on, word timestamps on, `language=en`. Configuration and engine version are recorded per transcript and in `logs/archive.jsonl`.
- Status lives in the `transcripts` table (`pending` / `transcribing` / `transcribed` / `failed` / `skipped`); completed transcripts are skipped on re-run, failures retried explicitly. Source audio is never modified.

### Corpus populations — methodological note

> The currently recovered and validated Calvary Spokane corpus represents material associated with the user's known exposure during the relevant period and is incomplete. A separate future research phase may attempt to reconstruct the church's broader 2004–2010 media ecosystem—including Heart Radio, Matters of the Heart, syndicated programming, legacy streaming infrastructure, third-party archives, and physical media. That broader population must remain analytically distinct from the validated exposure corpus unless independent evidence establishes exposure. Missing material in the current corpus should not, by itself, be treated as meaningful or intentional absence.

The deferred broader-ecosystem research phase is documented (not executed) in the archive workspace at `reports/corpus-populations.md`.

## Tests

The test suite is offline by default:

```bash
python -m pytest -q
```

It covers:

- date parsing and inclusive range boundaries;
- filename safety and stable identifiers;
- duplicate detection;
- item normalization and representative Subsplash/legacy parsing;
- supplemental source-provenance upserts and historical-video availability isolation;
- SQLite upserts preserving download facts;
- lifecycle and retry transitions;
- direct HTTP resume behavior, including preservation after malformed range replies;
- backend selection and delayed audio-only retrieval;
- checksum and fail-closed `ffprobe` behavior;
- deterministic CSV/JSON/report generation;
- legacy and subcommand CLI parsing.

## Known limitations

- Subsplash Core endpoints are public and versioned but are not a permanent archival contract. Raw response retention makes parser changes auditable.
- The Wayback listing snapshot was captured in 2011 and is itself incomplete for some older series. It supplements rather than replaces Subsplash; the union is the canonical inventory.
- The legacy media directory explicitly exposes the 2009 NYE update, but no currently public 2004–2008 NYE files were found. Absence from current public indexes is not proof that those services never occurred.
- Historical video links prove that video was once advertised; they do not prove the files survive. All 51 target-period links currently return 404 and have no Wayback media capture.
- The public bearer token is short-lived and must be refreshed from a public library page. Saved HTML contains `[REDACTED]`, never the token.
- Subsplash does not support server-side filtering by sermon date, so a complete metadata crawl must paginate the current app-wide collection.
- Some current items lack a usable sermon date. They remain `needs_review`; upload/import dates are not substituted.
- Historical media is heterogeneous. Some records use native Subsplash media, some use church-hosted files, some expose HLS or provider pages, and some contain malformed or obsolete external URLs.
- FTP URLs and unsupported schemes are retained as provenance but marked for review rather than accessed.
- A small number of legitimate records may have no accessible media. They remain `no_media`, not missing from inventory.
- `workers` is currently a conservative CLI contract; media orchestration remains serial even if a larger value is supplied.
- `download_attempts` counts failed item-level runs. Each run may make up to `--retries` backend attempts with exponential backoff.
- Use `--no-ffprobe` only when accepting weaker validation; the default intentionally refuses to mark files valid without `ffprobe`.
