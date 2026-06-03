import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

SAMPLE_SRT = """\
1
00:00:01,000 --> 00:00:03,000
Hello world this is a test

2
00:00:03,500 --> 00:00:06,000
Second line of the song

3
00:00:06,500 --> 00:00:09,000
Third and final verse here
"""

SAMPLE_LRC = """\
[00:01.00]Hello world this is a test
[00:03.50]Second line of the song
[00:06.50]Third and final verse here
"""

SAMPLE_TXT = """\
Hello world this is a test
Second line of the song
Third and final verse here
"""

SAMPLE_TXT_WITH_SECTIONS = """\
[Intro, swooshy]

[Intro]
I never asked to be queer

[Verse]
I was such a good little Christian kid
At church up to 5 times per week, I did

[Verse 2, double time, female]
They warned me about going to university
That to stand for truth, I'd face great adversity

[Outro]
Now I'm the victim of a theocratic agenda
"""

SAMPLE_TXT_SECTIONS_ONLY = """\
[Intro]
[Verse]
[Chorus]
"""


@pytest.fixture
def sample_srt(tmp_path):
    p = tmp_path / "lyrics.srt"
    p.write_text(SAMPLE_SRT, encoding="utf-8")
    return p


@pytest.fixture
def sample_lrc(tmp_path):
    p = tmp_path / "lyrics.lrc"
    p.write_text(SAMPLE_LRC, encoding="utf-8")
    return p


@pytest.fixture
def sample_txt(tmp_path):
    p = tmp_path / "lyrics.txt"
    p.write_text(SAMPLE_TXT, encoding="utf-8")
    return p


@pytest.fixture
def sample_txt_sections(tmp_path):
    p = tmp_path / "lyrics.txt"
    p.write_text(SAMPLE_TXT_WITH_SECTIONS, encoding="utf-8")
    return p


@pytest.fixture
def sample_txt_sections_only(tmp_path):
    p = tmp_path / "lyrics.txt"
    p.write_text(SAMPLE_TXT_SECTIONS_ONLY, encoding="utf-8")
    return p


@pytest.fixture
def sample_wav(tmp_path):
    p = tmp_path / "test.wav"
    _write_sine_wav(p, duration=1.0, sr=22050, freq=440)
    return p


def _write_sine_wav(path: Path, duration: float = 1.0, sr: int = 22050, freq: float = 440.0):
    import soundfile as sf

    t = np.linspace(0, duration, int(sr * duration), endpoint=False, dtype=np.float32)
    signal = (0.5 * np.sin(2 * np.pi * freq * t)).astype(np.float32)
    sf.write(str(path), signal, sr)


@pytest.fixture
def sample_wav_with_beats(tmp_path):
    p = tmp_path / "beats.wav"
    sr = 22050
    dur = 2.0
    t = np.linspace(0, dur, int(sr * dur), endpoint=False, dtype=np.float32)
    sig = np.zeros_like(t)
    for beat in np.arange(0, dur, 0.5):
        idx = int(beat * sr)
        if idx + 200 < len(sig):
            env = np.exp(-np.arange(200) / (sr * 0.01)).astype(np.float32)
            sig[idx:idx + 200] += env * 0.8 * np.sin(2 * np.pi * 880 * np.arange(200) / sr).astype(np.float32)
    import soundfile as sf
    sf.write(str(p), sig, sr)
    return p


@pytest.fixture
def suno_data_dir(tmp_path):
    d = tmp_path / "suno_output"
    d.mkdir()
    _write_sine_wav(d / "Song.wav", duration=2.0, sr=22050)
    (d / "lyrics.txt").write_text("[Intro]\nHello world\n[Verse]\nSecond line\n")
    return d


@pytest.fixture
def sample_stem_wav(tmp_path):
    p = tmp_path / "0 Lead Vocals.wav"
    _write_sine_wav(p, duration=1.0, sr=22050, freq=440)
    return p
