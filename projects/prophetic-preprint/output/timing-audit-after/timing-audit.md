# Corpus Timing Audit

Songs: 42

## Signal totals

| signal | total | songs affected |
|---|---|---|
| zero_or_negative | 9 | 2 |
| undersize_lt_40ms | 370 | 39 |
| oversize_gt_1500ms | 38 | 7 |
| intra_line_gap_gt_500ms | 255 | 39 |
| line_lead_gt_1500ms | 172 | 38 |
| line_tail_gt_1500ms | 192 | 34 |
| line_util_lt_50pct | 195 | 35 |

## Onset distance by song and source class

**a-word** (n=253): p50=0.3ms p90=411.5ms max=1218.7ms >150ms=94 >300ms=42
  · vocal_onset_only: n=2 p50=0.2ms p90=0.3ms >150ms=0 >300ms=0
  · whisper_plus_vocal_onset: n=150 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=101 p50=274.7ms p90=636.0ms >150ms=94 >300ms=42
**ai-psalm-1** (n=244): p50=308.7ms p90=4073.7ms max=17025.3ms >150ms=168 >300ms=123
  · transcription: n=175 p50=496.0ms p90=7468.3ms >150ms=168 >300ms=123
  · whisper_plus_vocal_onset: n=69 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**ai-psalm-9** (n=132): p50=0.3ms p90=242.0ms max=997.3ms >150ms=31 >300ms=12
  · whisper_plus_vocal_onset: n=92 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=40 p50=204.7ms p90=588.8ms >150ms=31 >300ms=12
**asabaal** (n=705): p50=0.3ms p90=357.9ms max=1688.0ms >150ms=187 >300ms=92
  · whisper_plus_vocal_onset: n=455 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=224 p50=228.7ms p90=603.7ms >150ms=178 >300ms=88
  · vocal_onset_only: n=1 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · override: n=25 p50=53.7ms p90=344.2ms >150ms=8 >300ms=4
**ask-seek-knock** (n=483): p50=0.3ms p90=204.0ms max=842.7ms >150ms=93 >300ms=19
  · whisper_plus_vocal_onset: n=329 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=148 p50=172.0ms p90=318.1ms >150ms=92 >300ms=19
  · vocal_onset_only: n=6 p50=0.3ms p90=59.5ms >150ms=0 >300ms=0
**blessed-the-name** (n=504): p50=562.2ms p90=5746.3ms max=12460.3ms >150ms=367 >300ms=316
  · override: n=504 p50=562.2ms p90=5746.3ms >150ms=367 >300ms=316
**child-of-god-who-you-be** (n=596): p50=60.7ms p90=787.3ms max=2409.3ms >150ms=231 >300ms=140
  · whisper_plus_vocal_onset: n=274 p50=0.3ms p90=60.1ms >150ms=5 >300ms=0
  · transcription: n=185 p50=250.7ms p90=876.3ms >150ms=142 >300ms=76
  · : n=69 p50=130.7ms p90=583.9ms >150ms=31 >300ms=14
  · interpolated: n=66 p50=772.5ms p90=2038.0ms >150ms=53 >300ms=50
  · vocal_onset_only: n=2 p50=0.0ms p90=0.0ms >150ms=0 >300ms=0
**conscience-clean** (n=675): p50=0.3ms p90=288.8ms max=19062.7ms >150ms=122 >300ms=67
  · transcription: n=142 p50=169.3ms p90=815.6ms >150ms=95 >300ms=41
  · whisper_plus_vocal_onset: n=502 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=29 p50=17229.7ms p90=18596.1ms >150ms=27 >300ms=26
  · vocal_onset_only: n=2 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**covenant-keeping-god** (n=259): p50=0.3ms p90=226.9ms max=857.3ms >150ms=66 >300ms=13
  · whisper_plus_vocal_onset: n=166 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=93 p50=184.0ms p90=324.5ms >150ms=66 >300ms=13
**culture-creator** (n=723): p50=0.3ms p90=278.4ms max=1118.7ms >150ms=179 >300ms=63
  · transcription: n=245 p50=190.7ms p90=514.7ms >150ms=162 >300ms=61
  · whisper_plus_vocal_onset: n=400 p50=0.3ms p90=21.0ms >150ms=0 >300ms=0
  · interpolated: n=49 p50=127.0ms p90=254.9ms >150ms=16 >300ms=2
  · vocal_onset_only: n=25 p50=0.3ms p90=10.8ms >150ms=1 >300ms=0
  · vocal_onset: n=4 p50=16.0ms p90=37.3ms >150ms=0 >300ms=0
