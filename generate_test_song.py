"""Generate test_song.mid — a 32-second multi-track demo that exercises
every visual treatment in synesthesia_visualizer_v2.html.

Tracks (channels are 0-indexed in mido):
  1. Drums  (ch 9  / GM ch 10) — kick, snare, hi-hat
  2. Bass   (ch 0  / GM ch 1)
  3. Melody (ch 1  / GM ch 2)
  4. Pads   (ch 2  / GM ch 3)
  5. Lead   (ch 3  / GM ch 4)

Run:  python generate_test_song.py
"""
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage, bpm2tempo

TPB = 480                      # ticks per beat
BPM = 100
QN = TPB                       # quarter note
HN = QN * 2                    # half note
EN = QN // 2                   # eighth
SN = QN // 4                   # sixteenth
WN = QN * 4                    # whole

mid = MidiFile(type=1, ticks_per_beat=TPB)

# ---- conductor / tempo track --------------------------------------------
conductor = MidiTrack()
conductor.append(MetaMessage('set_tempo', tempo=bpm2tempo(BPM), time=0))
conductor.append(MetaMessage('time_signature', numerator=4, denominator=4, time=0))
mid.tracks.append(conductor)


def add_notes(track, notes, channel):
    """notes is a list of (start_tick, duration_tick, pitch, velocity)
    written in absolute ticks; we convert to delta-time."""
    notes = sorted(notes, key=lambda n: n[0])
    events = []
    for (start, dur, pitch, vel) in notes:
        events.append((start,        'on',  pitch, vel))
        events.append((start + dur,  'off', pitch, 0))
    events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))
    last = 0
    for (t, kind, pitch, vel) in events:
        delta = t - last
        last = t
        if kind == 'on':
            track.append(Message('note_on',  note=pitch, velocity=vel, time=delta, channel=channel))
        else:
            track.append(Message('note_off', note=pitch, velocity=0,   time=delta, channel=channel))


# ============================================================================
# 1. DRUMS — channel 9 (= MIDI ch 10, GM percussion)
# ============================================================================
drums = MidiTrack()
drums.append(MetaMessage('track_name', name='Drums', time=0))
drums.append(Message('program_change', program=0, channel=9, time=0))

KICK, SNARE, CHAT, OHAT = 36, 38, 42, 46
drum_notes = []
# bars 1-2 quiet (just pads)
# bars 3-16 (14 bars) — drum pattern
for bar in range(2, 16):
    base = bar * WN
    # kick on 1 and 3 (each beat = QN)
    drum_notes.append((base + 0*QN, EN, KICK, 110))
    drum_notes.append((base + 2*QN, EN, KICK, 105))
    # extra ghost kick pickup in some bars
    if bar % 4 == 3:
        drum_notes.append((base + 3*QN + EN, EN, KICK,  85))
    # snare on 2 and 4
    drum_notes.append((base + 1*QN, EN, SNARE, 100))
    drum_notes.append((base + 3*QN, EN, SNARE, 100))
    # hat 8th notes through the bar
    for i in range(8):
        v = 70 if i % 2 == 0 else 55
        # open hat at end of every 4th bar
        if bar % 4 == 1 and i == 7:
            drum_notes.append((base + i*EN, EN, OHAT, 95))
        else:
            drum_notes.append((base + i*EN, SN, CHAT, v))
    # crash-like (open hat on beat 1) at bar 7 and 11
    if bar in (6, 10):
        drum_notes.append((base, QN, OHAT, 115))

add_notes(drums, drum_notes, channel=9)
drums.append(MetaMessage('end_of_track', time=0))
mid.tracks.append(drums)


# ============================================================================
# 2. BASS — channel 0
# ============================================================================
bass = MidiTrack()
bass.append(MetaMessage('track_name', name='Bass', time=0))
bass.append(Message('program_change', program=33, channel=0, time=0))  # finger bass

# chord progression (root notes for bass): Cm  Ab  Eb  Bb  — repeated
# MIDI: C2=36, Ab1=32, Eb2=39, Bb1=34
roots = [36, 32, 39, 34]
bass_notes = []
# bass enters at bar 2
for bar in range(2, 16):
    base = bar * WN
    root = roots[(bar - 2) % 4]
    # walking pattern: root, octave-up, fifth, root
    pattern = [(0,    QN + EN, root,      95),
               (QN + EN, EN,   root + 7,  80),
               (2*QN, QN,      root + 12, 90),
               (3*QN, QN,      root + 7,  85)]
    for (off, dur, p, v) in pattern:
        bass_notes.append((base + off, dur, p, v))

add_notes(bass, bass_notes, channel=0)
bass.append(MetaMessage('end_of_track', time=0))
mid.tracks.append(bass)


# ============================================================================
# 3. MELODY — channel 1
# ============================================================================
melody = MidiTrack()
melody.append(MetaMessage('track_name', name='Melody', time=0))
melody.append(Message('program_change', program=4, channel=1, time=0))  # electric piano

