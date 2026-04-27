# ============================================================================
# SYNESTHESIA VISUALIZER — Part 3: Scene Composition & Output
# ============================================================================
# Paste this AFTER Parts 1 & 2. It builds the camera, lights, render
# pipeline, post-processing, transport controls, and fullscreen output.
# ============================================================================

BASE = '/project1/synesthesia'
base = op(BASE)
if not base:
    raise RuntimeError('Run Parts 1 & 2 first — container not found')

# ---------------------------------------------------------------------------
# 1. CAMERA — orbiting with look-at
# ---------------------------------------------------------------------------
# The camera slowly orbits the origin so the viewer sees all geometry
# from shifting angles. It always looks at the centre of the scene.
cam = base.create(cameraCOMP, 'cam_orbit')
cam.nodeX = -300
cam.nodeY = -700
cam.par.tx = 0
cam.par.ty = 1.0
cam.par.tz = 5.0
# Look-at target: the origin
cam.par.lookatpath = ''  # we drive orbit via expressions below

# Orbit expressions — slow circular path
orbit_speed = base.create(constantCHOP, 'orbit_speed')
orbit_speed.nodeX = -500
orbit_speed.nodeY = -700
orbit_speed.par.value0 = 0.04  # revolutions per second

cam.par.tx.expr = 'math.sin(me.time.seconds * 0.04 * 6.283) * 5.0'
cam.par.tx.mode = ParMode.EXPRESSION
cam.par.tz.expr = 'math.cos(me.time.seconds * 0.04 * 6.283) * 5.0'
cam.par.tz.mode = ParMode.EXPRESSION
cam.par.ty.expr = '1.5 + math.sin(me.time.seconds * 0.02) * 0.5'
cam.par.ty.mode = ParMode.EXPRESSION
print('[Part 3] Camera — orbiting with look-at')

# ---------------------------------------------------------------------------
# 2. THREE-POINT LIGHTING
# ---------------------------------------------------------------------------
# Key light: main directional, warm white
key = base.create(lightCOMP, 'light_key')
key.nodeX = -100
key.nodeY = -700
key.par.tx = 3
key.par.ty = 4
key.par.tz = 2
key.par.dimmer = 1.2
key.par.lightcolorr = 1.0
key.par.lightcolorg = 0.95
key.par.lightcolorb = 0.85

# Fill light: soft blue from the side
fill = base.create(lightCOMP, 'light_fill')
fill.nodeX = 100
fill.nodeY = -700
fill.par.tx = -3
fill.par.ty = 2
fill.par.tz = -1
fill.par.dimmer = 0.5
fill.par.lightcolorr = 0.6
fill.par.lightcolorg = 0.7
fill.par.lightcolorb = 1.0

# Rim/back light: highlights edges
rim = base.create(lightCOMP, 'light_rim')
rim.nodeX = 300
rim.nodeY = -700
rim.par.tx = 0
rim.par.ty = -1
rim.par.tz = -4
rim.par.dimmer = 0.7
rim.par.lightcolorr = 0.8
rim.par.lightcolorg = 0.85
rim.par.lightcolorb = 1.0
print('[Part 3] 3-point lighting — key, fill, rim')

# ---------------------------------------------------------------------------
# 3. RENDER TOP — 1080p, 4x MSAA
# ---------------------------------------------------------------------------
render = base.create(renderTOP, 'render_main')
render.nodeX = 0
render.nodeY = -900
render.par.resolutionw = 1920
render.par.resolutionh = 1080
render.par.antialiasing = 4  # 4x MSAA
render.par.camera = cam.path
# Render all geometry in the container
render.par.geometry = '*'
render.par.lights = '*'
print('[Part 3] Render TOP — 1920x1080, 4x MSAA')

# ---------------------------------------------------------------------------
# 4. POST-PROCESSING: Bloom / Glow
# ---------------------------------------------------------------------------
# Bloom makes bright areas bleed light — essential for the glowing look.
bloom_blur = base.create(blurTOP, 'bloom_blur')
bloom_blur.nodeX = 200
bloom_blur.nodeY = -900
bloom_blur.inputConnectors[0].connect(render)
bloom_blur.par.size = 20  # blur radius

