import math
#!/usr/bin/env python3
"""Draws the example network from the Turtle (no other input).
Positions come from the topology (element + offset), the element shapes from the schematic WKT.
Usage: draw.py <data dir> <out.svg>"""
import sys, glob, re, math, html
import rdflib
from rdflib import RDF, RDFS, Namespace
from rdflib.collection import Collection
ERA = Namespace('http://data.europa.eu/949/'); GSP = Namespace('http://www.opengis.net/ont/geosparql#')
g = rdflib.Graph()
for f in sorted(glob.glob(sys.argv[1] + '/*.ttl')): g.parse(f)
SX, SY, X0, Y0 = 0.52, 2.5, 70, 440
def scr(lon, lat): return (X0 + (lon - 2.90) / 2e-4 * SX, Y0 - (lat - 52.60) / 1.2e-4 * SY)
def loc(x): return str(x).rsplit('/', 1)[-1]
def im(x): return 'nl' if '/example/nl/' in str(x) else 'be'
COL = {'be': '#004494', 'nl': '#c8500a'}
elems = {}
for e in g.subjects(RDF.type, ERA.LinearElement):
    wkt = str(g.value(g.value(e, GSP.hasGeometry), GSP.asWKT))
    pts = [scr(*map(float, p.split())) for p in re.findall(r'-?\d+\.\d+ -?\d+\.\d+', wkt)]
    elems[e] = (pts, float(g.value(e, ERA.lengthOfNetLinearElement)))
def seglens(pts): return [math.dist((a[0] / SX, a[1] / SY), (b[0] / SX, b[1] / SY)) for a, b in zip(pts, pts[1:])]   # lengths in schematic units, as in the WKT
def at(e, off):
    """screen point and unit tangent (origin -> end) at an offset in metres"""
    pts, L = elems[e]; sl = seglens(pts); d = off / L * sum(sl)
    for (a, b), s in zip(zip(pts, pts[1:]), sl):
        if d <= s + 1e-9:
            t = d / s; n = math.dist(a, b); return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t), ((b[0] - a[0]) / n, (b[1] - a[1]) / n)
        d -= s
def sub(e, lo, hi):
    pts, L = elems[e]; sl = seglens(pts); tot = sum(sl); out = [at(e, lo)[0]]; acc = 0
    for p, s in zip(pts[1:], sl):
        acc += s
        if lo / L * tot + 1e-9 < acc < hi / L * tot - 1e-9: out.append(p)
    out.append(at(e, hi)[0]); return out
ends = {}
for r in g.subjects(RDF.type, ERA.NetRelation):
    a, b = g.value(r, ERA.elementA), g.value(r, ERA.elementB)
    ends[(a, b)] = g.value(r, ERA.isOnOriginOfElementA).toPython(); ends[(b, a)] = g.value(r, ERA.isOnOriginOfElementB).toPython()
def pos(npr):
    tc = g.value(npr, ERA.hasTopoCoordinate); return g.value(tc, ERA.onLinearElement), float(g.value(tc, ERA.offsetFromOrigin))
def stretches(ref):
    """polylines covered by a linear or area reference"""
    if (ref, RDF.type, ERA.NetAreaReference) in g:
        return [s for m in Collection(g, g.value(ref, ERA.includes)) for s in stretches(m)]
    seq = list(Collection(g, g.value(ref, ERA.hasSequence)))
    (se, so), (ee, eo) = pos(g.value(ref, ERA.startsAt)), pos(g.value(ref, ERA.endsAt)); out = []
    for i, e in enumerate(seq):
        L = elems[e][1]; lo, hi = 0.0, L
        if len(seq) == 1: lo, hi = sorted((so, eo))
        elif i == 0: lo, hi = (0.0, so) if ends[(e, seq[1])] else (so, L)
        elif i == len(seq) - 1: lo, hi = (0.0, eo) if ends[(e, seq[-2])] else (eo, L)
        out.append(sub(e, lo, hi))
    return out