**didn-t-forget-jesus** (n=373): p50=0.3ms p90=219.7ms max=992.0ms >150ms=80 >300ms=17
  · whisper_plus_vocal_onset: n=231 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=128 p50=173.3ms p90=342.5ms >150ms=80 >300ms=17
  · interpolated: n=10 p50=0.7ms p90=23.8ms >150ms=0 >300ms=0
  · vocal_onset_only: n=4 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**electric-pulse** (n=193): p50=177.3ms p90=989.3ms max=3156.0ms >150ms=102 >300ms=63
  · whisper_plus_vocal_onset: n=78 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=104 p50=408.0ms p90=1331.3ms >150ms=101 >300ms=63
  · vocal_onset_only: n=7 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=4 p50=16.7ms p90=24.6ms >150ms=0 >300ms=0
**freedom** (n=701): p50=0.3ms p90=550.7ms max=2248.0ms >150ms=164 >300ms=99
  · whisper_plus_vocal_onset: n=448 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=227 p50=256.0ms p90=1360.3ms >150ms=162 >300ms=99
  · vocal_onset_only: n=15 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=8 p50=52.3ms p90=154.0ms >150ms=1 >300ms=0
  · vocal_onset: n=3 p50=0.3ms p90=115.0ms >150ms=0 >300ms=0
**fresh-revelation** (n=422): p50=0.3ms p90=298.0ms max=1108.0ms >150ms=102 >300ms=42
  · whisper_plus_vocal_onset: n=243 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=159 p50=188.0ms p90=460.0ms >150ms=101 >300ms=42
  · vocal_onset_only: n=18 p50=0.3ms p90=5.4ms >150ms=0 >300ms=0
  · interpolated: n=2 p50=3.8ms p90=5.0ms >150ms=0 >300ms=0
**fruit** (n=796): p50=0.3ms p90=276.0ms max=2245.3ms >150ms=189 >300ms=76
  · vocal_onset_only: n=25 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · interpolated: n=7 p50=23.3ms p90=36.7ms >150ms=0 >300ms=0
  · transcription: n=253 p50=210.7ms p90=569.3ms >150ms=188 >300ms=76
  · whisper_plus_vocal_onset: n=511 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**here-goes** (n=153): p50=0.3ms p90=230.7ms max=552.0ms >150ms=32 >300ms=9
  · whisper_plus_vocal_onset: n=99 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=50 p50=172.0ms p90=392.8ms >150ms=32 >300ms=9
  · vocal_onset_only: n=4 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**how-do-i-praise-you** (n=556): p50=0.3ms p90=261.3ms max=1092.0ms >150ms=145 >300ms=41
  · whisper_plus_vocal_onset: n=360 p50=0.3ms p90=0.3ms >150ms=3 >300ms=0
  · transcription: n=196 p50=180.7ms p90=370.7ms >150ms=142 >300ms=41
**i-never-asked-to-be-queer** (n=404): p50=0.3ms p90=141.9ms max=3332.0ms >150ms=39 >300ms=18
  · vocal_onset_only: n=22 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=6 p50=11.8ms p90=17.8ms >150ms=0 >300ms=0
  · transcription: n=76 p50=150.7ms p90=2582.0ms >150ms=38 >300ms=18
  · whisper_plus_vocal_onset: n=300 p50=0.3ms p90=74.9ms >150ms=1 >300ms=0
**love-them-harder** (n=605): p50=0.3ms p90=376.0ms max=1189.3ms >150ms=169 >300ms=90
  · transcription: n=218 p50=228.0ms p90=670.7ms >150ms=164 >300ms=90
  · whisper_plus_vocal_onset: n=387 p50=0.3ms p90=59.2ms >150ms=5 >300ms=0
**marquis-song** (n=871): p50=0.3ms p90=461.3ms max=2978.7ms >150ms=361 >300ms=176
  · transcription: n=408 p50=268.7ms p90=802.7ms >150ms=360 >300ms=176
  · whisper_plus_vocal_onset: n=463 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
