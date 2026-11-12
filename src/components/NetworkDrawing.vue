<script setup>
// The network, drawn from the Turtle. Every object is clickable and carries its IRI.
import { computed, ref, watch, onMounted } from 'vue'
import { ERA, value, instances, label, objects, shrink, isA } from '../lib/rdf.js'
import { elements, relations, at, pos, stretches, locate, path, im, W, H, Y0 } from '../lib/net.js'

const props = defineProps({
  layers: { type: Object, default: () => ({}) },
  highlight: { type: Array, default: () => [] },
  hover: { type: String, default: null },
  view: { type: Array, default: null },
})
const emit = defineEmits(['select'])
const pick = (ev, iri) => emit('select', iri, ev.ctrlKey || ev.metaKey)
const on = (k) => props.layers[k] !== false

const ORIENT = 'http://data.europa.eu/949/concepts/orientations/'
const OPC = ['#f6d5e5', '#e3d9f7', '#ffd9c2', '#d9f2d0', '#ffe9a8', '#cfe8ff', '#c9ece8']
const dist = (a, b) => Math.hypot(a[0] - b[0], a[1] - b[1])
const tri = (c, u, f, b) => path([[c[0] + u[0] * f, c[1] + u[1] * f], [c[0] - u[0] * b - u[1] * b, c[1] - u[1] * b + u[0] * b], [c[0] - u[0] * b + u[1] * b, c[1] - u[1] * b - u[0] * b]]) + 'Z'

