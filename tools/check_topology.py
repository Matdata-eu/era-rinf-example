#!/usr/bin/env python3
"""Consistency checks on the example that the SHACL does not make.
Usage: check_topology.py <data dir>   (exit code 1 when a check fails)"""
import sys, glob, re, itertools, collections
import rdflib
from rdflib import RDF, Namespace
from rdflib.collection import Collection
ERA = Namespace('http://data.europa.eu/949/'); GSP = Namespace('http://www.opengis.net/ont/geosparql#')
NV = 'http://data.europa.eu/949/concepts/navigabilities/'
g = rdflib.Graph()
for f in sorted(glob.glob(sys.argv[1] + '/*.ttl')):
    g.parse(f)
fails = []; done = []
def short(x): return str(x).split('/example/')[-1]
def check(name, bad):
    done.append((name, len(bad)))
    for b in bad: fails.append(f'{name}: {b}')
def coords(node):
    wkt = str(g.value(g.value(node, GSP.hasGeometry), GSP.asWKT))
    return [tuple(float(v) for v in p.split()) for p in re.findall(r'-?\d+\.\d+ -?\d+\.\d+', wkt)]
elems = set(g.subjects(RDF.type, ERA.LinearElement))
length = {e: float(g.value(e, ERA.lengthOfNetLinearElement)) for e in elems}
end_pt = {e: {True: coords(e)[0], False: coords(e)[-1]} for e in elems}   # True = origin

# 1 relations refer to linear elements, and the two ends named by isOnOrigin... are the same point
rels = list(g.subjects(RDF.type, ERA.NetRelation)); bad1 = []; bad2 = []; pairs = {}
for r in rels:
    a, b = g.value(r, ERA.elementA), g.value(r, ERA.elementB)
    if a not in elems or b not in elems: bad1.append(short(r)); continue
    oa, ob = g.value(r, ERA.isOnOriginOfElementA).toPython(), g.value(r, ERA.isOnOriginOfElementB).toPython()
    if end_pt[a][oa] != end_pt[b][ob]: bad2.append(f'{short(r)} {end_pt[a][oa]} != {end_pt[b][ob]}')
    pairs[frozenset([(a, oa), (b, ob)])] = str(g.value(r, ERA.navigability)).replace(NV, '')
check('net relation refers to two linear elements', bad1)
check('net relation joins two element ends at the same point', bad2)

# 2 every pair of element ends that meet has exactly one relation
at = collections.defaultdict(list)
for e in elems:
    for o in (True, False): at[end_pt[e][o]].append((e, o))
bad = []
for pt, ends in at.items():
    for x, y in itertools.combinations(ends, 2):
        if frozenset([x, y]) not in pairs: bad.append(f'{short(x[0])} / {short(y[0])} at {pt}')
check('every pair of element ends that meet has a net relation', bad)
check('no two relations for the same pair of ends', [] if len(pairs) == len(rels) else ['duplicate relation'])

# 3 offsets lie on their element
bad = []; tc_of = {}
for tc in g.subjects(RDF.type, ERA.TopologicalCoordinate):
    e, o = g.value(tc, ERA.onLinearElement), float(g.value(tc, ERA.offsetFromOrigin))
    if e not in elems or not (0 <= o <= length[e]): bad.append(f'{short(tc)} offset {o}')
check('topological coordinate lies on its linear element', bad)
def pos(npr):
    tc = g.value(npr, ERA.hasTopoCoordinate)
    return g.value(tc, ERA.onLinearElement), float(g.value(tc, ERA.offsetFromOrigin))

# 4 linear references: start on the first element, end on the last, consecutive elements navigable
bad = []; bad_nav = []
for n in g.subjects(RDF.type, ERA.NetLinearReference):
    seq = list(Collection(g, g.value(n, ERA.hasSequence)))
    (se, so), (ee, eo) = pos(g.value(n, ERA.startsAt)), pos(g.value(n, ERA.endsAt))
    if se != seq[0] or ee != seq[-1]: bad.append(short(n))
    for x, y in zip(seq, seq[1:]):
        nav = [v for k, v in pairs.items() if {e for e, _ in k} == {x, y}]
        if 'Both' not in nav: bad_nav.append(f'{short(n)}: {short(x)} -> {short(y)} {nav}')
    # direction of travel through the sequence must be continuous
    if len(seq) > 1:
        for i, (x, y) in enumerate(zip(seq, seq[1:])):
            k = [k for k in pairs if {e for e, _ in k} == {x, y}]
            if not k: continue
            leave = dict(k[0])[x]                 # x is left at its origin (True) or its end (False)
            if i == 0 and ((leave and so == 0 and length[x] > 0) or (not leave and so == length[x])):
                bad.append(f'{short(n)} starts at the end it should leave from')
