# ============================================================================
# SYNESTHESIA VISUALIZER - Part 3: Scene Composition & Output
# ============================================================================
# Paste this AFTER Parts 1 & 2. It builds the camera, lights, render
# pipeline, post-processing, transport controls, and fullscreen output.
# ============================================================================

BASE = '/project1/synesthesia'
base = op(BASE)
if not base:
    raise RuntimeError('Run Parts 1 & 2 first - container not found')

def _setpar(o, name, value):
    """Set a parameter if it exists, swallowing menu/value mismatches."""
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
# 1. CAMERA TARGET - a Null COMP at world origin so the orbit camera
#    has a stable look-at point. Without this, the camera orbits but
#    never rotates to face the geometry, giving a black render.
# ---------------------------------------------------------------------------
target = base.create(nullCOMP, 'cam_target')
target.nodeX = -150
target.nodeY = -700
target.par.tx = 0
target.par.ty = 0
target.par.tz = 0

# ---------------------------------------------------------------------------
# 2. CAMERA - orbiting with look-at
# ---------------------------------------------------------------------------
cam = base.create(cameraCOMP, 'cam_orbit')
cam.nodeX = -300
cam.nodeY = -700
cam.par.tx = 0
cam.par.ty = 1.0
cam.par.tz = 5.0

# Point the camera at the cam_target null on every cook.
for pname in ('lookat', 'lookatpath'):
    if hasattr(cam.par, pname):
        try:
            setattr(cam.par, pname, target.path)
            break
        except Exception:
            continue

# Slow orbit driven by absTime so it keeps moving while the timer is paused.
cam.par.tx.expr = 'math.sin(absTime.seconds * 0.04 * 6.283) * 5.0'
cam.par.tx.mode = ParMode.EXPRESSION
cam.par.tz.expr = 'math.cos(absTime.seconds * 0.04 * 6.283) * 5.0'
cam.par.tz.mode = ParMode.EXPRESSION
cam.par.ty.expr = '1.5 + math.sin(absTime.seconds * 0.02) * 0.5'
cam.par.ty.mode = ParMode.EXPRESSION
print('[Part 3] Camera - orbiting with look-at on cam_target')

# ---------------------------------------------------------------------------
# 3. THREE-POINT LIGHTING
# ---------------------------------------------------------------------------
key = base.create(lightCOMP, 'light_key')
key.nodeX = -100
key.nodeY = -700
key.par.tx = 3
key.par.ty = 4
key.par.tz = 2
_setpar(key, 'dimmer', 1.2)
_setpar(key, 'lightcolorr', 1.0)
_setpar(key, 'lightcolorg', 0.95)
_setpar(key, 'lightcolorb', 0.85)

fill = base.create(lightCOMP, 'light_fill')
fill.nodeX = 100
fill.nodeY = -700
fill.par.tx = -3
fill.par.ty = 2
fill.par.tz = -1
_setpar(fill, 'dimmer', 0.5)
_setpar(fill, 'lightcolorr', 0.6)
_setpar(fill, 'lightcolorg', 0.7)
_setpar(fill, 'lightcolorb', 1.0)

rim = base.create(lightCOMP, 'light_rim')
rim.nodeX = 300
rim.nodeY = -700
rim.par.tx = 0
rim.par.ty = -1
rim.par.tz = -4
_setpar(rim, 'dimmer', 0.7)
_setpar(rim, 'lightcolorr', 0.8)
_setpar(rim, 'lightcolorg', 0.85)
_setpar(rim, 'lightcolorb', 1.0)
print('[Part 3] 3-point lighting - key, fill, rim')

# ---------------------------------------------------------------------------
# 4. RENDER TOP - 1080p, 4x MSAA
# ---------------------------------------------------------------------------
# Geometry/Lights patterns must match only the relevant siblings -
# "*" would also pull in cameras, materials, DATs, etc. and trip warnings.
render = base.create(renderTOP, 'render_main')
render.nodeX = 0
render.nodeY = -900
render.par.resolutionw = 1920
render.par.resolutionh = 1080
_setpar(render, 'antialiasing', 4)
render.par.camera = cam.path
_setpar(render, 'geometry', '*_geo')
_setpar(render, 'lights',   'light_*')
print('[Part 3] Render TOP - 1920x1080, 4x MSAA, geometry=*_geo lights=light_*')

