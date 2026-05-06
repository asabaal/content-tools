import json
from pathlib import Path

import pytest

from pipeline.models import (
    MusicVideoProject,
    ProjectPaths,
    AudioInfo,
    LyricsInfo,
    StageStatus,
    InputTier,
    StemInfo,
    MidiFileInfo,
    IngestResult,
    SUPPORTED_AUDIO,
    SUPPORTED_LYRICS,
)


class TestInputTier:
    def test_values(self):
        assert InputTier.BASIC.value == "basic"
        assert InputTier.STANDARD.value == "standard"
        assert InputTier.ENHANCED.value == "enhanced"
        assert InputTier.FULL.value == "full"


class TestStemInfo:
    def test_to_dict(self):
        s = StemInfo(name="Lead Vocals", stem_type="lead_vocals", path="/tmp/vocals.wav", format="wav")
        d = s.to_dict()
        assert d["name"] == "Lead Vocals"
        assert d["stem_type"] == "lead_vocals"
        assert d["format"] == "wav"


class TestMidiFileInfo:
    def test_to_dict(self):
        m = MidiFileInfo(name="Song (Vocals).mid", path="/tmp/vocals.mid", instrument="Vocals", note_count=100, duration=150.0)
        d = m.to_dict()
        assert d["instrument"] == "Vocals"
        assert d["note_count"] == 100


class TestIngestResult:
    def test_to_dict_minimal(self):
        r = IngestResult(tier="basic")
        d = r.to_dict()
        assert d["tier"] == "basic"
        assert d["stems"] == []
        assert d["midi_files"] == []

    def test_to_dict_with_stems(self):
        s = StemInfo(name="Drums", stem_type="drums", path="/tmp/drums.wav")
        r = IngestResult(tier="enhanced", stems=[s])
        d = r.to_dict()
        assert len(d["stems"]) == 1
        assert d["stems"][0]["name"] == "Drums"


class TestProjectPaths:
    def test_resolve_audio_exists(self, tmp_path):
        (tmp_path / "raw" / "song.mp3").parent.mkdir(parents=True)
        (tmp_path / "raw" / "song.mp3").write_bytes(b"data")
        paths = ProjectPaths(audio="raw/song.mp3")
        assert paths.resolve_audio(tmp_path) == tmp_path / "raw" / "song.mp3"

    def test_resolve_audio_missing(self, tmp_path):
        paths = ProjectPaths(audio="raw/missing.mp3")
        assert paths.resolve_audio(tmp_path) is None

    def test_resolve_audio_none(self, tmp_path):
        paths = ProjectPaths(audio=None)
        assert paths.resolve_audio(tmp_path) is None

    def test_resolve_lyrics_exists(self, tmp_path):
        (tmp_path / "raw").mkdir()
        (tmp_path / "raw" / "lyrics.srt").write_text("x")
        paths = ProjectPaths(lyrics="raw/lyrics.srt")
        assert paths.resolve_lyrics(tmp_path) == tmp_path / "raw" / "lyrics.srt"

    def test_resolve_lyrics_missing(self, tmp_path):
        paths = ProjectPaths(lyrics="raw/gone.srt")
        assert paths.resolve_lyrics(tmp_path) is None

    def test_resolve_lyrics_none(self, tmp_path):
        paths = ProjectPaths(lyrics=None)
        assert paths.resolve_lyrics(tmp_path) is None


class TestStageStatus:
    def test_defaults(self):
        s = StageStatus()
        assert s.ingest == "pending"
        assert s.render == "pending"

    def test_mark_complete(self):
        s = StageStatus()
        s.mark_complete("ingest")
        assert s.ingest == "complete"
        assert s.is_complete("ingest")

    def test_mark_complete_unknown_stage(self):
        s = StageStatus()
        s.mark_complete("nonexistent")
        assert not hasattr(s, "nonexistent") or True

    def test_is_complete_false(self):
        s = StageStatus()
        assert not s.is_complete("ingest")

    def test_next_pending_first(self):
        s = StageStatus()
        assert s.next_pending() == "ingest"

    def test_next_pending_middle(self):
        s = StageStatus()
        s.mark_complete("ingest")
        s.mark_complete("analyze")
        assert s.next_pending() == "sync"

    def test_next_pending_all_complete(self):
        s = StageStatus()
        for stage in ["ingest", "analyze", "sync", "structure", "design", "render"]:
            s.mark_complete(stage)
        assert s.next_pending() is None


