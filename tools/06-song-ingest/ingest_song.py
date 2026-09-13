#!/usr/bin/env bash
# `ingest-song` — convenience alias for the song ingestion pipeline.
# Usage: tools/06-song-ingest/ingest_song.py "<project-dir>" [--stages ...]
PYTHON="${PYTHON:-/mnt/storage/python_env/basic_audio_env/bin/python}"
exec "$PYTHON" "$(dirname "$0")/song_ingest/cli.py" ingest "$@"
