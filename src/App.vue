<script setup>
import { computed, ref, watch, onMounted, onUnmounted } from 'vue'
import NetworkDrawing from './components/NetworkDrawing.vue'
import TurtleBox from './components/TurtleBox.vue'
import { scenes, LAYERS } from './scenes.js'
import { iri, home, FILES } from './lib/rdf.js'
import { bbox } from './lib/net.js'
import logo from './assets/era-logo.svg'

// two modes: the guided scenes, and "explore" (drawing + Turtle, no explanation)
const explore = ref(location.hash === '#explore')
const index = ref(Math.max(0, scenes.findIndex((s) => '#' + s.id === location.hash)))
const scene = computed(() => scenes[index.value])
const sceneBox = computed(() => (explore.value ? [] : scene.value.box.map(iri)))

// the Turtle box, with its own history inside a scene
const trail = ref([sceneBox.value])
const at = ref(0)
const box = computed(() => trail.value[at.value])
const hover = ref(null)
function push(next) { trail.value = [...trail.value.slice(0, at.value + 1), next]; at.value = trail.value.length - 1 }
function go(target, add) {
  if (!home(target)) return
  if (explore.value) showTurtle.value = true
  if (!add) return push([target])
  if (!box.value.includes(target)) push([...box.value, target])
}
const remove = (s) => push(box.value.filter((x) => x !== s))
const reset = () => push(sceneBox.value)
const pristine = computed(() => box.value.join() === sceneBox.value.join())

watch([index, explore], () => {
  trail.value = [sceneBox.value]; at.value = 0; hover.value = null
  window.history.replaceState(null, '', '#' + (explore.value ? 'explore' : scene.value.id))
})

// explore mode: layers and Turtle panel are the reader's choice
const showTurtle = ref(true)
const chosen = ref(Object.fromEntries(LAYERS.map(([k]) => [k, true])))
// where the Turtle sits in explore mode: on the right (default) or below the drawing; remembered per browser
const recall = () => { try { return localStorage.getItem('turtle-dock') } catch { return null } }
const dock = ref(recall() === 'below' ? 'below' : 'right')
watch(dock, (v) => { try { localStorage.setItem('turtle-dock', v) } catch { /* private window */ } })
// the Turtle window can take the whole page
const maximised = ref(false)

// all the Turtle of the example as one file
function download() {
  const text = Object.values(FILES).map((f) => `# ===== ${f.name} (${f.title}) =====\n${f.text.trim()}\n`).join('\n')
  const a = document.createElement('a')
  a.href = URL.createObjectURL(new Blob([text], { type: 'text/turtle;charset=utf-8' }))
  a.download = 'era-rinf-example.ttl'
  a.click()
  setTimeout(() => URL.revokeObjectURL(a.href), 1000)
}

// the drawing follows the scene until the reader starts exploring
const highlight = computed(() => (explore.value || !pristine.value ? box.value : (scene.value.highlight ?? scene.value.box).map(iri)))
const view = computed(() => {
  const f = explore.value ? null : scene.value.focus
  if (!f) return null
  if (Array.isArray(f)) return bbox(f.map(iri), 70)
  const [x, y, w, h] = bbox([iri(f.at)], 0)          // a window of a given width around one object
  return [x + w / 2 - f.width / 2, y + h / 2 - f.width * 0.28, f.width, f.width * 0.56]
})
const layers = computed(() => (explore.value ? chosen.value : scene.value.layers ?? {}))

const open = (i) => { explore.value = false; index.value = i }
const move = (d) => { index.value = Math.min(scenes.length - 1, Math.max(0, index.value + d)) }
function key(ev) {
  if (ev.key === 'Escape') maximised.value = false
  if (explore.value || ev.target.closest?.('input, textarea')) return
  if (ev.key === 'ArrowRight' || ev.key === 'PageDown') move(1)
  if (ev.key === 'ArrowLeft' || ev.key === 'PageUp') move(-1)
}
onMounted(() => window.addEventListener('keydown', key))
onUnmounted(() => window.removeEventListener('keydown', key))
</script>

