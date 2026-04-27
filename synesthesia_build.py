# ============================================================================
# SYNESTHESIA VISUALIZER  -  single-file builder
# ----------------------------------------------------------------------------
# Paste the entire contents of this file into TouchDesigner's Textport
# (Alt + P) and press Enter. It builds /project1/synesthesia from scratch.
#
# Strategy
# --------
# 1. Build the absolute minimum first: container, MIDI input, one sphere,
#    one camera, one light, one render. That validates the whole chain.
# 2. Then add the remaining four instruments one at a time. Each is wrapped
#    in its own try/except so a single failure does not stop the build.
# 3. Print a status line for every step and a summary report at the end.
#
# Every parameter name and method below is taken from the official
# TouchDesigner documentation:
#
#   https://docs.derivative.ca/CHOP_Class
#   https://docs.derivative.ca/OP_Class
#   https://docs.derivative.ca/MidiinCHOP_Class
#   https://docs.derivative.ca/Geometry_COMP
#   https://docs.derivative.ca/Camera_COMP
#   https://docs.derivative.ca/Light_COMP
#   https://docs.derivative.ca/Render_TOP
#   https://docs.derivative.ca/Phong_MAT
#
# Re-running the script is safe; it destroys /project1/synesthesia and
# rebuilds it from a clean slate.
# ============================================================================

import traceback

BASE_PATH = '/project1/synesthesia'

LAG_RISE = 0.02   # attack smoothing on the activity CHOPs (seconds)
LAG_FALL = 0.30   # release smoothing on the activity CHOPs (seconds)

# Drums is the minimum-build instrument. The other four are added afterwards.
MINIMUM = ('drums', 10, 'sphere', (1.00, 0.20, 0.10), (0.0, 0.0, 0.0), 0.80)

EXTRA_INSTRUMENTS = [
    ('bass',   1, 'sphere', (0.20, 0.30, 1.00), (-2.6,  0.0,  0.0), 0.60),
    ('melody', 2, 'torus',  (1.00, 0.85, 0.30), ( 2.6,  0.0,  0.0), 0.50),
    ('pads',   3, 'box',    (0.20, 0.80, 0.70), ( 0.0,  1.6, -1.2), 0.40),
    ('lead',   4, 'tube',   (0.95, 0.95, 0.85), ( 0.0, -1.6, -1.2), 0.50),
]


# ----------------------------------------------------------------------------
# Reporting
# ----------------------------------------------------------------------------
_report = []


def _log(status, label, detail=''):
    _report.append((status, label, detail))
    line = '[%-4s] %s' % (status, label)
    if detail:
        line += '  -  ' + detail
    print(line)


def ok(label, detail=''):
    _log('OK', label, detail)


def fail(label, detail=''):
    _log('FAIL', label, detail)


# ----------------------------------------------------------------------------
# Tiny wrappers around TD APIs. Each one is documented in the OP_Class /
# CHOP_Class pages linked at the top of the file.
# ----------------------------------------------------------------------------
def setpar(o, name, value):
    """Best-effort parameter set. Returns True if applied, False otherwise."""
    if o is None:
        return False
    par = getattr(o.par, name, None)
    if par is None:
        return False
    try:
        par.val = value
        return True
    except Exception:
        try:
            setattr(o.par, name, value)
            return True
        except Exception:
            return False


def expr_set(o, name, expression):
    """Bind a parameter to a Python expression. Returns True if applied."""
    if o is None:
        return False
    par = getattr(o.par, name, None)
    if par is None:
        return False
    try:
        par.expr = expression
        par.mode = ParMode.EXPRESSION
        return True
    except Exception:
        return False


def replace(parent_, op_type, name):
    """Destroy any existing child of parent_ named `name`, then create fresh.

    Per OP_Class: create() and destroy() are component-level operations,
    so parent_ must be a COMP.
    """
    existing = parent_.op(name)
    if existing:
        try:
            existing.destroy()
        except Exception as e:
            fail('destroy ' + parent_.path + '/' + name,
                 '%s: %s' % (type(e).__name__, e))
    return parent_.create(op_type, name)


