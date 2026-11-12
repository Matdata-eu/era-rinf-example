// One in-browser store over the example files, a second one over the bundled v3.3.4 ontology and code lists.
import { Parser, Store, DataFactory } from 'n3'
import be from '../../data/im-a-belgium.ttl?raw'
import nl from '../../data/im-b-netherlands.ttl?raw'
import shared from '../../data/era-managed.ttl?raw'
import vocabTtl from '../vocab/vocab.ttl?raw'

const { namedNode } = DataFactory
export const FILES = {
  be: { name: 'im-a-belgium.ttl', title: 'Infra Alfa (BE)', text: be },
  nl: { name: 'im-b-netherlands.ttl', title: 'Beta Spoor (NL)', text: nl },
  era: { name: 'era-managed.ttl', title: 'Managed by ERA', text: shared },
}
export const ERA = 'http://data.europa.eu/949/'
export const RDF = 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
export const RDFS = 'http://www.w3.org/2000/01/rdf-schema#'
export const GSP = 'http://www.opengis.net/ont/geosparql#'
export const PREFIXES = {}

export const data = new Store()
export const vocab = new Store()
const order = new Map() // subject -> position in its file, to keep the file order when several are shown
const preds = new Map() // subject -> its predicates in the order of the file

function load(store, text, graph) {
  const parser = new Parser()
  let n = 0
  for (const q of parser.parse(text, null, (p, iri) => { if (!(p in PREFIXES)) PREFIXES[p] = iri.value })) {
    store.addQuad(q.subject, q.predicate, q.object, graph ? namedNode(graph) : undefined)
    if (graph && !order.has(q.subject.value)) order.set(q.subject.value, [graph, n++])
    const ps = preds.get(q.subject.value) ?? preds.set(q.subject.value, []).get(q.subject.value)
    if (!ps.includes(q.predicate.value)) ps.push(q.predicate.value)
  }
}
for (const [k, f] of Object.entries(FILES)) load(data, f.text, k)
Object.assign(PREFIXES, { rdf: RDF, owl: 'http://www.w3.org/2002/07/owl#', skos: 'http://www.w3.org/2004/02/skos/core#' })
load(vocab, vocabTtl, null)

// longest namespace first, so era-nv: wins over era:
const byLength = () => Object.entries(PREFIXES).filter(([p]) => p !== '').sort((a, b) => b[1].length - a[1].length)
let sorted = byLength()
export function shrink(iri) {
  for (const [p, ns] of sorted) {
    if (iri.startsWith(ns)) {
      const local = iri.slice(ns.length)
      if (/^[A-Za-z0-9_][A-Za-z0-9_.-]*$/.test(local) && !local.endsWith('.')) return `${p}:${local}`
    }
  }
  return `<${iri}>`
}
export function expand(curie) {
  const i = curie.indexOf(':')
  const ns = PREFIXES[curie.slice(0, i)]
  return ns ? ns + curie.slice(i + 1) : curie
}
export const iri = (c) => (c.includes('://') ? c : expand(c))

export const hasSubject = (store, s) => store.getQuads(namedNode(s), null, null, null).length > 0
/** where an IRI can be described: 'data', 'vocab' or null (external) */
export function home(s) {
  if (hasSubject(data, s)) return 'data'
  if (hasSubject(vocab, s)) return 'vocab'
  return null
}
export const predicateOrder = (s) => preds.get(s) ?? []
export const fileOf = (s) => order.get(s)?.[0]
export const fileOrder = (s) => order.get(s) ?? ['zz', 0]

export function objects(s, p, store = data) {
  return store.getQuads(typeof s === 'string' ? namedNode(s) : s, namedNode(iri(p)), null, null).map((q) => q.object)
}
export const value = (s, p, store = data) => objects(s, p, store)[0]?.value
export function subjects(p, o, store = data) {
  return store.getQuads(null, namedNode(iri(p)), typeof o === 'string' ? namedNode(iri(o)) : o, null).map((q) => q.subject.value)
}
export const instances = (cls) => subjects(RDF + 'type', cls)
export const isA = (s, cls) => objects(s, RDF + 'type').some((o) => o.value === iri(cls))
export function list(head, store = data) {
  const out = []
  let n = head
  while (n && n.value !== RDF + 'nil') {
    const first = store.getQuads(n, namedNode(RDF + 'first'), null, null)[0]
    if (!first) break
    out.push(first.object)
    n = store.getQuads(n, namedNode(RDF + 'rest'), null, null)[0]?.object
  }
  return out
}
export function label(s) {
  for (const store of [data, vocab]) {
    const l = objects(s, RDFS + 'label', store)
    const en = l.find((x) => x.language === 'en') ?? l[0]
    if (en) return en.value
    const pl = objects(s, 'http://www.w3.org/2004/02/skos/core#prefLabel', store)
    const pen = pl.find((x) => x.language === 'en') ?? pl[0]
    if (pen) return pen.value
  }
  return shrink(s)
}