<template>
  <div class="page" :class="{ explore }">
    <header class="top">
      <img :src="logo" alt="European Union Agency for Railways" class="logo" />
      <div class="titles"><h1>RINF by example</h1><span>A fictive network on ERA ontology v3.3.4</span></div>
      <nav class="steps" aria-label="Scenes">
        <button v-for="(s, i) in scenes" :key="s.id" :class="{ on: !explore && i === index }" :title="s.title" :aria-label="s.title" @click="open(i)">{{ i + 1 }}</button>
      </nav>
      <button class="mode" :class="{ on: explore }" :aria-pressed="explore" @click="explore = !explore">{{ explore ? 'Back to the scenes' : 'Explore' }}</button>
    </header>

    <div v-if="explore" class="tools">
      <span class="lab">Layers</span>
      <label v-for="[k, name] in LAYERS" :key="k"><input v-model="chosen[k]" type="checkbox" /> {{ name }}</label>
      <span class="side">
        <button v-if="showTurtle" class="toggle" :title="dock === 'right' ? 'Put the Turtle below the drawing' : 'Put the Turtle to the right of the drawing'" @click="dock = dock === 'right' ? 'below' : 'right'">{{ dock === 'right' ? 'Turtle below' : 'Turtle on the right' }}</button>
        <button class="toggle" @click="showTurtle = !showTurtle">{{ showTurtle ? 'Hide Turtle' : 'Show Turtle' }}</button>
      </span>
    </div>

    <main :class="{ wide: !explore && !scene.focus, noturtle: explore && !showTurtle, below: explore && dock === 'below' }">
      <div class="drawing"><NetworkDrawing :layers="layers" :highlight="highlight" :hover="hover" :view="view" @select="go" /></div>
      <article v-if="!explore" class="text">
        <h2><span class="n">{{ index + 1 }}</span>{{ scene.title }}</h2>
        <div class="body" v-html="scene.text"></div>
      </article>
      <section v-if="!explore || showTurtle" class="right" :class="{ maximised }">
        <div class="bar">
          <span class="lab">Turtle</span>
          <button :disabled="at === 0" title="Back" @click="at--">←</button>
          <button :disabled="at >= trail.length - 1" title="Forward" @click="at++">→</button>
          <button :disabled="pristine" @click="reset">{{ explore ? 'Clear' : 'Reset to this scene' }}</button>
          <span class="hint">click = open · Ctrl + click = add</span>
          <button title="Download all the Turtle of the example as one file" @click="download">Download Turtle</button>
          <button :title="maximised ? 'Back to normal size (Esc)' : 'Maximise the Turtle window'" :aria-pressed="maximised" @click="maximised = !maximised">{{ maximised ? 'Restore' : 'Maximise' }}</button>
        </div>
        <TurtleBox :iris="box" @go="go" @hover="hover = $event" @remove="remove" />
      </section>
    </main>

    <footer v-if="!explore">
      <button :disabled="index === 0" @click="move(-1)">← Previous</button>
      <span>{{ index + 1 }} / {{ scenes.length }}</span>
      <button class="primary" :disabled="index === scenes.length - 1" @click="move(1)">Next →</button>
    </footer>
  </div>
</template>