const sols = instances(ERA + 'SectionOfLine').map((s) => ({ iri: s, paths: stretches(value(s, ERA + 'netReference')).map(path), link: value(s, ERA + 'solNature').endsWith('/20') }))
let ci = 0
const ops = [], borders = []
for (const op of instances(ERA + 'OperationalPoint')) {
  const refIri = value(op, ERA + 'netReference')
  const type = label(value(op, ERA + 'opType'))
  if (value(refIri, ERA + 'includes')) {
    const st = stretches(refIri), all = st.flat()
    const xs = all.map((p) => p[0]), ys = all.map((p) => p[1])
    const y0 = Math.min(...ys), y1 = Math.max(...ys)
    const below = y1 > Y0 + 10
    ops.push({ iri: op, paths: st.map(path), color: OPC[ci++ % OPC.length], name: value(op, ERA + 'opName'), uopid: value(op, ERA + 'uopid'), type,
      x: (Math.min(...xs) + Math.max(...xs)) / 2, y: below ? y1 + 62 : y0 - 62 })
  } else {
    const q = pos(refIri)
    borders.push({ iri: op, x: at(q.e, q.off).p[0], y: at(q.e, q.off).p[1], uopid: value(op, ERA + 'uopid'), im: im(op) })
  }
}
const lines = Object.values(elements).map((e) => {
  const lens = e.pts.slice(1).map((p, i) => dist(e.pts[i], p))
  const i = lens.indexOf(Math.max(...lens)), a = e.pts[i], b = e.pts[i + 1], n = lens[i]
  const m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2], u = [(b[0] - a[0]) / n, (b[1] - a[1]) / n]
  let ang = (Math.atan2(b[1] - a[1], b[0] - a[0]) * 180) / Math.PI
  if (Math.abs(ang) > 90) ang += 180
  return { ...e, d: path(e.pts), arrow: tri(m, u, 9, 6), m, ang, text: n > 75 ? [`${e.id} · ${e.length} m`] : [`${e.length} m`, e.id], origin: e.pts[0] }
})
const switches = instances(ERA + 'Switch').map((s) => { const q = pos(value(s, ERA + 'netReference')); return { iri: s, p: at(q.e, q.off).p, id: s.split('/sw_')[1], im: im(s) } })
const signals = instances(ERA + 'Signal').map((s) => {
  const refIri = value(s, ERA + 'netReference'), q = pos(refIri), { p, u } = at(q.e, q.off)
  const t = value(refIri, ERA + 'appliesToDirection') === ORIENT + '01' ? [-u[0], -u[1]] : u   // direction of travel it applies to
  const k = value(value(s, ERA + 'hasOrientation'), ERA + 'side').endsWith('Left') ? -1 : 1     // side is relative to the element
  const n = [u[1] * k * -1, -u[0] * k * -1], c = [p[0] + n[0] * 15, p[1] + n[1] * 15]
  return { iri: s, p, c, d: tri(c, t, 8, 5), id: value(s, ERA + 'signalId'), tx: c[0] - t[0] * 4, ty: c[1] + n[1] * 13 + 4 }
})
const platforms = instances(ERA + 'PlatformEdge').map((pe) => {
  const side = pe.endsWith('1') || pe.includes('EGT') ? -7 : 7   // Eastgate's platform is on the outside of the loop
  const st = stretches(value(pe, ERA + 'netReference')).map((s) => s.map(([x, y]) => [x, y + side]))
  const left = st.flat().reduce((a, b) => (b[0] < a[0] ? b : a))
  return { iri: pe, paths: st.map(path), id: value(pe, ERA + 'platformId'), lx: left[0] - 5, ly: left[1] + 3 }
})
const tunnels = instances(ERA + 'Tunnel').map((t) => {
  const st = stretches(value(t, ERA + 'netReference')), all = st.flat()
  return { iri: t, paths: st.map(path), name: label(t), x: all.reduce((a, p) => a + p[0], 0) / all.length, y: Math.min(...all.map((p) => p[1])) - 30 }
})
const crossings = instances(ERA + 'LevelCrossing').map((t) => {
  const pts = stretches(value(t, ERA + 'netReference')).map((s) => [(s[0][0] + s[s.length - 1][0]) / 2, s[0][1]])
  return { iri: t, pts, name: label(t), x: pts.reduce((a, p) => a + p[0], 0) / pts.length, y: Math.min(...pts.map((p) => p[1])) - 30 }
})
const posts = instances(ERA + 'KilometricPost').map((k) => { const q = pos(value(k, ERA + 'netReference')); return { iri: k, p: at(q.e, q.off).p, km: parseFloat(value(k, ERA + 'kilometer')) } })
// a primary location shares the net reference of its operational point: its mark sits halfway along the longest stretch
function middle(ref) {
  if (isA(ref, ERA + 'NetPointReference')) { const q = pos(ref); return at(q.e, q.off).p }
  const len = (p) => p.slice(1).reduce((t, q, i) => t + Math.hypot(q[0] - p[i][0], q[1] - p[i][1]), 0)
  const pts = stretches(ref).reduce((a, b) => (len(b) > len(a) ? b : a))
  let d = len(pts) / 2
  for (let i = 1; i < pts.length; i++) {
    const l = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1])
    if (d <= l) { const t = l ? d / l : 0; return [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * t, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * t] }
    d -= l
  }
  return pts[pts.length - 1]
}
// tracks: a running track or siding is a linear reference over one or more netelements
const trackList = ['RunningTrack', 'Siding'].flatMap((c) => instances(ERA + c).map((t) => {
  const ref = value(t, ERA + 'netReference')
  return { iri: t, sid: c === 'Siding', id: value(t, ERA + 'trackId') ?? value(t, ERA + 'sidingId'), paths: stretches(ref).map(path), m: middle(ref) }
}))
const locations = instances(ERA + 'PrimaryLocation').map((l) => ({ iri: l, p: middle(value(l, ERA + 'netReference')), code: value(l, ERA + 'primaryLocationCode') }))

const marks = computed(() => {
  const iris = [...props.highlight]
  const out = iris.map((s) => ({ ...locate(s), cls: 'hl' }))
  if (props.hover && !iris.includes(props.hover)) out.push({ ...locate(props.hover), cls: 'hl hov' })
  return out
})

// viewBox: follows the scene (animated), and the reader can zoom with the wheel and drag to pan
const FULL = [0, 0, W, H]
const svg = ref(null)
const vb = ref(props.view ?? FULL)
let raf = 0
function animate(target) {
  const from = [...vb.value], t0 = performance.now()
  cancelAnimationFrame(raf)
  const step = (t) => {
    const k = Math.min(1, (t - t0) / 450), e = 1 - Math.pow(1 - k, 3)
    vb.value = from.map((v, i) => v + (target[i] - v) * e)
    if (k < 1) raf = requestAnimationFrame(step)
  }
  raf = requestAnimationFrame(step)
}
watch(() => props.view, (to) => animate(to ?? FULL))
const reset = () => animate(props.view ?? FULL)

