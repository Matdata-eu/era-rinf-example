<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import NetworkDrawing from './components/NetworkDrawing.vue'
import TurtleBox from './components/TurtleBox.vue'
import { scenes } from './scenes.js'
import { iri, home, fileOrder } from './lib/rdf.js'
import { bbox } from './lib/net.js'
import logo from './assets/era-logo.svg'

const start = Math.max(0, scenes.findIndex((s) => '#' + s.id === location.hash))
const index = ref(start)
const scene = computed(() => scenes[index.value])
const sceneBox = computed(() => scene.value.box.map(iri))

// the Turtle box, with its own history inside a scene
const history = ref([sceneBox.value])
const at = ref(0)
const box = computed(() => history.value[at.value])
const hover = ref(null)
function push(next) { history.value = [...history.value.slice(0, at.value + 1), next]; at.value = history.value.length - 1 }
function go(target, add) {
  if (!home(target)) return
  if (!add) return push([target])
  if (!box.value.includes(target)) push([...box.value, target])
}
const remove = (s) => push(box.value.filter((x) => x !== s))
const reset = () => push(sceneBox.value)
const pristine = computed(() => box.value.join() === sceneBox.value.join())

watch(index, () => { history.value = [sceneBox.value]; at.value = 0; hover.value = null })
watch(index, () => window.history.replaceState(null, '', '#' + scene.value.id))

// the drawing follows the scene until the reader starts exploring
const highlight = computed(() => (pristine.value ? (scene.value.highlight ?? scene.value.box).map(iri) : box.value))
const view = computed(() => {
  const f = scene.value.focus
  if (!f) return null
  if (Array.isArray(f)) return bbox(f.map(iri), 70)
  const [x, y, w, h] = bbox([iri(f.at)], 0)          // a window of a given width around one object
  return [x + w / 2 - f.width / 2, y + h / 2 - f.width * 0.28, f.width, f.width * 0.56]
})
const layers = computed(() => scene.value.layers ?? {})

const move = (d) => { index.value = Math.min(scenes.length - 1, Math.max(0, index.value + d)) }
function key(ev) {
  if (ev.target.closest?.('input, textarea')) return
  if (ev.key === 'ArrowRight' || ev.key === 'PageDown') move(1)
  if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') move(-1)
}
onMounted(() => window.addEventListener('keydown', key))
onUnmounted(() => window.removeEventListener('keydown', key))
</script>

<template>
  <div class="page">
    <header class="top">
      <img :src="logo" alt="European Union Agency for Railways" class="logo" />
      <div class="titles"><h1>RINF by example</h1><span>A fictive network on ERA ontology v3.3.4</span></div>
      <nav class="steps" aria-label="Scenes">
        <button v-for="(s, i) in scenes" :key="s.id" :class="{ on: i === index }" :title="s.title" :aria-label="s.title" @click="index = i">{{ i + 1 }}</button>
      </nav>
    </header>

    <main :class="{ wide: !scene.focus }">
      <div class="drawing"><NetworkDrawing :layers="layers" :highlight="highlight" :hover="hover" :view="view" @select="go" /></div>
      <article class="text">
        <h2><span class="n">{{ index + 1 }}</span>{{ scene.title }}</h2>
        <div class="body" v-html="scene.text"></div>
      </article>
      <section class="right">
        <div class="bar">
          <span class="lab">Turtle</span>
          <button :disabled="at === 0" title="Back" @click="at--">←</button>
          <button :disabled="at >= history.length - 1" title="Forward" @click="at++">→</button>
          <button :disabled="pristine" @click="reset">Reset to this scene</button>
          <span class="hint">click = open · Ctrl + click = add</span>
        </div>
        <TurtleBox :iris="box" @go="go" @hover="hover = $event" @remove="remove" />
      </section>
    </main>

    <footer>
      <button :disabled="index === 0" @click="move(-1)">← Previous</button>
      <span>{{ index + 1 }} / {{ scenes.length }}</span>
      <button class="primary" :disabled="index === scenes.length - 1" @click="move(1)">Next →</button>
    </footer>
  </div>
