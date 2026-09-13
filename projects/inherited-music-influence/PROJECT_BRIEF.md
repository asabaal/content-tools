# Inherited Music Influence Archive

## Project purpose

Construct a complete, provenance-preserving database of the music represented in Greg Horan’s pre-2000 music archive so that Asabaal can systematically reconstruct the musical environment she was exposed to before she began independently choosing music for herself.

This is an **autobiographical influence-recovery project**.

The immediate question is not merely:

> What music did Greg own?

The larger question is:

> What music was plausibly present in Asabaal’s early listening environment, what does she actually recognize from childhood, and what musical characteristics from that environment can later be identified in her own listening preferences and artistic work?

The system should do the expensive organizational work once. Afterward, Asabaal’s primary workflow should be:

1. Open the prioritized queue.
2. Listen to a song.
3. Mark recognition/status.
4. Add autobiographical or musical notes.
5. Move to the next song.

She should not have to repeatedly reconstruct album metadata, track lists, source relationships, or whether she has already investigated a song.

---

# Canonical source

The primary source is Greg Horan’s historical Excel music catalog, currently supplied as:

`Music.xls`

The original workbook must be preserved unchanged as a canonical archival source.

Create a checksum/hash and store the untouched original or an immutable reference to it.

The workbook contains more than 1,000 catalog entries covering commercial albums, CDs, cassette tapes, compilations, and personally curated cassette series.

It also includes Greg’s explicit **Favorite** designation.

Important provenance rule:

**Favorite is a source-level assertion.**

If Greg marked an album Favorite, do NOT transform that into:

> Greg considered every track on this album a favorite song.

Instead derive:

`appears_on_dad_favorite_source = true`

That distinction must remain visible throughout the system.

---

# Historical context

Greg Horan was born in 1958.

Greg and Asabaal’s mother married in 1991.

Asabaal was born in 1992.

The collection therefore substantially predates Asabaal and represents part of the musical environment already present when she entered the household.

The archive also includes personally curated cassette series and family-event recordings such as:

* Party Tapes
* Mellow Tapes
* FM Rock tapes
* Instrumental tapes
* Oldies tapes
* Greg & Trina’s Wedding Reception
* Greg’s 35th Birthday Tape

These sources can contain stronger evidence of deliberate playback behavior than simple ownership.

Do not, however, invent track lists for homemade tapes where no reliable track list is available.

---

# Scope

Process the **entire Greg Horan archive**, not merely the initial Top 300 recognition list.

For every resolvable commercial release:

* identify the artist
* identify the exact or best-supported release
* retrieve the track list
* normalize individual songs/tracks
* determine release date
* determine label where available
* retain edition/version information
* retain source provenance
* associate every track with all relevant appearances in Greg’s archive

The result should support both:

1. a complete research dataset
2. a ranked listening queue

---

# Core entities

Do not model this as one giant flat spreadsheet internally.

At minimum distinguish the following entities.

## 1. Dad Source Record

One row/source from Greg’s original workbook.

Suggested fields:

* `dad_source_id`
* original row number
* artist as written
* title as written
* source/release type
* physical format
* catalog/tape number if present
* source year as written
* Favorite status
* original notes
* raw source values
* canonical-original reference

Preserve the source exactly enough that any normalized data can always be traced back to the workbook.

## 2. Release

A commercially released album, compilation, CD edition, etc.

Suggested fields:

* `release_id`
* canonical artist
* release title
* release type
* original release date
* specific edition date if relevant
* record label
* catalog number if available
* country/edition if relevant
* source metadata provider
* metadata confidence
* resolution status

Exact-edition resolution matters particularly for:

* Greatest Hits packages
* Best Of releases
* reissues
* remasters
* similarly named releases
* cassette/CD editions with different track lists

Do not silently choose an uncertain edition.

Create an unresolved/review queue when necessary.

## 3. Song / Recording

Songs need canonical identities independent of album appearances.

Suggested fields:

* `song_id`
* canonical artist
* canonical title
* alternate title
* recording/version
* original release date where known
* songwriting/work identifiers if useful
* popularity data
* popularity score
* popularity methodology version

Distinguish where practical between:

* underlying song/work
* specific recording
* live/remix/edit/remaster variants

Do not create duplicate canonical songs merely because the same recording appears on a studio album and a Greatest Hits compilation.

