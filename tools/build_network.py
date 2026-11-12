#!/usr/bin/env python3
"""Writes the first version of the example Turtle from one compact network definition.

The Turtle files are the source of truth once they are reviewed; this script only
exists so that the first version is consistent (offsets, relation flags, geometry).
Usage: build_network.py <output directory>
"""
import sys
from pathlib import Path

OUT = Path(sys.argv[1])
BASE = "http://data.europa.eu/949/example/"

PREFIXES = """@prefix be: <http://data.europa.eu/949/example/be/> .
@prefix nl: <http://data.europa.eu/949/example/nl/> .
@prefix era: <http://data.europa.eu/949/> .
@prefix org: <http://data.europa.eu/949/body/organisation/> .
@prefix orgrole: <http://data.europa.eu/949/body/organisation/organisationRole/> .
@prefix era-tdssc: <http://data.europa.eu/949/concepts/train-detection-specific-checks/> .
@prefix era-ldia: <http://data.europa.eu/949/concepts/lineside-distance-indication-appearance/> .
@prefix era-ldip: <http://data.europa.eu/949/concepts/lineside-distance-indication-positioning/> .
@prefix era-rsf: <http://data.europa.eu/949/concepts/rolling-stock-fire/> .
@prefix era-nv: <http://data.europa.eu/949/concepts/navigabilities/> .
@prefix era-orient: <http://data.europa.eu/949/concepts/orientations/> .
@prefix era-op-types: <http://data.europa.eu/949/concepts/op-types/> .
@prefix era-sn: <http://data.europa.eu/949/concepts/sol-natures/> .
@prefix era-trd: <http://data.europa.eu/949/concepts/track-running-directions/> .
@prefix era-sigtypes: <http://data.europa.eu/949/concepts/signal-types/> .
@prefix era-cls: <http://data.europa.eu/949/concepts/contact-line-systems/> .
@prefix era-ess: <http://data.europa.eu/949/concepts/energy-supply-systems/> .
@prefix era-etcslevel: <http://data.europa.eu/949/concepts/etcs-levels/> .
@prefix era-etcsbaseline: <http://data.europa.eu/949/concepts/etcs-baselines/> .
@prefix era-tds: <http://data.europa.eu/949/concepts/train-detection/> .
@prefix era-ntg: <http://data.europa.eu/949/concepts/nominal-track-gauges/> .
@prefix era-lclc: <http://data.europa.eu/949/concepts/load-capability-line-categories/> .
@prefix era-subloctype: <http://data.europa.eu/949/concepts/subsidiary-location-types/> .
@prefix era-organisation-roles: <http://data.europa.eu/949/concepts/organisation-roles/> .
@prefix eu-country: <http://publications.europa.eu/resource/authority/country/> .
@prefix gsp: <http://www.opengis.net/ont/geosparql#> .
@prefix time: <http://www.w3.org/2006/time#> .
@prefix foaf: <http://xmlns.com/foaf/0.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
"""

# ---------------------------------------------------------------------------
# Schematic plane -> North Sea.  x runs west to east, y south to north.
LON0, LAT0, SX, SY = 2.90, 52.60, 2e-4, 1.2e-4


def lonlat(p):
    return f"{LON0 + p[0] * SX:.5f} {LAT0 + p[1] * SY:.5f}"


# ---------------------------------------------------------------------------
# Nodes: name -> schematic point
N = {   # x is 520 units per km between km 0 and Midford, so both main tracks share one scale there
    "A1": (0, 40), "W1": (208, 40), "W6": (312, 40), "W2": (390, 40), "W3": (650, 40),
    "W7": (1300, 40), "W4": (1248, 0),
    "Xa": (1456, 40),
    "A2": (0, 0), "DS": (234, 0), "Xb": (1508, 0), "Wm": (1742, 0), "Wg": (2500, 0),
    "BORD": (2640, 0),
    "Wd": (130, 80), "D1": (0, 80), "D2": (0, 120),
    "Wy": (120, -40), "Y1": (0, -40), "Y2": (0, -80),
    "HIL": (2100, -70),
    "We1": (2940, 0), "We2": (3440, 0), "END": (3600, 0),
}

E = {
    # IM A, track 1 lane
    "a1": ("be", "A1", "W1", [], 400, False),
    "a2": ("be", "W1", "W6", [], 200, False),
    "a3": ("be", "W6", "W2", [], 150, False),
    "a4": ("be", "W2", "W3", [], 500, False),
    "a5": ("be", "W3", "W7", [], 1250, False),
    "a7": ("be", "W7", "Xa", [], 300, False),
    "a6": ("be", "Xa", "Wg", [(2440, 40)], 5400, False),
    # IM A, track 2 lane
    "b1": ("be", "A2", "DS", [], 450, False),
    "b2": ("be", "DS", "W4", [], 1950, True),
    "b6": ("be", "W4", "Xb", [], 500, True),
    "x2": ("be", "W4", "W7", [], 110, False),
    "b3": ("be", "Xb", "Wm", [], 450, False),
    "b4": ("be", "Wm", "Wg", [], 4850, False),
    "b5": ("be", "Wg", "BORD", [], 600, False),
    # Westhaven: loop, slip connection, depot, yard
    "c1": ("be", "W2", "W3", [(410, 80), (630, 80)], 520, True),
    "x1": ("be", "DS", "W6", [], 160, False),
    "d0": ("be", "W1", "Wd", [(170, 80)], 120, True),
    "d1": ("be", "Wd", "D1", [], 150, False),
    "d2": ("be", "Wd", "D2", [(70, 120)], 160, False),
    "y0": ("be", "Wy", "DS", [(180, -40)], 100, False),
    "y1": ("be", "Wy", "Y1", [], 400, False),
    "y2": ("be", "Wy", "Y2", [(80, -80)], 420, False),
    # Midford: crossover and branch
    "cx": ("be", "Xa", "Xb", [], 110, False),
    "br": ("be", "Wm", "HIL", [(1830, -70)], 800, False),
    # IM B: every element has its origin at its eastern end
    "B1": ("nl", "BORD", "We1", [], 4800, True),
    "B2": ("nl", "We1", "We2", [], 800, True),
    "B3": ("nl", "We1", "We2", [(2990, 40), (3390, 40)], 820, True),
    "B4": ("nl", "We2", "END", [], 400, True),
}