function toSvg(ev) {
  const m = svg.value.getScreenCTM().inverse()
  return [m.a * ev.clientX + m.e, m.d * ev.clientY + m.f]
}
function zoom(factor, around) {
  cancelAnimationFrame(raf)
  const [x, y, w, h] = vb.value
  const nw = Math.min(W * 1.5, Math.max(120, w * factor)), k = nw / w
  const [cx, cy] = around ?? [x + w / 2, y + h / 2]
  vb.value = [cx - (cx - x) * k, cy - (cy - y) * k, nw, h * k]
}
const wheel = (ev) => zoom(ev.deltaY > 0 ? 1.18 : 1 / 1.18, toSvg(ev))
let drag = null, dragged = false
function down(ev) { if (ev.button === 0) { drag = { x: ev.clientX, y: ev.clientY, vb: [...vb.value] }; dragged = false } }
function moveTo(ev) {
  if (!drag) return
  const dx = ev.clientX - drag.x, dy = ev.clientY - drag.y
  if (!dragged && Math.hypot(dx, dy) < 5) return
  dragged = true
  cancelAnimationFrame(raf)
  const scale = 1 / svg.value.getScreenCTM().a
  vb.value = [drag.vb[0] - dx * scale, drag.vb[1] - dy * scale, drag.vb[2], drag.vb[3]]
}
const up = () => { drag = null }
const swallow = (ev) => { if (dragged) { ev.stopPropagation(); dragged = false } }   // a drag is not a click
const border = borders.find((b) => b.im === 'be')
</script>

