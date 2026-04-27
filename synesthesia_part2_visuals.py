# ============================================================================
# SYNESTHESIA VISUALIZER - Part 2: Visual Generators
# ============================================================================
# Paste this AFTER Part 1. It builds geometry, materials, and shaders
# for every instrument inside /project1/synesthesia.
# ============================================================================

import math
import random

BASE = '/project1/synesthesia'
base = op(BASE)
if not base:
    raise RuntimeError('Run Part 1 first - container not found at ' + BASE)

# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------
def _set_glsl_dat(mat, vert_dat, pix_dat):
    """Point a GLSL MAT at vertex/pixel shader DATs across TD versions."""
    vert_names = ('vert', 'vertdat', 'vertexshader', 'glslvert', 'vertex')
    pix_names  = ('pixel', 'pixeldat', 'pixelshader', 'glslpixel', 'frag',
                  'fragdat', 'fragmentshader')
    for vp in vert_names:
        if hasattr(mat.par, vp):
            try:
                setattr(mat.par, vp, vert_dat.path)
                break
            except Exception:
                continue
    for fp in pix_names:
        if hasattr(mat.par, fp):
            try:
                setattr(mat.par, fp, pix_dat.path)
                break
            except Exception:
                continue


def bind_float(mat, slot, name, expr):
    """Bind a float (.x of a vec4) uniform on a GLSL MAT's Vectors page.

    GLSL MAT exposes 8 vector uniform slots named value0..value7. Each slot
    has a name parameter (value{i}name) and four float components
    (value{i}x..w). Setting an expression on .x makes the uniform live-track
    the expression on every cook - which is how MIDI activity reaches the
    shader.
    """
    name_par = getattr(mat.par, f'value{slot}name', None)
    x_par    = getattr(mat.par, f'value{slot}x',    None)
    if name_par is None or x_par is None:
        # Older TD builds might call them const0name / const0value etc.
        name_par = getattr(mat.par, f'const{slot}name', None)
        x_par    = getattr(mat.par, f'const{slot}value', None)
    if name_par is None or x_par is None:
        return False
    try:
        name_par.val = name
    except Exception:
        try:
            setattr(mat.par, name_par.name, name)
        except Exception:
            pass
    try:
        x_par.expr = expr
        x_par.mode = ParMode.EXPRESSION
    except Exception:
        try:
            x_par.expr = expr
        except Exception:
            return False
    return True


def make_glsl_mat(parent, name, vert, frag, x, y,
                  activity_chop=None, extra_uniforms=None):
    """Create a GLSL MAT with inline vertex+fragment shaders and bind the
    standard uActivity / uTime uniforms.

    activity_chop: name (relative to parent) of a CHOP whose first channel
                   is the instrument's 0..1 activity. Bound to uActivity.
    extra_uniforms: optional list of (name, expression) tuples for extra
                    float uniforms starting at slot 2.
    """
    g = parent.create(glslMAT, name)
    g.nodeX = x
    g.nodeY = y
    v_dat = parent.create(textDAT, name + '_vertex')
    v_dat.text = vert
    v_dat.nodeX = x - 200
    v_dat.nodeY = y
    f_dat = parent.create(textDAT, name + '_pixel')
    f_dat.text = frag
    f_dat.nodeX = x - 200
    f_dat.nodeY = y - 80
    _set_glsl_dat(g, v_dat, f_dat)

    if activity_chop:
        bind_float(g, 0, 'uActivity', f"op('{activity_chop}')[0] "
                                       f"if op('{activity_chop}') and "
                                       f"op('{activity_chop}').numChans "
                                       f"else 0.0")
    bind_float(g, 1, 'uTime', 'absTime.seconds')
    if extra_uniforms:
        for i, (uname, uexpr) in enumerate(extra_uniforms):
            bind_float(g, 2 + i, uname, uexpr)
    return g

# ==============================  KICK DRUM  ================================
# Red pressure sphere - blooms on hit with smooth decay
# ---------------------------------------------------------------------------
kick_geo = base.create(geometryCOMP, 'kick_geo')
kick_geo.nodeX = 0
kick_geo.nodeY = 0

kick_sphere = kick_geo.create(sphereSOP, 'sphere')
kick_sphere.par.rows = 48
kick_sphere.par.cols = 48
kick_sphere.par.radius = 0.5