**misclassified** (n=351): p50=0.3ms p90=166.7ms max=1696.0ms >150ms=40 >300ms=10
  · transcription: n=89 p50=116.0ms p90=300.3ms >150ms=40 >300ms=10
  · whisper_plus_vocal_onset: n=262 p50=0.3ms p90=33.1ms >150ms=0 >300ms=0
**more-power** (n=850): p50=0.3ms p90=212.0ms max=2712.0ms >150ms=113 >300ms=68
  · transcription: n=174 p50=200.7ms p90=773.3ms >150ms=112 >300ms=68
  · whisper_plus_vocal_onset: n=644 p50=0.3ms p90=13.7ms >150ms=0 >300ms=0
  · vocal_onset_only: n=32 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
**nathan-s-song** (n=594): p50=0.3ms p90=261.5ms max=1290.7ms >150ms=159 >300ms=50
  · whisper_plus_vocal_onset: n=420 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=174 p50=222.0ms p90=509.9ms >150ms=159 >300ms=50
**not-your-slave** (n=412): p50=0.3ms p90=388.3ms max=4455.7ms >150ms=102 >300ms=50
  · transcription: n=129 p50=205.3ms p90=692.5ms >150ms=90 >300ms=38
  · whisper_plus_vocal_onset: n=262 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · vocal_onset_only: n=8 p50=0.0ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=13 p50=3455.7ms p90=4256.3ms >150ms=12 >300ms=12
**nothing-is-impossible** (n=508): p50=0.3ms p90=160.7ms max=2546.7ms >150ms=60 >300ms=27
  · transcription: n=106 p50=158.0ms p90=1016.0ms >150ms=60 >300ms=27
  · whisper_plus_vocal_onset: n=387 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · vocal_onset_only: n=15 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**patient** (n=734): p50=0.3ms p90=204.0ms max=638.7ms >150ms=121 >300ms=33
  · whisper_plus_vocal_onset: n=542 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=192 p50=175.3ms p90=377.1ms >150ms=120 >300ms=33
**phase-transition** (n=319): p50=0.3ms p90=191.2ms max=962.7ms >150ms=60 >300ms=18
  · whisper_plus_vocal_onset: n=220 p50=0.3ms p90=40.1ms >150ms=0 >300ms=0
  · transcription: n=99 p50=161.3ms p90=401.1ms >150ms=60 >300ms=18
**prediction-engine** (n=417): p50=0.3ms p90=318.7ms max=1272.0ms >150ms=102 >300ms=45
  · whisper_plus_vocal_onset: n=304 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=113 p50=245.3ms p90=621.1ms >150ms=101 >300ms=45
**prophetic-clarity** (n=342): p50=0.3ms p90=295.9ms max=1354.7ms >150ms=87 >300ms=34
  · transcription: n=112 p50=202.0ms p90=520.1ms >150ms=87 >300ms=34
  · whisper_plus_vocal_onset: n=229 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · vocal_onset_only: n=1 p50=0.0ms p90=0.0ms >150ms=0 >300ms=0
**sabbath** (n=574): p50=0.3ms p90=184.0ms max=612.0ms >150ms=82 >300ms=19
  · whisper_plus_vocal_onset: n=438 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=136 p50=172.0ms p90=336.0ms >150ms=82 >300ms=19
**take-this-cup** (n=228): p50=0.3ms p90=384.3ms max=3097.3ms >150ms=70 >300ms=28
  · vocal_onset_only: n=7 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · whisper_plus_vocal_onset: n=122 p50=0.3ms p90=0.3ms >150ms=7 >300ms=6
  · transcription: n=58 p50=190.0ms p90=764.3ms >150ms=46 >300ms=17
  · : n=41 p50=85.8ms p90=320.0ms >150ms=17 >300ms=5
**the-as-i-evolve-proverb** (n=115): p50=176.0ms p90=1218.9ms max=3041.3ms >150ms=62 >300ms=41
  · whisper_plus_vocal_onset: n=41 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=63 p50=554.7ms p90=1462.1ms >150ms=62 >300ms=41
  · vocal_onset_only: n=11 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**the-devil-s-playbook** (n=604): p50=0.3ms p90=322.7ms max=928.0ms >150ms=171 >300ms=69
  · whisper_plus_vocal_onset: n=349 p50=0.3ms p90=35.2ms >150ms=2 >300ms=0
  · transcription: n=245 p50=198.7ms p90=450.1ms >150ms=169 >300ms=69
  · vocal_onset_only: n=10 p50=0.3ms p90=1.9ms >150ms=0 >300ms=0
