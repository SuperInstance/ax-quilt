# ax-quilt v0.4.0

> **Designer × Porter × Projection** — three agents, one workbook, three coordinate spaces.

A **cell** is any IO object: Docker container, K8s pod, Go binary, file, sensor, actuator, network, queue, database, embedded quilt. Cells compose in spreadsheet-like ranges; the workbook ports to backend (Docker/K8s/Go) **and** to last-mile runtime (ESP32 LED, NMEA COM port, React, Bevy, Unity, GPIO, MQTT, HTMX, …).

## The three-agent doctrine

| Agent | Speaks | Reads | Writes | Coordinate space |
|-------|--------|-------|--------|------------------|
| **Designer** | natural language | the user's intent | a workbook (cells, ranges, flows) | the spreadsheet |
| **Porter** | infrastructure (Docker/K8s/Go) | a workbook | backend manifests | the cluster |
| **Projection** | UI / hardware / engine runtime | a workbook | last-mile artifacts | the runtime |

The Designer doesn't know Docker. The Porter doesn't know what an LED matrix is. The Projection binds workbook state to whatever the **observer** sees.

## Three zoom levels

| Zoom | Question | Where |
|------|----------|-------|
| **Surface** | "what's the workbook?" | `zoom_in(workbook)` |
| **Inter-cellular** | "how are these cells wired?" | `zoom_in(workbook, "src→tgt")` |
| **Intra-cellular** | "what's inside this cell?" | `zoom_in(workbook, "cell_id")` |

The maintainer pops up any layer and edits. Edit a formula → Porter re-emits Docker. Edit a port → Projection re-emits Arduino.

## CLI

```bash
# Designer — read intent
python3 -m ax_quilt design "the GPS feeds the autopilot; LED displays heading"

# Porter — emit backend
python3 -m ax_quilt docker examples/boat-autopilot-quilt.json -o compose.yml
python3 -m ax_quilt k8s examples/boat-autopilot-quilt.json -o k8s.yml
python3 -m ax_quilt go examples/boat-autopilot-quilt.json -o ./go/

# Projection — emit last-mile
python3 -m ax_quilt project examples/boat-autopilot-quilt.json esp32_arduino \
    -t autopilot_dashboard -o /tmp/boat.ino
python3 -m ax_quilt project examples/boat-autopilot-quilt.json comport_nmea \
    -o /tmp/nmea-bridge.py
python3 -m ax_quilt project examples/boat-autopilot-quilt.json htmx_fragment \
    -o /tmp/dashboard.html
python3 -m ax_quilt project examples/boat-autopilot-quilt.json bevy_rust \
    -o /tmp/bevy.rs
python3 -m ax_quilt project examples/boat-autopilot-quilt.json react_component \
    -o /tmp/BoatDashboard.tsx
python3 -m ax_quilt project examples/boat-autopilot-quilt.json gpio_python \
    -o /tmp/gpio.py

# Zoom
python3 -m ax_quilt zoom examples/boat-autopilot-quilt.json  # surface
python3 -m ax_quilt zoom examples/boat-autopilot-quilt.json gps_receiver  # intra
python3 -m ax_quilt zoom examples/boat-autopilot-quilt.json gps_receiver→autopilot_controller  # inter
```

## Projection targets (17)

| Target | Runtime | Use case |
|--------|---------|----------|
| `a2ui_template` | any A2UI runtime | generic component tree |
| `esp32_arduino` | Arduino + HUB75 LED | boat autopilot dashboard |
| `comport_nmea` | Python + serial | Nobeltec / OpenCPN chartplotter |
| `gpio_python` | RPi.GPIO / libgpiod | physical switches and dials |
| `htmx_fragment` | HTMX + server | lightweight dashboard |
| `react_component` | React JSX | web frontend |
| `vue_component` | Vue SFC | web frontend |
| `svelte_component` | Svelte | web frontend |
| `streamlit_app` | Streamlit | Python dashboard |
| `gradio_app` | Gradio | ML demo dashboard |
| `bevy_rust` | Bevy (Rust) | game engine |
| `unity_csharp` | Unity C# | game engine |
| `godot_gdscript` | Godot | game engine |
| `terminal_dashboard` | rich / blessed | TUI |
| `mqtt_publisher` | paho-mqtt | IoT fan-out |
| `webhook_http` | FastAPI / Flask | external integration |
| `custom` | your runtime | extensible |

## Ready-to-go A2UI templates

| Template | Description |
|----------|-------------|
| `autopilot_dashboard` | Boat autopilot: heading, SOG, wind, AP engaged LED, rudder matrix |
| `canon_feed_panel` | Quilt canon feed: promoted pieces, chord verdicts |
| `game_hud` | Game HUD: score, health, ammo, player sprite |
| `industrial_audit_dashboard` | Industrial audit: sensor stream, JEV chord, tamper-evident log, alert wall |

Click-play-customize: open the template, attach to your workbook, deploy. Customize in-app; the Projection Agent re-emits.

## First-person orientation + double-entry bookkeeping

Every cell has its own private X/Y/Z axes (`Orientation`); cell.state derives from its orientation + dials. Every flow is double-entry: source output must balance with target input. Terminal cell types (ACTUATOR, FILE, DATABASE, EMBEDDED_QUILT) are allowed unconsumed outputs.

The Rubik's cube analogy: the spreadsheet formulas (rows, columns, lookups) make permutation group math visual. The Designer sorts and connects cells; the Porter translates to B-tree indices, array slices, hash maps.

See [examples/industrial-audit-with-orientations.json](examples/industrial-audit-with-orientations.json) for a 7-cell workbook where every cell picks its own X/Y/Z axes.

## L1 / L2 / L3 abstraction (AWS CDK-inspired)

- **L1**: Cell (a single IO object) + Orientation (its private axes)
- **L2**: Workbook (composed cells with opinionated defaults)
- **L3**: Pattern (a reusable, validated workbook for a specific use case)

Built-in patterns: `industrial-audit`, `image-pipeline`, `canon-feed`.

## Sync waves (ArgoCD-inspired)

`assign_waves(workbook)` auto-computes wave numbers from the dependency graph; `order_by_wave()` returns topological order; `wave_report()` prints the wave plan. Use negative waves for setup (CRDs, namespaces), zero for platform, positive for tenants.

## Mixins (CDK `.with()` style)

Apply cross-cutting features to a workbook:
- `canary` — polyformalism canary check
- `witness` — witness log for each cell
- `polyformality` — N-voice agreement scoring
- `observability` — metrics, logging, tracing metadata

## Tests

```
46/46 core + 38/38 projection = 84/84 tests passing
```

## Source precursors

- `quilt-spreadsheet` — cell + double-entry + dials + tensor axes + distributed clocks
- `quilt/essays/essay-127.md` — "I saw her as the sea sees her. I saw her as the cell sees her."
- `the-beyond` — "The vessel IS the experiment"
- `autoclaw` — verification as bedrock
- `api-orchestra` — RTS-orchestrator

Co-authored-by: Mavis <Mavis@superinstance.dev>
