# ============================================================================
# SYNESTHESIA VISUALIZER - Part 1: MIDI input and activity CHOPs
# ----------------------------------------------------------------------------
# Paste this whole script into TouchDesigner's Textport (Alt+P) and press
# Enter. It builds /project1/synesthesia and the per-instrument activity
# chain. Re-running is safe: the container is destroyed and rebuilt.
#
# After it prints "PART 1 COMPLETE":
#   1. Click /project1/synesthesia/midi_file_in and set its 'file' parameter
#      to your .mid file.
#   2. Paste Part 2.
# ============================================================================

BASE_PATH = '/project1/synesthesia'

# MIDI channel per instrument. Channel 10 is the GM drum channel.
CHANNELS = [
    ('drums',  10),
    ('bass',    1),
    ('melody',  2),
    ('pads',    3),
    ('lead',    4),
]

LAG_RISE = 0.02   # attack smoothing (seconds)
LAG_FALL = 0.30   # release smoothing (seconds)


def setpar(o, name, value):
    """Best-effort parameter set; ignore missing parameters or menu mismatches."""
    p = getattr(o.par, name, None)
    if p is None:
        return False
    try:
        p.val = value
        return True
    except Exception:
        try:
            setattr(o.par, name, value)
            return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# 1. Container - destroy + recreate so this script is idempotent
# ---------------------------------------------------------------------------
root = op('/project1')
existing = op(BASE_PATH)
if existing:
    existing.destroy()

base = root.create(containerCOMP, 'synesthesia')
base.nodeX = 0
base.nodeY = 0
print('[Part 1] container ready at', BASE_PATH)


# ---------------------------------------------------------------------------
# 2. MIDI File In CHOP
# ---------------------------------------------------------------------------
# Outputs channels named ch{midiChannel}n{noteNum} for notes and
# ch{midiChannel}c{ccNum} for control changes. We grab both per instrument.
try:
    midi = base.create(midifileinCHOP, 'midi_file_in')
except Exception:
    midi = base.create(midiinCHOP, 'midi_file_in')
midi.nodeX = -1200
midi.nodeY = 0
print('[Part 1] midi_file_in - load a .mid into its file parameter')


# ---------------------------------------------------------------------------
# 3. Per-instrument processing chain
#    select  ->  math(max)  ->  math(gain 1/127)  ->  lag  ->  rename
#    Output of activity_<name> is one channel named <name> in 0..1.
# ---------------------------------------------------------------------------
y = 400
for name, ch in CHANNELS:
    sel = base.create(selectCHOP, 'select_' + name)
    sel.inputConnectors[0].connect(midi)
    # Match note + CC channels for this MIDI channel. The trailing letter
    # prevents ch1* from also matching ch10*, ch11* etc.
    setpar(sel, 'channames', 'ch%dn* ch%dc*' % (ch, ch))
    sel.nodeX = -900
    sel.nodeY = y

    mx = base.create(mathCHOP, 'max_' + name)
    mx.inputConnectors[0].connect(sel)
    setpar(mx, 'chanop', 'max')
    mx.nodeX = -700
    mx.nodeY = y

    norm = base.create(mathCHOP, 'norm_' + name)
    norm.inputConnectors[0].connect(mx)
    setpar(norm, 'gain', 1.0 / 127.0)
    norm.nodeX = -500
    norm.nodeY = y

    lag = base.create(lagCHOP, 'lag_' + name)
    lag.inputConnectors[0].connect(norm)
    setpar(lag, 'lag1', LAG_RISE)
    setpar(lag, 'lag2', LAG_FALL)
    lag.nodeX = -300
    lag.nodeY = y

    rn = base.create(renameCHOP, 'activity_' + name)
    rn.inputConnectors[0].connect(lag)
    setpar(rn, 'renamefrom', '*')
    setpar(rn, 'renameto', name)
    rn.nodeX = -100
    rn.nodeY = y

    print('[Part 1] activity_%s ready (MIDI channel %d)' % (name, ch))
    y -= 150


# ---------------------------------------------------------------------------
# 4. Transport timer
# ---------------------------------------------------------------------------
timer = base.create(timerCHOP, 'transport_timer')
setpar(timer, 'length', 300)
setpar(timer, 'play', False)
timer.nodeX = -1200
timer.nodeY = -400
print('[Part 1] transport_timer ready (set play=True to start)')


print('')
print('============================================================')
print(' PART 1 COMPLETE')
print(' Next: load a .mid into midi_file_in, then paste Part 2.')
print('============================================================')