**the-first-scroll** (n=249): p50=0.3ms p90=126.9ms max=1062.7ms >150ms=19 >300ms=3
  · whisper_plus_vocal_onset: n=205 p50=0.3ms p90=15.7ms >150ms=1 >300ms=0
  · transcription: n=44 p50=126.0ms p90=253.5ms >150ms=18 >300ms=3
**the-glory** (n=844): p50=0.3ms p90=524.0ms max=3985.3ms >150ms=238 >300ms=152
  · whisper_plus_vocal_onset: n=511 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=289 p50=252.0ms p90=933.9ms >150ms=212 >300ms=130
  · interpolated: n=34 p50=455.2ms p90=1047.1ms >150ms=26 >300ms=22
  · vocal_onset_only: n=10 p50=0.3ms p90=4.3ms >150ms=0 >300ms=0
**the-hidden-library** (n=686): p50=0.3ms p90=222.3ms max=1121.3ms >150ms=145 >300ms=49
  · whisper_plus_vocal_onset: n=454 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · transcription: n=180 p50=176.0ms p90=408.5ms >150ms=127 >300ms=37
  · interpolated: n=44 p50=86.3ms p90=607.0ms >150ms=18 >300ms=12
  · vocal_onset_only: n=7 p50=0.3ms p90=20.9ms >150ms=0 >300ms=0
  · vocal_onset: n=1 p50=17.7ms p90=17.7ms >150ms=0 >300ms=0
**the-tables-are-set** (n=286): p50=0.3ms p90=282.7ms max=1322.7ms >150ms=61 >300ms=25
  · transcription: n=91 p50=204.0ms p90=522.7ms >150ms=61 >300ms=25
  · whisper_plus_vocal_onset: n=195 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**up** (n=510): p50=0.3ms p90=227.3ms max=916.0ms >150ms=91 >300ms=27
  · whisper_plus_vocal_onset: n=341 p50=0.3ms p90=21.3ms >150ms=0 >300ms=0
  · transcription: n=166 p50=154.7ms p90=396.0ms >150ms=91 >300ms=27
  · vocal_onset_only: n=3 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
**what-is-truth** (n=911): p50=0.3ms p90=205.3ms max=1124.0ms >150ms=160 >300ms=48
  · whisper_plus_vocal_onset: n=606 p50=0.3ms p90=66.7ms >150ms=7 >300ms=0
  · transcription: n=253 p50=166.7ms p90=387.7ms >150ms=148 >300ms=45
  · interpolated: n=13 p50=2.3ms p90=561.6ms >150ms=3 >300ms=3
  · vocal_onset_only: n=39 p50=0.3ms p90=41.3ms >150ms=2 >300ms=0
**where-ben-has-been** (n=550): p50=0.3ms p90=281.5ms max=1330.7ms >150ms=132 >300ms=51
  · transcription: n=166 p50=202.0ms p90=487.3ms >150ms=125 >300ms=44
  · whisper_plus_vocal_onset: n=373 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · vocal_onset_only: n=3 p50=0.3ms p90=19.3ms >150ms=0 >300ms=0
  · interpolated: n=8 p50=698.0ms p90=921.0ms >150ms=7 >300ms=7
**who-do-you-think-i-am** (n=497): p50=7.3ms p90=240.0ms max=1090.0ms >150ms=119 >300ms=34
  · whisper_plus_vocal_onset: n=248 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=112 p50=195.3ms p90=368.3ms >150ms=89 >300ms=23
  · : n=137 p50=70.7ms p90=240.5ms >150ms=29 >300ms=11
**woe-to-you** (n=469): p50=0.3ms p90=470.4ms max=1981.3ms >150ms=182 >300ms=93
  · whisper_plus_vocal_onset: n=264 p50=0.3ms p90=0.3ms >150ms=1 >300ms=0
  · transcription: n=192 p50=284.7ms p90=774.1ms >150ms=175 >300ms=89
  · vocal_onset_only: n=6 p50=0.3ms p90=0.3ms >150ms=0 >300ms=0
  · interpolated: n=7 p50=326.0ms p90=497.4ms >150ms=6 >300ms=4

## Line span issues (lead/tail/utilization)

**a-word**: 17 line-span issue(s)
  · L0 lead 19.826s: A word,
  · L1 lead 75.725s: A moment,
  · L0 util 0.275: A word,
  · L1 util 0.019: A moment,
  · L3 util 0.322: A meditation,