def connect(node, source):
    """Wire `source` into input 0 of `node` using the documented setInputs()."""
    if node is None or source is None:
        return False
    try:
        node.setInputs([source])
        return True
    except Exception as e:
        fail('connect',
             '%s -> %s: %s' % (source.path, node.path, e))
        return False


# Map our friendly shape names to TD SOP type globals (these names are
# defined inside TD's Python interpreter).
SOP_TYPES = {
    'sphere': sphereSOP,
    'torus':  torusSOP,
    'box':    boxSOP,
    'tube':   tubeSOP,
}


class step:
    """Context manager. Catches any exception, reports it, never propagates."""

    def __init__(self, label):
        self.label = label

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            return False
        fail(self.label, '%s: %s' % (exc_type.__name__, exc))
        traceback.print_exception(exc_type, exc, tb)
        return True   # swallow; the next step keeps going


# ----------------------------------------------------------------------------
# Per-instrument builders, used by both the minimum build and the loop.
# ----------------------------------------------------------------------------
def build_activity_chain(base, midi, name, channel, y):
    """select -> math(max) -> math(gain 1/127) -> lag -> rename.

    Output is a single-channel CHOP named `activity_<name>` whose channel is
    named <name> and ranges 0..1 over MIDI velocity.
    """
    sel = replace(base, selectCHOP, 'select_' + name)
    connect(sel, midi)
    setpar(sel, 'channames', 'ch%dn* ch%dc*' % (channel, channel))
    sel.nodeX = -900
    sel.nodeY = y

    mx = replace(base, mathCHOP, 'max_' + name)
    connect(mx, sel)
    setpar(mx, 'chanop', 'max')
    mx.nodeX = -700
    mx.nodeY = y

    norm = replace(base, mathCHOP, 'norm_' + name)
    connect(norm, mx)
    setpar(norm, 'gain', 1.0 / 127.0)
    norm.nodeX = -500
    norm.nodeY = y

    lag = replace(base, lagCHOP, 'lag_' + name)
    connect(lag, norm)
    setpar(lag, 'lag1', LAG_RISE)
    setpar(lag, 'lag2', LAG_FALL)
    lag.nodeX = -300
    lag.nodeY = y

    rn = replace(base, renameCHOP, 'activity_' + name)
    connect(rn, lag)
    setpar(rn, 'renamefrom', '*')
    setpar(rn, 'renameto', name)
    rn.nodeX = -100
    rn.nodeY = y
    return rn


def build_visual(base, name, sop_key, color, pos, pulse, x_offset):
    """Geometry COMP + shape SOP + Phong MAT, with activity-driven scale & emit."""
    sop_type = SOP_TYPES[sop_key]

    geo = replace(base, geometryCOMP, name + '_geo')
    geo.nodeX = x_offset
    geo.nodeY = 0
    setpar(geo, 'tx', pos[0])
    setpar(geo, 'ty', pos[1])
    setpar(geo, 'tz', pos[2])

    activity_path = "%s/activity_%s" % (BASE_PATH, name)
    scale_expr = "1.0 + op('%s')['%s'] * %s" % (activity_path, name, pulse)
    expr_set(geo, 'sx', scale_expr)
    expr_set(geo, 'sy', scale_expr)
    expr_set(geo, 'sz', scale_expr)

    # New geometryCOMPs ship with a default torus + Out SOP. Clear them so
    # only our chosen shape contributes to the render.
    for child in list(geo.children):
        try:
            child.destroy()
        except Exception:
            pass

    sop = geo.create(sop_type, 'shape')
    try:
        sop.render = True
        sop.display = True
    except Exception:
        pass

    mat = replace(base, phongMAT, name + '_mat')
    mat.nodeX = x_offset
    mat.nodeY = -180
    setpar(mat, 'diffr', color[0])
    setpar(mat, 'diffg', color[1])
    setpar(mat, 'diffb', color[2])
    setpar(mat, 'specr', 0.6)
    setpar(mat, 'specg', 0.6)
    setpar(mat, 'specb', 0.6)
    setpar(mat, 'shininess', 60)

    glow = "op('%s')['%s']" % (activity_path, name)
    expr_set(mat, 'emitr', "%s * %s" % (color[0], glow))
    expr_set(mat, 'emitg', "%s * %s" % (color[1], glow))
    expr_set(mat, 'emitb', "%s * %s" % (color[2], glow))

    setpar(geo, 'material', mat.path)
    return geo, mat