<style scoped>
.page { height: 100%; display: grid; grid-template-rows: auto 1fr auto; }
.page.explore { grid-template-rows: auto auto 1fr; }
.top { display: flex; align-items: center; gap: 18px; padding: 8px 18px; background: var(--c-panel); border-bottom: 3px solid var(--c-era); }
.logo { height: 38px; }
.titles h1 { margin: 0; font-size: 19px; color: var(--c-era); }
.titles span { font-size: 12.5px; color: var(--c-ink-soft); }
.steps { margin-left: auto; display: flex; gap: 4px; flex-wrap: wrap; }
.steps button { width: 26px; height: 26px; border-radius: 50%; border: 1px solid var(--c-stroke); background: var(--c-panel); color: var(--c-ink-soft); font-size: 12px; cursor: pointer; }
.steps button.on { background: var(--c-era); border-color: var(--c-era); color: #fff; font-weight: 700; }
.mode { border: 1px solid var(--c-era); background: var(--c-panel); color: var(--c-era); border-radius: 6px; padding: 6px 14px; font-size: 13px; font-weight: 600; cursor: pointer; white-space: nowrap; }
.mode.on { background: var(--c-era); color: #fff; }
.tools { display: flex; flex-wrap: wrap; align-items: center; gap: 4px 16px; padding: 6px 18px; background: var(--c-panel); border-bottom: 1px solid var(--c-stroke); font-size: 13px; }
.tools .lab { font-weight: 700; color: var(--c-era); }
.tools label { display: inline-flex; align-items: center; gap: 5px; cursor: pointer; white-space: nowrap; }
.tools .side { margin-left: auto; display: inline-flex; gap: 8px; }
.tools .toggle { border: 1px solid var(--c-stroke); background: var(--c-panel); border-radius: 6px; padding: 4px 12px; font-size: 13px; cursor: pointer; color: var(--c-ink); }
main { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); grid-template-rows: minmax(0, 1.1fr) minmax(0, 1fr); grid-template-areas: "draw box" "text box"; gap: 12px; padding: 12px 18px; min-height: 0; }
/* scenes that show the whole network give the drawing the full width */
main.wide { grid-template-columns: minmax(0, 1fr) minmax(0, 1.3fr); grid-template-areas: "draw draw" "text box"; grid-template-rows: minmax(0, 1.25fr) minmax(0, 1fr); }
/* explore: the Turtle to the right of the drawing, scrolling vertically; or below it in columns if the reader prefers */
.explore main { grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); grid-template-areas: "draw box"; }
.explore main.below { grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1.5fr) minmax(0, 1fr); grid-template-areas: "draw" "box"; }
.explore main.noturtle { grid-template-columns: minmax(0, 1fr); grid-template-rows: minmax(0, 1fr); grid-template-areas: "draw"; }
.explore main.below .right:not(.maximised) :deep(.box) { column-width: 30rem; column-gap: 28px; }
.explore .right :deep(.block) { break-inside: avoid; }
.drawing { grid-area: draw; } .text { grid-area: text; } .right { grid-area: box; }
.drawing { border: 1px solid var(--c-stroke); border-radius: 8px; overflow: hidden; background: var(--c-panel); min-height: 0; }
.text { background: var(--c-panel); border: 1px solid var(--c-stroke); border-radius: 8px; padding: 12px 20px; overflow: auto; min-height: 0; }
.text h2 { margin: 0 0 6px; font-size: 20px; color: var(--c-era); display: flex; align-items: center; gap: 10px; }
.text .n { display: inline-grid; place-items: center; width: 28px; height: 28px; border-radius: 50%; background: var(--c-era-yellow); color: var(--c-era); font-size: 15px; flex: none; }
.body { font-size: 15px; line-height: 1.5; max-width: 86ch; }
.body :deep(p) { margin: 0 0 8px; } .body :deep(ul) { margin: 0 0 8px; padding-left: 20px; }
.right { display: grid; grid-template-rows: auto 1fr; border-radius: 8px; overflow: hidden; border: 1px solid #0d1830; min-height: 0; }
.right.maximised { position: fixed; inset: 0; z-index: 20; border-radius: 0; }
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
  .page, .page.explore { height: auto; min-height: 100%; }
  main, main.wide, .explore main, .explore main.below, .explore main.noturtle { grid-template-columns: minmax(0, 1fr); grid-template-rows: auto; grid-template-areas: "draw" "text" "box"; padding: 10px 16px; }
  .explore main, .explore main.below, .explore main.noturtle { grid-template-areas: "draw" "box"; }
  .drawing { aspect-ratio: 16 / 9; }
  .explore .drawing { aspect-ratio: 4 / 3; }
  .right { height: 70vh; }
  .right.maximised { height: auto; }
  .steps { display: none; }
  .bar .hint { display: none; }
  .mode { margin-left: auto; }
}
</style>
