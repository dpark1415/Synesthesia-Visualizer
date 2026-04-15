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
    """Create a GLSL MAT with inline vertex + fragment shaders."""
    g = parent.create(glslMAT, name)
    g.nodeX = x
    g.nodeY = y
    # Write shader code into DATs
    v_dat = parent.create(textDAT, name + '_vert')
    v_dat.text = vert
    v_dat.nodeX = x - 150
    v_dat.nodeY = y
    f_dat = parent.create(textDAT, name + '_frag')
    f_dat.text = frag
    f_dat.nodeX = x - 150
    f_dat.nodeY = y - 80
    g.par.glslvertex = v_dat.path
    g.par.glslpixel = f_dat.path
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
    fragColor = vec4(col, 1.0);
}
'''
kick_vert = '''
uniform float uActivity;
in vec3 P; in vec3 N;
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
in Vert { vec3 wN; vec3 wP; } i;
void main(){
    float rim = pow(1.0-abs(dot(normalize(i.wN),normalize(-i.wP))),3.0);
    float pulse = uActivity;
    vec3 col = mix(vec3(0.0,0.15,0.2), vec3(0.0,0.9,1.0), pulse);
    col += vec3(0.3,1.0,1.0) * rim * pulse * 3.0;
    float alpha = mix(0.1, 0.95, pulse) + rim * 0.5;
    fragColor = vec4(col, clamp(alpha,0.0,1.0));
}
'''
snare_vert = '''
uniform float uActivity;
in vec3 P; in vec3 N;
out Vert { vec3 wN; vec3 wP; } o;
void main(){
    vec3 pos = P * (1.0 + uActivity * 0.6);
    o.wN = N; o.wP = pos;
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

# Instance positions via noise DAT
hh_script = base.create(scriptCHOP, 'hihat_instances')
hh_script.nodeX = 600
hh_script.nodeY = 150
hh_dat = base.create(textDAT, 'hihat_instance_dat')
hh_dat.nodeX = 600
hh_dat.nodeY = 250
lines = ['tx\tty\ttz']
import math
for i in range(30):
    a = i * 2.399  # golden angle
    r = 0.3 + (i / 30.0) * 1.2
    x = math.cos(a) * r
    y = math.sin(a * 0.7) * 0.5
    z = math.sin(a) * r
    lines.append(f'{x:.3f}\t{y:.3f}\t{z:.3f}')
hh_dat.text = '\n'.join(lines)

hh_geo.par.instancing = True
hh_geo.par.instancechop = ''  # will read from DAT via CHOP
print('[Part 2] Hi-hat — 30 spark particles')

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
in Vert { vec3 wN; vec3 wP; float disp; } i;
void main(){
    float rim = pow(1.0-abs(dot(normalize(i.wN),normalize(-i.wP))),2.5);
    vec3 deep = vec3(0.02, 0.01, 0.12);
    vec3 glow = vec3(0.1, 0.2, 0.9);
    vec3 bio  = vec3(0.0, 0.6, 0.8);
    vec3 col = mix(deep, glow, uActivity * 0.7);
    col += bio * rim * (0.5 + uActivity * 1.5);
    col += vec3(0.3, 0.1, 0.8) * i.disp * uActivity;
    fragColor = vec4(col, 1.0);
}
'''
bass_vert = '''
uniform float uActivity;
uniform float uTime;
in vec3 P; in vec3 N;
out Vert { vec3 wN; vec3 wP; float disp; } o;
// Simple 3D noise
float hash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5); }
float noise3(vec3 p){
    vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),
               mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
           mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),
               mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float n = noise3(P * 3.0 + uTime * 0.3) * 0.3 * (0.3 + uActivity);
    vec3 pos = P + N * n;
    o.wN = N; o.wP = pos; o.disp = n;
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

mel_dat = base.create(textDAT, 'melody_instance_dat')
mel_dat.nodeX = 300
mel_dat.nodeY = -150
mlines = ['tx\tty\ttz']
for i in range(50):
    t = i / 50.0 * math.pi * 4
    r = 0.5 + i / 50.0 * 2.0
    x = math.cos(t) * r
    y = math.sin(t * 1.3) * 0.8 + math.cos(i * 0.5) * 0.3
    z = math.sin(t) * r
    mlines.append(f'{x:.3f}\t{y:.3f}\t{z:.3f}')
mel_dat.text = '\n'.join(mlines)