# ============================================================================
# PHASE 1 - absolute minimum
#   container, MIDI input, one sphere, one camera, one light, one render
# ============================================================================
print('')
print('=' * 64)
print(' SYNESTHESIA VISUALIZER  -  single-file builder')
print('=' * 64)

base = None
with step('1. create container at ' + BASE_PATH):
    root = op('/project1')
    if root is None:
        raise RuntimeError("'/project1' not found - open a TD project first")
    existing = op(BASE_PATH)
    if existing:
        existing.destroy()
    base = root.create(containerCOMP, 'synesthesia')
    base.nodeX = 0
    base.nodeY = 0
    ok('1. container ready', BASE_PATH)


midi = None
if base is not None:
    with step('2. create midi_in (live MIDI In CHOP)'):
        midi = base.create(midiinCHOP, 'midi_in')
        midi.nodeX = -1200
        midi.nodeY = 0
        # 'active' is a documented MIDI In CHOP parameter.
        setpar(midi, 'active', True)
        ok('2. midi_in ready',
           'set midi_in.par.device on the MIDI Devices Mapper dialog')


# Drums activity chain + drums sphere = the minimum visual signal path.
mname, mchan, msop, mcolor, mpos, mpulse = MINIMUM

if base is not None and midi is not None:
    with step('3. build activity chain for ' + mname):
        build_activity_chain(base, midi, mname, mchan, 400)
        ok('3. activity_' + mname + ' chain ready')

    with step('4. build minimum visual: ' + mname + ' (' + msop + ')'):
        build_visual(base, mname, msop, mcolor, mpos, mpulse, 0)
        ok('4. ' + mname + '_geo + ' + mname + '_mat ready')


target = None
if base is not None:
    with step('5. create cam_target null COMP'):
        target = replace(base, nullCOMP, 'cam_target')
        target.nodeX = -200
        target.nodeY = -800
        ok('5. cam_target placed at origin')


cam = None
if base is not None:
    with step('6. create cam_main (orbit camera)'):
        cam = replace(base, cameraCOMP, 'cam_main')
        cam.nodeX = -400
        cam.nodeY = -800
        # absTime advances even when transport is paused, so the camera
        # always orbits and you can always see your scene.
        expr_set(cam, 'tx', 'math.sin(absTime.seconds * 0.18) * 7.0')
        expr_set(cam, 'tz', 'math.cos(absTime.seconds * 0.18) * 7.0')
        setpar(cam, 'ty', 2.0)
        if target is not None:
            setpar(cam, 'lookat', target.path)
        ok('6. cam_main orbiting cam_target')


key_light = None
if base is not None:
    with step('7. create light_key'):
        key_light = replace(base, lightCOMP, 'light_key')
        key_light.nodeX = 0
        key_light.nodeY = -800
        setpar(key_light, 'tx', 4)
        setpar(key_light, 'ty', 5)
        setpar(key_light, 'tz', 4)
        setpar(key_light, 'dimmer', 1.2)
        # Per Light_COMP docs: light colour is cr/cg/cb (NOT lightcolorr/g/b).
        setpar(key_light, 'cr', 1.0)
        setpar(key_light, 'cg', 0.95)
        setpar(key_light, 'cb', 0.85)
        ok('7. light_key ready')


