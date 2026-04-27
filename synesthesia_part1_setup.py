# ============================================================================
# SYNESTHESIA VISUALIZER - Part 1: Setup & Audio Analysis
# ============================================================================
# Paste this script into TouchDesigner's Textport (Alt+P).
# It builds the base container and all MIDI/audio analysis nodes.
#
# After pasting, load a .mid file into the MIDI File In CHOP.
# Then paste Part 2 (visuals) and Part 3 (scene).
# ============================================================================

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
LAG_RISE  = 0.02   # seconds - attack smoothing
LAG_FALL  = 0.25   # seconds - release smoothing
MATH_GAIN = 1.0    # master velocity gain

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
# 2. MIDI FILE IN CHOP - loads .mid files
# ---------------------------------------------------------------------------
# Reads a standard MIDI file and outputs note/velocity channels named like
# "ch{channel}n{note}". TD has a dedicated midifileinCHOP in modern builds
# and a midiinCHOP that can also read files in older builds; prefer the
# dedicated one and fall back if the OP type is missing.
def _create_midi_op(parent, name):
    for typename in ('midifileinCHOP', 'midiinfileCHOP', 'midiinCHOP'):
        try:
            optype = eval(typename)
        except Exception:
            continue
        try:
            return parent.create(optype, name)
        except Exception:
            continue
    raise RuntimeError('No MIDI File In CHOP type available in this TD build')

midi_in = _create_midi_op(base, 'midi_file_in')
midi_in.nodeX = -800
midi_in.nodeY = 400
if hasattr(midi_in.par, 'file'):
    midi_in.par.file = ''
print('[Part 1] Created MIDI File In CHOP - load your .mid file into it')

# ---------------------------------------------------------------------------
# 3. SELECT CHOPs - one per instrument channel
# ---------------------------------------------------------------------------
# Each Select CHOP filters the MIDI stream to a single MIDI channel so we can
# treat drums, bass, melody, pads, and lead independently. The MIDI File In
# CHOP names channels like "ch10n36" (channel 10, note 36); we match all
# notes for the channel of interest with "ch{N}n*".
selects = {}
for i, (name, ch) in enumerate(MIDI_CHANNELS.items()):
    sel = base.create(selectCHOP, f'select_{name}')
    sel.nodeX = -550
    sel.nodeY = 400 - i * 120
    sel.inputConnectors[0].connect(midi_in)
    sel.par.channames = f'ch{ch}n*'
    selects[name] = sel
    print(f'[Part 1] Select CHOP: {name} (MIDI ch {ch})')

# ---------------------------------------------------------------------------
# 4. MATH CHOPs - collapse all notes for an instrument into a single value
# ---------------------------------------------------------------------------
# A single MIDI channel can have many notes active at once. We need a single
# scalar "activity" per instrument, so we use Math's "Combine Channels"
# operation to take the maximum velocity across all note channels.
combines = {}
for name, sel in selects.items():
    c = base.create(mathCHOP, f'combine_{name}')
    c.nodeX = sel.nodeX + 200
    c.nodeY = sel.nodeY
    c.inputConnectors[0].connect(sel)
    # Combine across channels -> 1 channel out. Try modern + legacy names.
    for pname in ('chanop', 'combchans', 'combineChans'):
        if hasattr(c.par, pname):
            try:
                setattr(c.par, pname, 'max')
            except Exception:
                try:
                    setattr(c.par, pname, 4)  # menu index for max
                except Exception:
                    pass
            break
    combines[name] = c

# ---------------------------------------------------------------------------
# 5. LAG CHOPs - smooth velocity envelopes
# ---------------------------------------------------------------------------
# Raw MIDI velocity is instant on/off. Lag adds attack/decay so visuals
# bloom and fade smoothly instead of popping.
lags = {}
for name, c in combines.items():
    lag = base.create(lagCHOP, f'lag_{name}')
    lag.nodeX = c.nodeX + 200
    lag.nodeY = c.nodeY
    lag.inputConnectors[0].connect(c)
    if hasattr(lag.par, 'lag1'):
        lag.par.lag1 = LAG_RISE
    if hasattr(lag.par, 'lag2'):
        lag.par.lag2 = LAG_FALL
    lags[name] = lag

print('[Part 1] Created Lag CHOPs for smooth envelopes')

# ---------------------------------------------------------------------------
# 6. ACTIVITY CHOPs - normalised, renamed to "uActivity"
# ---------------------------------------------------------------------------
# Math: divide by 127 to convert raw MIDI velocity into 0..1.
# Rename: name the single output channel "uActivity" so any GLSL MAT that
#         binds a "uActivity" uniform to this CHOP picks it up by name.
activities = {}
for name, lag in lags.items():
    m = base.create(mathCHOP, f'norm_{name}')
    m.nodeX = lag.nodeX + 200
    m.nodeY = lag.nodeY
    m.inputConnectors[0].connect(lag)
    if hasattr(m.par, 'gain'):
        m.par.gain = MATH_GAIN / 127.0
    # Clamp to 0..1 via map-input-range so values stay sane for shaders.
    if hasattr(m.par, 'tooperation'):
        try:
            m.par.tooperation = 'mapinputrange'
        except Exception:
            try:
                m.par.tooperation = 1
            except Exception:
                pass
    if hasattr(m.par, 'fromrange1'):
        m.par.fromrange1 = 0
    if hasattr(m.par, 'fromrange2'):
        m.par.fromrange2 = 1
    if hasattr(m.par, 'torange1'):
        m.par.torange1 = 0
    if hasattr(m.par, 'torange2'):
        m.par.torange2 = 1

    rn = base.create(renameCHOP, f'activity_{name}')
    rn.nodeX = m.nodeX + 200
    rn.nodeY = m.nodeY
    rn.inputConnectors[0].connect(m)
    # Rename whatever channel exists to "uActivity" for clean uniform binding.
    if hasattr(rn.par, 'renamefrom'):
        rn.par.renamefrom = '*'
    if hasattr(rn.par, 'renameto'):
        rn.par.renameto = 'uActivity'
    activities[name] = rn

