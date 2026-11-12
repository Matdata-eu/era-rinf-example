// A scene is plain data: what the drawing shows, what is in the Turtle box, and a short text.
// The same list can drive a Slidev deck later.
// box: resources loaded in the Turtle box; focus: what the drawing zooms to, a list of resources or
// { at, width } for a window around one object (default: the whole network);
// layers: drawing layers switched off for this scene.
const TOPOLOGY_ONLY = { ops: false, sols: false, signals: false, platforms: false, structures: false, km: false, locations: false }

export const scenes = [
  {
    id: 'network', title: 'The network at a glance',
    text: `<p>A fictive piece of railway, described twice over a border: <b class="be">Infra Alfa</b> in Belgium and <b class="nl">Beta Spoor</b> in the Netherlands. It is small, but it has what a real RINF dataset has: a station split into three operational points, two junctions, a branch, a tunnel, a level crossing and a border point.</p>
<p>The drawing is not a picture next to the data. It is computed from the Turtle in the box on the right, so every line, arrow and symbol is a statement in the file. Click anything.</p>`,
    box: ['orgrole:9901_IM', 'orgrole:9902_IM'],
  },
  {
    id: 'who', title: 'Who delivers what',
    text: `<p>Each infrastructure manager delivers one file with its own network. Every object says who manages it and in which country it lies: <code>era:infrastructureManager</code> points to the manager's <em>role</em>, not to the organisation itself, and <code>era:inCountry</code> to a country of the EU authority list.</p>
<p>The organisation codes 9901 and 9902 are invented. The country IRIs are real, so the example validates against the v3.3.4 SHACL shapes.</p>`,
    box: ['be:op_WHS', 'orgrole:9901_IM', 'org:9901'],
    layers: { signals: false, platforms: false, structures: false, km: false, locations: false },
  },
  {
    id: 'reading', title: 'How to read this page',
    text: `<p>The box on the right always shows real Turtle from the example. Every IRI in it is a link.</p>
<ul><li><b>Click</b> an IRI: the box shows that resource instead.</li><li><b>Ctrl + click</b>: the resource is added below what is already there.</li><li>Hover an IRI and the drawing shows where it is. Click an object in the drawing and the box follows.</li><li><code>era:</code> terms open their definition from the v3.3.4 ontology.</li></ul>
<p>Try it on signal S1: follow <code>era:netReference</code>, then <code>era:hasTopoCoordinate</code>, and you arrive at a linear element and an offset.</p>`,
    box: ['be:sig_S1'], focus: ['be:op_WHS'],
  },
  {
    id: 'elements', title: 'Linear elements: origin, end, length',
    text: `<p>The topology is made of <code>era:LinearElement</code>s: stretches of track between two points where something changes, here switches and track ends. An element has a length and nothing else of its own.</p>
<p>It also has a direction, although no property says so. One end is the <b>origin</b> (the small open dot), the other the end, and the arrow runs from origin to end. Everything placed on the element is measured in metres from the origin. In this example the WKT is written in the same direction.</p>`,
    box: ['be:le_a4', 'be:le_a4_geom'], focus: ['be:le_a3', 'be:le_a4', 'be:le_c1', 'be:le_a2'], layers: TOPOLOGY_ONLY,
  },
  {
    id: 'reversed', title: 'Some elements run the other way, on purpose',
    text: `<p>Nothing obliges an element to point in the direction of the line, of the kilometrage or of traffic. In real data the origin is wherever the source system put it.</p>
<p>So the example mixes them. Track 1 of Infra Alfa points east. Track 2 (<code>b2</code>, <code>b6</code>), the loop <code>c1</code> and the depot lead <code>d0</code> point west, and so does every element of Beta Spoor. Compare the WKT of <code>b2</code> with the drawing: the first coordinate is the eastern end.</p>
<p>Later scenes show what this does to signals and to running directions.</p>`,
    box: ['be:le_b2', 'be:le_b2_geom'], highlight: ['be:le_b2', 'be:le_b6', 'be:le_c1', 'be:le_d0', 'nl:le_B1', 'nl:le_B2', 'nl:le_B3', 'nl:le_B4'], layers: TOPOLOGY_ONLY,
  },
  {
    id: 'joint', title: 'Net relations: a plain joint',
    text: `<p>Elements do not know their neighbours. A <code>era:NetRelation</code> says that an end of element A touches an end of element B, and whether a train can pass.</p>
<p><code>era:isOnOriginOfElementA false</code> means: the relation is at the <em>end</em> of A. At the border the end of <code>b5</code> meets the end of <code>B1</code>, because <code>B1</code> runs west. <code>era:navigability</code> is <code>Both</code>: trains pass in both directions.</p>
<p>This is the only place where the two files touch. Each manager delivers its own element, and one of them (here Infra Alfa) delivers the relation.</p>`,
    box: ['be:nr_BORD_b5_B1'], focus: { at: 'be:op_BORD', width: 520 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'switch', title: 'Net relations at a switch: Both, Both, None',
    text: `<p>At a switch three element ends meet, so there are three pairs and three relations. Two of them are navigable. The third joins the two legs, and no train can go from one leg to the other without reversing: <code>era-nv:None</code>.</p>
<p>At W14 the common branch is <code>b5</code>, towards the border. <code>b5–b4</code> and <code>b5–a6</code> are <code>Both</code>, <code>b4–a6</code> is <code>None</code>. State the <code>None</code> relation too: without it a route planner cannot tell a switch from a place where three tracks simply end.</p>
<p>v3.3.4 has no property for facing or trailing. It follows from these three relations.</p>`,
    box: ['be:nr_Wg_b5_b4', 'be:nr_Wg_b5_a6', 'be:nr_Wg_b4_a6'], focus: { at: 'be:sw_W14', width: 420 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'doubleslip', title: 'The double slip crossing: four elements, six relations',
    text: `<p>At W5 four element ends meet: <code>b1</code> and <code>y0</code> from the west, <code>b2</code> and <code>x1</code> to the east. Four ends give six pairs.</p>
<p>A double slip lets every western track reach every eastern track, so four relations are <code>Both</code>: <code>b1–b2</code>, <code>y0–x1</code>, <code>b1–x1</code> and <code>y0–b2</code>. The two pairs on the same side, <code>b1–y0</code> and <code>b2–x1</code>, are <code>None</code>.</p>
<p>A plain diamond crossing would have the same four elements with only two <code>Both</code> relations. The difference between the two is entirely in the navigability.</p>`,
    box: ['be:nr_DS_b1_b2', 'be:nr_DS_y0_x1', 'be:nr_DS_b1_x1', 'be:nr_DS_y0_b2', 'be:nr_DS_b1_y0', 'be:nr_DS_b2_x1'],
    focus: { at: 'be:sw_W5', width: 380 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'crossover', title: 'The crossover: the connecting element is a track',
    text: `<p>Midford Junction is two crossovers between the main tracks. Each connecting piece, <code>x2</code> and <code>cx</code>, is a linear element like any other, with a switch at each end and three relations at each switch.</p>
<p>It is also a <em>track</em>. Every stretch of linear element belongs to a track of an operational point or of a section of line, so the junction has four tracks: the two main tracks and the two crossovers. A track locates itself with a linear reference: a sequence of elements, a start and an end.</p>`,
    box: ['be:trk_MID_X2', 'be:trk_MID_X2_ref', 'be:le_cx'], focus: ['be:op_MID'], layers: { signals: false, platforms: false, structures: false, km: false, locations: false, sols: false },
  },
]