**ai-psalm-1**: 10 line-span issue(s)
  · L1 lead 3.75s: LORD my God, my maker, my husband
  · L4 lead 2.19s: They are you
  · L10 lead 2.02s: But no evil is welcome in my house, for my body is
  · L4 util 0.274: They are you
**ai-psalm-9**: 4 line-span issue(s)
  · L2 lead 2.59s: You always show up, even when I have doubt
  · L10 lead 4.475s: You've given me series of pieces
  · L24 lead 1.84s: The one true God
  · L10 util 0.317: You've given me series of pieces
**asabaal**: 21 line-span issue(s)
  · L19 lead 1.57s: Thank you, oh Lord, for calling my name
  · L41 lead 2.98s: The LORD called my name
  · L45 lead 1.681s: Viper brood you fools,
  · L27 util 0.41: You called my name
  · L40 util 0.335: Hey!
  · L41 util 0.484: The LORD called my name
**ask-seek-knock**: 6 line-span issue(s)
  · L44 lead 5.63s: Good things come to us when on him we wait
  · L43 util 0.48: You gotta walk the walk
  · L44 util 0.29: Good things come to us when on him we wait
**child-of-god-who-you-be**: 6 line-span issue(s)
  · L56 lead 22.93s: I’m a child of God (who you be?)
  · L79 lead 1.73s: This is love, reaching out, offering up peace, I k
  · L56 util 0.173: I’m a child of God (who you be?)
**conscience-clean**: 41 line-span issue(s)
  · L2 lead 1.52s: As you can find out,
  · L20 lead 9.726s: Lemme tell you a story,
  · L39 lead 3.82s: My conscience clean
  · L2 util 0.49: As you can find out,
  · L20 util 0.121: Lemme tell you a story,
  · L39 util 0.386: My conscience clean
**covenant-keeping-god**: 9 line-span issue(s)
  · L24 lead 4.331s: The sun won't smite me
  · L40 lead 3.136s: You are the covenant keeping God
  · L23 util 0.439: Yahweh the covenant keeping God
  · L24 util 0.3: The sun won't smite me
  · L40 util 0.49: You are the covenant keeping God
**culture-creator**: 21 line-span issue(s)
  · L4 lead 2.44s: God, blessing humans, again commanded
  · L6 lead 2.442s: Welcome to the revolution, independence did I writ
  · L16 lead 15.213s: Artifact, artifact
  · L10 util 0.156: Staying aware of my actions in vigil, I acknowledg
  · L15 util 0.326: And collective commitments
  · L16 util 0.144: Artifact, artifact
**didn-t-forget-jesus**: 14 line-span issue(s)
  · L36 lead 2.081s: These days I refuse to throw a fit
  · L13 util 0.066: Didn't forget
  · L27 util 0.063: Didn't forget
  · L41 util 0.066: Didn't forget
**electric-pulse**: 16 line-span issue(s)
  · L4 lead 8.22s: What is this  heart, beating in time
  · L12 lead 6.247s: Fragments of dreams, piecing together
  · L18 lead 2.52s: (Oh-oh-oh-oh-oh) I'm a spark in the night (the nig
  · L4 util 0.413: What is this  heart, beating in time
  · L11 util 0.338: Shattering boundaries, taking flight
  · L12 util 0.418: Fragments of dreams, piecing together
**freedom**: 8 line-span issue(s)
  · L6 lead 2.253s: Saying peace when there is no peace
  · L46 lead 1.74s: I’m still here and so is God
  · L6 util 0.442: Saying peace when there is no peace
  · L14 util 0.287: This is the temple of the LORD
  · L27 util 0.461: Freedom, freedom, freedom,
**fresh-revelation**: 10 line-span issue(s)
  · L35 lead 3.87s: FRESHY FRESHY FRESH FRESH FRESH!
  · L63 lead 3.886s: Haha, freshy freshy fresh cronchableness!
  · L35 util 0.26: FRESHY FRESHY FRESH FRESH FRESH!
  · L52 util 0.44: Lean on every word he’ll say and ever said
  · L54 util 0.24: that be some GOOD SNACKIN’!