# ---------------------------------------------------------------------------
# 5. POST-PROCESSING: Bloom / Glow
# ---------------------------------------------------------------------------
# Threshold first so only bright pixels bloom, then blur, then add back.
bloom_thresh = base.create(levelTOP, 'bloom_threshold')
bloom_thresh.nodeX = 200
bloom_thresh.nodeY = -1000
bloom_thresh.inputConnectors[0].connect(render)
_setpar(bloom_thresh, 'blacklevel', 0.55)

bloom_blur = base.create(blurTOP, 'bloom_blur')
bloom_blur.nodeX = 200
bloom_blur.nodeY = -900
bloom_blur.inputConnectors[0].connect(bloom_thresh)
_setpar(bloom_blur, 'size', 20)

bloom_comp = base.create(compositeTOP, 'bloom_comp')
bloom_comp.nodeX = 400
bloom_comp.nodeY = -900
bloom_comp.inputConnectors[0].connect(render)
bloom_comp.inputConnectors[1].connect(bloom_blur)
_setpar(bloom_comp, 'operand', 'add')
print('[Part 3] Bloom / glow post-processing')

# ---------------------------------------------------------------------------
# 6. FEEDBACK TRAILS
# ---------------------------------------------------------------------------
# Feedback creates ghostly trails from previous frames. The composite order
# must be: trails on the bottom (input 0), current frame on top (input 1)
# with "over" - that way the new frame shines through and old frames
# fade out behind it.
feedback = base.create(feedbackTOP, 'feedback')
feedback.nodeX = 600
feedback.nodeY = -900

fb_level = base.create(levelTOP, 'feedback_decay')
fb_level.nodeX = 600
fb_level.nodeY = -1000
fb_level.inputConnectors[0].connect(feedback)
_setpar(fb_level, 'opacity', 0.88)

fb_comp = base.create(compositeTOP, 'trail_comp')
fb_comp.nodeX = 800
fb_comp.nodeY = -900
fb_comp.inputConnectors[0].connect(fb_level)     # bg = faded previous
fb_comp.inputConnectors[1].connect(bloom_comp)   # fg = current frame
_setpar(fb_comp, 'operand', 'over')

# Feed the composite back into feedback
feedback.inputConnectors[0].connect(fb_comp)
print('[Part 3] Feedback trails')

# ---------------------------------------------------------------------------
# 7. COLOUR GRADING
# ---------------------------------------------------------------------------
grade = base.create(levelTOP, 'color_grade')
grade.nodeX = 1000
grade.nodeY = -900
grade.inputConnectors[0].connect(fb_comp)
_setpar(grade, 'gamma1', 0.95)
_setpar(grade, 'gamma2', 0.97)
_setpar(grade, 'gamma3', 1.02)
_setpar(grade, 'contrast', 1.08)
_setpar(grade, 'brightness1', 1.02)
print('[Part 3] Colour grading')

# ---------------------------------------------------------------------------
# 8. VIGNETTE - GLSL post-process
# ---------------------------------------------------------------------------
vig_dat = base.create(textDAT, 'vignette_compute')
vig_dat.nodeX = 1000
vig_dat.nodeY = -1100
vig_dat.text = (
    "// Vignette GLSL shader - darkens edges for cinematic focus\n"
    "uniform float uStrength;\n"
    "out vec4 fragColor;\n"
    "void main(){\n"
    "    vec2 uv = vUV.st;\n"
    "    vec2 center = uv - 0.5;\n"
    "    float dist = length(center);\n"
    "    float strength = (uStrength > 0.0) ? uStrength : 0.55;\n"
    "    float vig = smoothstep(0.45, 0.75, dist);\n"
    "    vec4 col = texture(sTD2DInputs[0], uv);\n"
    "    col.rgb *= 1.0 - vig * strength;\n"
    "    fragColor = TDOutputSwizzle(col);\n"
    "}\n"
)

vig_top = base.create(glslTOP, 'vignette')
vig_top.nodeX = 1200
vig_top.nodeY = -900
vig_top.inputConnectors[0].connect(grade)
for pname in ('pixeldat', 'pixelshader', 'glslpixel', 'fragshader'):
    if hasattr(vig_top.par, pname):
        try:
            setattr(vig_top.par, pname, vig_dat.path)
            break
        except Exception:
            continue
_setpar(vig_top, 'resolutionw', 1920)
_setpar(vig_top, 'resolutionh', 1080)
print('[Part 3] Vignette shader (vignette_compute)')

