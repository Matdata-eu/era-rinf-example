// A small Turtle writer that returns tokens instead of text, so every IRI can become a link.
import { DataFactory } from 'n3'
import { data, vocab, shrink, RDF, RDFS, list, home, predicateOrder } from './rdf.js'
const { namedNode } = DataFactory
const XSD = 'http://www.w3.org/2001/XMLSchema#'
const FIRST = [RDF + 'type', RDFS + 'label']

function term(t, store, depth, out) {
  if (t.termType === 'NamedNode') return out.push({ k: 'iri', iri: t.value, text: shrink(t.value) })
  if (t.termType === 'Literal') {
    const dt = t.datatype?.value
    if (dt === XSD + 'boolean' || dt === XSD + 'integer') return out.push({ k: 'num', text: t.value })
    const s = t.value.includes('\n') ? `"""${t.value}"""` : JSON.stringify(t.value)
    out.push({ k: 'lit', text: s })
    if (t.language) out.push({ k: 'lit', text: '@' + t.language })
    else if (dt && dt !== XSD + 'string') {
      out.push({ k: 'p', text: '^^' })
      out.push({ k: 'iri', iri: dt, text: shrink(dt), quiet: true })
    }
    return
  }
  // blank node: a collection or an anonymous node
  if (store.getQuads(t, namedNode(RDF + 'first'), null, null).length) {
    out.push({ k: 'p', text: '( ' })
    for (const m of list(t, store)) { term(m, store, depth, out); out.push({ k: 'p', text: ' ' }) }
    return out.push({ k: 'p', text: ')' })
  }
  const qs = store.getQuads(t, null, null, null)
  if (!qs.length || depth > 3) return out.push({ k: 'p', text: '[]' })
  out.push({ k: 'p', text: '[ ' })
  qs.forEach((q, i) => {
    predicate(q.predicate, out)
    term(q.object, store, depth + 1, out)
    out.push({ k: 'p', text: i < qs.length - 1 ? ' ; ' : ' ' })
  })
  out.push({ k: 'p', text: ']' })
}
function predicate(p, out) {
  if (p.value === RDF + 'type') out.push({ k: 'kw', text: 'a ' })
  else { out.push({ k: 'iri', iri: p.value, text: shrink(p.value), pred: true }); out.push({ k: 'p', text: ' ' }) }
}

/** Lines of tokens describing one subject, in Turtle. */
export function describe(s) {
  const where = home(s)
  if (!where) return null
  const store = where === 'data' ? data : vocab
  const qs = store.getQuads(namedNode(s), null, null, null)
  const preds = [...predicateOrder(s)]   // as written in the file
  preds.sort((a, b) => (FIRST.indexOf(a) + 1 || 99) - (FIRST.indexOf(b) + 1 || 99))
  const lines = []
  preds.forEach((p, i) => {
    const line = []
    if (i === 0) { line.push({ k: 'iri', iri: s, text: shrink(s), subject: true }); line.push({ k: 'p', text: ' ' }) }
    else line.push({ k: 'p', text: '    ' })
    predicate(namedNode(p), line)
    const objs = qs.filter((q) => q.predicate.value === p)
    objs.forEach((q, j) => { term(q.object, store, 0, line); if (j < objs.length - 1) line.push({ k: 'p', text: ', ' }) })
    line.push({ k: 'p', text: i === preds.length - 1 ? ' .' : ' ;' })
    lines.push(line)
  })
  return { subject: s, where, lines }
}