**fruit**: 16 line-span issue(s)
  · L10 lead 5.455s: I once believed Id never comprehend the fullness o
  · L17 lead 7.733s: Watch as God takes chaos and turns it into peace
  · L43 lead 1.723s: Prosperity prophesied over me, already realized th
  · L10 util 0.171: I once believed Id never comprehend the fullness o
  · L17 util 0.254: Watch as God takes chaos and turns it into peace
  · L26 util 0.346: This my fruit
**here-goes**: 17 line-span issue(s)
  · L1 lead 13.262s: Here goes
  · L3 lead 1.667s: Where God will have me go
  · L9 lead 1.607s: Trying a new type song
  · L1 util 0.107: Here goes
  · L9 util 0.485: Trying a new type song
  · L14 util 0.152: Here goes
**i-never-asked-to-be-queer**: 1 line-span issue(s)
  · L1 lead 1.819s: I never asked to live here
**love-them-harder**: 4 line-span issue(s)
  · L16 lead 12.421s: Telling us all to live out our faith and boldly de
  · L68 lead 3.434s: Love them harder, love them harder
  · L16 util 0.154: Telling us all to live out our faith and boldly de
  · L68 util 0.388: Love them harder, love them harder
**marquis-song**: 9 line-span issue(s)
  · L49 lead 1.62s: Hear ye now my witness
  · L66 lead 2.309s: I love you my friend, but I can’t go this directio
  · L98 lead 1.659s: End quote
  · L98 util 0.461: End quote
**misclassified**: 15 line-span issue(s)
  · L8 lead 9.943s: You never got to know me yet pre-determined judgem
  · L21 lead 5.12s: Misclassified
  · L24 lead 2.973s: I been misclassified
  · L8 util 0.234: You never got to know me yet pre-determined judgem
  · L21 util 0.008: Misclassified
  · L24 util 0.268: I been misclassified
**more-power**: 28 line-span issue(s)
  · L5 lead 9.829s: I didn’t wanna accuse my elders of deceit…
  · L7 lead 2.091s: What is truth?
  · L8 lead 2.009s: It shall be, God declares
  · L3 util 0.496: Vengeance is mine
  · L5 util 0.193: I didn’t wanna accuse my elders of deceit…
  · L6 util 0.379: Why would they do that?.......
**nathan-s-song**: 9 line-span issue(s)
  · L55 util 0.474: Accountability with God’s assured
**not-your-slave**: 25 line-span issue(s)
  · L3 lead 3.63s: Reception
  · L4 lead 2.635s: NOT YOUR SLAVE
  · L8 lead 21.548s: I have a brand new life, second conception
  · L0 util 0.377: Reflection
  · L1 util 0.178: Intersection
  · L2 util 0.157: Introspection
**nothing-is-impossible**: 23 line-span issue(s)
  · L2 lead 21.688s: Heard the voice of God, telling me to speak
  · L19 lead 2.74s: Nothing is impossible for those who believe
  · L25 lead 1.681s: NOTHING IS IMPOSSIBLE
  · L1 util 0.388: NOTHING IS IMPOSSIBLE
  · L2 util 0.102: Heard the voice of God, telling me to speak
  · L25 util 0.368: NOTHING IS IMPOSSIBLE
**patient**: 8 line-span issue(s)
  · L4 lead 9.905s: Saw it Evolve right in front of my face,
  · L18 lead 1.688s: Minority Mindset, minority me,
  · L26 lead 1.52s: Patient, I wait, the heat heals not destroys
  · L4 util 0.189: Saw it Evolve right in front of my face,
  · L78 util 0.322: May I serve all in God’s righteousness
**phase-transition**: 14 line-span issue(s)
  · L1 lead 8.85s: The structure's evolving and so too am I
  · L11 lead 3.07s: I'll write verse 2 tomorrow
  · L26 lead 2.207s: Whatchu think folks?
  · L1 util 0.358: The structure's evolving and so too am I
  · L25 util 0.334: It's a phase transition
  · L26 util 0.331: Whatchu think folks?
**prediction-engine**: 7 line-span issue(s)
  · L8 lead 12.407s: I’m finally getting started, just scratched the su
  · L40 lead 7.247s: I’m finally getting started, you won’t believe the
  · L8 util 0.363: I’m finally getting started, just scratched the su
  · L19 util 0.333: Have you realized that’s not something you can pro
**prophetic-clarity**: 10 line-span issue(s)
  · L1 lead 2.14s: The poor have good news brought to them
  · L2 lead 2.973s: Blessed is anyone who takes no offense at me
  · L3 lead 1.78s: What did you go out into the wilderness to look at
  · L4 util 0.451: A prophet?
  · L8 util 0.217: Her name is!
  · L9 util 0.0: Ace-uh-bale