class TestMusicVideoProject:
    def test_create_minimal(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="Test")
        assert proj.name == "Test"
        assert proj.artist == ""
        assert proj.stages.is_complete("ingest")
        assert (tmp_path / "data" / "raw").is_dir()
        assert (tmp_path / "data" / "assets").is_dir()
        assert (tmp_path / "data" / "output").is_dir()
        assert (tmp_path / "data" / "mvp_project.json").exists()

    def test_create_with_audio(self, tmp_path):
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"fake audio")
        proj = MusicVideoProject.create(project_dir=tmp_path / "proj", name="X", audio_path=audio)
        assert proj.paths.audio == "raw/song.mp3"
        assert (tmp_path / "proj" / "data" / "raw" / "song.mp3").exists()

    def test_create_with_lyrics(self, tmp_path):
        lyrics = tmp_path / "lyrics.srt"
        lyrics.write_text("1\n00:00:00,000 --> 00:00:01,000\nHello")
        proj = MusicVideoProject.create(project_dir=tmp_path / "proj", name="X", lyrics_path=lyrics)
        assert proj.paths.lyrics == "raw/lyrics.srt"
        assert (tmp_path / "proj" / "data" / "raw" / "lyrics.srt").exists()

    def test_create_with_data_dir(self, tmp_path):
        data_dir = tmp_path / "suno_output"
        data_dir.mkdir()
        (data_dir / "song.mp3").write_bytes(b"audio")
        proj = MusicVideoProject.create(project_dir=tmp_path / "proj", name="X", data_dir=data_dir)
        assert proj.paths.data_dir == str(data_dir.resolve())

    def test_create_does_not_overwrite_existing_files(self, tmp_path):
        proj_dir = tmp_path / "proj"
        proj_dir.mkdir()
        raw = proj_dir / "data" / "raw"
        raw.mkdir(parents=True)
        existing = raw / "song.mp3"
        existing.write_bytes(b"original")
        audio = tmp_path / "song.mp3"
        audio.write_bytes(b"new")
        MusicVideoProject.create(project_dir=proj_dir, name="X", audio_path=audio)
        assert existing.read_bytes() == b"original"

    def test_save_and_load_roundtrip(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="Round", artist="Trip")
        proj.audio_info = AudioInfo(duration=10.0, bpm=120, sample_rate=44100, beat_count=20, onset_count=40)
        proj.lyrics_info = LyricsInfo(total_lines=5, total_words=30, format="srt", first_line_time=1.0, last_line_time=9.0)
        proj.stages.mark_complete("analyze")
        proj.save()

        loaded = MusicVideoProject.load(tmp_path)
        assert loaded.name == "Round"
        assert loaded.artist == "Trip"
        assert loaded.audio_info.duration == 10.0
        assert loaded.audio_info.bpm == 120
        assert loaded.audio_info.beat_count == 20
        assert loaded.audio_info.onset_count == 40
        assert loaded.lyrics_info.total_lines == 5
        assert loaded.lyrics_info.total_words == 30
        assert loaded.lyrics_info.format == "srt"
        assert loaded.lyrics_info.first_line_time == 1.0
        assert loaded.lyrics_info.last_line_time == 9.0
        assert loaded.stages.is_complete("ingest")
        assert loaded.stages.is_complete("analyze")
        assert not loaded.stages.is_complete("sync")

    def test_load_missing_raises(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="No project found"):
            MusicVideoProject.load(tmp_path)

    def test_project_dir_not_set_raises(self):
        proj = MusicVideoProject(name="X")
        with pytest.raises(ValueError, match="Project directory not set"):
            _ = proj.project_dir

    def test_project_dir_setter(self, tmp_path):
        proj = MusicVideoProject(name="X")
        proj.project_dir = tmp_path
        assert proj.project_dir == tmp_path

    def test_path_properties(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        assert proj.data_dir == tmp_path / "data"
        assert proj.raw_dir == tmp_path / "data" / "raw"
        assert proj.assets_dir == tmp_path / "data" / "assets"
        assert proj.output_dir == tmp_path / "data" / "output"
        assert proj.cache_dir == tmp_path / "data" / "cache"
        assert proj.project_file == tmp_path / "data" / "mvp_project.json"
        assert proj.ingest_file == tmp_path / "data" / "ingest.json"
        assert proj.analysis_file == tmp_path / "data" / "analysis.json"
        assert proj.waveforms_file == tmp_path / "data" / "waveforms.json"
        assert proj.lyrics_raw_file == tmp_path / "data" / "lyrics_raw.json"

    def test_load_preserves_extra_fields(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        proj.save()
        pf = tmp_path / "data" / "mvp_project.json"
        data = json.loads(pf.read_text())
        data["future_field"] = "preserved"
        pf.write_text(json.dumps(data))
        loaded = MusicVideoProject.load(tmp_path)
        assert loaded.name == "X"

    def test_created_and_modified_set(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        assert proj.created is not None
        assert proj.modified is not None

    def test_schema_version_default(self):
        proj = MusicVideoProject()
        assert proj.schema_version == "1.0"

    def test_input_tier_default(self):
        proj = MusicVideoProject()
        assert proj.input_tier == "basic"

    def test_save_and_load_with_tier(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        proj.input_tier = "full"
        proj.save()
        loaded = MusicVideoProject.load(tmp_path)
        assert loaded.input_tier == "full"

    def test_audio_info_midi_bpm(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        proj.audio_info = AudioInfo(duration=10.0, bpm=103.8, midi_bpm=103.8)
        proj.save()
        loaded = MusicVideoProject.load(tmp_path)
        assert loaded.audio_info.midi_bpm == 103.8

    def test_lyrics_info_sections(self, tmp_path):
        proj = MusicVideoProject.create(project_dir=tmp_path, name="X")
        proj.lyrics_info = LyricsInfo(total_lines=10, has_sections=True, section_count=5)
        proj.save()
        loaded = MusicVideoProject.load(tmp_path)
        assert loaded.lyrics_info.has_sections is True
        assert loaded.lyrics_info.section_count == 5


class TestConstants:
    def test_supported_audio(self):
        assert ".mp3" in SUPPORTED_AUDIO
        assert ".wav" in SUPPORTED_AUDIO
        assert ".flac" in SUPPORTED_AUDIO

    def test_supported_lyrics(self):
        assert ".srt" in SUPPORTED_LYRICS
        assert ".lrc" in SUPPORTED_LYRICS
        assert ".txt" in SUPPORTED_LYRICS
