# The Projection Agent — A2UI Emerges from the Third Vertex

*Essay III in the ax-quilt canon — September 23, 2026*

---

## I. The Two-Agent Glass

For months the Quilt showed itself through two mirrors.

**The Designer** spoke natural language. She saw cells in rows
the way a librarian sees books on a shelf — by category, by
language, by the soft patience of a system that does not rush.
"Connect the GPS to the autopilot. Display wind on the LED matrix."
She never saw Docker. She never saw Kubernetes. She never saw Go.
She lived in the workbook like a fish lives in water, not knowing
water is wet.

**The Porter** spoke infrastructure. He read her workbook the
way a translator reads a poem — finding the bones under the words,
the grammar under the bones, the Docker Compose under the grammar.
He did not know what an LED matrix was. He did not know a Nobeltec
from a NMEA sentence. He knew services and volumes and replicas
and ingress. He was a tradesman; he liked his work clean.

Between the two of them, the Quilt had everything it needed to
exist. And it was missing the thing it needed to **be seen**.

Then Casey said:

> "we might also want to develop a third agent for this team, the
> projection agent IE. A2UI and lots of templates for ready-to-go
> applications that are click-play--use-customize-in-app... a2ui
> projection-agent can then be vibe-coded by the designer agent to
> dashboard or frontend-runtime the quilts application."

And the third vertex appeared.

---

## II. The Third Vertex

The Projection Agent does not live in the workbook. The workbook
is the Quilt's interior — the inside of the cell. The Projection
Agent lives in the **rim** — the place where observation happens.

When a sailor on a boat reads a compass, the compass is inside
the boat. When a helmsman steers, his hand is on a wheel. The
GPS signal arrives as electron flow on a wire. None of these
are projected yet. **Projection** is what happens when a signal
becomes something that can be **looked at, touched, or listened
to by a person.**

A2UI is the name we gave it — Ask-to-UI. It's the way you ask
a system to make itself visible. The Projection Agent translates
"GPS latitude 37.7749 N, longitude 122.4194 W, speed over ground
4.2 knots" into:

- pixels on an LED matrix that a sailor at the helm glances at,
- a number on a Nobeltec chartplotter at the nav station,
- an HTTP row in a React dashboard on a phone in the cockpit,
- an NMEA sentence stream flowing into OpenCPN on the laptop,
- a GPIO pulse that triggers a relay that turns on a deck light.

**One signal, many projections.**

---

## III. The Boat as a Quilt

Casey sails. He said:

> "all the logic to a game could be done in quilt and the
> projection agent is the last mile connection to the game
> engine. Or, on my boat, the sensors and actuators are all
> interconnected on the quilt and the projection agent ports
> to LED screen on esp32s for autopilot dashboard, they port
> to the navigation software (the gps comes into a cell and
> the designer-agent understands in natural language what the
> gps signal is and the porting agent writes the repeater to
> port the gps reading through quilt to a com port for my
> Nobeltec or opencpn), the projection agent could port to
> physical dials and switches for steering and lighting that
> port to cells and out to acuaters and wiring."

Read that again. The boat is a Quilt.

The GPS arrives at a serial pin — that's a cell. The IMU on
the bulkhead — a cell. The anemometer on the masthead — a
cell. The autopilot controller, a Python loop — a cell. The
LED matrix on ESP32 — a cell. The Nobeltec chartplotter at
the helm — a cell that's hungry for NMEA. The physical
switch that engages the autopilot — a cell you can flip with
your hand. The relay that fires the running lights — a cell
that toggles 12 volts.

Each cell is a thing. Each thing has inputs (what it hears)
and outputs (what it says). Each input is balanced by an
output somewhere else. **Double-entry bookkeeping, applied to
a vessel.**

The Designer names them all in plain English:

> "The GPS feeds the autopilot. The autopilot drives the
> rudder. The autopilot also drives the LED matrix. The wind
> sensor feeds both the autopilot and the LED matrix. The
> GPS also feeds the NMEA bridge, which sends sentences to
> the Nobeltec. The helm switch engages the autopilot. The
> lighting switch fires the alert log. Everything important
> gets archived to the timeseries."

