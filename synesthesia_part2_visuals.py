# ============================================================================
# SYNESTHESIA VISUALIZER — Part 2: Visual Generators
# ============================================================================
# Paste this AFTER Part 1. It builds geometry, materials, and shaders
# for every instrument inside /project1/synesthesia.
# ============================================================================

BASE = '/project1/synesthesia'
base = op(BASE)
if not base:
    raise RuntimeError('Run Part 1 first — container not found at ' + BASE)

# ---------------------------------------------------------------------------
# HELPER: quick inline GLSL material
# ---------------------------------------------------------------------------
def make_glsl_mat(parent, name, vert, frag, x=0, y=0):
    """Create a GLSL MAT with inline vertex + fragment shaders.

    The DATs are named <name>_vertex and <name>_pixel to match
    TouchDesigner's GLSL MAT parameter convention.
    """
    g = parent.create(glslMAT, name)
    g.nodeX = x
    g.nodeY = y
    # Write shader code into DATs
    v_dat = parent.create(textDAT, name + '_vertex')
    v_dat.text = vert
    v_dat.nodeX = x - 150
    v_dat.nodeY = y
    f_dat = parent.create(textDAT, name + '_pixel')
    f_dat.text = frag
    f_dat.nodeX = x - 150
    f_dat.nodeY = y - 80
    # GLSL MAT parameter names (try modern + legacy)
    for vp in ('vertexshader', 'glslvertex'):
        if hasattr(g.par, vp):
            setattr(g.par, vp, v_dat.path)
            break
    for fp in ('pixelshader', 'glslpixel'):
        if hasattr(g.par, fp):
            setattr(g.par, fp, f_dat.path)
            break
    return g

# ==============================  KICK DRUM  ================================
# Red pressure sphere — blooms on hit with smooth decay
# ---------------------------------------------------------------------------
kick_geo = base.create(geometryCOMP, 'kick_geo')
kick_geo.nodeX = 0
kick_geo.nodeY = 0

kick_sphere = kick_geo.create(sphereSOP, 'sphere')
kick_sphere.par.rows = 48
kick_sphere.par.cols = 48
kick_sphere.par.radius = 0.5

