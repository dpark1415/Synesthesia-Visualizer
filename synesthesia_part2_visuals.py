# ============================================================================
# SYNESTHESIA VISUALIZER - Part 2: Visual generators
# ----------------------------------------------------------------------------
# Paste AFTER Part 1. For each instrument it creates a Geometry COMP holding
# one simple SOP, plus a Phong MAT whose color and emission are driven by
# the matching activity_<name> CHOP via parameter expressions.
#
# No GLSL, no instancing, no textures. Five geometry COMPs, five materials.
# Re-running is safe: existing nodes with the same name are destroyed first.
# ============================================================================

BASE_PATH = '/project1/synesthesia'
base = op(BASE_PATH)
if not base:
    raise RuntimeError('Run Part 1 first - container missing at ' + BASE_PATH)


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
    """Destroy any existing child of `base` with this name, then create fresh."""
    existing = base.op(name)
    if existing:
        existing.destroy()
    return base.create(typ, name)


def expr_set(par, expression):
    par.expr = expression
    par.mode = ParMode.EXPRESSION


# ---------------------------------------------------------------------------
# Visual definitions
#   instrument, SOP type, base color (r,g,b), world position (x,y,z),
#   pulse amount (extra scale at full activity)
# ---------------------------------------------------------------------------
VISUALS = [
    ('drums',  sphereSOP, (1.00, 0.20, 0.10), ( 0.0,  0.0,  0.0), 0.80),
    ('bass',   sphereSOP, (0.20, 0.30, 1.00), (-2.6,  0.0,  0.0), 0.60),
    ('melody', torusSOP,  (1.00, 0.85, 0.30), ( 2.6,  0.0,  0.0), 0.50),
    ('pads',   boxSOP,    (0.20, 0.80, 0.70), ( 0.0,  1.6, -1.2), 0.40),
    ('lead',   tubeSOP,   (0.95, 0.95, 0.85), ( 0.0, -1.6, -1.2), 0.50),
]


for i, (name, sop_type, color, pos, pulse) in enumerate(VISUALS):
    # ---- Geometry COMP ----------------------------------------------------
    geo = replace(geometryCOMP, name + '_geo')
    geo.nodeX = i * 200
    geo.nodeY = 0
    setpar(geo, 'tx', pos[0])
    setpar(geo, 'ty', pos[1])
    setpar(geo, 'tz', pos[2])

    # Pulse uniform scale from the activity CHOP
    activity_path = "%s/activity_%s" % (BASE_PATH, name)
    scale_expr = "1.0 + op('%s')['%s'] * %s" % (activity_path, name, pulse)
    expr_set(geo.par.sx, scale_expr)
    expr_set(geo.par.sy, scale_expr)
    expr_set(geo.par.sz, scale_expr)

    # New geometryCOMPs ship with a default torus + Geo Out; clear them so
    # only our shape renders.
    for child in list(geo.children):
        try:
            child.destroy()
        except Exception:
            pass

    sop = geo.create(sop_type, 'shape')
    # Tame the default sizes so all five shapes share a similar footprint.
    if sop_type is sphereSOP:
        setpar(sop, 'radius', 0.5)
        setpar(sop, 'rows', 32)
        setpar(sop, 'cols', 32)
    elif sop_type is torusSOP:
        setpar(sop, 'radius1', 0.6)
        setpar(sop, 'radius2', 0.18)
        setpar(sop, 'rows', 32)
        setpar(sop, 'cols', 32)
    elif sop_type is boxSOP:
        setpar(sop, 'sizex', 0.9)
        setpar(sop, 'sizey', 0.9)
        setpar(sop, 'sizez', 0.9)
    elif sop_type is tubeSOP:
        setpar(sop, 'radius1', 0.18)
        setpar(sop, 'radius2', 0.18)
        setpar(sop, 'height', 1.4)
        setpar(sop, 'rows', 16)
        setpar(sop, 'cols', 24)

    # ---- Phong MAT --------------------------------------------------------
    mat = replace(phongMAT, name + '_mat')
    mat.nodeX = i * 200
    mat.nodeY = -180
    setpar(mat, 'diffr', color[0])
    setpar(mat, 'diffg', color[1])
    setpar(mat, 'diffb', color[2])
    setpar(mat, 'specr', 0.6)
    setpar(mat, 'specg', 0.6)
    setpar(mat, 'specb', 0.6)
    setpar(mat, 'shininess', 60)

    # Emission tracks activity so the shape glows on hits
    glow = "op('%s')['%s']" % (activity_path, name)
    expr_set(mat.par.emitr, "%s * %s" % (color[0], glow))
    expr_set(mat.par.emitg, "%s * %s" % (color[1], glow))
    expr_set(mat.par.emitb, "%s * %s" % (color[2], glow))

    setpar(geo, 'material', mat.path)
    print('[Part 2] %s_geo + %s_mat' % (name, name))


print('')
print('============================================================')
print(' PART 2 COMPLETE - 5 instrument visuals built')
print(' Next: paste Part 3.')
print('============================================================')