check('linear reference starts on its first and ends on its last element', bad)
check('consecutive elements of a linear reference are navigable', bad_nav)

# 5 area references list linear references
bad = []
for n in g.subjects(RDF.type, ERA.NetAreaReference):
    for m in Collection(g, g.value(n, ERA.includes)):
        if (m, RDF.type, ERA.NetLinearReference) not in g: bad.append(f'{short(n)} includes {short(m)}')
check('area reference includes linear references only', bad)

# 6 signals: the orientation is given on the element the signal stands on, with the same direction
bad = []
for s in g.subjects(RDF.type, ERA.Signal):
    o, ref = g.value(s, ERA.hasOrientation), g.value(s, ERA.netReference)
    if g.value(o, ERA.carrierLinearElement) != pos(ref)[0] or g.value(o, ERA.direction) != g.value(ref, ERA.appliesToDirection):
        bad.append(short(s))
check('signal orientation agrees with its net point reference', bad)

# 7 switches sit where elements meet
bad = []
for s in g.subjects(RDF.type, ERA.Switch):
    e, o = pos(g.value(s, ERA.netReference))
    if o not in (0, length[e]) or len(at[end_pt[e][o == 0]]) < 3: bad.append(short(s))
check('switch is placed on a point where at least three element ends meet', bad)

# 8 the border point records agree
ops = [o for o in g.subjects(RDF.type, ERA.OperationalPoint) if g.value(o, ERA.referenceBorderPoint)]
sig = {(str(g.value(o, ERA.uopid)), g.value(o, ERA.referenceBorderPoint), g.value(o, ERA.canonicalURI), tuple(coords(g.value(o, ERA.netReference)))) for o in ops}
check('border point records share UOPID, reference border point, canonical URI and position', [] if len(ops) == 2 and len(sig) == 1 else [str(sig)])

# 9 hasPart: every part of an OP or SoL has its linear reference in the container's area reference
bad = []
for c, p in g.subject_objects(ERA.hasPart):
    inc = set(Collection(g, g.value(g.value(c, ERA.netReference), ERA.includes)))
    if g.value(p, ERA.netReference) not in inc: bad.append(f'{short(c)} hasPart {short(p)}')
check('hasPart agrees with the area reference of the container', bad)

# 10 no linear element stretch belongs to two operational points or two sections of line
def windows(cls):
    res = []
    for c in g.subjects(RDF.type, cls):
        ref = g.value(c, ERA.netReference)
        if (ref, RDF.type, ERA.NetAreaReference) not in g: continue
        for n in Collection(g, g.value(ref, ERA.includes)):
            seq = list(Collection(g, g.value(n, ERA.hasSequence)))
            (se, so), (ee, eo) = pos(g.value(n, ERA.startsAt)), pos(g.value(n, ERA.endsAt))
            for i, e in enumerate(seq):
                lo, hi = 0.0, length[e]
                if len(seq) == 1: lo, hi = sorted((so, eo))
                elif i == 0:
                    k = [k for k in pairs if {x for x, _ in k} == {e, seq[1]}]; leave_origin = dict(k[0])[e]
                    lo, hi = (0.0, so) if leave_origin else (so, length[e])
                elif i == len(seq) - 1:
                    k = [k for k in pairs if {x for x, _ in k} == {e, seq[-2]}]; enter_origin = dict(k[0])[e]
                    lo, hi = (0.0, eo) if enter_origin else (eo, length[e])
                res.append((c, e, lo, hi))
    return res
cover = collections.defaultdict(list); bad = []
for c, e, lo, hi in windows(ERA.OperationalPoint) + windows(ERA.SectionOfLine):
    for c2, lo2, hi2 in cover[e]:
        if c2 != c and min(hi, hi2) - max(lo, lo2) > 1e-6: bad.append(f'{short(e)}: {short(c)} overlaps {short(c2)}')
    cover[e].append((c, lo, hi))
check('operational points and sections of line do not overlap', bad)
gaps = []
for e in elems:
    segs = sorted((lo, hi) for _, lo, hi in cover[e]); p = 0.0
    for lo, hi in segs:
        if lo - p > 1e-6: gaps.append(f'{short(e)} {p}-{lo}')
        p = max(p, hi)
    if length[e] - p > 1e-6: gaps.append(f'{short(e)} {p}-{length[e]}')
check('every linear element is covered by an operational point or a section of line', gaps)

for name, n in done: print(('ok   ' if n == 0 else 'FAIL ') + name + ('' if n == 0 else f' ({n})'))
for f in fails: print('   ', f)
print(f'{len(g)} triples, {len(elems)} linear elements, {len(rels)} net relations, {len(done)} checks, {len(fails)} failures')
sys.exit(1 if fails else 0)
