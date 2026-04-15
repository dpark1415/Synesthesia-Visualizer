# ============================================================================
# SYNESTHESIA VISUALIZER — Part 1: Setup & Audio Analysis
# ============================================================================
# Paste this script into TouchDesigner's Textport (Alt+P).
# It builds the base container and all MIDI/audio analysis nodes.
#
# After pasting, load a .mid file into the MIDI File In CHOP.
# Then paste Part 2 (visuals) and Part 3 (scene).
# ============================================================================

import td  # noqa — available in TouchDesigner

# ---------------------------------------------------------------------------
# CONFIG CONSTANTS
# ---------------------------------------------------------------------------
BASE_PATH = '/project1/synesthesia'
MIDI_CHANNELS = {
    'drums':  10,
    'bass':   1,
    'melody': 2,
    'pads':   3,
    'lead':   4,
}
LAG_RISE   = 0.02   # seconds — attack smoothing
LAG_FALL   = 0.25   # seconds — release smoothing
MATH_GAIN  = 1.0    # master velocity gain

# ---------------------------------------------------------------------------
# 1. CREATE BASE CONTAINER
# ---------------------------------------------------------------------------
root = op('/project1')
if op(BASE_PATH):
    op(BASE_PATH).destroy()

base = root.create(containerCOMP, 'synesthesia')
base.nodeX = 0
base.nodeY = 0
base.viewer = True
print('[Part 1] Created base container:', BASE_PATH)

# ---------------------------------------------------------------------------
# 2. MIDI FILE IN CHOP — loads .mid files
# ---------------------------------------------------------------------------
# This CHOP reads a standard MIDI file and outputs note/velocity channels.
midi_in = base.create(midiinCHOP, 'midi_file_in')
midi_in.nodeX = -600
midi_in.nodeY = 400
midi_in.par.file = ''  # user loads their .mid file here
print('[Part 1] Created MIDI File In CHOP — load your .mid file into it')

# ---------------------------------------------------------------------------
# 3. SELECT CHOPs — one per instrument channel
# ---------------------------------------------------------------------------
# Each Select CHOP filters the MIDI stream to a single channel so we can
# treat drums, bass, melody, pads, and lead independently.
selects = {}
x_pos = -300
for i, (name, ch) in enumerate(MIDI_CHANNELS.items()):
    sel = base.create(selectCHOP, f'select_{name}')
    sel.nodeX = x_pos
    sel.nodeY = 400 - i * 120
    sel.inputConnectors[0].connect(midi_in)
    # Filter to velocity channels matching this MIDI channel
    sel.par.channames = f'ch{ch}*v'
    selects[name] = sel
    print(f'[Part 1] Select CHOP: {name} (MIDI ch {ch})')

# ---------------------------------------------------------------------------
# 4. LAG CHOPs — smooth velocity envelopes
# ---------------------------------------------------------------------------
# Raw MIDI velocity is instant on/off. Lag adds attack/decay so visuals
# bloom and fade smoothly instead of popping.
lags = {}
for name, sel in selects.items():
    lag = base.create(lagCHOP, f'lag_{name}')
    lag.nodeX = sel.nodeX + 200
    lag.nodeY = sel.nodeY
    lag.inputConnectors[0].connect(sel)
    lag.par.lag1 = LAG_RISE   # rise time (attack)
    lag.par.lag2 = LAG_FALL   # fall time (decay)
    lags[name] = lag

print('[Part 1] Created Lag CHOPs for smooth envelopes')

# ---------------------------------------------------------------------------
# 5. MATH CHOPs — per-instrument activity level (0-1)
# ---------------------------------------------------------------------------
# Math CHOPs normalise and scale each channel so downstream visuals get a
# clean 0-1 "activity" signal. Adjust MATH_GAIN to taste.
maths = {}
for name, lag in lags.items():
    m = base.create(mathCHOP, f'activity_{name}')
    m.nodeX = lag.nodeX + 200
    m.nodeY = lag.nodeY
    m.inputConnectors[0].connect(lag)
    m.par.gain = MATH_GAIN
    m.par.postoff = 0
    # Clamp to 0-1 range
    m.par.torange1 = 0
    m.par.torange2 = 1
    maths[name] = m

print('[Part 1] Created Math CHOPs for activity levels')

# ---------------------------------------------------------------------------
# 6. MERGE CHOP — combined activity bus
# ---------------------------------------------------------------------------
# Merges all per-instrument activity signals into one CHOP so any
# downstream node can read all instruments from a single source.
merge = base.create(mergeCHOP, 'activity_all')
merge.nodeX = 400
merge.nodeY = 200
for name, m in maths.items():
    merge.inputConnectors[0].connect(m)

# Rename channels for clarity
rename = base.create(renameCHOP, 'activity_renamed')
rename.nodeX = 600
rename.nodeY = 200
rename.inputConnectors[0].connect(merge)
# We'll let channel names pass through from the math CHOPs

print('[Part 1] Created merged activity bus')

# ---------------------------------------------------------------------------
# 7. LFOs — ambient motion drivers
# ---------------------------------------------------------------------------
# These low-frequency oscillators drive gentle ambient motion in the
# visuals even when no MIDI notes are playing. They keep the scene alive.
lfo_configs = [
    ('lfo_slow',   0.05,  'sin'),   # very slow breathing
    ('lfo_medium', 0.15,  'sin'),   # medium sway
    ('lfo_fast',   0.4,   'sin'),   # faster shimmer
    ('lfo_noise',  0.1,   'noise'), # organic randomness
]

for lfo_name, freq, wave_type in lfo_configs:
    lfo = base.create(lfoCHOP, lfo_name)
    lfo.nodeX = -600
    lfo.nodeY = -200 - lfo_configs.index((lfo_name, freq, wave_type)) * 100
    lfo.par.frequency = freq
    if wave_type == 'noise':
        lfo.par.type = 4  # noise type
    else:
        lfo.par.type = 0  # sine type
    lfo.par.amplitude = 1
    lfo.par.offset = 0

print('[Part 1] Created LFO CHOPs for ambient motion')

# ---------------------------------------------------------------------------
# 8. TIMER CHOP — transport reference
# ---------------------------------------------------------------------------
timer = base.create(timerCHOP, 'transport_timer')
timer.nodeX = -600
timer.nodeY = -600
timer.par.length = 300       # 5 minutes max
timer.par.play = False       # start paused
print('[Part 1] Created transport timer')

# ---------------------------------------------------------------------------
# DONE — Part 1 complete
# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 1 COMPLETE — Setup & Audio Analysis')
print('=' * 60)
print(' Next: Paste synesthesia_part2_visuals.py')
print(' Container:', BASE_PATH)
print('=' * 60)