# Simple switches: node -> (label, common branch, leg, leg)
SW = {
    "W1": ("W1", "a2", "a1", "d0"),
    "W6": ("W6", "a3", "a2", "x1"),
    "W2": ("W2", "a3", "a4", "c1"),
    "W3": ("W3", "a5", "a4", "c1"),
    "Wd": ("W21", "d0", "d1", "d2"),
    "Wy": ("W31", "y0", "y1", "y2"),
    "W7": ("W7", "a7", "a5", "x2"),
    "W4": ("W4", "b2", "b6", "x2"),
    "Xa": ("W11", "a7", "a6", "cx"),
    "Xb": ("W12", "b3", "b6", "cx"),
    "Wm": ("W13", "b3", "b4", "br"),
    "Wg": ("W14", "b5", "b4", "a6"),
    "We1": ("101", "B1", "B2", "B3"),
    "We2": ("102", "B4", "B2", "B3"),
}
# Double slip crossing: node -> (label, [navigable pairs], [non-navigable pairs])
DS = {"DS": ("W5", [("b1", "b2"), ("y0", "x1"), ("b1", "x1"), ("y0", "b2")], [("b1", "y0"), ("b2", "x1")])}
# Plain joint between the two IMs (delivered by IM A)
JOINT = {}   # the two networks are not joined by a net relation; the border point is what they share

IMS = {
    "be": dict(country="BEL", org="9901", name="Infra Alfa", side="Left"),
    "nl": dict(country="NLD", org="9902", name="Beta Spoor", side="Right"),
}

# Kilometrage of the nodes on the two main lines (km).
KM = {"be": {"A1": 0, "A2": 0, "W1": .40, "DS": .45, "W6": .60, "W2": .75, "W3": 1.25, "W7": 2.50, "W4": 2.40, "Xa": 2.80,
             "Xb": 2.90, "Wm": 3.35, "Wg": 8.2, "BORD": 8.8},
      "nl": {"BORD": 6.0, "We1": 1.2, "We2": 0.4, "END": 0.0}}
KM_SIGN = {"be": 1, "nl": -1}  # km rises from->to (be) or falls (nl)
LRS = {"be": "line_100", "nl": "line_7"}
# Kilometric posts: (im, km, element, distance from the element's from node)
KP = [("be", 0, "a1", 0), ("be", 1, "a4", 250), ("be", 2, "a5", 750), ("be", 3, "a6", 200), ("be", 8, "a6", 5200),
      ("nl", 0, "B4", 400), ("nl", 1, "B2", 200), ("nl", 3, "B1", 3000), ("nl", 6, "B1", 0)]

out = {"be": [], "nl": [], "shared": []}


def w(im, text=""):
    out[im].append(text)


def sec(im, title, note=None):
    w(im, "\n" + "#" * 78)
    w(im, f"# {title}")
    if note:
        for line in note.split("\n"):
            w(im, f"# {line}")
    w(im, "#" * 78 + "\n")


def emit(im, subj, po, comment=None):
    if comment:
        for line in comment.split("\n"):
            w(im, f"# {line}")
    lines = [f"{subj} a {po[0]} ;"] if not po[0].startswith("@") else [f"{subj}"]
    body = po[1:]
    for i, (p, o) in enumerate(body):
        end = " ." if i == len(body) - 1 else " ;"
        lines.append(f"    {p} {o}{end}")
    w(im, "\n".join(lines) + "\n")


def lit(s, lang="en"):
    return f'"{s}"@{lang}'


def dbl(v):
    return f'"{float(v):.1f}"^^xsd:double'


def poly(e):
    im, a, b, via, L, rev = E[e]
    pts = [N[a]] + via + [N[b]]
    return pts


def origin(e):
    im, a, b, via, L, rev = E[e]
    return b if rev else a


def off(e, d):
    """Offset from the origin for a distance d measured from the from node."""
    L, rev = E[e][4], E[e][5]
    return L - d if rev else d