<template>
  <div class="wrap">
  <div class="zoom"><button title="Zoom in" @click="zoom(1 / 1.4)">+</button><button title="Zoom out" @click="zoom(1.4)">−</button><button title="Reset the view" @click="reset">⤢</button></div>
  <svg ref="svg" :viewBox="vb.join(' ')" class="net" :class="{ grabbing: dragged }" preserveAspectRatio="xMidYMid meet" role="img" aria-label="Schematic drawing of the example network"
    @wheel.prevent="wheel" @pointerdown="down" @pointermove="moveTo" @pointerup="up" @pointerleave="up" @click.capture="swallow">
    <g v-if="on('sols')">
      <g v-for="s in sols" :key="s.iri" class="pick" @click="pick($event, s.iri)"><title>{{ shrink(s.iri) }} · section of line {{ label(s.iri) }}{{ s.link ? ' (link)' : '' }}</title>
        <path v-for="(d, i) in s.paths" :key="i" :d="d" class="sol" :class="{ link: s.link }" /></g>
    </g>
    <g v-if="on('ops')">
      <g v-for="o in ops" :key="o.iri" class="pick" @click="pick($event, o.iri)"><title>{{ shrink(o.iri) }} · operational point</title>
        <path v-for="(d, i) in o.paths" :key="i" :d="d" class="op" :stroke="o.color" />
        <rect :x="o.x - 88" :y="o.y - 14" width="176" height="34" rx="5" :fill="o.color" />
        <text :x="o.x" :y="o.y" class="opname">{{ o.name }} ({{ o.uopid }})</text>
        <text :x="o.x" :y="o.y + 14" class="small">{{ o.type }}</text>
      </g>
    </g>
    <g v-if="border" class="pick" @click="pick($event, border.iri)"><title>{{ shrink(border.iri) }} · border point</title>
      <line :x1="border.x" y1="100" :x2="border.x" y2="690" class="border" />
      <line :x1="border.x" y1="100" :x2="border.x" y2="690" class="hit" />
      <text :x="border.x" y="70" class="opname">border point {{ border.uopid }}</text>
      <text :x="border.x - 12" y="92" class="imbe" text-anchor="end">Infra Alfa (BE)</text>
      <text :x="border.x + 12" y="92" class="imnl" text-anchor="start">Beta Spoor (NL)</text>
    </g>

    <g class="marks">
      <g v-for="(m, i) in marks" :key="i" :class="m.cls">
        <path v-for="(l, j) in m.lines" :key="j" :d="path(l)" />
        <circle v-for="(p, j) in m.points" :key="'p' + j" :cx="p[0]" :cy="p[1]" :r="m.chords ? 7 : 13" />
        <path v-for="(c, j) in m.chords ?? []" :key="'c' + j" :d="`M${c.a[0]},${c.a[1]} Q${c.c[0]},${c.c[1]} ${c.b[0]},${c.b[1]}`" class="chord" :class="c.nav" />
      </g>
    </g>

    <g v-if="on('structures')">
      <g v-for="t in tunnels" :key="t.iri" class="pick" @click="pick($event, t.iri)"><title>{{ shrink(t.iri) }}</title>
        <path v-for="(d, i) in t.paths" :key="i" :d="d" class="tunnel" /><text :x="t.x" :y="t.y" class="feat">{{ t.name }}</text></g>
      <g v-for="t in crossings" :key="t.iri" class="pick" @click="pick($event, t.iri)"><title>{{ shrink(t.iri) }}</title>
        <line v-for="(p, i) in t.pts" :key="i" :x1="p[0]" :y1="p[1] - 14" :x2="p[0]" :y2="p[1] + 14" class="lc" /><text :x="t.x" :y="t.y" class="feat">{{ t.name }}</text></g>
    </g>
    <g v-if="on('platforms')">
      <g v-for="p in platforms" :key="p.iri" class="pick" @click="pick($event, p.iri)"><title>{{ shrink(p.iri) }}</title>
        <path v-for="(d, i) in p.paths" :key="i" :d="d" class="pe" /><text :x="p.lx" :y="p.ly" class="small" text-anchor="end">pl. {{ p.id }}</text></g>
    </g>

    <g v-if="layers.tracks === true">
      <g v-for="t in trackList" :key="t.iri" class="pick" @click="pick($event, t.iri)"><title>{{ shrink(t.iri) }} · {{ t.sid ? 'siding' : 'running track' }} {{ t.id }}</title>
        <path v-for="(d, i) in t.paths" :key="i" :d="d" class="trk" :class="t.sid ? 'sid' : 'run'" /></g>
    </g>

    <g v-for="e in lines" :key="e.iri" class="pick" @click="pick($event, e.iri)"><title>{{ shrink(e.iri) }} · linear element, {{ e.length }} m</title>
      <path :d="e.d" class="hit" /><path :d="e.d" class="le" :class="e.im" /><path :d="e.arrow" :class="'fill-' + e.im" />
      <text v-for="(t, j) in e.text" :key="j" :transform="`translate(${e.m[0]},${e.m[1]}) rotate(${e.ang})`" :y="-13 - 11 * (e.text.length - 1 - j)" class="lelab" :class="'fill-' + e.im">{{ t }}</text>
    </g>

    <g v-if="layers.tracks === true">
      <g v-for="t in trackList" :key="t.iri" class="pick" @click="pick($event, t.iri)"><title>{{ shrink(t.iri) }} · {{ t.sid ? 'siding' : 'running track' }} {{ t.id }}</title>
        <text :x="t.m[0]" :y="t.m[1] + 12" class="trkt" :class="t.sid ? 'sid' : 'run'">{{ t.id }}</text></g>
    </g>
    <g v-if="on('km')">
      <g v-for="k in posts" :key="k.iri" class="pick" @click="pick($event, k.iri)"><title>{{ shrink(k.iri) }}</title>
        <line :x1="k.p[0]" :y1="k.p[1] + 4" :x2="k.p[0]" :y2="k.p[1] + 15" class="kp" /><text :x="k.p[0]" :y="k.p[1] + 25" class="kpt">km {{ k.km }}</text></g>
    </g>
    <g v-if="on('switches')">
      <g v-for="s in switches" :key="s.iri" class="pick" @click="pick($event, s.iri)"><title>{{ shrink(s.iri) }} · switch</title>
        <circle :cx="s.p[0]" :cy="s.p[1]" r="5" class="sw" />
        <text :x="s.p[0] + (s.im === 'nl' ? 8 : -8)" :y="s.p[1] + 17" class="swt" :text-anchor="s.im === 'nl' ? 'start' : 'end'">{{ s.id }}</text></g>
    </g>
    <g v-if="on('signals')">
      <g v-for="s in signals" :key="s.iri" class="pick" @click="pick($event, s.iri)"><title>{{ shrink(s.iri) }} · signal</title>
        <line :x1="s.p[0]" :y1="s.p[1]" :x2="s.c[0]" :y2="s.c[1]" class="sigl" /><path :d="s.d" class="sig" /><circle :cx="s.c[0]" :cy="s.c[1]" r="10" class="hitc" />
        <text :x="s.tx" :y="s.ty" class="sigt">{{ s.id }}</text></g>
    </g>
    <g v-if="on('locations')">
      <g v-for="l in locations" :key="l.iri" class="pick" @click="pick($event, l.iri)"><title>{{ shrink(l.iri) }} · primary location</title>
        <rect :x="l.p[0] - 4" :y="l.p[1] - 4" width="8" height="8" class="pl" :transform="`rotate(45 ${l.p[0]} ${l.p[1]})`" />
        <text :x="l.p[0]" :y="l.p[1] + 40" class="plt">PLC {{ l.code }}</text></g>
    </g>
  </svg>
  </div>