## 4. Track Appearance

Join table connecting a song/recording to a release.

Suggested fields:

* `release_id`
* `song_id`
* disc
* track number
* track title as printed
* version information

## 5. Dad Appearance

Join a canonical song back to Greg’s historical sources.

Suggested fields:

* `song_id`
* `dad_source_id`
* `release_id`
* `appears_on_dad_favorite_source`
* source format
* source type
* certainty
* notes

A song may therefore appear multiple times in Greg’s archive.

That information must not be discarded during deduplication.

---

# Personally curated cassette sources

Personally curated tapes are important behavioral evidence.

Model them as first-class historical sources.

Examples include Party Tapes, Mellow Tapes, FM Rock tapes, the wedding-reception tape, etc.

However:

**Never infer a homemade tape track list merely from its title or from unrelated public sources.**

Possible states should include:

* `tracklist_known`
* `tracklist_partial`
* `tracklist_unknown`
* `physical_media_recovery_needed`

This creates a future pathway for tape recovery without contaminating the present archive with guesses.

---

# User listening / recognition layer

The generated archival data and Asabaal’s annotations must be separated.

Regenerating metadata must never overwrite her listening notes.

Each canonical song should support at minimum:

### Recognition status

* `unreviewed`
* `definitely_recognize`
* `not_sure`
* `definitely_do_not_recognize`

These correspond to the current recognition-screening workflow.

Also support:

* `childhood_association`: yes / maybe / no / unknown
* `listened`: yes/no
* `first_reviewed_at`
* `last_listened_at`
* `listening_note`
* `memory_note`
* `musical_features`
* `possible_influence_note`
* `influence_confidence`

Preserve the difference between:

> I recognized this before replaying it.

and:

> I listened to it during the research project.

That distinction is autobiographically important.

---

# Prioritization

The complete database must include everything.

Separately generate a ranked listening queue.

## Fundamental ranking rule

**Greg evidence comes first. Popularity comes second.**

This should be implemented lexicographically rather than through a single opaque weighted number.

A massive cultural hit should not outrank stronger explicit evidence from Greg’s archive merely because its popularity number is high.

### Primary: Dad evidence

Explicit Favorite information from Greg’s workbook is the strongest available Dad-ranking signal.

At minimum capture:

* whether a song appears on any Favorite-marked source
* number of Favorite-marked sources containing it
* number of total Greg sources containing it
* whether it appears in a personally curated source, if the actual tape track list is known

Do not confuse these inferred source relationships with Greg explicitly ranking individual songs.

Give the derived fields names that make the distinction clear.

### Secondary: Song popularity / cultural ubiquity

Within comparable Dad-evidence groups, prioritize songs according to external popularity.

Popularity should attempt to measure:

> How likely was this song to be encountered or culturally recognized?

Prefer transparent evidence such as:

* major chart performance
* chart longevity
* certified sales where useful
* durable streaming/listening measures where legitimately accessible
* well-supported historical popularity datasets
* inclusion in major hit compilations or other defensible ubiquity indicators

Do not fabricate metrics.

Store the underlying popularity evidence, source, retrieval date, and methodology rather than retaining only a mystery score.

Produce a normalized `popularity_score` for sorting, but make it reproducible.

Version the methodology, for example:

`popularity_method = v1`

If external data is incomplete, represent missingness rather than assigning imaginary precision.

### Tertiary evidence

Possible tie breakers may include:

* appearance on multiple Greg sources
* known personally curated tape appearance
* release timing relevant to Asabaal’s childhood
* duplicate household representations across formats

Keep these fields available independently even if they are not heavily weighted initially.

---

# Top 300

Generate a dynamic:

`Top 300 Recognition Queue`

This is the main first-pass working set.

The Top 300 should be generated from the complete dataset using the prioritization system above.

It should NOT become the canonical database.

The current manually constructed Top 300 recognition list from the ChatGPT research conversation can be retained as a **seed/reference list** if supplied, but it is not authoritative.

Compare the generated Top 300 against the seed list as a quality check.

Interesting discrepancies should be reported rather than silently forced to match.

---

# Full listening queue

Also generate the entire ranked queue.

Asabaal should be able to continue past #300 without any additional restructuring.

Useful views:

* Top 300
* all songs
* unreviewed songs
* definite recognition
* unsure
* definite non-recognition
* childhood-associated songs
* Dad Favorite-source songs
* songs appearing on multiple Dad sources
* unresolved metadata
* personally curated tape material
* reviewed songs with notes

---

# Suggested output formats

Follow existing Content Tools repository conventions where possible.

Prefer durable machine-readable sources with generated human-facing views.

Recommended canonical/derived artifacts:

* SQLite database or equivalent structured datastore
* JSON/JSONL export
* CSV export
* generated Markdown tables
* optionally a simple local HTML interface if consistent with repo architecture

Do not make Markdown the sole database.

A lightweight interface is welcome, but do not spend substantial effort building UI before the dataset and provenance model are correct.

---

# Suggested project structure

Use repository conventions if they already provide a better pattern. Otherwise something approximately like:

```text
projects/inherited-music-influence/
├── PROJECT_BRIEF.md
├── README.md
├── source/
│   └── Music.xls
├── data/
│   ├── raw/
│   ├── normalized/
│   └── derived/
├── research/
│   ├── sources.md
│   ├── unresolved-releases.md
│   └── popularity-methodology.md
├── output/
│   ├── top-300.md
│   ├── full-listening-queue.md
│   └── archive-summary.md
├── src/
└── tests/
```

Adapt rather than forcing this structure if Content Tools already has established project conventions.

---

# Provenance requirements

This is autobiographical research. Provenance matters more than false completeness.

Every externally derived claim should retain enough source information to reconstruct where it came from.

For important metadata retain:

* provider/source
* source identifier or URL where practical
* retrieval date
* confidence
* manual override status

Do not silently overwrite original values with normalized ones.

Preserve both.

Examples:

`original_artist = "..."`

`canonical_artist = "..."`

---

# Ambiguity handling

Never hallucinate through an ambiguous release match.

Use statuses such as:

* resolved
* probable
* ambiguous
* unresolved
* requires_manual_review

Generate a human-review report.

Likely ambiguity classes include:

* same album title across editions
* Greatest Hits compilations
* reissues
* incomplete years
* spelling variants
* duplicate catalog rows
* homemade tapes
* incomplete cassette information

A partially resolved archive with explicit uncertainty is preferable to a seemingly complete but contaminated archive.

---

# Regeneration and preservation

The pipeline should be rerunnable.

Generated metadata may be refreshed.

User-authored research notes must survive regeneration.

Separate:

**source/archive data**

from:

**Asabaal annotation data**

from:

**generated views/rankings**

Do not make the user's notes dependent on row positions in a regenerated CSV.

Use stable IDs.

---

# Quality checks

At minimum test that:

1. Every meaningful original workbook row is represented.
2. No original source record disappears during normalization.
3. Songs appearing on multiple releases retain all appearances.
4. Favorite status remains source-level.
5. User notes survive regeneration.
6. Every generated ranking can be explained from stored fields.
7. Top 300 contains exactly 300 unique canonical songs when at least 300 resolvable songs exist.
8. Unresolved releases are reported rather than discarded.
9. Metadata provenance exists for externally enriched records.
10. Running the pipeline twice does not duplicate records.

---

# Deliverables

The first implementation should produce:

1. Preserved canonical `Music.xls` source.
2. Parsed representation of every Greg source row.
3. Release-resolution pipeline.
4. Commercial-release track lists.
5. Canonical song/recording database.
6. Song ↔ release ↔ Greg-source relationships.
7. Release dates and labels where supportable.
8. Popularity-research pipeline.
9. Transparent popularity score.
10. Dad-first priority algorithm.
11. Generated Top 300.
12. Complete ranked listening queue.
13. User recognition/listening annotation system.
14. Unresolved/ambiguous research report.
15. README explaining how to update, regenerate, and continue the project.
16. Tests and data-integrity checks.

---

# Definition of success

The project succeeds when Asabaal can open the archive, select the next prioritized song, listen to it, record a note, and move on—without needing to research what album it came from, whether it exists elsewhere in Greg’s history, whether she has previously reviewed it, or how it fits into the larger archive.

Over time the dataset should make it possible to move from:

> “My dad listened to classic rock.”

to evidence-backed autobiographical conclusions such as:

> “This is music demonstrably present in my early household environment; I explicitly remember this recording; this musical characteristic appears repeatedly in what I later chose and created.”

The archive should support those conclusions without prematurely asserting causation.