render = None
if base is not None:
    with step('8. create render_main (1920x1080)'):
        render = replace(base, renderTOP, 'render_main')
        render.nodeX = 600
        render.nodeY = -1000
        setpar(render, 'resolutionw', 1920)
        setpar(render, 'resolutionh', 1080)
        if cam is not None:
            setpar(render, 'camera', cam.path)
        # Glob patterns: pull in every *_geo and every light_*.
        setpar(render, 'geometry', '*_geo')
        setpar(render, 'lights', 'light_*')
        # Per Render_TOP docs: parameter is `antialias` (NOT antialiasing).
        setpar(render, 'antialias', 4)
        ok('8. render_main 1920x1080')


# ============================================================================
# PHASE 2 - add the remaining four instruments, one at a time
# ============================================================================
if base is not None and midi is not None:
    y = 250
    for i, (name, channel, sop_key, color, pos, pulse) in enumerate(EXTRA_INSTRUMENTS, start=1):
        with step('9.%d  %s  (channel %d, %s)' % (i, name, channel, sop_key)):
            build_activity_chain(base, midi, name, channel, y)
            build_visual(base, name, sop_key, color, pos, pulse, i * 200)
            ok('9.%d %s instrument ready' % (i, name))
        y -= 150


# ============================================================================
# PHASE 3 - extras: viewable output + transport, only after the core works
# ============================================================================
out = None
if base is not None and render is not None:
    with step('10. create OUT null TOP'):
        out = replace(base, nullTOP, 'OUT')
        out.nodeX = 1400
        out.nodeY = -1000
        connect(out, render)
        ok('10. OUT null TOP wired to render_main')


if base is not None and out is not None:
    with step('11. create window_out window COMP'):
        win = replace(base, windowCOMP, 'window_out')
        win.nodeX = 1600
        win.nodeY = -1000
        setpar(win, 'top', out.path)
        setpar(win, 'winw', 1920)
        setpar(win, 'winh', 1080)
        setpar(win, 'borders', False)
        ok('11. window_out fullscreen output ready')


if base is not None:
    with step('12. add fill + rim lights'):
        fill_l = replace(base, lightCOMP, 'light_fill')
        fill_l.nodeX = 200
        fill_l.nodeY = -800
        setpar(fill_l, 'tx', -4); setpar(fill_l, 'ty', 2); setpar(fill_l, 'tz', -2)
        setpar(fill_l, 'dimmer', 0.6)
        setpar(fill_l, 'cr', 0.55); setpar(fill_l, 'cg', 0.65); setpar(fill_l, 'cb', 1.0)

        rim_l = replace(base, lightCOMP, 'light_rim')
        rim_l.nodeX = 400
        rim_l.nodeY = -800
        setpar(rim_l, 'tx', 0); setpar(rim_l, 'ty', -1); setpar(rim_l, 'tz', -5)
        setpar(rim_l, 'dimmer', 0.8)
        setpar(rim_l, 'cr', 0.85); setpar(rim_l, 'cg', 0.85); setpar(rim_l, 'cb', 1.0)
        ok('12. light_fill + light_rim ready')


# ============================================================================
# REPORT
# ============================================================================
print('')
print('=' * 64)
print(' BUILD REPORT')
print('=' * 64)
oks = sum(1 for s, _, _ in _report if s == 'OK')
fails = sum(1 for s, _, _ in _report if s == 'FAIL')
print(' steps OK:   %d' % oks)
print(' steps FAIL: %d' % fails)
print('-' * 64)
for status, label, detail in _report:
    line = ' [%-4s] %s' % (status, label)
    if detail:
        line += '  -  ' + detail
    print(line)
print('=' * 64)
if fails == 0:
    print(' All steps succeeded.')
    print('')
    print(' Next:')
    print('   1. Set midi_in.par.device on the MIDI Devices Mapper dialog,')
    print('      OR replace midi_in with a midifileinCHOP for .mid playback.')
    print('   2. Middle-click OUT inside %s to preview.' % BASE_PATH)
    print("   3. op('%s/window_out').par.winopen.pulse() for fullscreen." % BASE_PATH)
else:
    print(' Some steps failed; see [FAIL] lines above for the exact error')
    print(' and the traceback printed immediately after each failure.')
print('=' * 64)
