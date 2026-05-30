# First Draft Karaoke Videos - Prophetic Preprint

## Overview

Generate karaoke lyric videos for all 42 songs on the Prophetic Preprint tracklist using the music-video-pipeline. This is a first draft pass with auto-sync (no manual sync review). Each song gets a unique mood assignment based on BPM and lyrical content.

## Source Assets

- **Audio**: 42 WAV files (full mix from Suno)
- **Stems**: 42 ZIP archives (tempo-locked, per-instrument WAVs)
- **MIDI**: 42 ZIP archives (per-instrument .mid files)
- **Lyrics**: `all-lyrics.txt` (single file, split into per-song files for pipeline)
- **Pipeline**: `/mnt/storage/repos/content-tools/music-video-pipeline/`

## Filename Mappings

Some tracklist names differ from the filenames on disk:

| Tracklist Name | Filename on Disk |
|---|---|
| Nathan's Song | Nathan's Song - v1 |
| What is Truth? | WHAT IS TRUTH - V1 |
| Where Ben Has Been | Where Ben Has Been - V1 |
| ELECTRIC PULSE | Electric Pulse (2025 Reimagination) - DRAFT |
| CULTURE CREATOR | CULTURE CREATOR - (AS I EVOLVE Teaser Demo) |
| Didn't Forget Jesus | Didn't Forget Jesus (2025 Reimagination) |
| PREDICTION ENGINE | Prediction Engine (2025 Reimagined) |
| Marquis' Song | Marquis' Song - Draft |
| How Do I Praise You? | How Do I Praise You_ |
| Who do you think I am? | Who do you think I am_ |

## Mood Assignments

Based on BPM and lyrical content/vibe. Distribution: ~8 songs per mood.

| # | Song | BPM | Mood | Rationale |
|---|------|-----|------|-----------|
| 1 | AI Psalm 9 | 69 | cool_ethereal | Slow atmospheric spoken word |
| 2 | THE TABLES ARE SET | 91 | dark_moody | Prophetic declaration |
| 3 | Who do you think I am? | 130 | bright_poppy | Upbeat, conversational |
| 4 | Take This Cup | 128 | high_energy | Intense repetitive hook |
| 5 | CHILD OF GOD (WHO YOU BE) | 82 | warm_intimate | Personal identity testimony |
| 6 | HERE GOES | 126 | bright_poppy | Playful, optimistic |
| 7 | THE AS I EVOLVE PROVERB | 106 | cool_ethereal | Meditative proverb atoms |
| 8 | CONSCIENCE CLEAN | 84 | warm_intimate | Confessional testimony |
| 9 | I Never Asked To Be Queer | 103 | dark_moody | Heavy personal/political |
| 10 | ASABAAL | 136 | high_energy | Fast rapped, aggressive |
| 11 | Nathan's Song | 108 | warm_intimate | Tribute, anthemic |
| 12 | A WORD | 148 | high_energy | Fast declarative |
| 13 | Ask, Seek, Knock | 100 | bright_poppy | Catchy upbeat hook |
| 14 | AI Psalm 1 | 73 | cool_ethereal | Slow multi-movement |
| 15 | THE GLORY | 120 | bright_poppy | Celebratory worship |
| 16 | NOTHING IS IMPOSSIBLE | 90 | high_energy | Rap-rock declarative |
| 17 | BLESSED (THE NAME) | 60 | cool_ethereal | Slow heavenly courtroom |
| 18 | PATIENT | 91 | warm_intimate | Contemplative |
| 19 | Didn't Forget Jesus | 100 | dark_moody | Personal struggle |
| 20 | MISCLASSIFIED | 94 | dark_moody | Lo-fi heavy themes |
| 21 | NOT YOUR SLAVE | 76 | high_energy | Aggressive punk energy |
| 22 | MORE POWER | 90 | high_energy | Declarative prophetic |
| 23 | WOE TO YOU | 97 | dark_moody | Prophetic warning |
| 24 | FREEDOM | 96 | bright_poppy | Anthemic gospel |
| 25 | PREDICTION ENGINE | 126 | cool_ethereal | Conceptual experimental |
| 26 | FRESH REVELATION | 68 | warm_intimate | Intimate playful |
| 27 | THE HIDDEN LIBRARY | 86 | dark_moody | Mystery, hidden knowledge |
| 28 | PROPHETIC CLARITY | 87 | bright_poppy | Clear declarative |
| 29 | THE FIRST SCROLL | 120 | dark_moody | Heavy prophetic scroll |
| 30 | FRUIT | 96 | bright_poppy | Playful fruity hooks |
| 31 | CULTURE CREATOR | 102 | cool_ethereal | Atmospheric movements |
| 32 | PHASE TRANSITION | 80 | cool_ethereal | Experimental physics |
| 33 | ELECTRIC PULSE | 130 | high_energy | Electric upbeat |
| 34 | UP | 124 | bright_poppy | Upbeat trading up |
| 35 | How Do I Praise You? | 78 | warm_intimate | Intimate questioning |
| 36 | SABBATH | 118 | warm_intimate | Restful contemplative |
| 37 | What is Truth? | 146 | high_energy | Fast intense |
| 38 | Love Them Harder | 129 | warm_intimate | Emotional heartbroken |
| 39 | Where Ben Has Been | 67 | cool_ethereal | Ambient spoken word |
| 40 | THE DEVIL'S PLAYBOOK | 125 | dark_moody | Dark classroom prophetic |
| 41 | Marquis' Song | 82 | dark_moody | Testimony confrontation |
| 42 | COVENANT KEEPING GOD | 75 | warm_intimate | Intimate worship |

## Execution Steps

### Step 1: Prep - Create `batch_videos.py`

A Python script that:
1. Parses `all-lyrics.txt` into 42 individual `lyrics.txt` files
2. Creates 42 project directories under `projects/` with symlinks to WAV, Stems ZIP, MIDI ZIP
3. Maps tracklist names to disk filenames (handles naming mismatches)
4. Runs `mvp init` + `mvp render --mood <assigned>` for each song

### Step 2: Run the batch script

Each song takes ~2-5 min for analysis + render. Total: ~2-3 hours for all 42.

### Step 3: Collect outputs

Copy all rendered `.mp4` files into a single `renders/` directory with numbered filenames:
- `01 - AI Psalm 9.mp4`
- `02 - THE TABLES ARE SET.mp4`
- ... etc

## Technical Details

- **Resolution**: 1920x1080 (pipeline default)
- **FPS**: 30 (pipeline default)
- **Codec**: H.264 + AAC (pipeline default)
- **Text reveal**: karaoke mode (word-by-word highlight)
- **Audio sync**: Auto-sync via MIDI > vocal stem > full mix onsets (no manual review)
- **Visual script**: Auto-generated per song by `mvp render --mood`
- **Storage**: Symlinks to source assets (no duplication of ~4GB WAVs)

## Post-First-Draft

After reviewing the first draft:
- Assess sync quality on a sample of songs
- Consider manual sync corrections for songs with poor auto-sync
- Adjust mood assignments if any feel mismatched
- Consider per-song color/palette customization
- Add background images or video clips if desired