kick_frag = '''
uniform float uActivity;
out vec4 fragColor;
in Vert { vec3 worldNorm; vec3 worldPos; } iVert;
void main(){
    float rim = pow(1.0 - abs(dot(normalize(iVert.worldNorm),
                    normalize(-iVert.worldPos))), 2.0);
    vec3 col = mix(vec3(0.3,0.02,0.02), vec3(1.0,0.15,0.05),
                   uActivity * 0.8 + rim * 0.5);
    col += vec3(1.0,0.3,0.1) * uActivity * rim * 2.0;
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
kick_vert = '''
uniform float uActivity;
out Vert { vec3 worldNorm; vec3 worldPos; } oVert;
void main(){
    vec3 pos = P * (1.0 + uActivity * 0.35);
    oVert.worldNorm = N;
    oVert.worldPos = pos;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
kick_mat = make_glsl_mat(base, 'kick_mat', kick_vert, kick_frag, 0, -100)
kick_geo.par.material = kick_mat.path
print('[Part 2] Kick drum — red pressure sphere')

# ==============================  SNARE  ====================================
# Cyan shockwave torus ring that expands on hit
# ---------------------------------------------------------------------------
snare_geo = base.create(geometryCOMP, 'snare_geo')
snare_geo.nodeX = 300
snare_geo.nodeY = 0

snare_torus = snare_geo.create(torusSOP, 'torus')
snare_torus.par.rows = 48
snare_torus.par.cols = 48
snare_torus.par.radius1 = 1.0
snare_torus.par.radius2 = 0.04

snare_frag = '''
uniform float uActivity;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; } iVert;
void main(){
    float rim = pow(1.0-abs(dot(normalize(iVert.wN),normalize(-iVert.wP))),3.0);
    float pulse = uActivity;
    vec3 col = mix(vec3(0.0,0.15,0.2), vec3(0.0,0.9,1.0), pulse);
    col += vec3(0.3,1.0,1.0) * rim * pulse * 3.0;
    float alpha = mix(0.1, 0.95, pulse) + rim * 0.5;
    fragColor = TDOutputSwizzle(vec4(col, clamp(alpha,0.0,1.0)));
}
'''
snare_vert = '''
uniform float uActivity;
out Vert { vec3 wN; vec3 wP; } oVert;
void main(){
    vec3 pos = P * (1.0 + uActivity * 0.6);
    oVert.wN = N;
    oVert.wP = pos;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
snare_mat = make_glsl_mat(base, 'snare_mat', snare_vert, snare_frag, 300, -100)
snare_geo.par.material = snare_mat.path
print('[Part 2] Snare — cyan shockwave torus')

# ==============================  HI-HAT  ===================================
# 30 instanced bright spark particles
# ---------------------------------------------------------------------------
hh_geo = base.create(geometryCOMP, 'hihat_geo')
hh_geo.nodeX = 600
hh_geo.nodeY = 0

hh_sphere = hh_geo.create(sphereSOP, 'spark')
hh_sphere.par.radius = 0.02
hh_sphere.par.rows = 8
hh_sphere.par.cols = 8

# Instance positions via tab-separated DAT (table format: header + rows)
hh_script = base.create(scriptCHOP, 'hihat_instances')
hh_script.nodeX = 600
hh_script.nodeY = 150
hh_dat = base.create(tableDAT, 'hihat_instance_dat')
hh_dat.nodeX = 600
hh_dat.nodeY = 250
import math
hh_dat.clear()
hh_dat.appendRow(['tx', 'ty', 'tz'])
for i in range(30):
    a = i * 2.399  # golden angle
    r = 0.3 + (i / 30.0) * 1.2
    x = math.cos(a) * r
    y = math.sin(a * 0.7) * 0.5
    z = math.sin(a) * r
    hh_dat.appendRow([f'{x:.3f}', f'{y:.3f}', f'{z:.3f}'])

# Wire instancing: read positions from the table DAT
hh_geo.par.instancing = True
if hasattr(hh_geo.par, 'instanceop'):
    hh_geo.par.instanceop = hh_dat.path
if hasattr(hh_geo.par, 'instancetx'):
    hh_geo.par.instancetx = 'tx'
    hh_geo.par.instancety = 'ty'
    hh_geo.par.instancetz = 'tz'

# Script CHOP callbacks DAT — drives per-spark velocity reactivity
hh_script_cb = base.create(textDAT, 'hihat_instances_callbacks')
hh_script_cb.nodeX = 800
hh_script_cb.nodeY = 150
hh_script_cb.text = '''# Script CHOP callbacks for hihat_instances
# Generates 30 channels of per-spark "twinkle" amplitude.

import math

def onSetupParameters(scriptOp):
    return

def onPulse(par):
    return

def onCook(scriptOp):
    scriptOp.clear()
    n = 30
    t = absTime.seconds
    activity = 0.0
    activity_chop = op('activity_drums')
    if activity_chop is not None and activity_chop.numChans > 0:
        activity = float(activity_chop[0])
    for i in range(n):
        chan = scriptOp.appendChan(f'spark{i}')
        phase = i * 2.399 + t * 4.0
        chan[0] = (0.5 + 0.5 * math.sin(phase)) * (0.2 + activity)
    scriptOp.numSamples = 1
    scriptOp.rate = me.time.rate
    return
'''
if hasattr(hh_script.par, 'callbacks'):
    hh_script.par.callbacks = hh_script_cb.path
elif hasattr(hh_script.par, 'dat'):
    hh_script.par.dat = hh_script_cb.path
print('[Part 2] Hi-hat — 30 spark particles + callback DAT')

# ==============================  BASS  =====================================
# Noise-displaced sphere, deep blue/purple, bioluminescent glow
# ---------------------------------------------------------------------------
bass_geo = base.create(geometryCOMP, 'bass_geo')
bass_geo.nodeX = 0
bass_geo.nodeY = -300

bass_sphere = bass_geo.create(sphereSOP, 'sphere')
bass_sphere.par.rows = 64
bass_sphere.par.cols = 64
bass_sphere.par.radius = 0.8

bass_frag = '''
uniform float uActivity;
uniform float uTime;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; float disp; } iVert;
void main(){
    float rim = pow(1.0-abs(dot(normalize(iVert.wN),normalize(-iVert.wP))),2.5);
    vec3 deep = vec3(0.02, 0.01, 0.12);
    vec3 glow = vec3(0.1, 0.2, 0.9);
    vec3 bio  = vec3(0.0, 0.6, 0.8);
    vec3 col = mix(deep, glow, uActivity * 0.7);
    col += bio * rim * (0.5 + uActivity * 1.5);
    col += vec3(0.3, 0.1, 0.8) * iVert.disp * uActivity;
    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
'''
bass_vert = '''
uniform float uActivity;
uniform float uTime;
out Vert { vec3 wN; vec3 wP; float disp; } oVert;
// Simple 3D noise
float bassHash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5); }
float bassNoise(vec3 p){
    vec3 ip=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(bassHash(ip),bassHash(ip+vec3(1,0,0)),f.x),
               mix(bassHash(ip+vec3(0,1,0)),bassHash(ip+vec3(1,1,0)),f.x),f.y),
           mix(mix(bassHash(ip+vec3(0,0,1)),bassHash(ip+vec3(1,0,1)),f.x),
               mix(bassHash(ip+vec3(0,1,1)),bassHash(ip+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float n = bassNoise(P * 3.0 + uTime * 0.3) * 0.3 * (0.3 + uActivity);
    vec3 pos = P + N * n;
    oVert.wN = N;
    oVert.wP = pos;
    oVert.disp = n;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
bass_mat = make_glsl_mat(base, 'bass_mat', bass_vert, bass_frag, 0, -400)
bass_geo.par.material = bass_mat.path
print('[Part 2] Bass — bioluminescent noise sphere')

# ==============================  MELODY  ===================================
# 50 gold instanced particles in arcing noise paths
# ---------------------------------------------------------------------------
mel_geo = base.create(geometryCOMP, 'melody_geo')
mel_geo.nodeX = 300
mel_geo.nodeY = -300

mel_sph = mel_geo.create(sphereSOP, 'particle')
mel_sph.par.radius = 0.025
mel_sph.par.rows = 8
mel_sph.par.cols = 8

mel_dat = base.create(tableDAT, 'melody_instance_dat')
mel_dat.nodeX = 300
mel_dat.nodeY = -150
mel_dat.clear()
mel_dat.appendRow(['tx', 'ty', 'tz'])
for i in range(50):
    t = i / 50.0 * math.pi * 4
    r = 0.5 + i / 50.0 * 2.0
    x = math.cos(t) * r
    y = math.sin(t * 1.3) * 0.8 + math.cos(i * 0.5) * 0.3
    z = math.sin(t) * r
    mel_dat.appendRow([f'{x:.3f}', f'{y:.3f}', f'{z:.3f}'])

mel_geo.par.instancing = True
if hasattr(mel_geo.par, 'instanceop'):
    mel_geo.par.instanceop = mel_dat.path
if hasattr(mel_geo.par, 'instancetx'):
    mel_geo.par.instancetx = 'tx'
    mel_geo.par.instancety = 'ty'
    mel_geo.par.instancetz = 'tz'

mel_frag_code = '''
uniform float uActivity;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; } iVert;
void main(){
    float rim = pow(1.0-abs(dot(normalize(iVert.wN),normalize(-iVert.wP))),2.0);
    vec3 gold = vec3(1.0, 0.85, 0.3);
    vec3 white = vec3(1.0, 0.95, 0.8);
    vec3 col = mix(gold * 0.3, white, uActivity * 0.6 + rim * 0.8);
    col += gold * rim * uActivity * 2.0;
    fragColor = TDOutputSwizzle(vec4(col, 0.6 + uActivity * 0.4));
}
'''
mel_vert_code = '''
out Vert { vec3 wN; vec3 wP; } oVert;
void main(){
    oVert.wN = N;
    oVert.wP = P;
    gl_Position = TDWorldToProj(TDDeform(P));
}
'''
mel_mat = make_glsl_mat(base, 'melody_mat', mel_vert_code, mel_frag_code,
                        300, -400)
mel_geo.par.material = mel_mat.path
print('[Part 2] Melody — 50 gold arc particles')

# ==============================  PADS  =====================================
# 3 layered translucent teal/violet nebula planes
# ---------------------------------------------------------------------------
pad_frag = '''
uniform float uActivity;
uniform float uTime;
uniform float uLayer;
out vec4 fragColor;
in Vert { vec2 uv; } iVert;
float padHash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5); }
float padNoise(vec2 p){
    vec2 ip=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(padHash(ip),padHash(ip+vec2(1,0)),f.x),
               mix(padHash(ip+vec2(0,1)),padHash(ip+vec2(1,1)),f.x),f.y);
}
float fbm(vec2 p){
    float v = 0.0;
    float a = 0.5;
    for(int k=0; k<5; k++){
        v += a * padNoise(p);
        p *= 2.01;
        a *= 0.5;
    }
    return v;
}
void main(){
    vec2 uv = iVert.uv * 3.0 + uLayer * 1.5;
    float n = fbm(uv + uTime * 0.08 + uLayer);
    vec3 teal = vec3(0.0, 0.5, 0.5);
    vec3 violet = vec3(0.4, 0.1, 0.6);
    vec3 col = mix(teal, violet, n + uLayer * 0.2);
    col *= 0.4 + uActivity * 0.8;
    float alpha = n * (0.15 + uActivity * 0.25);
    fragColor = TDOutputSwizzle(vec4(col, alpha));
}
'''
pad_vert = '''
out Vert { vec2 uv; } oVert;
void main(){
    oVert.uv = uv[0].st;
    gl_Position = TDWorldToProj(TDDeform(P));
}
'''
for layer in range(3):
    pname = f'pad_geo_{layer}'
    pg = base.create(geometryCOMP, pname)
    pg.nodeX = 600
    pg.nodeY = -300 - layer * 120
    rect = pg.create(rectangleSOP, 'plane')
    rect.par.sizex = 6
    rect.par.sizey = 6
    pm = make_glsl_mat(base, f'pad_mat_{layer}', pad_vert, pad_frag,
                       600, -400 - layer * 120)
    pg.par.material = pm.path

print('[Part 2] Pads — 3 nebula planes')

# ==============================  LEAD  =====================================
# Noise-displaced tube ribbon, white/gold with sway
# ---------------------------------------------------------------------------
lead_geo = base.create(geometryCOMP, 'lead_geo')
lead_geo.nodeX = 900
lead_geo.nodeY = 0

lead_tube = lead_geo.create(tubeSOP, 'ribbon')
lead_tube.par.rows = 80
lead_tube.par.cols = 12
lead_tube.par.radius1 = 0.06
lead_tube.par.radius2 = 0.06
lead_tube.par.height = 4

lead_frag = '''
uniform float uActivity;
uniform float uTime;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; } iVert;
void main(){
    float rim = pow(1.0-abs(dot(normalize(iVert.wN),normalize(-iVert.wP))),2.0);
    vec3 white = vec3(0.95, 0.93, 0.88);
    vec3 gold = vec3(1.0, 0.85, 0.4);
    vec3 col = mix(white, gold, rim * 0.6 + uActivity * 0.3);
    col += vec3(1.0,0.9,0.7) * rim * uActivity * 2.5;
    fragColor = TDOutputSwizzle(vec4(col, 0.7 + uActivity * 0.3));
}
'''
lead_vert = '''
uniform float uActivity;
uniform float uTime;
out Vert { vec3 wN; vec3 wP; } oVert;
float leadHash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5); }
float leadNoise(vec3 p){
    vec3 ip=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(leadHash(ip),leadHash(ip+vec3(1,0,0)),f.x),
               mix(leadHash(ip+vec3(0,1,0)),leadHash(ip+vec3(1,1,0)),f.x),f.y),
           mix(mix(leadHash(ip+vec3(0,0,1)),leadHash(ip+vec3(1,0,1)),f.x),
               mix(leadHash(ip+vec3(0,1,1)),leadHash(ip+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float sway = leadNoise(P * 2.0 + uTime * 0.5) * 0.3 * (0.4 + uActivity);
    vec3 pos = P + N * sway;
    oVert.wN = N;
    oVert.wP = pos;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
lead_mat = make_glsl_mat(base, 'lead_mat', lead_vert, lead_frag, 900, -100)
lead_geo.par.material = lead_mat.path
print('[Part 2] Lead — noise ribbon')

# ==============================  STARS  ====================================
# 200 instanced background particles
# ---------------------------------------------------------------------------
star_geo = base.create(geometryCOMP, 'stars_geo')
star_geo.nodeX = 900
star_geo.nodeY = -300

star_sph = star_geo.create(sphereSOP, 'star')
star_sph.par.radius = 0.012
star_sph.par.rows = 6
star_sph.par.cols = 6

star_dat = base.create(tableDAT, 'stars_instance_dat')
star_dat.nodeX = 900
star_dat.nodeY = -200
import random
star_dat.clear()
star_dat.appendRow(['tx', 'ty', 'tz'])
rng = random.Random(42)
for i in range(200):
    x = (rng.random() - 0.5) * 12
    y = (rng.random() - 0.5) * 8
    z = (rng.random() - 0.5) * 12
    star_dat.appendRow([f'{x:.3f}', f'{y:.3f}', f'{z:.3f}'])

star_geo.par.instancing = True
if hasattr(star_geo.par, 'instanceop'):
    star_geo.par.instanceop = star_dat.path
if hasattr(star_geo.par, 'instancetx'):
    star_geo.par.instancetx = 'tx'
    star_geo.par.instancety = 'ty'
    star_geo.par.instancetz = 'tz'

star_mat = base.create(constantMAT, 'star_mat')
star_mat.nodeX = 900
star_mat.nodeY = -400
star_mat.par.colorr = 0.9
star_mat.par.colorg = 0.9
star_mat.par.colorb = 0.95
star_mat.par.alpha = 0.6
star_geo.par.material = star_mat.path
print('[Part 2] Stars — 200 background particles')

# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 2 COMPLETE — Visual Generators')
print('=' * 60)
print(' Next: Paste synesthesia_part3_scene.py')
print('=' * 60)