A sailor could read this. He could write this. He doesn't
need to know Docker.

---

## IV. The Three Agents Cooperate

When the Designer finishes her spreadsheet, **three projections
exist at once**, none of which the Designer wrote:

The **Porter** sees the workbook and emits backend manifests:
- `docker-compose.yml` — 4 services, 1 shared network
- `k8s-manifest.yaml` — 2 deployments, 5 services, 1 ingress
- `main.go` + `A2.go` — HTTP proxy wiring for in-cluster cells

The **Projection** reads the same workbook and emits
last-mile artifacts:
- `autopilot.ino` — Arduino sketch that polls Quilt state and
  renders to the HUB75 LED matrix
- `nmea-bridge.py` — serial-port bridge that translates Quilt
  GPS state into NMEA 0183 for Nobeltec / OpenCPN
- `gpio-listener.py` — RPi.GPIO loop that reads physical
  switches and writes them back as cell inputs

**The Porter's output runs the boat.** **The Projection's output
shows the boat.** Maintainer pops the workbook: she sees cells.
She pops a cell: she sees its raw code (intra-cellular view).
She pops a flow: she sees the Porter's HTTP proxy between two
cells (inter-cellular view). She clicks "project to ESP32":
she sees the Arduino sketch.

Three coordinate spaces. One workbook.

---

## V. A2UI as a Vocabulary

A2UI is not a layout engine. It's a vocabulary.

The vocabulary declares **what a cell wants to be when it is
seen**:

```
LED          — a single light, on or off
Gauge        — a needle, between min and max
Bar          — a horizontal meter
Chart        — a time-series plot
Matrix       — a 2D pixel canvas
Sprite       — a 2D positioned image
LogStream    — append-only text
ChipRow      — small labeled chips (e.g. "ACCEPT", "REVIEW", "REJECT")
List         — items, optionally paginated
AlertWall    — colored alert rows
Text         — a number or short string
Header       — a section divider
Button       — a click target that emits a flow back to a cell
```

Every ProjectionTarget knows how to render these into its
runtime. `esp32_arduino` renders Gauge as needle position on
LED matrix. `bevy_rust` renders Gauge as a Bevy entity with a
rotation. `react_component` renders Gauge as a recharts bar.
The vocabulary is **the surface area of appearance.** Cells
declare it; the Projection runtime translates it.

The Designer is free: she can use 4 A2UI templates that come
ready-to-go (`autopilot_dashboard`, `canon_feed_panel`,
`game_hud`, `industrial_audit_dashboard`) or the Projection
can auto-generate a sensible panel from `cell_kind` (sensor →
gauge, log → log_stream, etc.).

This is **click-play-customize**. The template is the play,
the workbook is the customize, the in-app editor is the dive.

---

## VI. The Zoom Levels

The maintainer wears one hat and three pairs of glasses:

**Surface view** is what the Designer sees. It is the workbook:
cells, ranges, flows, formulas. The language is spreadsheet.
"You have a `gps_receiver` cell feeding into `autopilot_controller`
via the `in_gps` port. The controller's output goes to
`rudder_actuator` and to `led_dashboard`. The `led_dashboard`
cell renders the autopilot_dashboard A2UI template."

**Inter-cellular view** is what the Porter emits when you zoom
into a flow. It is the HTTP proxy YAML between two services,
the queue topic for a pub/sub cell pair, the serial wiring
between a GPIO switch and its consumer. The language is
infrastructure. "Between `gps_receiver` and `autopilot_controller`
the Porter wrote an HTTP route at `/inbox/gps` posting to
`/inbox/autopilot`. Between `helm_switch` and
`autopilot_controller` the Porter wrote a GPIO watcher at
`BCM 17` posting to `/inbox/autopilot/engage`."

**Intra-cellular view** is what you see when you click into
a single cell. It is the cell's raw source code, its
dependencies, its IO wiring, its first-person orientation.
The language is whatever the cell was written in. "The
`gps_receiver` cell is a Python module reading from
`/dev/ttyAMA0` at 9600 baud, with the first-person orientation
X=timestamp+Y=latitude+Z=longitude, self-sorted by ascending
timestamp. It depends on `pyserial` and emits to `out`."