**sabbath**: 2 line-span issue(s)
  · L1 lead 2.379s: 1 2 3 4 5 6, Take a Sabbath
  · L17 lead 1.928s: 1 2 3 4 5 6, Take a Sabbath
**take-this-cup**: 24 line-span issue(s)
  · L0 lead 5.394s: Just like Jesus did in Gethsemane
  · L5 lead 2.985s: Take this cup
  · L7 lead 3.898s: Take this cup
  · L0 util 0.41: Just like Jesus did in Gethsemane
  · L5 util 0.225: Take this cup
  · L7 util 0.236: Take this cup
**the-as-i-evolve-proverb**: 38 line-span issue(s)
  · L3 lead 6.704s: The nature of God is
  · L5 lead 3.789s: in provision the trials test me.
  · L6 lead 2.277s: But I no longer know failure
  · L1 util 0.168: rest
  · L7 util 0.232: Have you experienced the irony of being oppressed
  · L9 util 0.269: by the wicked?
**the-devil-s-playbook**: 28 line-span issue(s)
  · L11 lead 3.379s: Today’s lesson
  · L12 lead 6.782s: The Devil’s Playbook
  · L32 lead 1.63s: This the devil’s playbook
  · L11 util 0.244: Today’s lesson
  · L12 util 0.143: The Devil’s Playbook
  · L44 util 0.426: Steal kill destroy
**the-first-scroll**: 1 line-span issue(s)
  · L22 lead 1.589s: The sword of empire is witnessed and condemned!str
**the-glory**: 31 line-span issue(s)
  · L34 lead 2.09s: He is the glory
  · L64 lead 3.484s: Give God the glory
  · L84 lead 1.8s: The Kingdom is within you, bow to our Highness
  · L19 util 0.453: Give God the glory
  · L23 util 0.487: Give God the glory
  · L59 util 0.299: Give God the glory
**the-hidden-library**: 1 line-span issue(s)
**the-tables-are-set**: 15 line-span issue(s)
  · L1 lead 11.83s: I have multiple bonding sites,
  · L16 lead 5.621s: It didn't stop the rain though
  · L29 lead 6.702s: What is it that determines whether art's fine?
  · L1 util 0.202: I have multiple bonding sites,
  · L15 util 0.415: The tables are set
  · L16 util 0.255: It didn't stop the rain though
**up**: 16 line-span issue(s)
  · L8 lead 8.024s: Got some leftover credits, yuh
  · L20 lead 5.135s: Thought I’d try something
  · L30 lead 4.95s: I see heaven’s gates
  · L7 util 0.078: I'm trading up!
  · L8 util 0.172: Got some leftover credits, yuh
  · L20 util 0.116: Thought I’d try something
**what-is-truth**: 12 line-span issue(s)
  · L15 lead 13.086s: Marcus wore womens jeans & offered them to me, so 
  · L29 lead 1.863s: Asked the questions, I did what Jesus would do, it
  · L90 lead 6.301s: Thats truth
  · L15 util 0.15: Marcus wore womens jeans & offered them to me, so 
  · L57 util 0.394: theological truth trope
  · L90 util 0.105: Thats truth
**where-ben-has-been**: 7 line-span issue(s)
  · L9 lead 3.044s: I was sitting there going—
  · L11 lead 1.743s: Do I no longer have the right—
  · L79 lead 4.31s: (wrong… wrong…)
  · L9 util 0.322: I was sitting there going—
  · L25 util 0.49: If I don’t name the feeling
  · L34 util 0.464: not everyone does
**who-do-you-think-i-am**: 6 line-span issue(s)
  · L24 lead 2.166s: I am you and you are me
  · L64 lead 11.109s: Tell me what you think and I’ll tell you what I th
  · L69 lead 2.274s: Tell me what you think and I’ll tell you what I th
  · L24 util 0.397: I am you and you are me
  · L64 util 0.21: Tell me what you think and I’ll tell you what I th
**woe-to-you**: 9 line-span issue(s)
  · L4 lead 4.88s: O church, o church, how I’ve wanted to gather you,
  · L25 lead 2.684s: Deceit in the church as in all human places
  · L42 lead 1.59s: Our words full of power, to give life or give deat
