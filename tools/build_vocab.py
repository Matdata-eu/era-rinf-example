#!/usr/bin/env python3
"""Writes src/vocab/vocab.ttl: the v3.3.4 ontology plus the SKOS concepts (and their schemes) the example uses.
Usage: build_vocab.py <example data dir> <era-ontology clone at v3.3.4> <out.ttl>"""
import sys, glob
import rdflib
from rdflib import RDF, Namespace, URIRef
SKOS = Namespace('http://www.w3.org/2004/02/skos/core#')
data = rdflib.Graph()
for f in glob.glob(sys.argv[1] + '/*.ttl'): data.parse(f)
onto = rdflib.Graph(); onto.parse(sys.argv[2] + '/ontology.ttl')
skos = rdflib.Graph()
for f in glob.glob(sys.argv[2] + '/era-skos/*.ttl'): skos.parse(f)
out = rdflib.Graph()
for t in onto: out.add(t)
used = {o for o in data.objects() if isinstance(o, URIRef) and (o, None, None) in skos}
schemes = set()
for c in used:
    for t in skos.triples((c, None, None)): out.add(t)
    schemes |= set(skos.objects(c, SKOS.inScheme))
for s in schemes:
    for p, o in skos.predicate_objects(s):
        if p != SKOS.hasTopConcept: out.add((s, p, o))
for p, n in data.namespaces(): out.bind(p, n)
out.serialize(sys.argv[3], format='turtle')
print(len(out), 'triples,', len(used), 'concepts,', len(schemes), 'schemes')