# A simple lyrical melody in C minor that arcs up over each 4-bar phrase
# pitches: C4=60, D4=62, Eb4=63, F4=65, G4=67, Ab4=68, Bb4=70, C5=72
melody_notes = []
phrase_a = [
    (0,        EN+SN, 67, 95),    # G
    (EN+SN,    SN,   70, 80),    # Bb
    (QN,       EN,   72, 100),   # C5
    (QN+EN,    EN,   70, 90),    # Bb
    (2*QN,     QN,   68, 95),    # Ab
    (3*QN,     QN+EN,67, 90),    # G
]
phrase_b = [
    (0,        EN,   65, 90),
    (EN,       EN,   67, 95),
    (QN,       EN+SN,68, 100),
    (QN+EN+SN, SN,   70, 88),
    (2*QN,     QN,   72, 105),
    (3*QN,     QN,   75, 110),
]
phrase_c = [
    (0,        QN,   72, 95),
    (QN,       EN,   70, 90),
    (QN+EN,    EN,   68, 90),
    (2*QN,     QN+EN,67, 95),
    (3*QN+EN,  EN,   68, 90),
]
phrase_d = [
    (0,        HN,   63, 90),    # Eb sustained
    (2*QN,     HN,   65, 95),    # F sustained
]
# melody enters at bar 4 (index 3): phrases A,B,C,D over 4 bars each pair
phrases = [phrase_a, phrase_b, phrase_a, phrase_c]
for i, phrase in enumerate(phrases):
    bar = 4 + i * 2
    if bar >= 16: break
    # each phrase spans 2 bars
    base = bar * WN
    for (off, dur, p, v) in phrase:
        melody_notes.append((base + off, dur, p, v))
# closing held note
melody_notes.append((14 * WN, WN, 72, 80))

add_notes(melody, melody_notes, channel=1)
melody.append(MetaMessage('end_of_track', time=0))
mid.tracks.append(melody)


# ============================================================================
# 4. PADS — channel 2 (long sustained chords)
# ============================================================================
pads = MidiTrack()
pads.append(MetaMessage('track_name', name='Pads', time=0))
pads.append(Message('program_change', program=89, channel=2, time=0))  # warm pad

# voicings: triads in mid register, slightly inverted
chord_voicings = [
    [60, 63, 67],  # Cm  : C  Eb G
    [56, 60, 63],  # Ab  : Ab C  Eb (Ab=56)
    [58, 63, 65],  # Eb  : Eb G  Bb (Eb=63 is in melody; pad uses lower voicing)
    [58, 62, 65],  # Bb  : Bb D  F  (Bb=58)
]
pad_notes = []
for bar in range(0, 16):
    base = bar * WN
    voicing = chord_voicings[bar % 4]
    # one whole-note chord per bar with rising velocity over phrases
    vel = 60 if bar < 4 else (75 if bar < 8 else 85)
    for p in voicing:
        pad_notes.append((base, WN, p, vel))

add_notes(pads, pad_notes, channel=2)
pads.append(MetaMessage('end_of_track', time=0))
mid.tracks.append(pads)


# ============================================================================
# 5. LEAD — channel 3 (expressive line, joins later)
# ============================================================================
lead = MidiTrack()
lead.append(MetaMessage('track_name', name='Lead', time=0))
lead.append(Message('program_change', program=81, channel=3, time=0))  # square lead

# Lead joins at bar 7 with high register expressive phrases
lead_notes = []
# phrase 1 — bar 7 (high arc)
b = 6 * WN
lead_notes += [
    (b + 0,     EN,   84, 110),
    (b + EN,    EN,   86, 100),
    (b + QN,    EN+SN,87, 115),
    (b + QN+EN+SN, SN,86, 90),
    (b + 2*QN,  HN,   89, 120),     # high climax
]
# phrase 2 — bar 9
b = 8 * WN
lead_notes += [
    (b + 0,     QN,   84, 100),
    (b + QN,    EN,   82, 95),
    (b + QN+EN, EN,   84, 100),
    (b + 2*QN,  EN,   86, 105),
    (b + 2*QN+EN,EN,  87, 115),
    (b + 3*QN,  QN,   89, 120),
]
# phrase 3 — bar 11 cadence
b = 10 * WN
lead_notes += [
    (b + 0,     EN,   82, 100),
    (b + EN,    EN,   80, 95),
    (b + QN,    EN,   79, 90),
    (b + QN+EN, EN,   77, 90),
    (b + HN,    HN,   75, 105),
]
# final long lead note from bar 13
b = 12 * WN
lead_notes += [
    (b + 0,     2*WN, 84, 100),
]

add_notes(lead, lead_notes, channel=3)
lead.append(MetaMessage('end_of_track', time=0))
mid.tracks.append(lead)


# ---- write file ---------------------------------------------------------
out = 'test_song.mid'
mid.save(out)
print(f'Wrote {out}: {len(mid.tracks)} tracks, {mid.length:.2f}s')