mel_geo.par.instancing = True

mel_frag_code = '''
uniform float uActivity;
out vec4 fragColor;
in Vert { vec3 wN; vec3 wP; } i;
void main(){
    float rim = pow(1.0-abs(dot(normalize(i.wN),normalize(-i.wP))),2.0);
    vec3 gold = vec3(1.0, 0.85, 0.3);
    vec3 white = vec3(1.0, 0.95, 0.8);
    vec3 col = mix(gold * 0.3, white, uActivity * 0.6 + rim * 0.8);
    col += gold * rim * uActivity * 2.0;
    fragColor = vec4(col, 0.6 + uActivity * 0.4);
}
'''
mel_mat = make_glsl_mat(base, 'melody_mat',
    'in vec3 P; in vec3 N;\n'
    'out Vert { vec3 wN; vec3 wP; } o;\n'
    'void main(){ o.wN=N; o.wP=P;\n'
    '  gl_Position=TDWorldToProj(TDDeform(P)); }',
    mel_frag_code, 300, -400)
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
in Vert { vec2 uv; } i;
float hash2(vec2 p){ return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5); }
float noise2(vec2 p){
    vec2 i2=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(hash2(i2),hash2(i2+vec2(1,0)),f.x),
               mix(hash2(i2+vec2(0,1)),hash2(i2+vec2(1,1)),f.x),f.y);
}
float fbm(vec2 p){ float v=0.0,a=0.5;
    for(int i=0;i<5;i++){ v+=a*noise2(p); p*=2.01; a*=0.5; } return v; }
void main(){
    vec2 uv = i.uv * 3.0 + uLayer * 1.5;
    float n = fbm(uv + uTime * 0.08 + uLayer);
    vec3 teal = vec3(0.0, 0.5, 0.5);
    vec3 violet = vec3(0.4, 0.1, 0.6);
    vec3 col = mix(teal, violet, n + uLayer * 0.2);
    col *= 0.4 + uActivity * 0.8;
    float alpha = n * (0.15 + uActivity * 0.25);
    fragColor = vec4(col, alpha);
}
'''
pad_vert = '''
in vec3 P; in vec2 uv0;
out Vert { vec2 uv; } o;
void main(){ o.uv = uv0;
  gl_Position = TDWorldToProj(TDDeform(P)); }
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
in Vert { vec3 wN; vec3 wP; } i;
void main(){
    float rim = pow(1.0-abs(dot(normalize(i.wN),normalize(-i.wP))),2.0);
    vec3 white = vec3(0.95, 0.93, 0.88);
    vec3 gold = vec3(1.0, 0.85, 0.4);
    vec3 col = mix(white, gold, rim * 0.6 + uActivity * 0.3);
    col += vec3(1.0,0.9,0.7) * rim * uActivity * 2.5;
    fragColor = vec4(col, 0.7 + uActivity * 0.3);
}
'''
lead_vert = '''
uniform float uActivity;
uniform float uTime;
in vec3 P; in vec3 N;
out Vert { vec3 wN; vec3 wP; } o;
float hash(vec3 p){ return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5); }
float noise3(vec3 p){
    vec3 i=floor(p), f=fract(p); f=f*f*(3.0-2.0*f);
    return mix(mix(mix(hash(i),hash(i+vec3(1,0,0)),f.x),
               mix(hash(i+vec3(0,1,0)),hash(i+vec3(1,1,0)),f.x),f.y),
           mix(mix(hash(i+vec3(0,0,1)),hash(i+vec3(1,0,1)),f.x),
               mix(hash(i+vec3(0,1,1)),hash(i+vec3(1,1,1)),f.x),f.y),f.z);
}
void main(){
    float sway = noise3(P * 2.0 + uTime * 0.5) * 0.3 * (0.4 + uActivity);
    vec3 pos = P + N * sway;
    o.wN = N; o.wP = pos;
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

star_dat = base.create(textDAT, 'stars_instance_dat')
star_dat.nodeX = 900
star_dat.nodeY = -200
slines = ['tx\tty\ttz']
import random
random.seed(42)
for i in range(200):
    x = (random.random() - 0.5) * 12
    y = (random.random() - 0.5) * 8
    z = (random.random() - 0.5) * 12
    slines.append(f'{x:.3f}\t{y:.3f}\t{z:.3f}')
star_dat.text = '\n'.join(slines)

star_geo.par.instancing = True

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
