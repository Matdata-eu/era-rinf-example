// Everything the drawing needs, computed from the Turtle: element shapes from the schematic WKT,
// positions from the topology (linear element + offset from origin).
import { data, ERA, GSP, RDF, objects, value, instances, isA, list, subjects } from './rdf.js'

export const SX = 0.52, SY = 2.5, X0 = 70, Y0 = 440
export const W = X0 * 2 + 3600 * SX, H = 720
const scr = (lon, lat) => [X0 + ((lon - 2.9) / 2e-4) * SX, Y0 - ((lat - 52.6) / 1.2e-4) * SY]
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1])
const schem = (a, b) => Math.hypot((a[0] - b[0]) / SX, (a[1] - b[1]) / SY)   // lengths in schematic units, as in the WKT
const num = (s, p) => parseFloat(value(s, p))

export const elements = {}
for (const e of instances(ERA + 'LinearElement')) {
  const wkt = value(value(e, GSP + 'hasGeometry'), GSP + 'asWKT')
  const pts = [...wkt.matchAll(/(-?\d+\.\d+) (-?\d+\.\d+)/g)].map((m) => scr(+m[1], +m[2]))
  elements[e] = { iri: e, pts, length: num(e, ERA + 'lengthOfNetLinearElement'), id: e.split('/le_')[1], im: e.includes('/nl/') ? 'nl' : 'be' }
}
const seglens = (pts) => pts.slice(1).map((p, i) => schem(pts[i], p))

/** screen point and unit tangent (origin to end) at an offset in metres */
export function at(e, off) {
  const { pts, length } = elements[e]
  const sl = seglens(pts)
  let d = (off / length) * sl.reduce((a, b) => a + b, 0)
  for (let i = 0; i < sl.length; i++) {
    if (d <= sl[i] + 1e-9 || i === sl.length - 1) {
      const a = pts[i], b = pts[i + 1], t = Math.min(1, d / sl[i]), n = dist(a, b)
      return { p: [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t], u: [(b[0] - a[0]) / n, (b[1] - a[1]) / n] }
    }
    d -= sl[i]
  }
}
export function sub(e, lo, hi) {
  const { pts, length } = elements[e]
  const sl = seglens(pts), tot = sl.reduce((a, b) => a + b, 0)
  const out = [at(e, lo).p]
  let acc = 0
  sl.forEach((s, i) => { acc += s; if ((lo / length) * tot + 1e-9 < acc && acc < (hi / length) * tot - 1e-9) out.push(pts[i + 1]) })
  out.push(at(e, hi).p)
  return out
}

// net relations: which end of A meets which end of B
export const relations = instances(ERA + 'NetRelation').map((r) => ({
  iri: r,
  a: value(r, ERA + 'elementA'), b: value(r, ERA + 'elementB'),
  aOrigin: value(r, ERA + 'isOnOriginOfElementA') === 'true', bOrigin: value(r, ERA + 'isOnOriginOfElementB') === 'true',
  nav: value(r, ERA + 'navigability').split('/').pop(),
}))
const endOf = {}
for (const r of relations) { endOf[r.a + '|' + r.b] = r.aOrigin; endOf[r.b + '|' + r.a] = r.bOrigin }

export function pos(npr) {
  const tc = value(npr, ERA + 'hasTopoCoordinate')
  return tc ? { e: value(tc, ERA + 'onLinearElement'), off: num(tc, ERA + 'offsetFromOrigin') } : null
}
export const posTc = (tc) => ({ e: value(tc, ERA + 'onLinearElement'), off: num(tc, ERA + 'offsetFromOrigin') })