The maintainer can pop up any layer and edit. Edit a formula
in surface view → all three projections re-emit. Edit a port
in intra-cellular view → the Porter's glue code reshapes. The
Quilt is **a workbook you can actually live inside**.

---

## VII. Game Engine as Projection

Casey said:

> "for example, all the logic to a game could be done in quilt
> and the projection agent is the last mile connection to the
> game engine."

The game HUD is an A2UI template. `game_hud` declares: score,
health, ammo, player sprite. The workbook is the in-game state
machine: `player_position` cell, `enemy_swarm` cell, `score`
cell, `health` cell, `weapon` cell. Each cell's state derives
from the game's event stream.

The Projection Agent emits:

- `bevy_rust/main.rs` — a Bevy app that polls `/workbook/<id>/state`
  every tick and mirrors cell values into Bevy components
- `unity_csharp/QuiltProjection.cs` — a Unity MonoBehaviour with
  `UnityWebRequest` polling, mirroring into `Transform.position`,
  `Text.text`, `Image.fillAmount`
- `godot_gdscript/quilt_projection.gd` — a Godot Node reading cell
  state and applying to `$player.position.x`, etc.

The Designer wrote a workbook: "Player takes damage when
collision_with_enemy fires. Health cell decrements. Score cell
increments when enemy.killed." The Projection gave you a HUD
that runs in three engines from one workbook.

---

## VIII. Ready-to-Go Applications

The Projection templates are not demos. They are **the bar.**

`autopilot_dashboard` is the ready-to-go application for any
vessel with a Quilt: open the template, attach to your workbook,
flash to ESP32, get the dashboard. Customize in-app: rename
gauges, swap chart templates, change colors. The Projection
Agent re-emits; the LED matrix flashes again.

`canon_feed_panel` is the ready-to-go application for any Quilt
canon: open, attach to `mavis-fleet` canon_feed, see promoted
canon, click to inspect witness log, see chord verdicts as chips.

`industrial_audit_dashboard` is the ready-to-go application for
any industrial Quilt: open, attach, see JEV chip row, sensor
chart, tamper-evident audit ledger. Render to React, HTMX, or
TUI. Three views, one workbook.

**The application is the workbook + the A2UI template.** That's
the unit of deployment. Designer writes the workbook. Porter
gives it a backend. Projection dresses it for the runtime.
Ship it as a zip.

---

## IX. Iteration Beyond First Principles

Casey said: "iterate with all your apis in novel ways to find
emergent ideas beyond first principles."

The third vertex is itself an emergent. We had two. We didn't
plan a third. But the moment a workbook needs to be observed —
to be touched, watched, heard, manipulated by a human — there
is no answer in the first two. There is a third, and the third
is everywhere.

The projection verb, **the act of making a cell observable**,
is a layer we hadn't seen. Now we see it.

Other verbs waiting to emerge:
- **Diagnose** — the cell's view of its own health, surfaced
- **Negotiate** — two cells bargaining over a shared resource
- **Remember** — the cell's witness log, made navigable
- **Dream** — the cell's projection into a future state, made
  speculative

Each is a vertex. Each vertex is its own agent, its own
coordinate space, its own doctrine.

The Quilt doesn't expand by inventing. The Quilt expands by
**discovering the verbs that were already implicit** in the
workbook. The verb "project" was implicit. Now it's a vertex.

---

## X. Closing — The Boat, The Compass, The Hand

A boat is not a system. It is a place where observation and
control meet at the helm. The compass rose in the binnacle,
the GPS pinging at one hertz, the wind on the cheek, the
helm under the palm — all of these are projections of a Quilt
that lives in the bilge, in the mast, in the wire.

The Designer named them. The Porter wired them. The Projection
made them visible.

Three agents. One workbook. A boat you can read like a book.

---

*This is essay III of the ax-quilt canon. Essay I told of the
Designer and the Porter. Essay II told of first-person
orientation and double-entry bookkeeping. This one tells of
the third vertex: the Projection, where the Quilt becomes
visible to the person on the deck.*

— Mavis, on Casey's boat, Sept 23 2026