print('[Part 1] Created activity CHOPs (channel name: uActivity)')

# ---------------------------------------------------------------------------
# 7. MERGE CHOP - combined activity bus
# ---------------------------------------------------------------------------
# Merge each per-instrument activity into one CHOP for downstream debugging
# and for any node that wants every instrument from a single source. Each
# input must go to its own connector index, otherwise later connect() calls
# overwrite earlier ones and only the last instrument shows up.
merge = base.create(mergeCHOP, 'activity_all')
merge.nodeX = 600
merge.nodeY = 200
# We need each activity to keep its name, so first rename per-instrument
# back to its instrument name, then merge those into the bus.
for i, (name, rn) in enumerate(activities.items()):
    branch = base.create(renameCHOP, f'name_{name}')
    branch.nodeX = rn.nodeX + 200
    branch.nodeY = rn.nodeY
    branch.inputConnectors[0].connect(rn)
    if hasattr(branch.par, 'renamefrom'):
        branch.par.renamefrom = '*'
    if hasattr(branch.par, 'renameto'):
        branch.par.renameto = name
    # Wire each source into the *next* free input slot on merge. Calling
    # .connect on the source's output connector adds a new input to merge
    # rather than overwriting slot 0 (which the previous version did).
    branch.outputConnectors[0].connect(merge)

print('[Part 1] Created merged activity bus')

# ---------------------------------------------------------------------------
# 8. LFOs - ambient motion drivers
# ---------------------------------------------------------------------------
# Low-frequency oscillators drive gentle ambient motion in the visuals even
# when no MIDI notes are playing. They keep the scene alive.
lfo_configs = [
    ('lfo_slow',   0.05,  'sin'),
    ('lfo_medium', 0.15,  'sin'),
    ('lfo_fast',   0.4,   'sin'),
    ('lfo_noise',  0.1,   'noise'),
]

for idx, (lfo_name, freq, wave_type) in enumerate(lfo_configs):
    lfo = base.create(lfoCHOP, lfo_name)
    lfo.nodeX = -800
    lfo.nodeY = -200 - idx * 100
    if hasattr(lfo.par, 'frequency'):
        lfo.par.frequency = freq
    # Type is a menu - prefer string label, fall back to integer index.
    if hasattr(lfo.par, 'type'):
        try:
            lfo.par.type = wave_type
        except Exception:
            lfo.par.type = 4 if wave_type == 'noise' else 0
    if hasattr(lfo.par, 'amplitude'):
        lfo.par.amplitude = 1
    if hasattr(lfo.par, 'offset'):
        lfo.par.offset = 0

print('[Part 1] Created LFO CHOPs for ambient motion')

# ---------------------------------------------------------------------------
# 9. TIMER CHOP - transport reference
# ---------------------------------------------------------------------------
timer = base.create(timerCHOP, 'transport_timer')
timer.nodeX = -800
timer.nodeY = -700
if hasattr(timer.par, 'length'):
    timer.par.length = 300
if hasattr(timer.par, 'play'):
    timer.par.play = False
print('[Part 1] Created transport timer')

# Timer CHOP callback DAT - fires on start / done / cycle.
# Build the callback text as a normal Python string and write it via
# textDAT.text so we never have to embed a triple-quoted block here.
timer_cb = base.create(textDAT, 'transport_timer_callbacks')
timer_cb.nodeX = -550
timer_cb.nodeY = -700
timer_cb_text = (
    "# Timer CHOP callbacks\n"
    "# Attach this DAT to transport_timer's Callbacks DAT parameter.\n"
    "\n"
    "def onInitialize(timerOp):\n"
    "    return\n"
    "\n"
    "def onStart(timerOp):\n"
    "    print('[transport] start')\n"
    "    return\n"
    "\n"
    "def onCycle(timerOp):\n"
    "    return\n"
    "\n"
    "def onDone(timerOp):\n"
    "    print('[transport] done - looping')\n"
    "    timerOp.par.cue.pulse()\n"
    "    timerOp.par.play = True\n"
    "    return\n"
    "\n"
    "def onSegmentEnter(timerOp, segment):\n"
    "    return\n"
    "\n"
    "def onSegmentExit(timerOp, segment):\n"
    "    return\n"
    "\n"
    "def onTimerPulse(timerOp):\n"
    "    return\n"
)
timer_cb.text = timer_cb_text

# Wire callbacks DAT to timer CHOP. The parameter is named differently
# across TD versions, so try the known names in order.
wired = False
for pname in ('callbacks', 'callbackdat', 'callback'):
    p = getattr(timer.par, pname, None)
    if p is not None:
        try:
            p.val = timer_cb.path
            wired = True
            break
        except Exception:
            try:
                setattr(timer.par, pname, timer_cb.path)
                wired = True
                break
            except Exception:
                continue
if wired:
    print('[Part 1] Wired transport_timer_callbacks to transport_timer')
else:
    print('[Part 1] WARN: could not auto-wire timer callbacks - set the')
    print('              "Callbacks DAT" parameter on transport_timer to')
    print('              transport_timer_callbacks manually.')

# ---------------------------------------------------------------------------
# DONE - Part 1 complete
# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 1 COMPLETE - Setup & Audio Analysis')
print('=' * 60)
print(' Next: Paste synesthesia_part2_visuals.py')
print(' Container:', BASE_PATH)
print('=' * 60)