</template>

<style scoped>
.page { height: 100%; display: grid; grid-template-rows: auto 1fr auto; }
.top { display: flex; align-items: center; gap: 18px; padding: 8px 18px; background: var(--c-panel); border-bottom: 3px solid var(--c-era); }
.logo { height: 38px; }
.titles h1 { margin: 0; font-size: 19px; color: var(--c-era); }
.titles span { font-size: 12.5px; color: var(--c-ink-soft); }
.steps { margin-left: auto; display: flex; gap: 4px; flex-wrap: wrap; }
.steps button { width: 26px; height: 26px; border-radius: 50%; border: 1px solid var(--c-stroke); background: var(--c-panel); color: var(--c-ink-soft); font-size: 12px; cursor: pointer; }
.steps button.on { background: var(--c-era); border-color: var(--c-era); color: #fff; font-weight: 700; }
main { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); grid-template-rows: minmax(0, 1.25fr) minmax(0, 1fr); grid-template-areas: "draw box" "text box"; gap: 12px; padding: 12px 18px; min-height: 0; }
/* scenes that show the whole network give the drawing the full width */
main.wide { grid-template-areas: "draw draw" "text box"; grid-template-rows: minmax(0, 1.45fr) minmax(0, 1fr); }
.drawing { grid-area: draw; } .text { grid-area: text; } .right { grid-area: box; }
.drawing { border: 1px solid var(--c-stroke); border-radius: 8px; overflow: hidden; background: var(--c-panel); min-height: 0; }
.text { background: var(--c-panel); border: 1px solid var(--c-stroke); border-radius: 8px; padding: 12px 20px; overflow: auto; min-height: 0; }
.text h2 { margin: 0 0 6px; font-size: 20px; color: var(--c-era); display: flex; align-items: center; gap: 10px; }
.text .n { display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--c-era-yellow); color: var(--c-era); font-size: 15px; flex: none; }
.body { font-size: 15px; line-height: 1.5; max-width: 86ch; }
.body :deep(p) { margin: 0 0 8px; } .body :deep(ul) { margin: 0 0 8px; padding-left: 20px; }
.right { display: grid; grid-template-rows: auto 1fr; border-radius: 8px; overflow: hidden; border: 1px solid #0d1830; min-height: 0; }
.bar { display: flex; align-items: center; gap: 6px; padding: 6px 10px; background: #0d1830; color: #c8d3ea; font-size: 12px; }
.bar .lab { font-weight: 700; color: var(--c-era-yellow); margin-right: 6px; }
.bar button { background: #22325a; color: #e6ecfa; border: 0; border-radius: 4px; padding: 3px 9px; font-size: 12px; cursor: pointer; }
.bar button:disabled { opacity: 0.35; cursor: default; }
.bar .hint { margin-left: auto; color: #8fa0bd; }
footer { display: flex; justify-content: center; align-items: center; gap: 18px; padding: 8px; background: var(--c-panel); border-top: 1px solid var(--c-stroke); font-size: 13px; color: var(--c-ink-soft); }
footer button { border: 1px solid var(--c-stroke); background: var(--c-panel); border-radius: 6px; padding: 6px 14px; font-size: 13px; cursor: pointer; color: var(--c-ink); }
footer button.primary { background: var(--c-era); color: #fff; border-color: var(--c-era); }
footer button:disabled { opacity: 0.4; cursor: default; }
@media (max-width: 900px) {
  .page { height: auto; min-height: 100%; }
  main, main.wide { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto; grid-template-areas: "draw" "text" "box"; padding: 10px 16px; }
  .drawing { aspect-ratio: 16 / 9; }
  .right { height: 70vh; }
  .steps { display: none; }
  .bar .hint { display: none; }
}
</style>
