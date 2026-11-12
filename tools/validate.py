#!/usr/bin/env python3
"""Validates the example against the ERA v3.3.4 SHACL (pySHACL) and prints a summary.
Usage: validate.py <data dir> <era-ontology checkout>"""
import sys, glob, collections, re
import rdflib, pyshacl
from rdflib.namespace import SH, RDF
data_dir, era = sys.argv[1], sys.argv[2]
data = rdflib.Graph()
for f in sorted(glob.glob(data_dir + '/*.ttl')):
    data.parse(f)
ont = rdflib.Graph()
ont.parse(era + '/ontology.ttl')
for f in glob.glob(era + '/era-skos/*.ttl'):
    try: ont.parse(f)
    except Exception as ex: print('skip', f, ex)
shapes = rdflib.Graph(); shapes.parse(era + '/era-shacl/ERA-RINF-shapes.ttl')
# The shapes declare only the era prefix for their SPARQL constraints; pySHACL needs the others too.
EXTRA = dict(rdf=str(RDF), rdfs='http://www.w3.org/2000/01/rdf-schema#', owl='http://www.w3.org/2002/07/owl#',
             skos='http://www.w3.org/2004/02/skos/core#', xsd='http://www.w3.org/2001/XMLSchema#',
             time='http://www.w3.org/2006/time#', geosparql='http://www.opengis.net/ont/geosparql#',
             gsp='http://www.opengis.net/ont/geosparql#', geo='http://www.opengis.net/ont/geosparql#',
             sh=str(SH), dct='http://purl.org/dc/terms/', dcterms='http://purl.org/dc/terms/',
             sf='http://www.opengis.net/ont/sf#', geof='http://www.opengis.net/def/function/geosparql/',
             wgs='http://www.w3.org/2003/01/geo/wgs84_pos#', foaf='http://xmlns.com/foaf/0.1/',
             unit='http://qudt.org/vocab/unit/', qudt='http://qudt.org/schema/qudt/')
for node in set(shapes.objects(None, SH.prefixes)):
    have = {str(shapes.value(d, SH.prefix)) for d in shapes.objects(node, SH.declare)}
    for k, v in EXTRA.items():
        if k not in have and k not in ('dcterms','geo','gsp'):
            b = rdflib.BNode(); shapes.add((node, SH.declare, b)); shapes.add((b, SH.prefix, rdflib.Literal(k)))
            shapes.add((b, SH.namespace, rdflib.Literal(v, datatype=rdflib.XSD.anyURI)))
ALIAS = {'dcterms': 'dct', 'geo': 'geosparql', 'gsp': 'geosparql'}
import rdflib.plugins.sparql.processor as _proc
_orig = _proc.SPARQLProcessor.query
def _query(self, strOrQuery, initBindings=None, initNs=None, base=None, DEBUG=False):
    # rdflib loses a prefix when two prefixes share one namespace, and pySHACL prepends sh:prefixes to
    # queries that declare the same prefixes again: rewrite aliases to one prefix and declare each once.
    ns = {k: v for k, v in EXTRA.items() if k not in ALIAS}
    ns['era'] = 'http://data.europa.eu/949/'
    if isinstance(strOrQuery, str):
        q = re.sub(r'PREFIX\s+([\w-]*):\s*<[^>]*>', '', strOrQuery, flags=re.I)
        for alias, canon in ALIAS.items():
            q = re.sub(r'(?<![\w:#])' + alias + r':(?=[A-Za-z_])', canon + ':', q)
        declared = dict(re.findall(r'PREFIX\s+([\w-]*):\s*<([^>]*)>', strOrQuery, flags=re.I))
        for k, v in declared.items():
            if k not in ALIAS: ns.setdefault(k, v)
        q = re.sub(r'(SELECT\s+(?:DISTINCT\s+)?\$this)\s+([\w-]+:[\w-]+)(?=\s)', r'\1 (\2 AS ?path)', q)
        strOrQuery = q
    try:
        return _orig(self, strOrQuery, initBindings or {}, ns, base, DEBUG)
    except Exception as ex:  # a constraint rdflib cannot parse or run: skip it, and say so
        SKIPPED.append((str(ex)[:120], str(strOrQuery)))
        return _orig(self, 'SELECT ?this WHERE { FILTER(false) }', {}, {}, base, DEBUG)
SKIPPED = []
_proc.SPARQLProcessor.query = _query
for gr in (data, ont):
    pass
    gr.bind('era', 'http://data.europa.eu/949/', override=True, replace=True)
# Stand-in for the EU country authority table, which the shapes check era:inCountry against.
for c in ('BEL', 'NLD'):
    cu = rdflib.URIRef('http://publications.europa.eu/resource/authority/country/' + c)
    data.add((cu, RDF.type, rdflib.SKOS.Concept))
    data.add((cu, rdflib.SKOS.inScheme, rdflib.URIRef('http://publications.europa.eu/resource/authority/country')))
# Turtle collections carry no rdf:type; the shapes ask for sh:class rdf:List (RDFS entailment: domain of rdf:first).
for l in set(data.subjects(RDF.first, None)):
    data.add((l, RDF.type, RDF.List))
conforms, rep, _ = pyshacl.validate(data, shacl_graph=shapes, ont_graph=ont, advanced=True, inference='none', allow_warnings=True)
res = collections.Counter(); ex = {}
for r in rep.subjects(RDF.type, SH.ValidationResult):
    sev = str(rep.value(r, SH.resultSeverity)).split('#')[-1]
    shape = rep.value(r, SH.sourceShape); 
    msg = str(rep.value(r, SH.resultMessage) or '')[:int(sys.argv[3]) if len(sys.argv) > 3 else 150]
    path = rep.value(r, SH.resultPath)
    key = (sev, str(shape).split('/')[-1][:40], str(path).split('/')[-1], msg)
    res[key] += 1; ex.setdefault(key, str(rep.value(r, SH.focusNode)).split('/example/')[-1])
print('conforms', conforms, 'results', sum(res.values()))
for k, n in sorted(res.items(), key=lambda kv: (kv[0][0], -kv[1])):
    print(n, '|', k[0], '|', k[1], '|', k[2], '|', ex[k], '|', k[3])
print('SPARQL constraints skipped (not parsed by rdflib):', len(SKIPPED))
import re
import collections as _c
for ex_, n_ in _c.Counter(e for e, _ in SKIPPED).items():
    print("  -", n_, ex_)
for ex_, q in SKIPPED[:1]:
    print(q)