bloom_level = base.create(levelTOP, 'bloom_threshold')
bloom_level.nodeX = 200
bloom_level.nodeY = -1000
bloom_level.inputConnectors[0].connect(bloom_blur)
bloom_level.par.opacity = 0.45  # bloom intensity

# Composite bloom back onto render
bloom_comp = base.create(compositeTOP, 'bloom_comp')
bloom_comp.nodeX = 400
bloom_comp.nodeY = -900
bloom_comp.inputConnectors[0].connect(render)
bloom_comp.inputConnectors[1].connect(bloom_level)
bloom_comp.par.operand = 0  # Add mode
print('[Part 3] Bloom / glow post-processing')

# ---------------------------------------------------------------------------
# 5. FEEDBACK TRAILS
# ---------------------------------------------------------------------------
# Feedback creates ghostly trails from previous frames — gives motion blur
# and a dreamy afterimage effect.
feedback = base.create(feedbackTOP, 'feedback')
feedback.nodeX = 600
feedback.nodeY = -900

fb_level = base.create(levelTOP, 'feedback_decay')
fb_level.nodeX = 600
fb_level.nodeY = -1000
fb_level.inputConnectors[0].connect(feedback)
fb_level.par.opacity = 0.88  # trail persistence (higher = longer trails)

fb_comp = base.create(compositeTOP, 'trail_comp')
fb_comp.nodeX = 800
fb_comp.nodeY = -900
fb_comp.inputConnectors[0].connect(bloom_comp)
fb_comp.inputConnectors[1].connect(fb_level)
fb_comp.par.operand = 27  # Over mode

# Feed the composite back into feedback
feedback.inputConnectors[0].connect(fb_comp)
print('[Part 3] Feedback trails')

# ---------------------------------------------------------------------------
# 6. COLOUR GRADING
# ---------------------------------------------------------------------------
# Subtle colour correction to unify the palette — slight teal in shadows,
# warm highlights.
grade = base.create(levelTOP, 'color_grade')
grade.nodeX = 1000
grade.nodeY = -900
grade.inputConnectors[0].connect(fb_comp)
grade.par.gamma1 = 0.95
grade.par.gamma2 = 0.97
grade.par.gamma3 = 1.02
grade.par.contrast = 1.08
grade.par.brightness1 = 1.02
print('[Part 3] Colour grading')

# ---------------------------------------------------------------------------
# 7. VIGNETTE — GLSL post-process
# ---------------------------------------------------------------------------
vig_dat = base.create(textDAT, 'vignette_compute')
vig_dat.nodeX = 1000
vig_dat.nodeY = -1100
vig_dat.text = '''// Vignette GLSL shader -- darkens edges for cinematic focus
uniform float uStrength;
out vec4 fragColor;
void main(){
    vec2 uv = vUV.st;
    vec2 center = uv - 0.5;
    float dist = length(center);
    float strength = (uStrength > 0.0) ? uStrength : 0.55;
    float vig = smoothstep(0.45, 0.75, dist);
    vec4 col = texture(sTD2DInputs[0], uv);
    col.rgb *= 1.0 - vig * strength;
    fragColor = TDOutputSwizzle(col);
}
'''

vig_top = base.create(glslTOP, 'vignette')
vig_top.nodeX = 1200
vig_top.nodeY = -900
vig_top.inputConnectors[0].connect(grade)
if hasattr(vig_top.par, 'pixeldat'):
    vig_top.par.pixeldat = vig_dat.path
elif hasattr(vig_top.par, 'glslpixel'):
    vig_top.par.glslpixel = vig_dat.path
vig_top.par.resolutionw = 1920
vig_top.par.resolutionh = 1080
print('[Part 3] Vignette shader (vignette_compute)')

# ---------------------------------------------------------------------------
# 8. NULL TOP — final output reference
# ---------------------------------------------------------------------------
final_null = base.create(nullTOP, 'OUT')
final_null.nodeX = 1400
final_null.nodeY = -900
final_null.inputConnectors[0].connect(vig_top)
print('[Part 3] Final output null: OUT')

