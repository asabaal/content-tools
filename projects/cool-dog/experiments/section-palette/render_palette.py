#!/usr/bin/env python3
"""Deterministically render twelve Cool Dog section-palette sketches."""
from __future__ import annotations

import argparse, hashlib, json, subprocess, wave
from dataclasses import asdict, dataclass
from pathlib import Path
import mido
import numpy as np
from scipy.signal import butter, sosfilt

SR=48_000; TPB=480
# Motif A: carried forward from the original minor-bounce experiment.
MOTIF_A=(76,-1,79,78,76,74,71,74,76,79,78,83,81,79,78,75)
# Motif B: new "Steward" identity: rising fifth, inward semitone, then open ascent.
MOTIF_B=(64,67,71,70,66,69,72,71)

@dataclass(frozen=True)
class Section:
    slug:str; title:str; bpm:int; bars:int; mode:str; chords:tuple[tuple[int,...],...]
    treatment:str; groove:str; lead_voice:str; bass_voice:str; description:str

SECTIONS=(
 Section("01_opening_chant","Opening Cool Dog Chant",124,8,"E Aeolian",((52,55,59),(48,52,55),(50,54,57),(47,50,54)),"a_chant","bounce","pulse","round","Motif A in a square chant-sized register with four-bar vocal windows."),
 Section("02_movement_i_rap","Movement I Rap",96,8,"E Aeolian",((40,47,52),(43,47,50),(36,43,48),(38,45,50)),"a_fragments","hiphop","pluck","sub","Two- and three-note A fragments answer dense rap phrases over a syncopated pocket."),
 Section("03_memory_prechorus","Memory / Pre-Chorus",92,8,"E Aeolian / C Lydian color",((52,55,59,64),(48,52,55,59),(55,59,62,66),(50,54,57,64)),"a_stretched","halftime","glass","moving","A is augmented into long, wistful arcs over melodic inversions."),
 Section("04_dead_raiser_response","Dead-Raiser Call-and-Response",112,8,"E minor pentatonic",((40,47,52),(43,50,55),(38,45,50),(47,54,59)),"a_hits","stopstart","brass","stabs","A collapses into hard punctuation figures after deliberate response gaps."),
 Section("05_poppy_hook","Poppy Hook",132,8,"E Aeolian",((52,55,59),(50,54,57),(48,52,55),(47,50,54)),"a_percussive","pop","chip","answer","A becomes rapid alternating lead/bass packets with octave displacement."),
 Section("06_movement_ii_creation","Movement II Creation",110,8,"E Dorian / G major",((40,47,52,54),(43,50,55,57),(45,52,57,59),(47,54,59,62)),"a_reharm","brokenbeat","wide","active","A is reharmonized in Dorian while bass and drums become independently melodic."),
 Section("07_steward_shards","Steward of the Shards",108,8,"B Phrygian dominant over E minor",((47,51,54,59),(48,52,55,60),(45,52,57,60),(46,50,53,58)),"b_debut","shards","crystal","pedal","Motif B enters alone as crystalline shards, then answers a small A fragment."),
 Section("08_animate_payoff","Now I Too Can Animate",118,8,"E Dorian → E major lift",((40,47,52,54),(45,52,57,61),(47,54,59,63),(52,56,59,64)),"ab_unlock","driving","wide","active","B unlocks an ascending A contour; final harmony changes mode to E major."),
 Section("09_reading_open","Spoken Reading Opening",84,8,"E Aeolian suspended",((40,47,52,59),(43,50,55,62),(36,43,48,55),(38,45,50,57)),"shards_sparse","cinematic_sparse","bell","drone","Widely spaced A and B shard tones leave maximum narration space."),
 Section("10_gathering_fragments","Gathering Fragments Build",88,8,"E Aeolian → Dorian",((40,47,52,55),(43,50,55,59),(45,52,57,61),(47,54,59,62)),"ab_assemble","cinematic_build","glass","moving","A and B fragments enter in increasing lengths as harmonic motion accelerates."),
 Section("11_reading_climax","Movement III Climax",100,8,"E Dorian / B altered",((40,47,52,54),(46,53,58,62),(43,50,55,59),(47,54,59,63)),"ab_counterpoint","cinematic_peak","wide","pedal","Complete A and B overlap in contrary registers before a dominant launch."),
 Section("12_final_reprise","Final Combined Reprise",126,12,"E Dorian → Aeolian → E major",((40,47,52,54),(43,50,55,59),(38,45,50,57),(47,54,59,63),(40,47,52,55),(52,56,59,64)),"ab_final","final","chip","active","Chant A, transformed A, Steward B, and cinematic harmony converge contrapuntally."),
)

