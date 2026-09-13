# Music.xls — Inspection Report (2026-09-13)

Source: `projects/inherited-music-influence/source/Music.xls` (preserved copy of
`projects/Music.xls`).
SHA-256: `a8cdb6fc3851a5de9df14939684ef2dce52956b8896aef173b2b83f60c06d5da`
Legacy Composite Document (.xls), Author "Greg & Trina Horan", created 2000-11-01,
last saved 2026-09-13. Read via LibreOffice → xlsx conversion (`data/raw/Music.xlsx`,
deterministic artifact; the .xls original is never opened for writing).

## Sheets

- `Main` — 1201 rows × 14 cols; **1176 data rows** (row 1 = header). This is the archive.
- `Sheet2` (7 empty rows), `Sheet3` (1 empty cell) — no content.

## Columns (header row, position → meaning as observed)

| # | Header | Observed semantics |
|---|--------|--------------------|
| 0 | *(blank)* | Row number as text. 1176 values, 1175 unique — **two rows are both numbered "1"** (row 2 "A Season Of Song" and row 3 "Abdul, Paula, Forever Your Girl"). Numbering is otherwise monotonically increasing 1..1176. → do **not** use as stable ID; use sheet row number. |
| 1 | ARTIST | "Last, First" style ("Abdul, Paula", "Brooks, Garth"), band names plain ("AC/DC"), franchise names for soundtracks ("Back To The Future"), tape-series names ("FM Rock 1"), "Bond, James" (a joke entry for 007 themes). |
| 2 | +Band Name | Parenthetical qualifiers: `(various artists)` ×70 (compilations/soundtracks where ARTIST holds the series/movie name), performer credits `(.38 Special)`, `& The E Street Band`, `& Wings`, `(with Crazy Horse)`, `(solo)`. |
| 3 | Various Misc | Rare: `(various artists)` ×5, `(Vince Guaraldi Trio)`, and **one cross-reference: `(see Red Rider #1)`** on "Cochrane, Tom & Red Rider". |
| 4 | ALBUM TITLE | Release / tape title. |
| 5 | *(blank header)* | Edition qualifiers: `(Box Set)` ×6, `(6 Pack)` ×6, `(Greatest Hits)` ×4, `(White Album)`, `(The # 1's)`. |
| 6 | YEAR | 1963–2000, all `YYYY` when present; **26 empty**. |
| 7 | MEDIA | Album ×465, Tape ×359, CD ×352. |
| 8 | Tape1 | 607 non-empty. For Album/CD rows: the numbered cassette this item was **dubbed onto**. For Tape-type rows: likely the tape's own physical number — **semantics ambiguous for Tape rows; documented, not resolved.** |
| 9 | Tape2 | 68 non-empty (second dub target). |
| 10 | Order | 799 non-empty. Position/order of the item on the dub tape. |
| 11 | Special | `Xmas` ×13. |
| 12 | Misc | `Album` ×24 (media re-affirmation on rows whose title might suggest otherwise, e.g. Beatles "Abbey Road"). |
| 13 | Favorite | `Favorite` ×**174**; empty otherwise. **Source-level assertion about the album.** |

## Source-type census

- Commercial albums/CDs: the bulk of rows (MEDIA Album/CD).
- **Named personally-curated tape series** (row where ARTIST ≈ ALBUM ≈ series name):
  FM Rock 1–7, Instrumentals 1–4 (Hard/Soft/Rock/Mellow Instrumentals), Mellow Tape
  01–11, Mellow Gold (Album), Oldies 1–3, **Party Tape 01–17** (Party Tape 15 =
  "Greg & Trina's Wedding Reception", Party Tape 17 = "Greg's 35th Birthday Tape").
  These are single rows with **no track lists** in the workbook → `tracklist_unknown`.
- Compilations/soundtracks: 70 rows tagged `(various artists)` in +Band Name plus
  5 "Various Misc" rows (soundtrack/series names as artist).
- **Dub-tape linkage**: every Album/CD row with Tape1/Tape2/Order records that Greg
  dubbed that album onto numbered cassettes (tape #6, #12, #74, #165, #185, …).
  Cassette #N's contents are therefore *derivable* from the workbook (all rows
  dubbed to N, ordered by Order) — a future derived view, not invented data.

## Favorite semantics

174 rows marked `Favorite` — always album-level. No per-song favorite data exists.
→ `appears_on_dad_favorite_source` derived per song; never "favorite song".

## Duplicate / ambiguity census

- Zero exact (ARTIST, ALBUM) duplicate rows after trimming (the double "1" rows are
  different albums).
- 46 rows have tape-series-like titles (custom tapes) — excluded from commercial
  release resolution.
- One intentional cross-reference row ("see Red Rider #1") — alias, flagged.
- 26 rows missing year; 1 row artist "Bond, James" (novelty); "(see …)" refs.
- Ambiguity classes for release resolution: Greatest Hits/Best Of title collisions
  across artists (fine — artist scoped), same-title different-edition per artist
  (year disambiguates), empty years, soundtrack franchise-name artists,
  spelling variants.

## Named tapes vs. brief's examples — all present

Party Tapes (17), Mellow Tapes (11 + Mellow Gold), FM Rock (7), Instrumentals (4),
Oldies (3), Greg & Trina's Wedding Reception, Greg's 35th Birthday Tape. ✓