# ---------------------------------------------------------------------------
# 9. WINDOW COMP — fullscreen output
# ---------------------------------------------------------------------------
win = base.create(windowCOMP, 'window_out')
win.nodeX = 1600
win.nodeY = -900
win.par.top = final_null.path
win.par.winw = 1920
win.par.winh = 1080
win.par.borders = False  # borderless for clean fullscreen
print('[Part 3] Window COMP — fullscreen output')

# ---------------------------------------------------------------------------
# 10. TRANSPORT CONTROLS — play / pause / restart / change file
# ---------------------------------------------------------------------------
transport_dat = base.create(textDAT, 'transport_controls')
transport_dat.nodeX = -600
transport_dat.nodeY = -900
transport_dat.text = '''# =====================================================
# TRANSPORT CONTROLS
# =====================================================
# Importable helpers. Call from Textport, keyboard
# callback, or any DAT:
#   import transport_controls as tc
#   tc.play()

TIMER_PATH = '/project1/synesthesia/transport_timer'
MIDI_PATH  = '/project1/synesthesia/midi_file_in'
WIN_PATH   = '/project1/synesthesia/window_out'

def _timer():
    return op(TIMER_PATH)

def play():
    t = _timer()
    if t is not None:
        t.par.play = True

def pause():
    t = _timer()
    if t is not None:
        t.par.play = False

def restart():
    t = _timer()
    if t is not None:
        t.par.cue.pulse()

def load_midi(path):
    m = op(MIDI_PATH)
    if m is not None:
        m.par.file = path

def fullscreen():
    w = op(WIN_PATH)
    if w is not None:
        w.par.winopen.pulse()

def windowed():
    w = op(WIN_PATH)
    if w is not None:
        w.par.winclose.pulse()
'''
print('[Part 3] Transport control helpers saved')

# ---------------------------------------------------------------------------
# 11. PLAY / PAUSE KEYBOARD SCRIPT
# ---------------------------------------------------------------------------
kb_dat = base.create(textDAT, 'keyboard_shortcuts')
kb_dat.nodeX = -600
kb_dat.nodeY = -1050
kb_dat.text = '''# Keyboard In DAT callbacks
# Wired to keyboard_in DAT (created below). Edit freely.

def onKey(dat, key, state):
    # state == True on key-down, False on key-up
    if not state:
        return
    timer = op('/project1/synesthesia/transport_timer')
    if timer is None:
        return
    if key == 'space':
        timer.par.play = not bool(timer.par.play.eval())
    elif key == 'r':
        timer.par.cue.pulse()
    elif key == 'f':
        win = op('/project1/synesthesia/window_out')
        if win is not None:
            win.par.winopen.pulse()
    elif key == 'esc':
        win = op('/project1/synesthesia/window_out')
        if win is not None:
            win.par.winclose.pulse()
    return
'''

# Keyboard In DAT that fires the callback
kb_in = base.create(keyboardinDAT, 'keyboard_in')
kb_in.nodeX = -800
kb_in.nodeY = -1050
if hasattr(kb_in.par, 'callbacks'):
    kb_in.par.callbacks = kb_dat.path
elif hasattr(kb_in.par, 'callbackdat'):
    kb_in.par.callbackdat = kb_dat.path
print('[Part 3] Keyboard shortcuts wired (space=play, r=restart, f=fullscreen, esc=close)')

# ---------------------------------------------------------------------------
# DONE — all three parts complete!
# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 3 COMPLETE — Scene & Output')
print('=' * 60)
print('')
print(' YOUR SYNESTHESIA VISUALIZER IS READY!')
print('')
print(' Quick start:')
print('  1. Click on midi_file_in and load a .mid file')
print('  2. Press Play on the timeline (or paste the play')
print('     command from the transport_controls DAT)')
print('  3. Open window_out for fullscreen visuals')
print('')
print(' All nodes are inside:', BASE)
print('=' * 60)