# ---------------------------------------------------------------------------
# 9. NULL TOP - final output reference
# ---------------------------------------------------------------------------
final_null = base.create(nullTOP, 'OUT')
final_null.nodeX = 1400
final_null.nodeY = -900
final_null.inputConnectors[0].connect(vig_top)
print('[Part 3] Final output null: OUT')

# ---------------------------------------------------------------------------
# 10. WINDOW COMP - fullscreen output
# ---------------------------------------------------------------------------
win = base.create(windowCOMP, 'window_out')
win.nodeX = 1600
win.nodeY = -900
_setpar(win, 'top', final_null.path)
_setpar(win, 'winw', 1920)
_setpar(win, 'winh', 1080)
_setpar(win, 'borders', False)
print('[Part 3] Window COMP - fullscreen output')

# ---------------------------------------------------------------------------
# 11. TRANSPORT CONTROLS - play / pause / restart / change file
# ---------------------------------------------------------------------------
transport_dat = base.create(textDAT, 'transport_controls')
transport_dat.nodeX = -800
transport_dat.nodeY = -900
transport_dat.text = (
    "# =====================================================\n"
    "# TRANSPORT CONTROLS\n"
    "# =====================================================\n"
    "# Importable helpers. Call from Textport, keyboard\n"
    "# callback, or any DAT:\n"
    "#   import transport_controls as tc\n"
    "#   tc.play()\n"
    "\n"
    "TIMER_PATH = '/project1/synesthesia/transport_timer'\n"
    "MIDI_PATH  = '/project1/synesthesia/midi_file_in'\n"
    "WIN_PATH   = '/project1/synesthesia/window_out'\n"
    "\n"
    "def _timer():\n"
    "    return op(TIMER_PATH)\n"
    "\n"
    "def play():\n"
    "    t = _timer()\n"
    "    if t is not None:\n"
    "        t.par.play = True\n"
    "\n"
    "def pause():\n"
    "    t = _timer()\n"
    "    if t is not None:\n"
    "        t.par.play = False\n"
    "\n"
    "def restart():\n"
    "    t = _timer()\n"
    "    if t is not None:\n"
    "        t.par.cue.pulse()\n"
    "\n"
    "def load_midi(path):\n"
    "    m = op(MIDI_PATH)\n"
    "    if m is not None:\n"
    "        m.par.file = path\n"
    "\n"
    "def fullscreen():\n"
    "    w = op(WIN_PATH)\n"
    "    if w is not None:\n"
    "        w.par.winopen.pulse()\n"
    "\n"
    "def windowed():\n"
    "    w = op(WIN_PATH)\n"
    "    if w is not None:\n"
    "        w.par.winclose.pulse()\n"
)
print('[Part 3] Transport control helpers saved')

# ---------------------------------------------------------------------------
# 12. PLAY / PAUSE KEYBOARD SCRIPT
# ---------------------------------------------------------------------------
kb_dat = base.create(textDAT, 'keyboard_shortcuts')
kb_dat.nodeX = -800
kb_dat.nodeY = -1050
kb_dat.text = (
    "# Keyboard In DAT callbacks\n"
    "# Wired to keyboard_in DAT (created below). Edit freely.\n"
    "\n"
    "def onKey(dat, key, state):\n"
    "    # state == True on key-down, False on key-up\n"
    "    if not state:\n"
    "        return\n"
    "    timer = op('/project1/synesthesia/transport_timer')\n"
    "    if timer is None:\n"
    "        return\n"
    "    if key == 'space':\n"
    "        timer.par.play = not bool(timer.par.play.eval())\n"
    "    elif key == 'r':\n"
    "        timer.par.cue.pulse()\n"
    "    elif key == 'f':\n"
    "        win = op('/project1/synesthesia/window_out')\n"
    "        if win is not None:\n"
    "            win.par.winopen.pulse()\n"
    "    elif key == 'esc':\n"
    "        win = op('/project1/synesthesia/window_out')\n"
    "        if win is not None:\n"
    "            win.par.winclose.pulse()\n"
    "    return\n"
)

kb_in = base.create(keyboardinDAT, 'keyboard_in')
kb_in.nodeX = -1000
kb_in.nodeY = -1050
for pname in ('callbacks', 'callbackdat'):
    if hasattr(kb_in.par, pname):
        try:
            setattr(kb_in.par, pname, kb_dat.path)
            break
        except Exception:
            continue
print('[Part 3] Keyboard shortcuts wired (space=play, r=restart, f=fullscreen, esc=close)')

# ---------------------------------------------------------------------------
# DONE - all three parts complete!
# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 3 COMPLETE - Scene & Output')
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
