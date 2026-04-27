# ============================================================================
# SYNESTHESIA VISUALIZER - Part 3: Camera, lights, render, window
# ----------------------------------------------------------------------------
# Paste AFTER Parts 1 & 2. Adds an orbiting camera, three lights, the render
# pipeline, a single bloom pass, and a fullscreen Window COMP.
#
# Re-running is safe: existing nodes are destroyed first.
# ============================================================================

BASE_PATH = '/project1/synesthesia'
base = op(BASE_PATH)
if not base:
    raise RuntimeError('Run Parts 1 and 2 first')


def setpar(o, name, value):
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


def replace(typ, name):
    existing = base.op(name)
    if existing:
        existing.destroy()
    return base.create(typ, name)


def expr_set(par, expression):
    par.expr = expression
    par.mode = ParMode.EXPRESSION


# ---------------------------------------------------------------------------
# 1. Camera target (look-at anchor at origin)
# ---------------------------------------------------------------------------
target = replace(nullCOMP, 'cam_target')
target.nodeX = -200
target.nodeY = -800
setpar(target, 'tx', 0)
setpar(target, 'ty', 0)
setpar(target, 'tz', 0)


# ---------------------------------------------------------------------------
# 2. Camera - slow orbit driven by absTime so it moves even when paused
# ---------------------------------------------------------------------------
cam = replace(cameraCOMP, 'cam_main')
cam.nodeX = -400
cam.nodeY = -800
expr_set(cam.par.tx, 'math.sin(absTime.seconds * 0.18) * 7.0')
expr_set(cam.par.tz, 'math.cos(absTime.seconds * 0.18) * 7.0')
setpar(cam, 'ty', 2.0)
for pname in ('lookat', 'lookatpath'):
    if hasattr(cam.par, pname):
        try:
            setattr(cam.par, pname, target.path)
            break
        except Exception:
            continue
print('[Part 3] cam_main orbiting cam_target')


# ---------------------------------------------------------------------------
# 3. Three-point lighting
# ---------------------------------------------------------------------------
key = replace(lightCOMP, 'light_key')
key.nodeX = 0
key.nodeY = -800
setpar(key, 'tx', 4); setpar(key, 'ty', 5); setpar(key, 'tz', 4)
setpar(key, 'dimmer', 1.2)
setpar(key, 'lightcolorr', 1.0)
setpar(key, 'lightcolorg', 0.95)
setpar(key, 'lightcolorb', 0.85)

fill = replace(lightCOMP, 'light_fill')
fill.nodeX = 200
fill.nodeY = -800
setpar(fill, 'tx', -4); setpar(fill, 'ty', 2); setpar(fill, 'tz', -2)
setpar(fill, 'dimmer', 0.6)
setpar(fill, 'lightcolorr', 0.55)
setpar(fill, 'lightcolorg', 0.65)
setpar(fill, 'lightcolorb', 1.0)

rim = replace(lightCOMP, 'light_rim')
rim.nodeX = 400
rim.nodeY = -800
setpar(rim, 'tx', 0); setpar(rim, 'ty', -1); setpar(rim, 'tz', -5)
setpar(rim, 'dimmer', 0.8)
setpar(rim, 'lightcolorr', 0.85)
setpar(rim, 'lightcolorg', 0.85)
setpar(rim, 'lightcolorb', 1.0)
print('[Part 3] light_key, light_fill, light_rim')


# ---------------------------------------------------------------------------
# 4. Render TOP - 1080p, picks up *_geo and light_*
# ---------------------------------------------------------------------------
render = replace(renderTOP, 'render_main')
render.nodeX = 600
render.nodeY = -1000
setpar(render, 'resolutionw', 1920)
setpar(render, 'resolutionh', 1080)
setpar(render, 'camera', cam.path)
setpar(render, 'geometry', '*_geo')
setpar(render, 'lights', 'light_*')
setpar(render, 'antialiasing', 4)
print('[Part 3] render_main 1920x1080')


# ---------------------------------------------------------------------------
# 5. Bloom: threshold -> blur -> add over original
# ---------------------------------------------------------------------------
thresh = replace(levelTOP, 'bloom_threshold')
thresh.nodeX = 800
thresh.nodeY = -1100
thresh.inputConnectors[0].connect(render)
setpar(thresh, 'blacklevel', 0.55)

blur = replace(blurTOP, 'bloom_blur')
blur.nodeX = 1000
blur.nodeY = -1100
blur.inputConnectors[0].connect(thresh)
setpar(blur, 'size', 22)

bloom = replace(compositeTOP, 'bloom_comp')
bloom.nodeX = 1200
bloom.nodeY = -1000
bloom.inputConnectors[0].connect(render)
bloom.inputConnectors[1].connect(blur)
setpar(bloom, 'operand', 'add')
print('[Part 3] bloom pipeline')


# ---------------------------------------------------------------------------
# 6. Output null + Window COMP
# ---------------------------------------------------------------------------
out = replace(nullTOP, 'OUT')
out.nodeX = 1400
out.nodeY = -1000
out.inputConnectors[0].connect(bloom)

win = replace(windowCOMP, 'window_out')
win.nodeX = 1600
win.nodeY = -1000
setpar(win, 'top', out.path)
setpar(win, 'winw', 1920)
setpar(win, 'winh', 1080)
setpar(win, 'borders', False)
print('[Part 3] OUT + window_out ready')


print('')
print('============================================================')
print(' PART 3 COMPLETE')
print('')
print(' Start playback:')
print("   op('%s/transport_timer').par.play = True" % BASE_PATH)
print(' Open fullscreen:')
print("   op('%s/window_out').par.winopen.pulse()" % BASE_PATH)
print(' View output: middle-click OUT in /project1/synesthesia')
print('============================================================')