</template>

<style scoped>
.wrap { position: relative; width: 100%; height: 100%; }
.net { width: 100%; height: 100%; display: block; background: var(--c-panel); cursor: grab; touch-action: none; }
.net.grabbing { cursor: grabbing; }
.zoom { position: absolute; top: 8px; right: 8px; display: flex; flex-direction: column; gap: 4px; z-index: 1; }
.zoom button { width: 28px; height: 28px; border: 1px solid var(--c-stroke); border-radius: 6px; background: var(--c-panel); color: var(--c-ink); font-size: 16px; line-height: 1; cursor: pointer; }
.zoom button:hover { border-color: var(--c-era); color: var(--c-era); }
text { font-family: var(--font); font-size: 11px; fill: var(--c-ink); text-anchor: middle; user-select: none; }
.pick { cursor: pointer; }
.pick:hover .le, .pick:hover .pe { stroke-width: 4.5; }
.pick:hover .sw { stroke-width: 3.5; }
.hit { fill: none; stroke: transparent; stroke-width: 16; }
.hitc { fill: transparent; }
.le { fill: none; stroke-width: 2.6; stroke-linejoin: round; }
.le.be { stroke: var(--c-be); } .le.nl { stroke: var(--c-nl); }
.fill-be { fill: var(--c-be); } .fill-nl { fill: var(--c-nl); }
.lelab { font-size: 10.5px; font-weight: 700; }
.op { fill: none; stroke-width: 30; stroke-linecap: round; stroke-linejoin: round; }
.sol { fill: none; stroke: #e3e6ea; stroke-width: 30; stroke-linejoin: round; }
.sol.link { stroke: #8d99ab; }
.trk { fill: none; stroke-width: 13; stroke-linejoin: round; opacity: 0.5; }
.trk.run { stroke: #1f9e8f; } .trk.sid { stroke: #a2679f; }
.pick:hover .trk { opacity: 0.8; }
.trkt { font-size: 9px; font-weight: 700; text-anchor: middle; paint-order: stroke; stroke: #fff; stroke-width: 3px; }
.trkt.run { fill: #11695f; } .trkt.sid { fill: #7a437a; }
.tunnel { fill: none; stroke: #555; stroke-width: 13; stroke-dasharray: 3 3; opacity: 0.45; }
.lc { stroke: #8a4b08; stroke-width: 6; opacity: 0.8; }
.pe { fill: none; stroke: #333; stroke-width: 4; }
.sw { fill: #fff; stroke: #111; stroke-width: 2; }
.swt { font-weight: 700; font-size: 10.5px; }
.sig { fill: var(--c-sig); } .sigl { stroke: var(--c-sig); stroke-width: 1.2; }
.sigt { fill: var(--c-sig); font-size: 10px; font-weight: 700; }
.kp { stroke: #111; stroke-width: 1.5; } .kpt { font-size: 9.5px; fill: #444; }
.pl { fill: #111; } .plt { font-size: 9.5px; }
.small { font-size: 10px; fill: #333; }
.opname { font-weight: 700; font-size: 12px; }
.feat { font-size: 10px; font-style: italic; }
.border { stroke: #111; stroke-width: 1.5; stroke-dasharray: 7 5; }
.imbe { fill: var(--c-be); font-weight: 700; font-size: 14px; } .imnl { fill: var(--c-nl); font-weight: 700; font-size: 14px; }
.marks path { fill: none; stroke: var(--c-hl); stroke-width: 15; stroke-linecap: round; stroke-linejoin: round; opacity: 0.85; }
.marks circle { fill: var(--c-hl); fill-opacity: 0.55; stroke: #b88a00; stroke-width: 2; }
.marks path.chord { stroke-width: 5; opacity: 1; stroke: #1f9d55; }
.marks path.chord.None { stroke: #d0021b; stroke-dasharray: 2 7; }
.marks .hov path { stroke: #ff9d2e; opacity: 0.7; } .marks .hov circle { fill: #ff9d2e; stroke: #c05a00; }
</style>
