# You and I — clean lyric transcription (machine first pass)

Source: phone video IMG_8244.MOV (mono AAC 44.1 kHz, 3:20) — see data/audio/source-provenance.json.
Model: faster-whisper large-v3 (int8, CPU). Three configs run; B (beam 1, no VAD) is the base text,
reconciled against C (beam 5, no VAD). Config A (VAD on) returned zero segments — VAD filters sung
vocals over accompaniment. **Machine first pass; every ⚠ line needs human verification against the audio.**

⚠ = configs disagree or low segment confidence — per-line detail (and which specific words are
low-probability) in reports/transcription-uncertainty.md. [instrumental] = gap with no transcribed vocals.

⚠ Every day filled with memories When it ain't the same as true loving
If you ever think that you are not enough
Remember that for me you are the one


There's something to be grateful for
I can't believe that I'm just yours
There's people wishing me their whole lives
There's something like you and I
Once again the early days
⚠ It wasn't just a party, it was a day
⚠ I loved my people, I
⚠ Brought our faces in the night
⚠ Oh, oh, oh


⚠ In the years from our own embrace
⚠ There's one thing I hope to say
I never imagined that I'd have such love like this before
Every day I feel it growing even more
There's something to be grateful for
I can't believe that I'm just yours
⚠ You've been always there for my life
There's something like you and I
I won't forget the world today
⚠ It wasn't just a tiny new day
⚠ I got a mind in my forewarned
⚠ All I needed was a light in my mind


⚠ In my mind
[instrumental]

⚠ I'll call the lights


⚠ When it's night
[instrumental]

It's something to be grateful for
Can't believe that I'm just yours
There's people wishing their whole lives
Something like you and I
I won't forget the early days
It wasn't just a highly new phase
I love you my little brown
[outro instrumental]

⚠ Thank you.