def point_at(e, d):
    pts, L = poly(e), E[e][4]
    seg = [((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** .5 for i in range(len(pts) - 1)]
    t = sum(seg) * d / L
    for i, s in enumerate(seg):
        if t <= s or i == len(seg) - 1:
            f = 0 if s == 0 else min(1, t / s)
            return (pts[i][0] + f * (pts[i + 1][0] - pts[i][0]), pts[i][1] + f * (pts[i + 1][1] - pts[i][1]))
        t -= s


def sub_line(e, d0, d1):
    """Schematic polyline of the part of e between d0 and d1 (in that order)."""
    pts, L = poly(e), E[e][4]
    seg = [((pts[i + 1][0] - pts[i][0]) ** 2 + (pts[i + 1][1] - pts[i][1]) ** 2) ** .5 for i in range(len(pts) - 1)]
    tot = sum(seg)
    lo, hi = sorted((d0, d1))
    res = [point_at(e, lo)]
    acc = 0
    for i, s in enumerate(seg[:-1]):
        acc += s
        dd = acc / tot * L
        if lo < dd < hi:
            res.append(pts[i + 1])
    res.append(point_at(e, hi))
    return res if d0 <= d1 else res[::-1]


def le(e):
    return f"{E[e][0]}:le_{e}"


def geometry(im, iri, wkt):
    """Geometry node of iri (the shapes ask for an IRI, not a blank node)."""
    emit(im, f"{iri}_geom", ["gsp:Geometry", ("gsp:asWKT", f'"{wkt}"^^gsp:wktLiteral')])


def wkt_point(p):
    return f"POINT({lonlat(p)})"


def wkt_line(pts):
    return "LINESTRING(" + ", ".join(lonlat(p) for p in pts) + ")"


def km_of(e, d):
    im, a = E[e][0], E[e][1]
    if a not in KM[im]:
        return None
    return KM[im][a] + KM_SIGN[im] * d / 1000


def direction(e, travel):
    """travel 'ft' = from the from node to the to node, 'tf' = the other way."""
    rev = E[e][5]
    normal = (travel == "ft") != rev
    return "era-orient:00" if normal else "era-orient:01"


def npr(im, iri, e, d, applies=None, lrs=True, geom=True, comment=None):
    """Net point reference with its topological coordinate (and LRS coordinate on the main lines)."""
    po = ["era:NetPointReference", ("era:hasTopoCoordinate", f"{iri}_tc")]
    if applies:
        po.append(("era:appliesToDirection", applies))
    km = km_of(e, d)
    if lrs and km is not None:
        posts = [k for (i, k, _, _) in KP if i == im and k <= km + 1e-9]
        if posts:
            k = max(posts)
            po.append(("era:hasLrsCoordinate", f"{iri}_lrs"))
    if geom:
        po.append(("gsp:hasGeometry", f"{iri}_geom"))
    emit(im, iri, po, comment)
    if geom:
        geometry(im, iri, wkt_point(point_at(e, d)))
    emit(im, f"{iri}_tc", ["era:TopologicalCoordinate", ("era:onLinearElement", le(e)),
                           ("era:offsetFromOrigin", dbl(off(e, d)))])
    if lrs and km is not None and posts:
        emit(im, f"{iri}_lrs", ["era:LinearPositioningSystemCoordinate",
                                ("era:kmPost", f"{im}:kp_{LRS[im]}_{k}"),
                                ("era:offsetFromKilometricPost", dbl(round((km - k) * 1000, 1)))])
    return iri


def nlr(im, iri, parts, comment=None):
    """Net linear reference. parts = [(element, d_start, d_end)] in the direction of the reference."""
    seq = " ".join(le(e) for e, _, _ in parts)
    pts = []
    for e, d0, d1 in parts:
        seg = sub_line(e, d0, d1)
        pts += seg if not pts or pts[-1] != seg[0] else seg[1:]
    emit(im, iri, ["era:NetLinearReference", ("era:hasSequence", f"( {seq} )"),
                   ("era:startsAt", f"{iri}_start"), ("era:endsAt", f"{iri}_end"),
                   ("gsp:hasGeometry", f"{iri}_geom")], comment)
    geometry(im, iri, wkt_line(pts))
    LINES[iri] = pts
    npr(im, f"{iri}_start", parts[0][0], parts[0][1], lrs=False, geom=False)
    npr(im, f"{iri}_end", parts[-1][0], parts[-1][2], lrs=False, geom=False)
    return iri


LINES = {}
AREAS = []


def nar(im, iri, nlrs, comment=None):
    emit(im, iri, ["era:NetAreaReference", ("era:includes", "( " + " ".join(nlrs) + " )"),
                   ("gsp:hasGeometry", f"{iri}_geom")], comment)
    AREAS.append((im, iri, nlrs, len(out[im])))
    out[im].append(None)  # the geometry is written once the linear references are known
    return iri


def common(im):
    return [("era:inCountry", f"eu-country:{IMS[im]['country']}"),
            ("era:infrastructureManager", f"orgrole:{IMS[im]['org']}_IM")]


def validity(im, iri, start="2026-01-01"):
    emit(im, f"{iri}_validity", ["era:TemporalFeature, time:Interval", ("time:hasBeginning", f"{iri}_validity_begin")])
    emit(im, f"{iri}_validity_begin", ["time:Instant", ("time:inXSDDate", f'"{start}"^^xsd:date')])
    return ("era:validity", f"{iri}_validity")


# ---------------------------------------------------------------------------
# Organisations and lines
for im, d in IMS.items():
    w(im, PREFIXES)
    w(im, f"# RINF reference example - infrastructure manager \"{d['name']}\" ({d['country']}).")
    w(im, "# Fictive data on ERA ontology v3.3.4. Everything except the country is invented.")
    w(im, "# Geometries are schematic and lie in the North Sea.")
    sec(im, "1. Infrastructure manager",
        "era:infrastructureManager on every element points to the OrganisationRole, not to the Body.")
    emit(im, f"org:{d['org']}", ["era:Body", ("era:organisationCode", f'"{d["org"]}"'),
                                ("rdfs:label", lit(d["name"])), ("era:role", f"orgrole:{d['org']}_IM")],
         "The shapes require organisation IRIs in the ERA namespace; code 99xx is not a real organisation code.")
    emit(im, f"orgrole:{d['org']}_IM", ["era:OrganisationRole", ("era:hasOrganisationRole", "era-organisation-roles:IM"),
                                       ("era:roleOf", f"org:{d['org']}")])

# ---------------------------------------------------------------------------
# Topology
for im in IMS:
    sec(im, "2. Topology: linear elements",
        "Each element runs from its origin to its end. The WKT is written in that same direction,\n"
        "so the first coordinate is the origin. Offsets on an element are metres from the origin.")
    for e, (eim, a, b, via, L, rev) in E.items():
        if eim != im:
            continue
        pts = poly(e)[::-1] if rev else poly(e)
        o, t = (b, a) if rev else (a, b)
        emit(im, le(e), ["era:LinearElement", ("rdfs:label", lit(f"{e} ({o} to {t})")),
                         ("era:lengthOfNetLinearElement", dbl(L)), ("gsp:hasGeometry", f"{le(e)}_geom")])
        geometry(im, le(e), wkt_line(pts))


def rel(im, node, ea, eb, nav, comment=None):
    iri = f"{im}:nr_{node}_{ea}_{eb}"
    emit(im, iri, ["era:NetRelation",
                   ("era:elementA", le(ea)), ("era:isOnOriginOfElementA", "true" if origin(ea) == node else "false"),
                   ("era:elementB", le(eb)), ("era:isOnOriginOfElementB", "true" if origin(eb) == node else "false"),
                   ("era:navigability", f"era-nv:{nav}")], comment)


for im in IMS:
    sec(im, "3. Topology: net relations",
        "One relation per pair of elements that meet in a point.\n"
        "isOnOriginOfElementA/B says which end of each element is at that point.\n"
        "A simple switch has three: two navigable (Both) and one between its two legs (None).")
    for node, (label, c, l1, l2) in SW.items():
        if E[c][0] != im:
            continue
        w(im, f"# --- switch {label} at node {node}: common branch {c}, legs {l1} and {l2}")
        rel(im, node, c, l1, "Both")
        rel(im, node, c, l2, "Both")
        rel(im, node, l1, l2, "None")
    for node, (label, yes, no) in DS.items():
        if im != "be":
            continue
        w(im, f"# --- double slip crossing {label} at node {node}: four elements, six relations")
        for a, b in yes:
            rel(im, node, a, b, "Both")
        for a, b in no:
            rel(im, node, a, b, "None")
    for node, (a, b) in JOINT.items():
        if im != "be":
            continue
        w(im, "# --- the border: the last element of this IM meets the first element of the neighbour.")
        w(im, "#     Each IM delivers its own element; this IM delivers the relation.")
        rel(im, node, a, b, "Both")

# ---------------------------------------------------------------------------
# Line referencing
for im in IMS:
    line = LRS[im]
    sec(im, "4. Line referencing",
        "A linear positioning system per line, with kilometric posts placed on the topology.")
    emit(im, f"{im}:{line}", ["era:LinearPositioningSystem", ("rdfs:label", lit(f"Line {line.split('_')[1]}")),
                             ("era:lineId", f'"{line.split("_")[1]}"')])
    if im == "be":
        emit(im, "be:line_101", ["era:LinearPositioningSystem", ("rdfs:label", lit("Line 101 (Hillend branch)")),
                                 ("era:lineId", '"101"')])
    for (kim, k, e, d) in KP:
        if kim != im:
            continue
        iri = f"{im}:kp_{line}_{k}"
        emit(im, iri, ["era:KilometricPost", ("rdfs:label", lit(f"km {k}")), ("era:hasLRS", f"{im}:{line}"),
                       ("era:kilometer", dbl(k)), *common(im), ("era:netReference", f"{iri}_ref")])
        npr(im, f"{iri}_ref", e, d, lrs=False)

# ---------------------------------------------------------------------------
# Subsystems shared by tracks
sec("be", "5. Subsystems that tracks point to",
    "Contact line system, ETCS and train detection are not infrastructure elements in v3.3.4:\n"
    "they have no net reference. Their extent is the set of tracks that point to them.")
emit("be", "be:cls_3kv", ["era:ContactLineSystem", ("rdfs:label", lit("Overhead contact line 3 kV DC")),
                          ("era:contactLineSystemType", "era-cls:10"), ("era:energySupplySystem", "era-ess:DC30"),
                          ("era:maxTrainCurrent", '"2400"^^xsd:integer'), ("era:umax2", '"3900"^^xsd:integer'),
                          ("era:maxCurrentStandstillPantograph", '"200"^^xsd:integer'),
                          ("era:minimumContactWireHeight", dbl(4.8)), ("era:maximumContactWireHeight", dbl(6.2))])
emit("be", "be:cls_none", ["era:ContactLineSystem", ("rdfs:label", lit("Not electrified")),
                           ("era:contactLineSystemType", "era-cls:40")],
     "Open world: leaving out era:contactLineSystem means 'unknown'. 'Not electrified' has to be stated.")
emit("be", "be:etcs_l2", ["era:ETCS", ("rdfs:label", lit("ETCS level 2, baseline 3 release 2")),
                          ("era:etcsLevelType", "era-etcslevel:30"), ("era:etcsBaseline", "era-etcsbaseline:50")])
emit("be", "be:tds_axle", ["era:TrainDetectionSystem", ("rdfs:label", lit("Axle counters")),
                           ("era:trainDetectionSystemType", "era-tds:20"),
                           ("era:trainDetectionSystemSpecificCheck", "era-tdssc:NotApplicable")])
emit("be", "be:ldi_km", ["era:LinesideDistanceIndication", ("rdfs:label", lit("Kilometre posts every 1000 m")),
                         ("era:linesideDistanceIndicationAppearance", "era-ldia:00"),
                         ("era:linesideDistanceIndicationFrequency", '"1000"^^xsd:integer'),
                         ("era:linesideDistanceIndicationPositioning", "era-ldip:00")])
sec("nl", "5. Subsystems that tracks point to",
    "Contact line system and train detection are not infrastructure elements in v3.3.4:\n"
    "they have no net reference. Their extent is the set of tracks that point to them.")
emit("nl", "nl:cls_1500", ["era:ContactLineSystem", ("rdfs:label", lit("Overhead contact line 1.5 kV DC")),
                           ("era:contactLineSystemType", "era-cls:10"), ("era:energySupplySystem", "era-ess:DC40"),
                           ("era:maxTrainCurrent", '"4000"^^xsd:integer'), ("era:umax2", '"1950"^^xsd:integer'),
                           ("era:maxCurrentStandstillPantograph", '"300"^^xsd:integer'),
                           ("era:minimumContactWireHeight", dbl(4.9)), ("era:maximumContactWireHeight", dbl(5.75))])
emit("nl", "nl:ldi_km", ["era:LinesideDistanceIndication", ("rdfs:label", lit("Kilometre posts every 1000 m")),
                         ("era:linesideDistanceIndicationAppearance", "era-ldia:00"),
                         ("era:linesideDistanceIndicationFrequency", '"1000"^^xsd:integer'),
                         ("era:linesideDistanceIndicationPositioning", "era-ldip:00")])
emit("nl", "nl:tds_tc", ["era:TrainDetectionSystem", ("rdfs:label", lit("Track circuits")),
                         ("era:trainDetectionSystemType", "era-tds:10"),
                         ("era:trainDetectionSystemSpecificCheck", "era-tdssc:NotApplicable")])

# ---------------------------------------------------------------------------
# Operational points, sections of line and their tracks
# track: (id, class, label, parts, extra predicate-objects)
MAIN_BE = [("era:wheelSetGauge", "era-ntg:30"), ("era:contactLineSystem", "be:cls_3kv"),
           ("era:etcs", "be:etcs_l2"), ("era:trainDetectionSystem", "be:tds_axle")]
SIDE_BE = [("era:wheelSetGauge", "era-ntg:30"), ("era:contactLineSystem", "be:cls_3kv"),
           ("era:trainDetectionSystem", "be:tds_axle"), ("era:notApplicable", "era:etcs")]
BRANCH = [("era:wheelSetGauge", "era-ntg:30"), ("era:contactLineSystem", "be:cls_none"),
          ("era:trainDetectionSystem", "be:tds_axle"), ("era:notApplicable", "era:etcs")]
MAIN_NL = [("era:wheelSetGauge", "era-ntg:30"), ("era:contactLineSystem", "nl:cls_1500"),
           ("era:trainDetectionSystem", "nl:tds_tc"), ("era:notYetAvailable", "era:etcs")]


def speed(v):
    return ("era:maximumPermittedSpeed", f'"{v}"^^xsd:integer')


def tdir(c):
    return ("era:trackDirection", f"era-trd:{c}")


def sol_track(im, c):
    """Properties that only tracks of a section of line carry."""
    return [tdir(c), ("era:linesideDistanceIndication", f"{im}:ldi_km")]


OPS = [
    # (im, id, uopid, name, type, tracks)
    ("be", "WHS", "BEWHS", "Westhaven", "10", [
        ("1", "era:RunningTrack", "Westhaven track 1", [("a1", 0, 400), ("a2", 0, 200), ("a3", 0, 150), ("a4", 0, 500), ("a5", 0, 750)], MAIN_BE + [speed(90)]),
        ("2", "era:RunningTrack", "Westhaven track 2", [("b1", 0, 450), ("b2", 0, 1550)], MAIN_BE + [speed(90)]),
        ("3", "era:RunningTrack", "Westhaven track 3", [("c1", 0, 520)], MAIN_BE + [speed(40)]),
        ("5", "era:RunningTrack", "Westhaven connection 2-1", [("x1", 0, 160)], MAIN_BE + [speed(40)]),
    ]),
    ("be", "WHD", "BEWHD", "Westhaven Depot", "50", [
        ("L", "era:Siding", "Depot lead", [("d0", 20, 120)], SIDE_BE),
        ("D1", "era:Siding", "Depot siding D1", [("d1", 0, 150)], SIDE_BE),
        ("D2", "era:Siding", "Depot siding D2", [("d2", 0, 160)], SIDE_BE),
    ]),
    ("be", "WHY", "BEWHY", "Westhaven Yard", "40", [
        ("L", "era:Siding", "Yard lead", [("y0", 0, 80)], SIDE_BE),
        ("Y1", "era:Siding", "Yard siding Y1", [("y1", 0, 400)], SIDE_BE),
        ("Y2", "era:Siding", "Yard siding Y2", [("y2", 0, 420)], SIDE_BE),
    ]),
    ("be", "MID", "BEMID", "Midford Junction", "80", [
        ("1", "era:RunningTrack", "Midford track 1", [("a5", 1050, 1250), ("a7", 0, 300), ("a6", 0, 200)], MAIN_BE + [speed(120)]),
        ("2", "era:RunningTrack", "Midford track 2", [("b2", 1850, 1950), ("b6", 0, 500)], MAIN_BE + [speed(120)]),
        ("X1", "era:RunningTrack", "Midford crossover 2-1", [("x2", 0, 110)], MAIN_BE + [speed(60)]),
        ("X2", "era:RunningTrack", "Midford crossover 1-2", [("cx", 0, 110)], MAIN_BE + [speed(60)]),
    ]),
    ("be", "DUN", "BEDUN", "Dunes Junction", "80", [
        ("1", "era:RunningTrack", "Dunes Junction track 1", [("a6", 5200, 5400)], MAIN_BE + [speed(100)]),
        ("2", "era:RunningTrack", "Dunes Junction track 2", [("b4", 4650, 4850), ("b5", 0, 200)], MAIN_BE + [speed(100)]),
    ]),
    ("be", "HIL", "BEHIL", "Hillend siding", "130", [
        ("S1", "era:Siding", "Hillend siding S1", [("br", 0, 800)], BRANCH),
    ]),
    ("nl", "EGT", "NLEGT", "Eastgate", "20", [
        ("1", "era:RunningTrack", "Eastgate track 1", [("B4", 400, 0), ("B2", 800, 0), ("B1", 4800, 4500)], MAIN_NL + [speed(80)]),
        ("2", "era:RunningTrack", "Eastgate track 2", [("B3", 820, 0)], MAIN_NL + [speed(40)]),
    ]),
]
BORDER = {"be": ("b5", 600), "nl": ("B1", 0)}
BORDER_UOPID = "EU99901"

SOLS = [
    # (im, id, from op, to op, nature, line, length, tracks)
    ("be", "WHS_MID", "WHS", "MID", "10", "line_100", 300, [
        ("1", "era:RunningTrack", "Westhaven - Midford track 1", [("a5", 750, 1050)], MAIN_BE + [speed(140), *sol_track("be", "10")]),
        ("2", "era:RunningTrack", "Westhaven - Midford track 2", [("b2", 1550, 1850)], MAIN_BE + [speed(140), *sol_track("be", "30")]),
    ]),
    # links inside the Westhaven station area: from the switch, along the first metres of the branching leg
    ("be", "WHS_WHD", "WHS", "WHD", "20", "line_100", 20, [
        ("1", "era:RunningTrack", "Westhaven - Westhaven Depot link", [("d0", 0, 20)], SIDE_BE + [speed(40), *sol_track("be", "30")]),
    ]),
    ("be", "WHS_WHY", "WHS", "WHY", "20", "line_100", 20, [
        ("1", "era:RunningTrack", "Westhaven - Westhaven Yard link", [("y0", 100, 80)], SIDE_BE + [speed(40), *sol_track("be", "30")]),
    ]),
    ("be", "MID_DUN", "MID", "DUN", "10", "line_100", 5000, [
        ("1", "era:RunningTrack", "Midford - Dunes track 1", [("a6", 200, 5200)], MAIN_BE + [speed(140), *sol_track("be", "30")]),
    ]),
    ("be", "DUN_BORD", "DUN", "BORD", "10", "line_100", 400, [
        ("1", "era:RunningTrack", "Dunes - border single track", [("b5", 200, 600)], MAIN_BE + [speed(100), *sol_track("be", "30")]),
    ]),
    ("be", "MID_HIL", "MID", "HIL", "10", "line_100", 450, [
        ("2", "era:RunningTrack", "Midford - Hillend track 2", [("b3", 0, 450)], MAIN_BE + [speed(120), *sol_track("be", "30")]),
    ]),
    ("be", "HIL_DUN", "HIL", "DUN", "10", "line_100", 4650, [
        ("2", "era:RunningTrack", "Hillend - Dunes track 2", [("b4", 0, 4650)], MAIN_BE + [speed(140), *sol_track("be", "20")]),
    ]),
    ("nl", "EGT_BORD", "EGT", "BORD", "10", "line_7", 4500, [
        ("1", "era:RunningTrack", "Eastgate - border", [("B1", 4500, 0)], MAIN_NL + [speed(100), *sol_track("nl", "30")]),
    ]),
]


def tracks(im, owner, tr):
    refs = []
    for (tid, cls, label, parts, extra) in tr:
        iri = f"{im}:trk_{owner}_{tid}"
        idp = "era:sidingId" if cls == "era:Siding" else "era:trackId"
        po = [cls, ("rdfs:label", lit(label)), (idp, f'"{tid}"'), *common(im),
              ("era:netReference", f"{iri}_ref"), *extra]
        emit(im, iri, po)
        refs.append(nlr(im, f"{iri}_ref", parts))
    return refs


for im in IMS:
    sec(im, "6. Operational points and their tracks",
        "An operational point covers an area: its net reference includes the linear references of its tracks.\n"
        "A track is a sequence of linear elements with a start and an end, which may lie inside an element.")
    for (oim, oid, uopid, name, typ, tr) in OPS:
        if oim != im:
            continue
        iri = f"{im}:op_{oid}"
        w(im, f"# ---------- {name} ({uopid})")
        po = ["era:OperationalPoint", ("rdfs:label", lit(name)), ("era:opName", lit(name)), ("era:uopid", f'"{uopid}"'),
              ("era:opType", f"era-op-types:{typ}"), *common(im), ("era:netReference", f"{iri}_ref"),
              ("era:hasPart", ", ".join(f"{im}:trk_{oid}_{t[0]}" for t in tr)), validity(im, iri)]
        emit(im, iri, po)
        refs = [f"{im}:trk_{oid}_{t[0]}_ref" for t in tr]
        nar(im, f"{iri}_ref", refs)
        tracks(im, oid, tr)
    # border point
    e, d = BORDER[im]
    iri = f"{im}:op_BORD"
    w(im, f"# ---------- Border point ({BORDER_UOPID})")
    emit(im, iri, ["era:OperationalPoint", ("rdfs:label", lit("Dunes border")), ("era:opName", lit("Dunes border")),
                   ("era:uopid", f'"{BORDER_UOPID}"'), ("era:opType", "era-op-types:90"), *common(im),
                   ("era:netReference", f"{iri}_ref"),
                   ("era:referenceBorderPoint", f"<http://data.europa.eu/949/referenceBorderPoints/{BORDER_UOPID}>"),
                   ("era:canonicalURI", f"<{BASE}operationalPoint/{BORDER_UOPID}>"), validity(im, iri)],
         "Both IMs deliver a record for the border point, with the same UOPID (prefix EU, not a country code),\n"
         "the same reference border point and the same canonical URI. It is a point on this IM's last element.")
    npr(im, f"{iri}_ref", e, d)

    sec(im, "7. Sections of line and their tracks",
        "A section of line runs from opStart to opEnd. era:trackDirection on its tracks is relative to that:\n"
        "N (10) = same direction, O (20) = opposite, B (30) = both.")
    for (sim, sid, a, b, nature, line, length, tr) in SOLS:
        if sim != im:
            continue
        iri = f"{im}:sol_{sid}"
        emit(im, iri, ["era:SectionOfLine", ("rdfs:label", lit(f"{a} - {b}")), ("era:opStart", f"{im}:op_{a}"),
                       ("era:opEnd", f"{im}:op_{b}"), ("era:solNature", f"era-sn:{nature}"),
                       ("era:lengthOfSectionOfLine", dbl(length / 1000)), ("era:nationalLine", f"{im}:{line}"),
                       *common(im), ("era:netReference", f"{iri}_ref"),
                       ("era:hasPart", ", ".join(f"{im}:trk_{sid}_{t[0]}" for t in tr)), validity(im, iri)])
        nar(im, f"{iri}_ref", [f"{im}:trk_{sid}_{t[0]}_ref" for t in tr])
        tracks(im, sid, tr)

# ---------------------------------------------------------------------------
# Switches
for im in IMS:
    sec(im, "8. Switches",
        "A switch has one net point reference, at the point where its elements meet, given on the common branch.\n"
        "v3.3.4 has no switch properties: facing or trailing follows from the net relations at that point.")
    for node, (label, c, l1, l2) in SW.items():
        if E[c][0] != im:
            continue
        iri = f"{im}:sw_{label}"
        d = 0 if E[c][1] == node else E[c][4]
        emit(im, iri, ["era:Switch", ("rdfs:label", lit(f"Switch {label}")), *common(im), ("era:netReference", f"{iri}_ref")])
        npr(im, f"{iri}_ref", c, d, applies="era-orient:02")
    if im == "be":
        iri = "be:sw_W5"
        emit(im, iri, ["era:Switch", ("rdfs:label", lit("Double slip crossing W5")), *common(im), ("era:netReference", f"{iri}_ref")],
             "A double slip crossing has no common branch; the reference is given on track 2 (element b1).")
        npr(im, f"{iri}_ref", "b1", 450, applies="era-orient:02")

# ---------------------------------------------------------------------------
# Signals: (im, id, element, d, travel, type, label)
SIG = [
    ("be", "S1", "a4", 430, "ft", "04", "Exit signal track 1"),
    ("be", "S3", "c1", 430, "ft", "04", "Exit signal track 3"),
    ("be", "S2", "b2", 300, "tf", "04", "Exit signal track 2"),
    ("be", "H2", "b2", 1550, "tf", "01", "Home signal track 2"),
    ("be", "MD", "b2", 1850, "ft", "08", "Midford protection signal D"),
    ("be", "MC", "a6", 200, "tf", "08", "Midford protection signal C"),
    ("be", "B1", "a6", 1600, "ft", "07", "Block signal track 1"),
    ("be", "MA", "a5", 1050, "ft", "08", "Midford protection signal A"),
    ("be", "MB", "b3", 60, "tf", "08", "Midford protection signal B"),
    ("be", "HA", "b3", 390, "ft", "08", "Hillend protection signal A"),
    ("be", "HB", "b4", 300, "tf", "08", "Hillend protection signal B"),
    ("be", "HC", "br", 300, "tf", "08", "Hillend protection signal C"),
    ("be", "B2", "b4", 3300, "tf", "07", "Block signal track 2"),
    ("be", "DA", "a6", 4950, "ft", "08", "Dunes protection signal A"),
    ("be", "DB", "b5", 200, "tf", "08", "Dunes protection signal B"),
    ("nl", "EH", "B1", 4500, "ft", "01", "Eastgate home signal west"),
    ("nl", "EX1", "B2", 100, "tf", "04", "Eastgate exit signal track 1"),
    ("nl", "EX2", "B3", 100, "tf", "04", "Eastgate exit signal track 2"),
    ("nl", "EX3", "B2", 700, "ft", "04", "Eastgate exit signal track 1 east"),
    ("nl", "EX4", "B3", 680, "ft", "04", "Eastgate exit signal track 2 east"),
    ("nl", "EHE", "B4", 300, "tf", "01", "Eastgate home signal east"),
]
for im in IMS:
    sec(im, "9. Signals",
        "Three statements about direction, each in its own frame:\n"
        " - era:appliesToDirection on the net point reference: relative to the linear element (origin to end);\n"
        " - era:hasOrientation: direction and side relative to the carrier linear element;\n"
        " - era:signalOrientation: relative to the direction of the line (rising kilometrage).\n"
        "On an element that runs against the line they give different values.")
    for (sim, sid, e, d, travel, typ, label) in SIG:
        if sim != im:
            continue
        iri = f"{im}:sig_{sid}"
        dirn = direction(e, travel)
        # relative to the line: rising km is from->to for IM A and to->from for IM B
        line_normal = (travel == "ft") == (KM_SIGN[im] == 1)
        drv = IMS[im]["side"]
        side = drv if dirn == "era-orient:00" else ("Right" if drv == "Left" else "Left")
        emit(im, iri, ["era:Signal", ("rdfs:label", lit(label)), ("era:signalId", f'"{sid}"'),
                       ("era:signalType", f"era-sigtypes:{typ}"),
                       ("era:signalOrientation", "era-orient:00" if line_normal else "era-orient:01"),
                       ("era:hasOrientation", f"{iri}_orientation"), *common(im), ("era:netReference", f"{iri}_ref")])
        emit(im, f"{iri}_orientation", ["era:Orientation", ("era:carrierLinearElement", le(e)),
                                       ("era:direction", dirn), ("era:side", f"era-orient:{side}")])
        npr(im, f"{iri}_ref", e, d, applies=dirn)

# ---------------------------------------------------------------------------
# Other elements
sec("be", "10. Tunnel, level crossing, platform edges, document")
emit("be", "be:doc_tunnel_plan", ["era:Document", ("foaf:name", '"midford-tunnel-emergency-plan.pdf"'),
                                  ("era:documentUrl", '"https://example.org/documents/midford-tunnel-emergency-plan.pdf"^^xsd:anyURI'),
                                  ("dcterms:language", '"en"')])
emit("be", "be:tun_MID", ["era:Tunnel", ("rdfs:label", lit("Midford tunnel")), ("era:tunnelIdentification", '"T-100-1"'),
                          ("era:lengthOfTunnel", dbl(1200)), ("era:hasEmergencyPlan", "true"),
                          ("era:hasEvacuationAndRescuePoints", "true"), ("era:rollingStockFireCategory", "era-rsf:10"),
                          ("era:tunnelDocRef", "be:doc_tunnel_plan"), *common("be"),
                          ("era:netReference", "be:tun_MID_ref"),
                          ("era:notYetAvailable", "era:verificationSRT"), ("era:notYetAvailable", "era:demonstrationSRT"),
                          ("era:notYetAvailable", "era:nationalRollingStockFireCategory")],
     "The tunnel covers both tracks: an area reference with one linear reference per track.\n"
     "Three required parameters are not surveyed yet and are flagged with era:notYetAvailable.")
nar("be", "be:tun_MID_ref", ["be:tun_MID_ref_1", "be:tun_MID_ref_2"])
nlr("be", "be:tun_MID_ref_1", [("a6", 2300, 3500)])
nlr("be", "be:tun_MID_ref_2", [("b4", 1750, 2950)])
emit("be", "be:lc_1", ["era:LevelCrossing", ("rdfs:label", lit("Dune road level crossing")), *common("be"),
                       ("era:netReference", "be:lc_1_ref")],
     "The level crossing crosses both tracks: an area reference with one very short linear reference per track.")
nar("be", "be:lc_1_ref", ["be:lc_1_ref_1", "be:lc_1_ref_2"])
nlr("be", "be:lc_1_ref_1", [("a6", 4695, 4705)])
nlr("be", "be:lc_1_ref_2", [("b4", 4145, 4155)])
PLAT = [("be", "WHS_1", "1", [("a4", 125, 375)]), ("be", "WHS_3", "3", [("c1", 140, 380)]),
        ("be", "WHS_2", "2", [("b2", 425, 675)]),
        ("nl", "EGT_2", "2", [("B3", 620, 220)])]
sec("nl", "10. Platform edge")
for (im, pid, label, parts) in PLAT:
    iri = f"{im}:pe_{pid}"
    L = abs(parts[0][2] - parts[0][1])
    emit(im, iri, ["era:PlatformEdge", ("rdfs:label", lit(f"Platform {label}")), ("era:platformId", f'"{label}"'),
                   ("era:lengthOfPlatform", dbl(L)), *common(im), ("era:netReference", f"{iri}_ref")])
    nlr(im, f"{iri}_ref", parts)

# ---------------------------------------------------------------------------
# Primary and subsidiary locations
PL = [("be", "WHS", "BE99001", "Westhaven", True, False),
      ("be", "WHY", "BE99002", "Westhaven Yard", False, True),
      ("be", "HIL", "BE99003", "Hillend siding", False, True),
      ("be", "WHD", "BE99004", "Westhaven Depot", False, False),
      ("be", "MID", "BE99005", "Midford Junction", False, False),
      ("be", "DUN", "BE99006", "Dunes Junction", False, False),
      ("be", "BORD", "BE99007", "Dunes border", False, False),
      ("nl", "EGT", "NL99001", "Eastgate", True, False),
      ("nl", "BORD", "NL99002", "Dunes border", False, False)]
SL = [("be", "WHS_PF", "01", "Westhaven platforms", "WHS", "39"),
      ("be", "WHY_LP", "02", "Westhaven Yard loading point", "WHY", "43"),
      ("be", "WHD_GT", "03", "Westhaven Depot gate", "WHD", "05")]
for im in IMS:
    sec(im, "11. Primary and subsidiary locations",
        "Location codes for the telematics messages. Every operational point points to its primary location,\n"
        "and the primary location has the same net reference as its operational point (the same node).\n"
        "A subsidiary location points to the primary location it belongs to.")
    for (pim, pid, code, name, pax, freight) in PL:
        if pim != im:
            continue
        iri = f"{im}:pl_{pid}"
        emit(im, iri, ["era:PrimaryLocation", ("rdfs:label", lit(name)), ("era:primaryLocationCode", f'"{code}"'),
                       ("era:primaryLocationName", lit(name)), ("era:passengerFlag", str(pax).lower()),
                       ("era:freightFlag", str(freight).lower()), *common(im), ("era:netReference", f"{im}:op_{pid}_ref")])
        w(im, f"{im}:op_{pid} era:primaryLocation {iri} .\n")
    for (sim, sid, code, name, pl, typ) in SL:
        if sim != im:
            continue
        emit(im, f"{im}:sl_{sid}", ["era:SubsidiaryLocation", ("rdfs:label", lit(name)),
                                   ("era:subsidiaryLocationCode", f'"{code}"'), ("era:subsidiaryLocationName", lit(name)),
                                   ("era:subsidiaryLocationType", f"era-subloctype:{typ}"),
                                   ("era:linkedToPrimaryLocation", f"{im}:pl_{pl}")])

# ---------------------------------------------------------------------------
# Shared stand-in for ERA-managed data
w("shared", PREFIXES)
w("shared", "# Stand-in for data that ERA manages. An IM does not deliver this; it is here so that the example is complete.\n")
emit("shared", f"<http://data.europa.eu/949/referenceBorderPoints/{BORDER_UOPID}>",
     ["era:ReferenceBorderPoint", ("rdfs:label", lit("Dunes border (fictive reference border point)")),
      ("era:borderPointId", f'"{BORDER_UOPID}"'),
      ("gsp:hasGeometry", f"<http://data.europa.eu/949/referenceBorderPoints/{BORDER_UOPID}/geometry>")])
emit("shared", f"<http://data.europa.eu/949/referenceBorderPoints/{BORDER_UOPID}/geometry>",
     ["gsp:Geometry", ("gsp:asWKT", f'"{wkt_point(N["BORD"])}"^^gsp:wktLiteral')])

for (im, iri, nlrs, idx) in AREAS:
    parts = ", ".join("(" + ", ".join(lonlat(p) for p in LINES[n]) + ")" for n in nlrs)
    out[im][idx] = f'{iri}_geom a gsp:Geometry ;\n    gsp:asWKT "MULTILINESTRING({parts})"^^gsp:wktLiteral .\n'

OUT.mkdir(parents=True, exist_ok=True)
for k, name in (("be", "im-a-belgium.ttl"), ("nl", "im-b-netherlands.ttl"), ("shared", "era-managed.ttl")):
    (OUT / name).write_text("\n".join(out[k]).rstrip() + "\n", encoding="utf-8")
    print(name, len(out[k]))
