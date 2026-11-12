<script setup>
// The Turtle box. Every IRI is a link: click replaces the box with that resource, Ctrl + click adds it.
import { computed } from 'vue'
import { describe } from '../lib/turtle.js'
import { home, FILES, fileOf, shrink } from '../lib/rdf.js'

const props = defineProps({ iris: { type: Array, default: () => [] } })
const emit = defineEmits(['go', 'hover', 'remove'])
const blocks = computed(() => props.iris.map((s) => describe(s)).filter(Boolean))
const source = (b) => (b.where === 'vocab' ? 'ERA ontology v3.3.4' : FILES[fileOf(b.subject)]?.name ?? '')

function click(ev, t) {
  ev.preventDefault()
  if (home(t.iri)) emit('go', t.iri, ev.ctrlKey || ev.metaKey)
  else window.open(t.iri, '_blank', 'noopener')
}
</script>

<template>
  <div class="box">
    <p v-if="!blocks.length" class="empty">Click an object in the drawing to see its triples.</p>
    <section v-for="b in blocks" :key="b.subject" class="block" :class="b.where">
      <header><span class="src">{{ source(b) }}</span>
        <button v-if="blocks.length > 1" class="x" title="Remove from the box" @click="emit('remove', b.subject)">×</button></header>
      <pre><template v-for="(line, i) in b.lines" :key="i"><template v-for="(t, j) in line" :key="j"><a v-if="t.k === 'iri'" :href="t.iri" :class="{ subj: t.subject, pred: t.pred, quiet: t.quiet, ext: !home(t.iri) }" :title="home(t.iri) ? 'Click to open, Ctrl + click to add' : 'Opens in a new tab'" @click="click($event, t)" @mouseenter="emit('hover', t.iri)" @mouseleave="emit('hover', null)">{{ t.text }}</a><span v-else :class="t.k">{{ t.text }}</span></template>{{ '\n' }}</template></pre>
    </section>
  </div>
</template>

<style scoped>
.box { height: 100%; overflow: auto; background: var(--c-code-bg); color: var(--c-code); padding: 10px 14px 18px; }
.empty { color: #9aa7bd; font-size: 14px; }
.block { margin-bottom: 14px; }
.block header { display: flex; justify-content: space-between; align-items: center; font: 11px var(--font); color: #8fa0bd; border-bottom: 1px solid #2c3a55; padding-bottom: 2px; margin-bottom: 4px; }
.block.vocab header { color: #e3c56b; }
.x { background: none; border: 0; color: #8fa0bd; font-size: 15px; cursor: pointer; line-height: 1; }
.x:hover { color: #fff; }
pre { margin: 0; font: 12.5px/1.55 var(--mono); white-space: pre-wrap; word-break: break-word; tab-size: 4; }
a { color: #8fd0ff; text-decoration: none; border-bottom: 1px dotted transparent; cursor: pointer; }
a:hover { border-bottom-color: currentColor; background: rgba(255, 214, 23, 0.18); }
a.subj { color: #ffd617; font-weight: 700; }
a.pred { color: #c3b1ff; }
a.quiet { color: #7f8ea8; }
a.ext { color: #9fe3b0; }
.lit { color: #f2b98a; } .num { color: #9fe3b0; } .kw { color: #ff8fb8; } .p { color: #9aa7bd; }
</style>
