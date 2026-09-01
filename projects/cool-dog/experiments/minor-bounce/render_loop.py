#!/usr/bin/env python3
"""Render deterministic Cool Dog minor-bounce loop variations.

The composition is original. Notes are encoded below in beat/pitch/duration tuples.
Audio synthesis uses only NumPy/SciPy; MIDI export uses mido; MP3 uses ffmpeg.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

import mido
import numpy as np
from scipy.signal import butter, sosfilt

SR = 48_000
BARS = 12
BEATS = BARS * 4


@dataclass(frozen=True)
class Variant:
    name: str
    bpm: int
    mode: str
    lead: tuple[int, ...]
    bass: tuple[int, ...]
    swing: float
    blips: bool


# One pitch per eighth-note. -1 is a rest. These are deliberately original motifs.
VARIANTS = (
    Variant("a_aeolian_skip", 122, "E Aeolian", (76, -1, 79, 78, 76, 71, 74, -1, 76, 79, 83, 81, 79, 78, 74, 71), (40, 40, 36, 38), 0.00, False),
    Variant("b_dorian_arcade", 126, "E Dorian", (76, 79, 78, -1, 74, 76, 71, 74, 76, 79, 81, 83, 81, 79, 78, -1), (40, 38, 35, 42), 0.035, True),
    Variant("c_phrygian_wink", 120, "E Phrygian/Aeolian", (76, 77, 71, 74, 76, -1, 79, 78, 76, 74, 71, 70, 71, 74, 78, -1), (40, 41, 36, 38), 0.02, True),
    Variant("d_aeolian_bounce", 124, "E Aeolian with chromatic approach tones", (76, -1, 79, 78, 76, 74, 71, 74, 76, 79, 78, 83, 81, 79, 78, 75), (40, 36, 38, 35), 0.025, True),
)


def midi_hz(note: int) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def env(n: int, attack: float = .006, release: float = .035) -> np.ndarray:
    if n <= 1:
        return np.zeros(n)
    a = min(n // 3, int(attack * SR)); r = min(n // 2, int(release * SR))
    e = np.ones(n)
    if a: e[:a] = np.linspace(0, 1, a, endpoint=False)
    if r: e[-r:] = np.linspace(1, 0, r, endpoint=True)
    return e


def add_tone(buf: np.ndarray, start: float, dur: float, note: int, amp: float, voice: str) -> None:
    i = int(round(start * SR)); n = min(len(buf) - i, int(round(dur * SR)))
    if n <= 1: return
    t = np.arange(n) / SR; f = midi_hz(note)
    if voice == "lead":
        x = .68 * np.sin(2*np.pi*f*t) + .22 * np.sin(2*np.pi*2*f*t) + .10 * np.sin(2*np.pi*3*f*t)
        x += .055 * np.sign(np.sin(2*np.pi*f*t))
    elif voice == "bass":
        x = .78 * np.sin(2*np.pi*f*t) + .22 * np.sin(2*np.pi*2*f*t)
    else:
        x = np.sin(2*np.pi*f*t) * (.75 + .25*np.sin(2*np.pi*7*t))
    buf[i:i+n] += amp * x * env(n, .004 if voice != "bass" else .008, .025)


def add_drums(buf: np.ndarray, beat: float, sec_per_beat: float, rng: np.random.Generator, kind: str) -> None:
    start = beat * sec_per_beat; i = int(round(start * SR))
    dur = .12 if kind == "kick" else .055; n = min(len(buf)-i, int(dur*SR))
    if n <= 1: return
    t = np.arange(n)/SR
    if kind == "kick":
        phase = 2*np.pi*(78*t - 27*t*t)
        x = np.sin(phase)*np.exp(-t*32)
    else:
        x = rng.standard_normal(n)*np.exp(-t*75)
        x = sosfilt(butter(2, 5000, btype="highpass", fs=SR, output="sos"), x)
    buf[i:i+n] += (.34 if kind == "kick" else .095) * x * env(n, .001, .012)


def events(v: Variant):
    lead=[]; bass=[]; blips=[]
    for bar in range(BARS):
        motif = list(v.lead)
        if bar in (3, 7, 11): motif[-4:] = [71, 74, 75, 76]
        if bar in (2, 6, 10): motif[8:12] = [83, 81, 79, 78]
        for step, note in enumerate(motif):
            if note >= 0:
                shift = v.swing if step % 2 else 0
                lead.append((bar*4 + step*.25 + shift, note + (12 if bar == 10 and step < 8 else 0), .205, 91))
        root=v.bass[bar % 4]
        for q in range(4):
            bass.append((bar*4+q, root if q != 3 else root+7, .42, 76))
        if v.blips:
            for at, p in ((1.5, root+31), (3.5, root+34)):
                blips.append((bar*4+at, p, .10, 58))
    return lead,bass,blips


def render(v: Variant, out: Path) -> dict:
    spb=60/v.bpm; duration=BEATS*spb; n=int(round(duration*SR)); mix=np.zeros(n)
    lead,bass,blips=events(v)
    for b,p,d,vel in lead: add_tone(mix,b*spb,min(d*spb,duration-b*spb),p,.27,"lead")
    for b,p,d,vel in bass: add_tone(mix,b*spb,d*spb,p,.22,"bass")
    for b,p,d,vel in blips: add_tone(mix,b*spb,d*spb,p,.075,"blip")
    rng=np.random.default_rng(0xC001D06)
    for half in np.arange(0,BEATS,.5):
        if half % 1 == 0: add_drums(mix,float(half),spb,rng,"kick")
        else: add_drums(mix,float(half),spb,rng,"hat")
    mix=sosfilt(butter(2, 18_000, fs=SR, output="sos"),mix)
    peak=float(np.max(np.abs(mix))); mix*=.88/max(peak,1e-9)
    pcm=np.int16(np.clip(mix,-1,1)*32767)
    wav=out/f"{v.name}.wav"
    with wave.open(str(wav),"wb") as f:
        f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR); f.writeframes(pcm.tobytes())
    write_midi(v,lead,bass,blips,out/f"{v.name}.mid")
    subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(wav),"-codec:a","libmp3lame","-b:a","192k","-map_metadata","-1",str(out/f"{v.name}.mp3")],check=True)
    seam=np.concatenate([mix[-1024:],mix[:1024]])
    return {"name":v.name,"bpm":v.bpm,"mode":v.mode,"duration_seconds":n/SR,"peak":float(np.max(np.abs(mix))),"endpoint_jump":float(abs(mix[0]-mix[-1])),"seam_max_delta":float(np.max(np.abs(np.diff(seam)))),"wav_sha256":hashlib.sha256(wav.read_bytes()).hexdigest()}


def write_midi(v: Variant, lead, bass, blips, path: Path) -> None:
    mid=mido.MidiFile(type=1,ticks_per_beat=480)
    meta=mido.MidiTrack(); mid.tracks.append(meta)
    meta.append(mido.MetaMessage("track_name",name=v.name,time=0)); meta.append(mido.MetaMessage("set_tempo",tempo=mido.bpm2tempo(v.bpm),time=0))
    for name,program,evs in (("Lead",81,lead),("Bass",38,bass),("Blips",80,blips)):
        tr=mido.MidiTrack(); mid.tracks.append(tr); tr.append(mido.MetaMessage("track_name",name=name,time=0)); tr.append(mido.Message("program_change",program=program,time=0))
        msgs=[]
        for b,p,d,vel in evs: msgs += [(int(round(b*480)),1,p,vel),(int(round((b+d)*480)),0,p,0)]
        last=0
        for tick,on,p,vel in sorted(msgs,key=lambda x:(x[0],x[1])):
            tr.append(mido.Message("note_on" if on else "note_off",note=p,velocity=vel,time=tick-last)); last=tick
    mid.save(path)


def main() -> None:
    ap=argparse.ArgumentParser(); ap.add_argument("--output",type=Path,default=Path(__file__).parent/"output"); ap.add_argument("--final",default="d_aeolian_bounce")
    args=ap.parse_args(); args.output.mkdir(parents=True,exist_ok=True)
    report=[render(v,args.output) for v in VARIANTS]
    chosen=next(v for v in VARIANTS if v.name==args.final)
    for ext in ("wav","mp3","mid"):
        src=args.output/f"{chosen.name}.{ext}"; (args.output/f"cooldog_minor_bounce_final.{ext}").write_bytes(src.read_bytes())
    (args.output/"validation.json").write_text(json.dumps({"selected":args.final,"variants":report},indent=2)+"\n")
    print(json.dumps({"selected":args.final,"output":str(args.output),"variants":report},indent=2))


if __name__ == "__main__": main()