CHORD_PROGRESSIONS={
 "01_opening_chant":("Em","C","D","Bm"),
 "02_movement_i_rap":("Em5","G/D","C5","D5"),
 "03_memory_prechorus":("Em(add11)","Cmaj7","Gmaj7","D(add9)"),
 "04_dead_raiser_response":("Em5","G5","D5","B5"),
 "05_poppy_hook":("Em","D","C","Bm"),
 "06_movement_ii_creation":("Em(add6)","G6","Am6","Bm(add11)"),
 "07_steward_shards":("B","C","Am","B-flat augmented color"),
 "08_animate_payoff":("Em(add6)","A/C-sharp","B/D-sharp","E"),
 "09_reading_open":("Em(add9)","G(add9)","C(add9)","D(add9)"),
 "10_gathering_fragments":("Em7","Gmaj7","A6","Bm(add11)"),
 "11_reading_climax":("Em(add6)","B-flat altered","Gmaj7","B(add11)"),
 "12_final_reprise":("Em6","Gmaj7","D5","B(add11)","Em7","E"),
}

def hz(p): return 440*2**((p-69)/12)
def envelope(n,a=.006,r=.04):
 e=np.ones(n); ai=min(n//3,int(a*SR)); ri=min(n//2,int(r*SR))
 if ai:e[:ai]=np.linspace(0,1,ai,endpoint=False)
 if ri:e[-ri:]=np.linspace(1,0,ri,endpoint=True)
 return e

def tone(buf,start,dur,pitch,amp,voice):
 i=round(start*SR); n=min(len(buf)-i,round(dur*SR))
 if n<2:return
 t=np.arange(n)/SR; f=hz(pitch); ph=2*np.pi*f*t
 if voice in ("chip","pulse"): x=.72*np.sin(ph)+.18*np.sin(2*ph)+.10*np.sign(np.sin(ph))
 elif voice in ("glass","crystal","bell"): x=.66*np.sin(ph)+.22*np.sin(2.01*ph)+.12*np.sin(3.98*ph)
 elif voice in ("wide","brass"): x=.58*np.sin(ph)+.25*np.sin(2*ph)+.12*np.sin(3*ph)+.05*np.sin(ph*1.006)
 elif voice in ("sub","round","moving","active","pedal","stabs","answer"): x=.82*np.sin(ph)+.18*np.sin(2*ph)
 else:x=np.sin(ph)
 buf[i:i+n]+=amp*x*envelope(n,.003 if voice in ("chip","pulse") else .012,.025 if voice not in ("glass","bell") else .12)

def note(events,beat,pitch,dur,vel=90):
 if pitch>=0:events.append((float(beat),int(pitch),float(dur),int(vel)))

def make_events(s):
 lead=[]; counter=[]; bass=[]; pad=[]; spb=60/s.bpm
 for bar in range(s.bars):
  chord=s.chords[bar%len(s.chords)]; root=chord[0]
  for p in chord: note(pad,bar*4,p,3.72,42)
  if s.bass_voice=="drone": note(bass,bar*4,root-12,3.75,60)
  elif s.bass_voice=="pedal":
   for q in (0,2):note(bass,bar*4+q,40 if bar<6 else 47,.8,67)
  elif s.bass_voice in ("active","moving"):
   walk=(root-12,root-5,root,root-2)
   for q,p in enumerate(walk):note(bass,bar*4+q,p,.68,74)
  else:
   for q in range(4):note(bass,bar*4+q,root-12 if q<3 else root-5,.48,75)

 t=s.treatment
 if t in ("a_chant","a_percussive","a_reharm"):
  step=.25 if t=="a_percussive" else .5
  reps=2 if step==.25 else 1
  for bar in range(s.bars):
   seq=MOTIF_A if t!="a_reharm" else tuple(p+(2 if p in (71,78) else 0) if p>=0 else p for p in MOTIF_A)
   for k,p in enumerate(seq[:int(4/step)]): note(lead,bar*4+k*step,p+(12 if t=="a_percussive" and k%5==0 else 0),step*.72,92)
   if t=="a_percussive":
    for k,p in enumerate(MOTIF_A[8:16]):note(counter,bar*4+.125+k*.5,p-12,.18,68)
 elif t=="a_fragments":
  for bar in range(s.bars):
   for off,idx in ((1.5,(0,2,3)),(3.25,(4,6))):
    for k,j in enumerate(idx):note(lead,bar*4+off+k*.22,MOTIF_A[j],.14,82)
 elif t=="a_stretched":
  pitches=(76,79,78,74,71,74,75,76)
  for bar,p in enumerate(pitches):note(lead,bar*4+.25,p,2.7,76)
 elif t=="a_hits":
  for bar in range(s.bars):
   for off,p in ((1.65,76),(1.9,79),(3.65,74),(3.9,76)):note(lead,bar*4+off,p,.13,100)
 elif t=="b_debut":
  for bar in range(s.bars):
   for k,p in enumerate(MOTIF_B):note(lead,bar*4+k*.5,p+12,.28,86)
   if bar>=4:
    for k,p in enumerate((76,79,78,74)):note(counter,bar*4+2+k*.45,p,.22,65)
 elif t=="ab_unlock":
  for bar in range(s.bars):
   seq=MOTIF_B if bar<4 else tuple(p for p in MOTIF_A[:8] if p>=0)
   for k,p in enumerate(seq):note(lead,bar*4+k*.48,p+(12 if bar>=6 else 0),.30,90)
   if bar>=4:
    for k,p in enumerate(MOTIF_B):note(counter,bar*4+k*.5,p-12,.32,64)
 elif t=="shards_sparse":
  shards=((76,71),(67,70),(79,74),(66,72))
  for bar in range(s.bars):
   for k,p in enumerate(shards[bar%4]):note(lead,bar*4+.5+k*2,p,1.05,58)
 elif t=="ab_assemble":
  for bar in range(s.bars):
   length=2+min(6,bar)
   for k,p in enumerate([p for p in MOTIF_A if p>=0][:length]):note(lead,bar*4+k*(3.5/length),p,.22,70+bar*2)
   for k,p in enumerate(MOTIF_B[:max(2,bar)]):note(counter,bar*4+.25+k*(3.4/max(2,bar)),p+12,.20,58+bar*2)
 elif t in ("ab_counterpoint","ab_final"):
  for bar in range(s.bars):
   for k,p in enumerate(MOTIF_A[:8]):note(lead,bar*4+k*.5,p+(12 if t=="ab_final" and bar>=8 else 0),.28,88)
   for k,p in enumerate(MOTIF_B):note(counter,bar*4+.25+k*.5,p+(0 if bar%2 else 12),.26,70)
 return lead,counter,bass,pad

def drums(buf,s,spb):
 rng=np.random.default_rng(20260831+sum(map(ord,s.slug)))
 for eighth in range(s.bars*8):
  beat=eighth*.5; i=round(beat*spb*SR); n=min(len(buf)-i,int(.09*SR)); t=np.arange(n)/SR
  if n<2:continue
  if s.groove in ("cinematic_sparse",) and eighth%8 not in (0,):continue
  if s.groove=="stopstart" and eighth%8 in (2,3,6):continue
  kick=eighth%8 in ((0,4) if s.groove not in ("hiphop","brokenbeat") else (0,3,6))
  if kick:x=np.sin(2*np.pi*(72*t-22*t*t))*np.exp(-t*34); amp=.28
  else:
   x=rng.standard_normal(n)*np.exp(-t*72); x=sosfilt(butter(2,5200,btype="highpass",fs=SR,output="sos"),x); amp=.055
  buf[i:i+n]+=amp*x*envelope(n,.001,.01)

def midi_write(path,s,tracks):
 mid=mido.MidiFile(type=1,ticks_per_beat=TPB); meta=mido.MidiTrack();mid.tracks.append(meta)
 meta.append(mido.MetaMessage("track_name",name=s.title,time=0));meta.append(mido.MetaMessage("set_tempo",tempo=mido.bpm2tempo(s.bpm),time=0))
 for name,program,events in tracks:
  tr=mido.MidiTrack();mid.tracks.append(tr);tr.append(mido.MetaMessage("track_name",name=name,time=0));tr.append(mido.Message("program_change",program=program,time=0)); msgs=[]
  for b,p,d,v in events:msgs.extend(((round(b*TPB),1,p,v),(round((b+d)*TPB),0,p,0)))
  last=0
  for tick,on,p,v in sorted(msgs,key=lambda x:(x[0],x[1])):tr.append(mido.Message("note_on" if on else "note_off",note=p,velocity=v,time=tick-last));last=tick
 mid.save(path)

def render(s,out):
 d=s.bars*4*60/s.bpm;n=round(d*SR);mix=np.zeros(n);spb=60/s.bpm
 lead,counter,bass,pad=make_events(s)
 for evs,voice,amp in ((pad,"glass",.055),(bass,s.bass_voice,.17),(counter,"crystal",.10),(lead,s.lead_voice,.22)):
  for b,p,dur,v in evs:tone(mix,b*spb,min(dur*spb,d-b*spb),p,amp*v/100,voice)
 drums(mix,s,spb);mix=sosfilt(butter(2,17500,fs=SR,output="sos"),mix);mix*=.86/max(np.max(np.abs(mix)),1e-9)
 folder=out/s.slug;folder.mkdir(parents=True,exist_ok=True);wavp=folder/f"{s.slug}.wav";mp3p=folder/f"{s.slug}.mp3";midp=folder/f"{s.slug}.mid"
 pcm=np.int16(np.clip(mix,-1,1)*32767)
 with wave.open(str(wavp),"wb") as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(SR);w.writeframes(pcm.tobytes())
 midi_write(midp,s,(("Lead",81,lead),("Steward_Counter",98,counter),("Bass",38,bass),("Harmony",89,pad)))
 subprocess.run(["ffmpeg","-hide_banner","-loglevel","error","-y","-i",str(wavp),"-codec:a","libmp3lame","-b:a","192k","-map_metadata","-1",str(mp3p)],check=True)
 meta=asdict(s)|{"duration_seconds":n/SR,"chord_progression":CHORD_PROGRESSIONS[s.slug],"chord_midi":s.chords,"motif_a":MOTIF_A,"motif_b":MOTIF_B,"event_counts":{"lead":len(lead),"counter":len(counter),"bass":len(bass),"harmony":len(pad)},"endpoint_jump":float(abs(mix[0]-mix[-1])),"wav_sha256":hashlib.sha256(wavp.read_bytes()).hexdigest()}
 (folder/"section.json").write_text(json.dumps(meta,indent=2)+"\n");return meta

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--output",type=Path,default=Path(__file__).parent/"output");args=ap.parse_args();args.output.mkdir(parents=True,exist_ok=True)
 report=[render(s,args.output) for s in SECTIONS]
 signatures={s["slug"]:(s["bpm"],s["mode"],s["chords"],s["treatment"],s["groove"]) for s in report}
 assert len(set(signatures.values()))==len(SECTIONS),"sections are not structurally distinct"
 (args.output/"palette_manifest.json").write_text(json.dumps({"motif_a":MOTIF_A,"motif_b":MOTIF_B,"sections":report},indent=2)+"\n")
 print(json.dumps({"rendered":len(report),"output":str(args.output),"durations":{x['slug']:x['duration_seconds'] for x in report}},indent=2))
if __name__=="__main__":main()
