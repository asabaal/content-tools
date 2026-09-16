# You and I — transcription uncertainty report

Base text: config B (faster-whisper large-v3 int8 CPU, beam 1, VAD off, condition_on_previous_text off).
Reconciliation: config C (beam 5, VAD off) aligned by time overlap. Config A (VAD on) → zero
segments (VAD filters singing over accompaniment — do not use VAD for sung vocals).

## Lines needing human verification (⚠ in lyrics-clean.md)

- **[13.94–24.30]** (logprob -0.64, B/C similarity 0.60)
  - B: `Every day filled with memories When it ain't the same as true loving`
  - C: `Every day's filled with memories`
  - low-probability words: Every, filled, When, the, same, as
- **[51.62–54.46]** (logprob -0.63, B/C similarity 0.72)
  - B: `It wasn't just a party, it was a day`
  - C: `It wasn't just a Friday good day`
  - low-probability words: It, party,, it
- **[54.46–56.98]** (logprob -0.63, B/C similarity 0.54)
  - B: `I loved my people, I`
  - C: `I love you my beautiful bride`
  - low-probability words: I, I
- **[57.56–60.48]** (logprob -0.63, B/C similarity 0.48)
  - B: `Brought our faces in the night`
  - C: `But I'm racing in my own`
  - low-probability words: Brought, faces, in, the
- **[61.02–65.38]** (logprob -0.63, B/C similarity 0.12)
  - B: `Oh, oh, oh`
  - C: `But I'm racing in my own`
  - low-probability words: Oh,
- **[70.74–75.08]** (logprob -0.63, B/C similarity 1.00)
  - B: `In the years from our own embrace`
  - C: `In the years from our own embrace`
  - low-probability words: from, embrace
- **[76.76–80.90]** (logprob -0.63, B/C similarity 1.00)
  - B: `There's one thing I hope to say`
  - C: `There's one thing I hope to say`
- **[99.82–102.88]** (logprob -0.37, B/C similarity 0.47)
  - B: `You've been always there for my life`
  - C: `You've been pushing it all night`
  - low-probability words: You've, been, always, my
- **[107.64–110.44]** (logprob -0.84, B/C similarity 1.00)
  - B: `It wasn't just a tiny new day`
  - C: `It wasn't just a tiny new day`
  - low-probability words: It, tiny
- **[110.44–113.64]** (logprob -0.84, B/C similarity 0.48)
  - B: `I got a mind in my forewarned`
  - C: `I thought it might be time for a ride`
  - low-probability words: I, a, mind, in, forewarned
- **[113.64–119.46]** (logprob -0.84, B/C similarity 0.16)
  - B: `All I needed was a light in my mind`
  - C: `Oh, my Jesus, I can't hide, I can't hide, I can't hide, I can't hide.`
  - low-probability words: All, needed, light, in, mind
- **[126.26–130.40]** (logprob -0.84, B/C similarity 0.19)
  - B: `In my mind`
  - C: `Oh, my Jesus, I can't hide, I can't hide, I can't hide, I can't hide.`
- **[137.64–144.64]** (logprob -0.46, B/C similarity 0.26)
  - B: `I'll call the lights`
  - C: `Oh, my Jesus, I can't hide, I can't hide, I can't hide, I can't hide.`
  - low-probability words: I'll, call, the, lights
- **[148.64–150.52]** (logprob -0.46, B/C similarity 0.00)
  - B: `When it's night`
  - C: ``
  - low-probability words: When, it's, night
- **[198.04–199.06]** (logprob -0.55, B/C similarity 0.00)
  - B: `Thank you.`
  - C: ``
  - low-probability words: Thank

## Agreed-by-both-configs lines (acoustically supported)

- [24.30] If you ever think that you are not enough
- [30.66] Remember that for me you are the one
- [38.02] There's something to be grateful for
- [40.62] I can't believe that I'm just yours
- [43.52] There's people wishing me their whole lives
- [46.40] There's something like you and I
- [49.38] Once again the early days
- [70.74] In the years from our own embrace
- [76.76] There's one thing I hope to say
- [86.38] Every day I feel it growing even more
- [94.28] There's something to be grateful for
- [97.00] I can't believe that I'm just yours
- [102.88] There's something like you and I
- [105.58] I won't forget the world today
- [107.64] It wasn't just a tiny new day
- [161.64] It's something to be grateful for
- [164.64] Can't believe that I'm just yours
- [166.74] There's people wishing their whole lives
- [169.62] Something like you and I
- [172.48] I won't forget the early days

## Notes
- C exhibited a repetition loop ("oh my jesus i can't hide…") across 113–148 s — classic Whisper
  music failure; B's sparse readings for those spans are retained but marked ⚠.
- "Thank you." at 198.04 s appears to be spoken (end of recording), kept for completeness.
- No lyrics 0–13.9 s (instrumental intro) or 180–198 s (outro).

## Per-line low-probability words (machine record)

See data/transcripts/low-probability-words.json for the word-level probability
record behind each ⚠ line. Note: sung vocals systematically score lower than
speech in Whisper word confidences — a marked word means "listen here", not
"definitely wrong."
