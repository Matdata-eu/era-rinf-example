// A scene is plain data: what the drawing shows, what is in the Turtle box, and a short text.
// The same list can drive a Slidev deck later.
// box: resources loaded in the Turtle box; focus: what the drawing zooms to, a list of resources or
// { at, width } for a window around one object (default: the whole network);
// layers: drawing layers switched off for this scene.
export const LAYERS = [
  ['ops', 'Operational points'], ['sols', 'Sections of line'], ['tracks', 'Tracks'], ['switches', 'Switches'], ['signals', 'Signals'],
  ['platforms', 'Platform edges'], ['structures', 'Tunnel, level crossing'], ['km', 'Kilometre posts'], ['locations', 'Primary locations'],
]
const TOPOLOGY_ONLY = { ops: false, sols: false, signals: false, platforms: false, structures: false, km: false, locations: false }

export const scenes = [
  {
    id: 'network', title: 'The network at a glance',
    text: `<p>A fictive piece of railway on both sides of a border: <b class="be">Infra Alfa</b> in Belgium and <b class="nl">Beta Spoor</b> in the Netherlands. It is small, but it has what a real RINF dataset has: a station area split into three operational points, two junctions, a private siding, a tunnel, a level crossing, primary locations and a border point.</p>
<p>The drawing is generated from the Turtle on the right. Positions come from the linear elements and offsets in the data, so when the Turtle changes, the drawing changes with it. Click anything to see its triples.</p>`,
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
<ul><li><b>Click</b> an IRI: the box shows that resource instead.</li><li><b>Ctrl + click</b>: the resource is added below what is already there.</li><li>Hover an IRI and the drawing shows where it is. Click an object in the drawing and the box follows.</li><li><code>era:</code> terms open their definition from the v3.3.4 ontology.</li><li>Scroll to zoom the drawing and drag to move it. <b>Explore</b> in the top bar shows the drawing and the Turtle without the explanations.</li></ul>
<p>Try it on signal S1: follow <code>era:netReference</code>, then <code>era:hasTopoCoordinate</code>, and you arrive at a linear element and an offset.</p>`,
    box: ['be:sig_S1'], focus: ['be:op_WHS'],
  },
  {
    id: 'elements', title: 'Netelements: origin, end, length',
    text: `<p>The topology is made of netelements, in the ontology <code>era:LinearElement</code>: stretches between two points where something changes, here switches and ends of the network. A netelement has a length and nothing else of its own.</p>
<p>It also has a direction, although no property says so. One end is the <b>origin</b>, the other the end, and the arrow in the drawing runs from origin to end. Everything placed on the netelement is measured in metres from the origin. In this example the WKT is written in the same direction.</p>`,
    box: ['be:le_a4', 'be:le_a4_geom'], focus: ['be:le_a3', 'be:le_a4', 'be:le_c1', 'be:le_a2'], layers: TOPOLOGY_ONLY,
  },
  {
    id: 'reversed', title: 'Some netelements run the other way, on purpose',
    text: `<p>Nothing obliges a netelement to point in the direction of the line, of the kilometrage or of traffic. In real data the origin is wherever the source system put it.</p>
<p>So the example mixes them. The netelements <code>a1</code> to <code>a7</code> of Infra Alfa point east. <code>b2</code>, <code>b6</code>, <code>c1</code> and <code>d0</code> point west, and so does every netelement of Beta Spoor. Compare the WKT of <code>b2</code> with the drawing: the first coordinate is the eastern end.</p>
<p>Later scenes show what this does to signals and to running directions.</p>`,
    box: ['be:le_b2', 'be:le_b2_geom'], highlight: ['be:le_b2', 'be:le_b6', 'be:le_c1', 'be:le_d0', 'nl:le_B1', 'nl:le_B2', 'nl:le_B3', 'nl:le_B4'], layers: TOPOLOGY_ONLY,
  },
  {
    id: 'relation', title: 'Netrelations: a topology connection defining navigability',
    text: `<p>Netelements do not know their neighbours. A netrelation, <code>era:NetRelation</code>, says that an end of netelement A touches an end of netelement B, and whether a train can pass from one to the other.</p>
<p><code>era:isOnOriginOfElementA true</code> means: the connection is at the <em>origin</em> of A, here <code>b5</code>. <code>era:isOnOriginOfElementB false</code>: it is at the <em>end</em> of B, here <code>b4</code>. <code>era:navigability</code> is <code>Both</code>: trains pass in both directions.</p>`,
    box: ['be:nr_Wg_b5_b4'], focus: { at: 'be:sw_W14', width: 420 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'switch', title: 'Netrelations at a switch: Both, Both, None',
    text: `<p>At a switch, three netelement ends meet, so there are three netrelations. Two of them are navigable. The third joins the two legs, and no train can go from one leg to the other without reversing: <code>era-nv:None</code>.</p>
<p>At W14 the common branch is <code>b5</code>, towards the border. <code>b5–b4</code> and <code>b5–a6</code> are <code>Both</code>, <code>b4–a6</code> is <code>None</code>. State the <code>None</code> relation too to indicate the connectivity between the two netelements.</p>`,
    box: ['be:nr_Wg_b5_b4', 'be:nr_Wg_b5_a6', 'be:nr_Wg_b4_a6'], focus: { at: 'be:sw_W14', width: 420 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'doubleslip', title: 'The double slip crossing: four netelements, six netrelations',
    text: `<p>At W5 four netelement ends meet: <code>b1</code> and <code>y0</code> from the west, <code>b2</code> and <code>x1</code> to the east. Four ends give six pairs.</p>
<p>A double slip lets every western netelement reach every eastern one, so four netrelations are <code>Both</code>: <code>b1–b2</code>, <code>y0–x1</code>, <code>b1–x1</code> and <code>y0–b2</code>. The two pairs on the same side, <code>b1–y0</code> and <code>b2–x1</code>, are <code>None</code>.</p>
<p>A plain diamond crossing would have the same four netelements with only two <code>Both</code> netrelations. The difference between the two is entirely in the navigability.</p>`,
    box: ['be:nr_DS_b1_b2', 'be:nr_DS_y0_x1', 'be:nr_DS_b1_x1', 'be:nr_DS_y0_b2', 'be:nr_DS_b1_y0', 'be:nr_DS_b2_x1'],
    focus: { at: 'be:sw_W5', width: 380 }, layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'crossover', title: 'The crossover: a netelement between two switches',
    text: `<p>Midford Junction is two crossovers between the main line netelements. Each connecting piece, <code>x2</code> and <code>cx</code>, is a netelement like any other, with a switch at each end and three netrelations at each switch.</p>
<p>Follow <code>cx</code>: at W11 it meets <code>a7</code> and <code>a6</code>, at W12 it meets <code>b6</code> and <code>b3</code>. A train on <code>a7</code> can reach <code>b3</code> over <code>cx</code>, because <code>a7–cx</code> and <code>cx–b3</code> are both navigable.</p>`,
    box: ['be:le_cx', 'be:nr_Xa_a7_cx', 'be:nr_Xb_b3_cx'], focus: ['be:op_MID'], layers: { ...TOPOLOGY_ONLY, switches: true },
  },
  {
    id: 'border', title: 'The border: one border point, one record per manager',
    text: `<p>The two networks meet at an operational point of type <em>border point</em>. Each manager delivers its own record for it, and the two records describe the same place:</p>
<ul><li><code>era:opType</code> is <code>era-op-types:90</code>, border point.</li><li><code>era:referenceBorderPoint</code> points to the reference border point, which ERA manages and lists in the RINF application guide.</li><li><code>era:uopid</code> is the <code>era:borderPointId</code> of that reference point. It starts with <code>EU</code>, not with a country code.</li><li>The coordinates are exactly those of the reference point.</li></ul>
<p>The SHACL shapes check all of this, and also that every record pointing to the same reference point has the same identifier and coordinates. Each manager's last section of line ends at its own record of the border point.</p>`,
    box: ['be:op_BORD', 'nl:op_BORD', 'http://data.europa.eu/949/referenceBorderPoints/EU99901'],
    focus: { at: 'be:op_BORD', width: 760 }, layers: { signals: false, platforms: false, structures: false, locations: false },
  },
]