kick_frag = '''uniform float uActivity;
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
kick_vert = '''uniform float uActivity;
out Vert { vec3 worldNorm; vec3 worldPos; } oVert;
void main(){
    vec4 wp = TDDeform(P);
    vec3 pos = P * (1.0 + uActivity * 0.35);
    oVert.worldNorm = TDDeformNorm(N);
    oVert.worldPos = (TDDeform(pos)).xyz;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
kick_mat = make_glsl_mat(base, 'kick_mat', kick_vert, kick_frag,
                         0, -100, activity_chop='activity_drums')
kick_geo.par.material = kick_mat.path
print('[Part 2] Kick drum - red pressure sphere')

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

snare_frag = '''uniform float uActivity;
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
snare_vert = '''uniform float uActivity;
out Vert { vec3 wN; vec3 wP; } oVert;
void main(){
    vec3 pos = P * (1.0 + uActivity * 0.6);
    oVert.wN = TDDeformNorm(N);
    oVert.wP = (TDDeform(pos)).xyz;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
snare_mat = make_glsl_mat(base, 'snare_mat', snare_vert, snare_frag,
                          300, -100, activity_chop='activity_drums')
snare_geo.par.material = snare_mat.path
print('[Part 2] Snare - cyan shockwave torus')

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

# Static instance positions in a tab DAT (golden-spiral cloud).
hh_dat = base.create(tableDAT, 'hihat_instance_dat')
hh_dat.nodeX = 600
hh_dat.nodeY = 250
hh_dat.clear()
hh_dat.appendRow(['tx', 'ty', 'tz'])
for i in range(30):
    a = i * 2.399
    r = 0.3 + (i / 30.0) * 1.2
    x = math.cos(a) * r
    y = math.sin(a * 0.7) * 0.5
    z = math.sin(a) * r
    hh_dat.appendRow([f'{x:.3f}', f'{y:.3f}', f'{z:.3f}'])

# Wire instancing on the geo COMP to read positions from the table DAT.
hh_geo.par.instancing = True
for pname in ('instanceop', 'instanceopdat', 'instanceCHOPDAT'):
    if hasattr(hh_geo.par, pname):
        try:
            setattr(hh_geo.par, pname, hh_dat.path)
            break
        except Exception:
            continue
for ax_par, ax_col in (('instancetx', 'tx'),
                        ('instancety', 'ty'),
                        ('instancetz', 'tz')):
    if hasattr(hh_geo.par, ax_par):
        try:
            setattr(hh_geo.par, ax_par, ax_col)
        except Exception:
            pass

# Brightness reacts to the drum activity via the same uniform pattern as
# the geometry shaders, so we don't need a Script CHOP at all.
hh_frag = '''uniform float uActivity;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; } iVert;
void main(){
    float rim = pow(1.0-abs(dot(normalize(iVert.wN),normalize(-iVert.wP))),1.5);
    vec3 hot = vec3(1.0, 0.95, 0.7);
    vec3 dim = vec3(0.15, 0.12, 0.08);
    vec3 col = mix(dim, hot, 0.3 + uActivity * 0.7 + rim * 0.4);
    col += hot * uActivity * 1.5;
    fragColor = TDOutputSwizzle(vec4(col, 0.6 + uActivity * 0.4));
}
'''
hh_vert = '''uniform float uActivity;
out Vert { vec3 wN; vec3 wP; } oVert;
void main(){
    vec3 pos = P * (1.0 + uActivity * 0.4);
    oVert.wN = TDDeformNorm(N);
    oVert.wP = (TDDeform(pos)).xyz;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
hh_mat = make_glsl_mat(base, 'hihat_mat', hh_vert, hh_frag,
                       600, -100, activity_chop='activity_drums')
hh_geo.par.material = hh_mat.path
print('[Part 2] Hi-hat - 30 spark particles')

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

bass_frag = '''uniform float uActivity;
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
bass_vert = '''uniform float uActivity;
uniform float uTime;
out Vert { vec3 wN; vec3 wP; float disp; } oVert;
float bassHash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453); }
float bassNoise(vec3 p){
    vec3 ip=floor(p); vec3 f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(bassHash(ip),bassHash(ip+vec3(1,0,0)),f.x),
               mix(bassHash(ip+vec3(0,1,0)),bassHash(ip+vec3(1,1,0)),f.x),f.y),
           mix(mix(bassHash(ip+vec3(0,0,1)),bassHash(ip+vec3(1,0,1)),f.x),
               mix(bassHash(ip+vec3(0,1,1)),bassHash(ip+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float n = bassNoise(P.xyz * 3.0 + uTime * 0.3) * 0.3 * (0.3 + uActivity);
    vec3 pos = P.xyz + N * n;
    oVert.wN = TDDeformNorm(N);
    oVert.wP = (TDDeform(pos)).xyz;
    oVert.disp = n;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
bass_mat = make_glsl_mat(base, 'bass_mat', bass_vert, bass_frag,
                         0, -400, activity_chop='activity_bass')
bass_geo.par.material = bass_mat.path
print('[Part 2] Bass - bioluminescent noise sphere')

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
for pname in ('instanceop', 'instanceopdat', 'instanceCHOPDAT'):
    if hasattr(mel_geo.par, pname):
        try:
            setattr(mel_geo.par, pname, mel_dat.path)
            break
        except Exception:
            continue
for ax_par, ax_col in (('instancetx', 'tx'),
                        ('instancety', 'ty'),
                        ('instancetz', 'tz')):
    if hasattr(mel_geo.par, ax_par):
        try:
            setattr(mel_geo.par, ax_par, ax_col)
        except Exception:
            pass

mel_frag = '''uniform float uActivity;
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
mel_vert = '''uniform float uActivity;
out Vert { vec3 wN; vec3 wP; } oVert;
void main(){
    oVert.wN = TDDeformNorm(N);
    oVert.wP = (TDDeform(P)).xyz;
    gl_Position = TDWorldToProj(TDDeform(P));
}
'''
mel_mat = make_glsl_mat(base, 'melody_mat', mel_vert, mel_frag,
                        300, -400, activity_chop='activity_melody')
mel_geo.par.material = mel_mat.path
print('[Part 2] Melody - 50 gold arc particles')

# ==============================  PADS  =====================================
# 3 layered translucent teal/violet nebula planes
# ---------------------------------------------------------------------------
pad_frag = '''uniform float uActivity;
uniform float uTime;
uniform float uLayer;
out vec4 fragColor;
in Vert { vec2 uv; } iVert;
float padHash(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453); }
float padNoise(vec2 p){
    vec2 ip=floor(p); vec2 f=fract(p); f=f*f*(3.0-2.0*f);
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
pad_vert = '''out Vert { vec2 uv; } oVert;
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
    if hasattr(rect.par, 'sizex'):
        rect.par.sizex = 6
    if hasattr(rect.par, 'sizey'):
        rect.par.sizey = 6
    pm = make_glsl_mat(base, f'pad_mat_{layer}', pad_vert, pad_frag,
                       600, -400 - layer * 120,
                       activity_chop='activity_pads',
                       extra_uniforms=[('uLayer', str(float(layer)))])
    pg.par.material = pm.path

print('[Part 2] Pads - 3 nebula planes')

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

lead_frag = '''uniform float uActivity;
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
lead_vert = '''uniform float uActivity;
uniform float uTime;
out Vert { vec3 wN; vec3 wP; } oVert;
float leadHash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453); }
float leadNoise(vec3 p){
    vec3 ip=floor(p); vec3 f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(leadHash(ip),leadHash(ip+vec3(1,0,0)),f.x),
               mix(leadHash(ip+vec3(0,1,0)),leadHash(ip+vec3(1,1,0)),f.x),f.y),
           mix(mix(leadHash(ip+vec3(0,0,1)),leadHash(ip+vec3(1,0,1)),f.x),
               mix(leadHash(ip+vec3(0,1,1)),leadHash(ip+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float sway = leadNoise(P.xyz * 2.0 + uTime * 0.5) * 0.3 * (0.4 + uActivity);
    vec3 pos = P.xyz + N * sway;
    oVert.wN = TDDeformNorm(N);
    oVert.wP = (TDDeform(pos)).xyz;
    gl_Position = TDWorldToProj(TDDeform(pos));
}
'''
lead_mat = make_glsl_mat(base, 'lead_mat', lead_vert, lead_frag,
                         900, -100, activity_chop='activity_lead')
lead_geo.par.material = lead_mat.path
print('[Part 2] Lead - noise ribbon')

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
star_dat.clear()
star_dat.appendRow(['tx', 'ty', 'tz'])
rng = random.Random(42)
for i in range(200):
    x = (rng.random() - 0.5) * 12
    y = (rng.random() - 0.5) * 8
    z = (rng.random() - 0.5) * 12
    star_dat.appendRow([f'{x:.3f}', f'{y:.3f}', f'{z:.3f}'])

star_geo.par.instancing = True
for pname in ('instanceop', 'instanceopdat', 'instanceCHOPDAT'):
    if hasattr(star_geo.par, pname):
        try:
            setattr(star_geo.par, pname, star_dat.path)
            break
        except Exception:
            continue
for ax_par, ax_col in (('instancetx', 'tx'),
                        ('instancety', 'ty'),
                        ('instancetz', 'tz')):
    if hasattr(star_geo.par, ax_par):
        try:
            setattr(star_geo.par, ax_par, ax_col)
        except Exception:
            pass

star_mat = base.create(constantMAT, 'star_mat')
star_mat.nodeX = 900
star_mat.nodeY = -400
if hasattr(star_mat.par, 'colorr'):
    star_mat.par.colorr = 0.9
    star_mat.par.colorg = 0.9
    star_mat.par.colorb = 0.95
if hasattr(star_mat.par, 'alpha'):
    star_mat.par.alpha = 0.6
star_geo.par.material = star_mat.path
print('[Part 2] Stars - 200 background particles')

# ---------------------------------------------------------------------------
print('')
print('=' * 60)
print(' PART 2 COMPLETE - Visual Generators')
print('=' * 60)
print(' Next: Paste synesthesia_part3_scene.py')
print('=' * 60)