def path(pts): return 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)
def lab(x): return html.escape(str(g.value(x, RDFS.label) or loc(x)))
o = []; T = lambda x, y, s, c='', a='middle': o.append(f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="{a}" class="{c}">{s}</text>')

# sections of line and operational points as bands under the tracks
SOLC = ['#e9ecef']; OPC = ['#ffe9a8', '#cfe8ff', '#d9f2d0', '#f6d5e5', '#e3d9f7', '#ffd9c2', '#c9ece8']
for s in sorted(g.subjects(RDF.type, ERA.SectionOfLine)):
    for st in stretches(g.value(s, ERA.netReference)): o.append(f'<path d="{path(st)}" class="sol"/>')
opi = 0; oplabels = []
for op in sorted(g.subjects(RDF.type, ERA.OperationalPoint)):
    ref = g.value(op, ERA.netReference); name = f'{lab(op)} ({g.value(op, ERA.uopid)})'
    typ = lab(g.value(op, ERA.opType)) if (g.value(op, ERA.opType), RDFS.label, None) in g else 'type ' + loc(g.value(op, ERA.opType))
    if (ref, RDF.type, ERA.NetAreaReference) in g:
        c = OPC[opi % len(OPC)]; opi += 1; xs = []; ys = []
        for st in stretches(ref):
            o.append(f'<path d="{path(st)}" class="op" stroke="{c}"/>'); xs += [p[0] for p in st]; ys += [p[1] for p in st]
        oplabels.append(((min(xs) + max(xs)) / 2, min(ys), max(ys), name, typ, c))
    else:
        (x, y), _ = at(*pos(ref))
        if im(op) == 'be':
            o.append(f'<line x1="{x:.1f}" y1="100" x2="{x:.1f}" y2="690" class="border"/>')
            T(x, 70, f'border point {g.value(op, ERA.uopid)}, one record per IM', 'opname')
            T(x - 12, 92, 'Infra Alfa (BE)', 'imbe', 'end'); T(x + 12, 92, 'Beta Spoor (NL)', 'imnl', 'start')

# tunnels, level crossings, platform edges
for t in g.subjects(RDF.type, ERA.Tunnel):
    sts = stretches(g.value(t, ERA.netReference))
    for st in sts: o.append(f'<path d="{path(st)}" class="tunnel"/>')
    T(sum(p[0] for st in sts for p in st) / sum(len(st) for st in sts), min(p[1] for st in sts for p in st) - 30, lab(t), 'feat')
for t in g.subjects(RDF.type, ERA.LevelCrossing):
    sts = stretches(g.value(t, ERA.netReference)); xs = [(st[0][0] + st[-1][0]) / 2 for st in sts]; ys = [st[0][1] for st in sts]
    for x, y in zip(xs, ys): o.append(f'<line x1="{x:.1f}" y1="{y-14:.1f}" x2="{x:.1f}" y2="{y+14:.1f}" class="lc"/>')
    T(sum(xs) / len(xs), min(ys) - 30, lab(t), 'feat')
for pe in g.subjects(RDF.type, ERA.PlatformEdge):
    for st in stretches(g.value(pe, ERA.netReference)):
        side = -7 if loc(pe).endswith('1') or 'EGT' in loc(pe) else 7   # platform 3 lies between tracks 3 and 1; Eastgate's on the outside
        st = [(x, y + side) for x, y in st]; o.append(f'<path d="{path(st)}" class="pe"/>')
        lx_ = min(st, key=lambda p: p[0]); T(lx_[0] - 5, lx_[1] + 3, 'pl. ' + str(g.value(pe, ERA.platformId)), 'small', 'end')

# linear elements with their origin -> end arrow
for e, (pts, L) in sorted(elems.items()):
    c = COL[im(e)]; o.append(f'<path d="{path(pts)}" class="le" stroke="{c}"/>')
    sl = seglens(pts); i = sl.index(max(sl)); (ax, ay), (bx, by) = pts[i], pts[i + 1]
    mx, my = (ax + bx) / 2, (ay + by) / 2; n = math.dist(pts[i], pts[i + 1]); ux, uy = (bx - ax) / n, (by - ay) / n
    tri = [(mx + ux * 9, my + uy * 9), (mx - ux * 6 - uy * 6, my - uy * 6 + ux * 6), (mx - ux * 6 + uy * 6, my - uy * 6 - ux * 6)]
    o.append(f'<path d="{path(tri)}Z" fill="{c}"/>')
    ang = math.degrees(math.atan2(by - ay, bx - ax)); ang = ang + 180 if abs(ang) > 90 else ang
    lines = [f'{loc(e)[3:]} · {L:g} m'] if n > 75 else [f'{L:g} m', loc(e)[3:]]   # short elements: two lines
    for j, t in enumerate(lines):
        o.append(f'<text transform="translate({mx:.1f},{my:.1f}) rotate({ang:.1f})" y="{-13 - 11 * (len(lines) - 1 - j)}" text-anchor="middle" class="lelab" fill="{c}">{t}</text>')

# kilometre posts
for kp in g.subjects(RDF.type, ERA.KilometricPost):
    (x, y), (ux, uy) = at(*pos(g.value(kp, ERA.netReference)))
    o.append(f'<line x1="{x:.1f}" y1="{y+4:.1f}" x2="{x:.1f}" y2="{y+15:.1f}" class="kp"/>'); T(x, y + 25, f'km {float(g.value(kp, ERA.kilometer)):g}', 'kpt')

# switches
for s in g.subjects(RDF.type, ERA.Switch):
    (x, y), _ = at(*pos(g.value(s, ERA.netReference)))
    o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" class="sw"/>')
    T(x + 8, y + 17, loc(s)[3:], 'swt', 'start') if im(s) == 'nl' else T(x - 8, y + 17, loc(s)[3:], 'swt', 'end')

# signals: the triangle points in the direction of travel the signal applies to
ORI = 'http://data.europa.eu/949/concepts/orientations/'
for s in g.subjects(RDF.type, ERA.Signal):
    ref = g.value(s, ERA.netReference); (x, y), (ux, uy) = at(*pos(ref))
    if str(g.value(ref, ERA.appliesToDirection)) == ORI + '01': ux, uy = -ux, -uy
    side = loc(g.value(g.value(s, ERA.hasOrientation), ERA.side)); k = -1 if side == 'Left' else 1   # side is relative to the element (origin -> end)
    ex, ey = at(*pos(ref))[1]
    nx, ny = ey * k * -1 * -1, -ex * k * -1; cx, cy = x + nx * 15, y + ny * 15
    tri = [(cx + ux * 8, cy + uy * 8), (cx - ux * 5 - uy * 5, cy - uy * 5 + ux * 5), (cx - ux * 5 + uy * 5, cy - uy * 5 - ux * 5)]
    o.append(f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{cx:.1f}" y2="{cy:.1f}" class="sigl"/><path d="{path(tri)}Z" class="sig"/>')
    T(cx - ux * 4, cy + ny * 13 + 4, str(g.value(s, ERA.signalId)), 'sigt')

# primary locations
# a primary location shares the net reference of its operational point: mark it halfway along the longest stretch
def middle(ref):
    if (ref, RDF.type, ERA.NetPointReference) in g: return at(*pos(ref))[0]
    seg = lambda p: [math.dist(a, b) for a, b in zip(p, p[1:])]
    pts = max(stretches(ref), key=lambda p: sum(seg(p))); d = sum(seg(pts)) / 2
    for a, b, l in zip(pts, pts[1:], seg(pts)):
        if d <= l: t = d / l if l else 0; return a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        d -= l
    return pts[-1]
for pl in g.subjects(RDF.type, ERA.PrimaryLocation):
    x, y = middle(g.value(pl, ERA.netReference))
    o.append(f'<rect x="{x-4:.1f}" y="{y-4:.1f}" width="8" height="8" class="pl" transform="rotate(45 {x:.1f} {y:.1f})"/>')
    T(x, y - 9, 'PLC ' + str(g.value(pl, ERA.primaryLocationCode)), 'plt')

for x, y0, y1, name, typ, c in oplabels:
    above = name.startswith(('Westhaven Depot', 'Midford', 'Westhaven (', 'Eastgate'))
    y = y0 - 62 if above else y1 + 62
    o.append(f'<rect x="{x-88:.1f}" y="{y-14:.1f}" width="176" height="34" rx="5" fill="{c}"/>'); T(x, y, name, 'opname'); T(x, y + 14, typ, 'small')

# legend
lx, ly = 70, 750
leg = [('<path d="M0,0 L40,0" class="le" stroke="#004494"/><path d="M26,0 L14,-6 L14,6Z" fill="#004494"/>', 'linear element, arrow from origin to end, length'),
       ('<circle cx="20" cy="0" r="5" class="sw"/>', 'switch (net point reference)'),
       ('<line x1="20" y1="8" x2="20" y2="-4" class="sigl"/><path d="M28,-4 L15,-9 L15,1Z" class="sig"/>', 'signal: direction of travel it applies to, and side of the track'),
       ('<path d="M0,0 L40,0" class="op" stroke="#ffe9a8"/>', 'operational point (area reference)'),
       ('<path d="M0,0 L40,0" class="sol"/>', 'section of line (area reference)'),
       ('<path d="M0,0 L40,0" class="tunnel"/>', 'tunnel'), ('<line x1="20" y1="-10" x2="20" y2="10" class="lc"/>', 'level crossing'),
       ('<path d="M0,0 L40,0" class="pe"/>', 'platform edge'), ('<rect x="16" y="-4" width="8" height="8" class="pl" transform="rotate(45 20 0)"/>', 'primary location'),
       ('<line x1="20" y1="-6" x2="20" y2="6" class="kp"/>', 'kilometre post')]
for i, (sym, txt) in enumerate(leg):
    x, y = lx + (i % 5) * 380, ly + (i // 5) * 26
    o.append(f'<g transform="translate({x},{y})">{sym}<text x="50" y="4" class="small" text-anchor="start">{txt}</text></g>')
W, H = int(X0 * 2 + 3600 * SX), 800
css = '''text{font-family:Arial,Helvetica,sans-serif;font-size:11px;fill:#222}.le{fill:none;stroke-width:2.6;stroke-linejoin:round}
.lelab{font-size:10.5px;font-weight:bold}.op{fill:none;stroke-width:30;stroke-linecap:round;stroke-linejoin:round;opacity:.95}
.sol{fill:none;stroke:#e3e6ea;stroke-width:30;stroke-linecap:butt;stroke-linejoin:round}.tunnel{fill:none;stroke:#555;stroke-width:13;stroke-dasharray:3 3;opacity:.45}
.lc{stroke:#8a4b08;stroke-width:6;opacity:.8}.pe{fill:none;stroke:#333;stroke-width:4}.sw{fill:#fff;stroke:#111;stroke-width:2}
.swt{font-weight:bold;font-size:10.5px}.sig{fill:#d0021b}.sigl{stroke:#d0021b;stroke-width:1.2}.sigt{fill:#d0021b;font-size:10px;font-weight:bold}
.kp{stroke:#111;stroke-width:1.5}.kpt{font-size:9.5px;fill:#444}.pl{fill:#111}.plt{font-size:9.5px}.small{font-size:10px;fill:#333}.opname{font-weight:bold;font-size:12px}
.feat{font-size:10px;font-style:italic}.border{stroke:#111;stroke-width:1.5;stroke-dasharray:7 5}.imbe{fill:#004494;font-weight:bold;font-size:14px}.imnl{fill:#c8500a;font-weight:bold;font-size:14px}
.title{font-size:16px;font-weight:bold}'''
svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"><style>{css}</style><rect width="{W}" height="{H}" fill="#fff"/>' \
      f'<text x="70" y="30" class="title">RINF reference example: network drawn from the Turtle (schematic, not to scale)</text>' + '\n'.join(o) + '</svg>'
dev = 0
for npr in g.subjects(RDF.type, ERA.NetPointReference):
    geo = g.value(npr, GSP.hasGeometry)
    if geo and g.value(npr, ERA.hasTopoCoordinate):
        dev = max(dev, math.dist(at(*pos(npr))[0], scr(*map(float, re.findall(r'-?\d+\.\d+', str(g.value(geo, GSP.asWKT)))))))
print('largest distance between a point geometry and its topological position: %.1f px' % dev)
open(sys.argv[2], 'w').write(svg); print(sys.argv[2], W, H)