/** polylines covered by a linear or an area reference */
export function stretches(ref) {
  if (isA(ref, ERA + 'NetAreaReference')) return list(objects(ref, ERA + 'includes')[0]).flatMap((m) => stretches(m.value))
  const seq = list(objects(ref, ERA + 'hasSequence')[0]).map((t) => t.value)
  const s = pos(value(ref, ERA + 'startsAt')), en = pos(value(ref, ERA + 'endsAt'))
  return seq.map((e, i) => {
    const L = elements[e].length
    let lo = 0, hi = L
    if (seq.length === 1) [lo, hi] = [Math.min(s.off, en.off), Math.max(s.off, en.off)]
    else if (i === 0) [lo, hi] = endOf[e + '|' + seq[1]] ? [0, s.off] : [s.off, L]
    else if (i === seq.length - 1) [lo, hi] = endOf[e + '|' + seq[i - 1]] ? [0, en.off] : [en.off, L]
    return sub(e, lo, hi)
  })
}

const OWNER = ['netReference', 'hasTopoCoordinate', 'startsAt', 'endsAt', 'hasOrientation', 'hasLrsCoordinate', 'validity', 'primaryLocation'].map((p) => ERA + p)
  .concat([GSP + 'hasGeometry', 'http://www.w3.org/2006/time#hasBeginning'])
const AREA = ['contactLineSystem', 'etcs', 'trainDetectionSystem', 'linesideDistanceIndication'].map((p) => ERA + p)

/** Where a resource is on the drawing: { points: [[x,y]], lines: [[[x,y],...]] }. Works for any node of the example. */
export function locate(s, seen = new Set()) {
  const none = { points: [], lines: [] }
  if (!s || seen.has(s)) return none
  seen.add(s)
  if (elements[s]) return { points: [], lines: [elements[s].pts] }
  if (isA(s, ERA + 'NetRelation')) {
    const r = relations.find((x) => x.iri === s)
    // a chord from a point a little way along A to a point a little way along B, bending through the meeting point
    const along = (e, origin) => {
      const L = elements[e].length, px = elements[e].pts.slice(1).reduce((t, q, i) => t + dist(elements[e].pts[i], q), 0)
      const d = L * Math.min(0.45, 34 / px)
      return at(e, origin ? d : L - d).p
    }
    const node = at(r.a, r.aOrigin ? 0 : elements[r.a].length).p
    return { points: [node], lines: [], chords: [{ a: along(r.a, r.aOrigin), b: along(r.b, r.bOrigin), c: node, nav: r.nav }] }
  }
  if (isA(s, ERA + 'TopologicalCoordinate')) { const q = posTc(s); return { points: [at(q.e, q.off).p], lines: [] } }
  if (isA(s, ERA + 'NetPointReference')) { const q = pos(s); return q ? { points: [at(q.e, q.off).p], lines: [] } : none }
  if (isA(s, ERA + 'NetLinearReference') || isA(s, ERA + 'NetAreaReference')) return { points: [], lines: stretches(s) }
  const ref = value(s, ERA + 'netReference')
  if (ref) return locate(ref, seen)
  // a subsystem node: every track that points to it
  const users = AREA.flatMap((p) => subjects(p, s))
  if (users.length) return { points: [], lines: users.flatMap((t) => locate(t, new Set(seen)).lines) }
  // a helper node (geometry, validity, orientation, LRS coordinate ...): its owner
  for (const p of OWNER) { const o = subjects(p, s)[0]; if (o) return locate(o, seen) }
  const lrs = subjects(ERA + 'hasLRS', s)
  if (lrs.length) return { points: lrs.flatMap((k) => locate(k, new Set(seen)).points), lines: [] }
  const sl = value(s, ERA + 'linkedToPrimaryLocation')
  if (sl) return locate(sl, seen)
  return none
}

export const path = (pts) => 'M' + pts.map(([x, y]) => `${x.toFixed(1)},${y.toFixed(1)}`).join(' L')
export const im = (s) => (s.includes('/nl/') ? 'nl' : 'be')
export function bbox(iris, pad = 60) {
  const pts = iris.flatMap((s) => { const l = locate(s); return [...l.points, ...l.lines.flat()] })
  if (!pts.length) return null
  const xs = pts.map((p) => p[0]), ys = pts.map((p) => p[1])
  return [Math.min(...xs) - pad, Math.min(...ys) - pad, Math.max(...xs) - Math.min(...xs) + 2 * pad, Math.max(...ys) - Math.min(...ys) + 2 * pad]
}
