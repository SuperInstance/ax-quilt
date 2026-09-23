"""ax-quilt Projection Agent — A2UI, last-mile UI porting.

The Projection Agent is the THIRD vertex of the Designer/Porter/Projection triangle:

  Designer   — speaks NL, thinks in spreadsheets/cells, never sees Docker/K8s/Go
  Porter     — emits Docker/K8s/Go manifests (the BACKEND plumbing)
  Projection — emits UI/frontend/physical-runtime (the LAST-MILE presentation)

Why a third agent? Designer and Porter operate in the cell layer
(inside the Quilt). Projection operates in the OBSERVER layer
(outside the Quilt, where humans/dashboards/engines see it).

Three coordinate spaces:
  Workbook    → backend manifests (Porter)
  Workbook    → UI/frontend templates (Projection, surface view)
  Cell        → intra-cellular raw code (Projection, zoom-in view)
  Cell→Cell   → inter-cellular flow logic (Porter)

Projection Agent binds:
  - A2UI (Ask-2-UI) declarative component model
  - Templates for ready-to-go applications (click-play-customize)
  - Game-engine ports (Unity/Godot/Bevy shaders that read cells)
  - Hardware ports (ESP32 LED matrix, COM port feeds, GPIO)
  - Frontend runtime (React/Vue/Svelte/HTMX/Streamlit/Gradio)

A boat example:
  sensor_gps.cell  →  workbook flows to  →
  projection.agent → "Nobeltec COM port @ /dev/ttyUSB0, 4800 baud"
                  → "LED dashboard @ esp32-001, matrix 64x32"
                  → "OpenCPN NMEA feed via TCP localhost:10110"

A game example:
  cell:player_position  →  projection.agent  →
  → "Bevy transform: Translation::new(x, y, 0)"
  → "Unity: playerGO.transform.position = new Vector3(x, y, 0)"
  → "Godot: $player.position = Vector2(x, y)"

The maintainer's zoom story:
  - See the spreadsheet (high-level, Designer view)
  - Click a cell → see intra-cellular logic (cell.py raw code)
  - Click a flow → see inter-cellular logic (Porter output)
  - Click "project" → see Projection Agent output (A2UI templates)
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple

# Local imports — work both as module and as script
try:
    from ..cells.cell import Cell, IOType, Workbook
    from ..zoom import IntraCellView, InterCellView, SurfaceView
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cells.cell import Cell, IOType, Workbook
    from zoom import IntraCellView, InterCellView, SurfaceView


# ─── Projection Target Enum ─────────────────────────────────

class ProjectionTarget(Enum):
    """Where the Projection Agent can render to."""
    A2UI_TEMPLATE = "a2ui_template"           # declarative component tree (any runtime)
    REACT_COMPONENT = "react_component"       # React JSX
    VUE_COMPONENT = "vue_component"           # Vue SFC
    SVELTE_COMPONENT = "svelte_component"     # Svelte
    HTMX_FRAGMENT = "htmx_fragment"           # HTMX HTML fragment
    STREAMLIT_APP = "streamlit_app"           # Python Streamlit
    GRADIO_APP = "gradio_app"                 # Python Gradio
    BEVY_RUST = "bevy_rust"                   # Bevy (Rust game engine)
    UNITY_CSHARP = "unity_csharp"             # Unity (C#)
    GODOT_GDSCRIPT = "godot_gdscript"         # Godot (GDScript)
    ESP32_ARDUINO = "esp32_arduino"           # ESP32 Arduino sketch (LED matrix)
    COMPORT_NMEA = "comport_nmea"             # NMEA0183 over serial (Nobeltec, OpenCPN)
    TERMINAL_DASHBOARD = "terminal_dashboard" # blessed/rich TUI
    GPIO_PYTHON = "gpio_python"               # RPi.GPIO / libgpiod
    MQTT_PUBLISHER = "mqtt_publisher"         # MQTT topic publish
    WEBHOOK_HTTP = "webhook_http"             # HTTP webhook
    CUSTOM = "custom"


# ─── A2UI primitive types ───────────────────────────────────

@dataclass
class A2UIComponent:
    """A declarative component in the A2UI tree."""
    type: str                              # "text", "gauge", "chart", "button", "led", "matrix", etc.
    props: Dict[str, Any] = field(default_factory=dict)
    bindings: Dict[str, str] = field(default_factory=dict)  # prop_name → cell.port.path
    children: List["A2UIComponent"] = field(default_factory=list)


@dataclass
class A2UITemplate:
    """A reusable, ready-to-go A2UI template."""
    name: str
    description: str
    targets: List[ProjectionTarget]
    components: List[A2UIComponent]
    tags: List[str] = field(default_factory=list)


# ─── Template registry (click-play-customize) ───────────────

TEMPLATES: Dict[str, A2UITemplate] = {
    "autopilot_dashboard": A2UITemplate(
        name="autopilot_dashboard",
        description="Boat autopilot dashboard: GPS + heading + wind + rudder. ESP32 LED matrix or terminal TUI.",
        targets=[ProjectionTarget.ESP32_ARDUINO, ProjectionTarget.TERMINAL_DASHBOARD,
                 ProjectionTarget.HTMX_FRAGMENT, ProjectionTarget.REACT_COMPONENT],
        tags=["boat", "autopilot", "sensor", "real-time"],
        components=[
            A2UIComponent(type="header",
                          props={"text": "Autopilot Dashboard"},
                          bindings={}),
            A2UIComponent(type="gauge",
                          props={"label": "Heading", "min": 0, "max": 360, "unit": "°"},
                          bindings={"value": "imu_heading.heading_deg"}),
            A2UIComponent(type="gauge",
                          props={"label": "Speed (SOG)", "min": 0, "max": 30, "unit": "kn"},
                          bindings={"value": "gps.sog_knots"}),
            A2UIComponent(type="gauge",
                          props={"label": "Wind speed", "min": 0, "max": 60, "unit": "kn"},
                          bindings={"value": "anemometer.wind_kts"}),
            A2UIComponent(type="led",
                          props={"label": "AP engaged"},
                          bindings={"on": "autopilot.engaged"}),
            A2UIComponent(type="matrix",
                          props={"label": "Rudder", "width": 64, "height": 32},
                          bindings={"pixels": "rudder_indicator.matrix"}),
        ],
    ),
    "canon_feed_panel": A2UITemplate(
        name="canon_feed_panel",
        description="Quilt canon feed: list promoted pieces, click to inspect witness log, chord-verdict chips.",
        targets=[ProjectionTarget.HTMX_FRAGMENT, ProjectionTarget.REACT_COMPONENT,
                 ProjectionTarget.STREAMLIT_APP, ProjectionTarget.GRADIO_APP],
        tags=["canon", "feed", "witness", "chord"],
        components=[
            A2UIComponent(type="header",
                          props={"text": "Canon Feed"},
                          bindings={}),
            A2UIComponent(type="list",
                          props={"label": "Promoted pieces"},
                          bindings={"items": "canon_feed.items"}),
            A2UIComponent(type="chip_row",
                          props={"label": "Chord verdicts"},
                          bindings={"chips": "canon_feed.chord_verdicts"}),
        ],
    ),
    "game_hud": A2UITemplate(
        name="game_hud",
        description="Game HUD: player_position, score, health, ammo. Ports to Bevy/Unity/Godot.",
        targets=[ProjectionTarget.BEVY_RUST, ProjectionTarget.UNITY_CSHARP,
                 ProjectionTarget.GODOT_GDSCRIPT, ProjectionTarget.REACT_COMPONENT],
        tags=["game", "hud", "runtime"],
        components=[
            A2UIComponent(type="text",
                          props={"label": "Score"},
                          bindings={"value": "score.value"}),
            A2UIComponent(type="bar",
                          props={"label": "Health", "max": 100},
                          bindings={"value": "player.health"}),
            A2UIComponent(type="bar",
                          props={"label": "Ammo", "max": 30},
                          bindings={"value": "player.ammo"}),
            A2UIComponent(type="sprite",
                          props={"label": "Player"},
                          bindings={"x": "player.position.x",
                                    "y": "player.position.y"}),
        ],
    ),
    "industrial_audit_dashboard": A2UITemplate(
        name="industrial_audit_dashboard",
        description="Industrial audit dashboard: sensor streams + JEV verdict + tamper-evident log + alert wall.",
        targets=[ProjectionTarget.HTMX_FRAGMENT, ProjectionTarget.REACT_COMPONENT,
                 ProjectionTarget.TERMINAL_DASHBOARD],
        tags=["industrial", "audit", "tamper-evident"],
        components=[
            A2UIComponent(type="header",
                          props={"text": "Industrial Audit"},
                          bindings={}),
            A2UIComponent(type="chart",
                          props={"label": "Sensor stream"},
                          bindings={"data": "plc_sensor.stream"}),
            A2UIComponent(type="chip_row",
                          props={"label": "JEV chord"},
                          bindings={"chips": "oracle_gate.verdict_chips"}),
            A2UIComponent(type="log_stream",
                          props={"label": "Audit ledger"},
                          bindings={"entries": "audit_ledger.entries"}),
            A2UIComponent(type="alert_wall",
                          props={"label": "Active alerts"},
                          bindings={"alerts": "alert_wall.active"}),
        ],
    ),
}


# ─── Projection Agent ───────────────────────────────────────

class ProjectionAgent:
    """The third vertex of the Designer/Porter/Projection triangle.

    The Projection Agent emits the LAST-MILE presentation layer:
    - UI templates (A2UI → React/Vue/Svelte/HTMX)
    - Game engine ports (Bevy/Unity/Godot)
    - Hardware ports (ESP32 LED, COM port NMEA, GPIO)
    - Frontend runtime apps (Streamlit/Gradio/TUI)

    Distinguishing principle: Designer thinks in cells (workbook layer),
    Porter thinks in plumbing (workbook→backend), Projection thinks in
    OBSERVATION — how a human/engine/operator sees the cell state.
    """

    def __init__(self, template: Optional[str] = None):
        self.template_name = template
        self.template = TEMPLATES.get(template) if template else None

    # ─── Main entry: project a workbook ───────────────────

    def project(self, workbook: Workbook, target: ProjectionTarget) -> Dict[str, Any]:
        """Project a workbook into a presentation-layer artifact."""
        if target == ProjectionTarget.A2UI_TEMPLATE:
            return {"a2ui": self._to_a2ui(workbook)}
        elif target == ProjectionTarget.ESP32_ARDUINO:
            return {"arduino_ino": self._to_esp32(workbook)}
        elif target == ProjectionTarget.COMPORT_NMEA:
            return {"nmea_bridge": self._to_comport_nmea(workbook)}
        elif target == ProjectionTarget.HTMX_FRAGMENT:
            return {"htmx_html": self._to_htmx(workbook)}
        elif target == ProjectionTarget.BEVY_RUST:
            return {"bevy_rust": self._to_bevy(workbook)}
        elif target == ProjectionTarget.TERMINAL_DASHBOARD:
            return {"tui": self._to_tui(workbook)}
        elif target == ProjectionTarget.GPIO_PYTHON:
            return {"gpio_py": self._to_gpio(workbook)}
        elif target in (ProjectionTarget.REACT_COMPONENT,
                        ProjectionTarget.VUE_COMPONENT,
                        ProjectionTarget.SVELTE_COMPONENT,
                        ProjectionTarget.STREAMLIT_APP,
                        ProjectionTarget.GRADIO_APP):
            return {"frontend_source": self._to_frontend(workbook, target)}
        elif target in (ProjectionTarget.UNITY_CSHARP, ProjectionTarget.GODOT_GDSCRIPT):
            return {"engine_source": self._to_game_engine(workbook, target)}
        elif target == ProjectionTarget.MQTT_PUBLISHER:
            return {"mqtt_config": self._to_mqtt(workbook)}
        elif target == ProjectionTarget.WEBHOOK_HTTP:
            return {"webhook_routes": self._to_webhook(workbook)}
        else:
            return {"error": f"target {target} not yet implemented"}

    # ─── A2UI template generator ──────────────────────────

    def _to_a2ui(self, workbook: Workbook) -> Dict:
        """Generate a generic A2UI component tree from workbook."""
        if self.template:
            return {
                "template": self.template.name,
                "components": [self._component_to_dict(c) for c in self.template.components],
            }
        # Otherwise auto-generate from cells
        components = []
        for cell in workbook.cells.values():
            components.append(A2UIComponent(
                type=self._infer_component_type(cell),
                props={"label": self._cell_name(cell), "cell_id": cell.id},
                bindings={"value": f"{cell.id}.state"},
            ))
        return {
            "template": "auto",
            "components": [self._component_to_dict(c) for c in components],
        }

    @staticmethod
    def _component_to_dict(c: A2UIComponent) -> Dict:
        d = {"type": c.type, "props": c.props, "bindings": c.bindings}
        if c.children:
            d["children"] = [ProjectionAgent._component_to_dict(child) for child in c.children]
        return d

    @staticmethod
    def _infer_component_type(cell: Cell) -> str:
        kind = (cell.metadata.get("cell_kind") or cell.formula or "").lower()
        if "gauge" in kind or "sensor" in kind: return "gauge"
        if "led" in kind or "indicator" in kind: return "led"
        if "chart" in kind or "stream" in kind: return "chart"
        if "log" in kind or "ledger" in kind: return "log_stream"
        if "matrix" in kind: return "matrix"
        return "text"

    @staticmethod
    def _cell_name(cell: Cell) -> str:
        return cell.metadata.get("name") or cell.id

    @staticmethod
    def _cell_kind(cell: Cell) -> str:
        return cell.metadata.get("cell_kind") or cell.formula or ""

    # ─── ESP32 Arduino sketch ─────────────────────────────

    def _to_esp32(self, workbook: Workbook) -> str:
        """Generate an Arduino sketch that reads cells and renders to LED matrix."""
        cells_with_gauge = [c for c in workbook.cells.values()
                           if any("gauge" in (self._cell_kind(c) or "").lower() for _ in [1])]
        bindings = []
        for comp in (self.template.components if self.template else []):
            if comp.type == "gauge":
                bindings.append(
                    f'  // gauge: {comp.props.get("label", "?")} ← {comp.bindings.get("value", "?")}'
                )
            elif comp.type == "led":
                bindings.append(
                    f'  // led: {comp.props.get("label", "?")} ← {comp.bindings.get("on", "?")}'
                )
            elif comp.type == "matrix":
                bindings.append(
                    f'  // matrix: {comp.props.get("width", 64)}x{comp.props.get("height", 32)} ← {comp.bindings.get("pixels", "?")}'
                )

        return f"""// Auto-generated by ax-quilt Projection Agent
// Template: {self.template_name or 'auto'}
// Workbook: {workbook.name}
// Cells: {len(workbook.cells)}

#include <WiFi.h>
#include <ArduinoJson.h>
#include <HTTPClient.h>
#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

const char* QUILT_HOST = "{os.getenv('QUILT_HOST', 'quilt.lan')}";
const int   QUILT_PORT  = {os.getenv('QUILT_PORT', '8080')};
const char* WORKBOOK_ID = "{workbook.name}";

HUB75_I2S_CFG mxConfig(64, 32, 1);
MatrixPanel_I2S_DMA *dma_display = nullptr;

void setup() {{
  Serial.begin(115200);
  dma_display = new MatrixPanel_I2S_DMA(mxConfig);
  dma_display->begin();
  dma_display->setBrightness8(90);
  dma_display->clearScreen();
}}

{chr(10).join(bindings) if bindings else "  // auto-bindings inferred from workbook"}

void loop() {{
  if (WiFi.status() != WL_CONNECTED) return;
  HTTPClient http;
  http.begin(String("http://") + QUILT_HOST + ":" + QUILT_PORT + "/workbook/" + WORKBOOK_ID + "/state");
  int code = http.GET();
  if (code == 200) {{
    String body = http.getString();
    DynamicJsonDocument doc(8192);
    deserializeJson(doc, body);
    render(doc.as<JsonVariant>());
  }}
  http.end();
  delay(250);
}}

void render(JsonVariant state) {{
  dma_display->clearScreen();
  dma_display->setTextSize(1);
  dma_display->setTextColor(dma_display->color565(0, 255, 128));
  dma_display->setCursor(2, 2);
  dma_display->println("Autopilot");
  // ... per-component rendering driven by cell state
  dma_display->flipDMABuffer();
}}
"""

    # ─── NMEA COM port bridge (Nobeltec / OpenCPN) ──────

    def _to_comport_nmea(self, workbook: Workbook) -> str:
        """Generate a Python bridge that reads GPS cell and writes NMEA to a serial port.

        Nobeltec and OpenCPN accept NMEA 0183 sentences over a virtual COM port.
        The bridge maps GPS cell state to NMEA sentences.
        """
        gps_cells = [c for c in workbook.cells.values()
                     if any(k in (self._cell_kind(c) or "").lower() for k in ("gps", "nmea"))]
        return f"""#!/usr/bin/env python3
# Auto-generated by ax-quilt Projection Agent
# Workbook: {workbook.name}
# Maps GPS cell state → NMEA 0183 over a serial port for Nobeltec / OpenCPN.

import json
import time
import serial
import urllib.request

QUILT_HOST = "{os.getenv('QUILT_HOST', 'localhost:8080')}"
WORKBOOK = "{workbook.name}"
SERIAL_PORT = "{os.getenv('SERIAL_PORT', '/dev/ttyUSB0')}"
BAUDRATE = {os.getenv('NMEA_BAUD', '4800')}


def fetch_state():
    with urllib.request.urlopen(f"http://{{QUILT_HOST}}/workbook/{{WORKBOOK}}/state") as r:
        return json.load(r)


def state_to_nmea(state):
    \"\"\"Build NMEA sentences from cell state.\"\"\"
    out = []
    gps = state.get("gps") or {{}}
    if "lat" in gps and "lon" in gps:
        # GPRMC — recommended minimum specific GNSS data
        lat = gps["lat"]
        lon = gps["lon"]
        sog = gps.get("sog_knots", 0.0)
        cog = gps.get("cog_deg", 0.0)
        ts = time.strftime("%H%M%S.00", time.gmtime())
        ds = time.strftime("%d%m%y", time.gmtime())
        out.append(
            f"{{ts}},A,{{lat:08.4f}},N,{{lon:09.4f}},W,{{sog:.1f}},{{cog:.1f}},{{ds}},,,A"
        )
        # GPGGA — fix data
        out.append(
            f"{{ts}},{{lat:08.4f}},N,{{lon:09.4f}},W,1,08,1.0,10.0,M,0.0,M,,"
        )
    return out


def main():
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
        print(f"NMEA bridge live on {{SERIAL_PORT}} @ {{BAUDRATE}} baud")
        while True:
            try:
                state = fetch_state()
                for nmea in state_to_nmea(state):
                    line = "$GPRMC," + nmea.split(",", 1)[1] if nmea.startswith("$") else nmea
                    ser.write((line + "\\r\\n").encode())
            except Exception as e:
                print(f"err: {{e}}")
            time.sleep(1.0)


if __name__ == "__main__":
    main()
"""

    # ─── HTMX fragment (server-side rendering) ──────────

    def _to_htmx(self, workbook: Workbook) -> str:
        cells = list(workbook.cells.values())
        cards = []
        for cell in cells[:20]:
            kind = self._cell_kind(cell) or "generic"
            name = self._cell_name(cell)
            cards.append(f"""
<div class="card" id="cell-{cell.id}" hx-get="/workbook/{workbook.name}/cell/{cell.id}"
     hx-trigger="every 1s" hx-swap="outerHTML">
  <h3>{name}</h3>
  <p class="kind">{kind}</p>
  <div class="state" id="state-{cell.id}">…</div>
</div>""")
        return f"""<!-- Auto-generated by ax-quilt Projection Agent -->
<!-- Workbook: {workbook.name} -->
<div class="ax-quilt-projection" id="workbook-{workbook.name}">
  <h1>{workbook.name}</h1>
  <p>{workbook.flow_description or 'Cell projection'}</p>
  <div class="cell-grid">
    {chr(10).join(cards)}
  </div>
</div>
<style>
.ax-quilt-projection .cell-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 1rem; }}
.ax-quilt-projection .card {{ padding: 0.75rem; border: 1px solid #ccc; border-radius: 6px; }}
.ax-quilt-projection .kind {{ color: #888; font-size: 0.8em; }}
</style>
"""

    # ─── Bevy (Rust game engine) ────────────────────────

    def _to_bevy(self, workbook: Workbook) -> str:
        return f"""// Auto-generated by ax-quilt Projection Agent → Bevy (Rust)
// Workbook: {workbook.name}
// Binds cells → Bevy resources/components.

use bevy::prelude::*;

#[derive(Resource)]
pub struct QuiltState {{
    pub workbook_id: String,
    // cell-derived fields inferred from cell kinds:
    pub player_position: Vec2,
    pub score: u32,
    pub health: u32,
    pub ammo: u32,
}}

fn main() {{
    App::new()
        .add_plugins(DefaultPlugins)
        .insert_resource(QuiltState {{
            workbook_id: "{workbook.name}".to_string(),
            player_position: Vec2::ZERO,
            score: 0,
            health: 100,
            ammo: 30,
        }})
        .add_systems(Startup, setup)
        .add_systems(Update, sync_from_quilt)
        .run();
}}

fn setup(mut commands: Commands) {{
    commands.spawn(Camera2dBundle::default());
}}

fn sync_from_quilt(mut state: ResMut<QuiltState>, mut q_player: Query<&mut Transform, With<Player>>) {{
    // Pull state from quilt every tick
    // let body = reqwest::blocking::get(format!("http://quilt/{{}}/state", state.workbook_id))?.json()?;
    // state.player_position = body.player.position;
    // for mut t in q_player.iter_mut() {{
    //     t.translation = state.player_position.extend(0.0);
    // }}
}}
"""

    # ─── Terminal UI (blessed / rich) ──────────────────

    def _to_tui(self, workbook: Workbook) -> str:
        cells = list(workbook.cells.values())
        rows = []
        for cell in cells[:30]:
            rows.append(f"  {{label: '{self._cell_name(cell)}', value: state['{cell.id}']}}")
        return f"""#!/usr/bin/env python3
# Auto-generated by ax-quilt Projection Agent → Terminal TUI
# Workbook: {workbook.name}

import json, time, urllib.request
from rich.live import Live
from rich.table import Table
from rich.console import Console

WORKBOOK = "{workbook.name}"
QUILT = "http://localhost:8080"


def fetch():
    with urllib.request.urlopen(f"{{QUILT}}/workbook/{{WORKBOOK}}/state") as r:
        return json.load(r)


def render(state) -> Table:
    t = Table(title=f"{{WORKBOOK}} (ax-quilt projection)")
    t.add_column("Cell")
    t.add_column("Kind")
    t.add_column("State", justify="right")
    for cid, cdef in state.get("cells", {{}}).items():
        t.add_row(cid, cdef.get("kind", "?"), str(cdef.get("state", "?")))
    return t


if __name__ == "__main__":
    console = Console()
    with Live(render({{}}), refresh_per_second=2) as live:
        while True:
            try:
                live.update(render(fetch()))
            except Exception as e:
                console.print(f"[red]{{e}}[/red]")
            time.sleep(0.5)
"""

    # ─── GPIO (RPi physical switches/dials) ─────────────

    def _to_gpio(self, workbook: Workbook) -> str:
        """Generate GPIO Python for RPi physical switches/dials."""
        body = """#!/usr/bin/env python3
# Auto-generated by ax-quilt Projection Agent -> GPIO
# Workbook: __WB_NAME__
# Maps physical dials/switches to quilt cells.

import RPi.GPIO as GPIO
import json, time, urllib.request

WORKBOOK = "__WB_NAME__"

CELL_PINS = {
    # cell_id -> BCM_PIN (auto-inferred from cell.metadata.pin)
}


def setup():
    GPIO.setmode(GPIO.BCM)
    for cid, pin in CELL_PINS.items():
        GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)


def read_dial(pin):
    return GPIO.input(pin)


def publish(state):
    req = urllib.request.Request(
        "http://localhost:8080/workbook/" + WORKBOOK + "/input",
        data=json.dumps(state).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        urllib.request.urlopen(req)
    except Exception as e:
        print("publish err: " + str(e))


def main():
    setup()
    while True:
        state = {cid: read_dial(p) for cid, p in CELL_PINS.items()}
        publish(state)
        time.sleep(0.1)


if __name__ == "__main__":
    main()
"""
        return body.replace("__WB_NAME__", workbook.name)

    # ─── Generic frontend (React/Vue/Svelte) ──────────

    def _to_frontend(self, workbook: Workbook, target: ProjectionTarget) -> str:
        components = (self.template.components if self.template
                      else [A2UIComponent(type="text", props={"label": self._cell_name(c)},
                                          bindings={"value": f"{c.id}.state"})
                            for c in workbook.cells.values()])
        if target == ProjectionTarget.REACT_COMPONENT:
            return self._react(workbook, components)
        if target == ProjectionTarget.VUE_COMPONENT:
            return self._vue(workbook, components)
        if target == ProjectionTarget.SVELTE_COMPONENT:
            return self._svelte(workbook, components)
        if target == ProjectionTarget.STREAMLIT_APP:
            return self._streamlit(workbook, components)
        if target == ProjectionTarget.GRADIO_APP:
            return self._gradio(workbook, components)
        return ""

    def _react(self, wb, comps):
        body = """// Auto-generated React component for workbook __WB_NAME__
import React, { useEffect, useState } from 'react';

const QUILT_URL = `http://localhost:8080/workbook/__WB_NAME__/state`;

export function __WB_CAMELProjection() {
  const [state, setState] = useState({});
  useEffect(() => {
    const tick = async () => {
      const r = await fetch(QUILT_URL);
      const d = await r.json();
      setState(d);
    };
    const id = setInterval(tick, 1000);
    tick();
    return () => clearInterval(id);
  }, []);
  return (
    <div className="ax-quilt-projection">
      <h1>__WB_NAME__</h1>
      {comps.map((c, i) => (
        <div key={i} className="cell">
          {c.props.label}: {String(state[c.bindings.value] || '…')}
        </div>
      ))}
    </div>
  );
}
"""
        camel = wb.name.replace('-', '').replace('_', '')
        return body.replace('__WB_NAME__', wb.name).replace('__WB_CAMEL', camel)

    def _vue(self, wb, comps):
        body = """<!-- Auto-generated Vue SFC for workbook __WB_NAME__ -->
<template>
  <div class="ax-quilt-projection">
    <h1>__WB_NAME__</h1>
    <div v-for="(c, i) in comps" :key="i" class="cell">
      {{ c.props.label }}: {{ state[c.bindings.value] || '…' }}
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
const state = ref({});
const QUILT_URL = `http://localhost:8080/workbook/__WB_NAME__/state`;
let id;
onMounted(() => {
  const tick = async () => {
    state.value = await (await fetch(QUILT_URL)).json();
  };
  id = setInterval(tick, 1000);
  tick();
});
onUnmounted(() => clearInterval(id));
</script>
"""
        return body.replace('__WB_NAME__', wb.name)

    def _svelte(self, wb, comps):
        body = """<!-- Auto-generated Svelte component for workbook __WB_NAME__ -->
<script>
  import { onMount, onDestroy } from 'svelte';
  const QUILT_URL = `http://localhost:8080/workbook/__WB_NAME__/state`;
  let state = {};
  let id;
  onMount(() => {
    const tick = async () => state = await (await fetch(QUILT_URL)).json();
    id = setInterval(tick, 1000);
    tick();
  });
  onDestroy(() => clearInterval(id));
</script>

<div class="ax-quilt-projection">
  <h1>__WB_NAME__</h1>
  {#each comps as c}
    <div class="cell">{c.props.label}: {state[c.bindings.value] || '…'}</div>
  {/each}
</div>
"""
        return body.replace('__WB_NAME__', wb.name)

    def _streamlit(self, wb, comps):
        body = """# Auto-generated Streamlit app for workbook __WB_NAME__
import streamlit as st
import requests, time

st.title("__WB_NAME__")

QUILT_URL = f"http://localhost:8080/workbook/__WB_NAME__/state"

placeholder = st.empty()
while True:
    try:
        state = requests.get(QUILT_URL).json()
        with placeholder.container():
            for c in comps:
                st.metric(c['props']['label'], state.get(c['bindings']['value'], '…'))
    except Exception as e:
        st.error(str(e))
    time.sleep(1.0)
"""
        return body.replace('__WB_NAME__', wb.name)

    def _gradio(self, wb, comps):
        body = """# Auto-generated Gradio app for workbook __WB_NAME__
import gradio as gr
import requests

QUILT_URL = f"http://localhost:8080/workbook/__WB_NAME__/state"


def fetch_state():
    return requests.get(QUILT_URL).json()


with gr.Blocks(title="__WB_NAME__") as demo:
    gr.Markdown(f"# __WB_NAME__")
    components_html = "<br>".join(
        f"<b>{c['props']['label']}</b>: {state.get('" + c['bindings']['value'] + "', '…')}"
        for c in comps
    )
    gr.HTML(components_html)
    timer = gr.Timer(1.0)
    timer.tick(fn=lambda: fetch_state(), outputs=[])

demo.launch()
"""
        return body.replace('__WB_NAME__', wb.name)

    # ─── Game engine ports (Unity / Godot) ─────────────

    def _to_game_engine(self, wb, target: ProjectionTarget) -> str:
        if target == ProjectionTarget.UNITY_CSHARP:
            body = """// Auto-generated Unity C# for workbook __WB_NAME__
using UnityEngine;

public class QuiltProjection__WB_UNDERSCORE : MonoBehaviour {
    public string quiltHost = "http://localhost:8080";
    public string workbook = "__WB_NAME__";
    public GameObject player;

    void Update() {
        StartCoroutine(SyncFromQuilt());
    }

    System.Collections.IEnumerator SyncFromQuilt() {
        var req = UnityEngine.Networking.UnityWebRequest.Get($"{quiltHost}/workbook/{workbook}/state");
        yield return req.SendWebRequest();
        if (req.result == UnityEngine.Networking.UnityWebRequest.Result.Success) {
            // Parse JSON, update GameObject transforms/components
        }
    }
}
"""
            underscore = wb.name.replace('-', '_')
            return (body.replace('__WB_NAME__', wb.name)
                        .replace('__WB_UNDERSCORE', underscore))
        if target == ProjectionTarget.GODOT_GDSCRIPT:
            body = """# Auto-generated Godot GDScript for workbook __WB_NAME__
extends Node

const QUILT_URL = "http://localhost:8080/workbook/__WB_NAME__/state"

func _process(delta):
    $HTTPRequest.request(QUILT_URL)

func _on_HTTPRequest_request_completed(result, response_code, headers, body):
    if response_code == 200:
        var json = JSON.parse_string(body.get_string_from_utf8())
        # apply json['player']['position']['x'] to $player.position.x, etc.
        pass
"""
            return body.replace('__WB_NAME__', wb.name)
        return ""

    # ─── MQTT / Webhook ─────────────────────────────────

    def _to_mqtt(self, wb: Workbook) -> Dict:
        return {
            "broker": os.getenv("MQTT_BROKER", "mqtt.lan"),
            "port": int(os.getenv("MQTT_PORT", "1883")),
            "topics": [
                {"topic": f"quilt/{wb.name}/{c.id}",
                 "retain": False, "qos": 1}
                for c in wb.cells.values()
            ],
        }

    def _to_webhook(self, wb: Workbook) -> Dict:
        return {
            "routes": [
                {"path": f"/webhook/{wb.name}/{c.id}", "method": "POST",
                 "target_cell": c.id}
                for c in wb.cells.values()
            ]
        }


# ─── Three-agent doctrine registry ─────────────────────────

THREE_AGENT_DOCTRINE = """
DESIGNER ─ PORTER ─ PROJECTION: the three vertices of ax-quilt

Each agent speaks one language. They never cross-talk.

  DESIGNER  speaks natural language. Sees cells, ranges, flows.
            "Connect the GPS to the autopilot. Display wind on the LED matrix."
            Output: a Workbook.

  PORTER    speaks infrastructure. Reads a Workbook, emits Docker/K8s/Go.
            "image-pipeline.docker.json: 4 services, 1 volume."
            Output: backend manifests.

  PROJECTION speaks presentation. Reads a Workbook, emits UI/HW/engine source.
            "ESP32 Arduino sketch for the LED matrix. NMEA bridge for Nobeltec."
            Output: last-mile artifacts.

The maintainer can pop up any layer:
  - Workbook         (Designer view, spreadsheets)
  - Backend manifest (Porter view, Docker/K8s/Go)
  - Projection artifact (UI/HW/engine view)
  - Zoom into a cell → intra-cellular raw code
  - Zoom into a flow → inter-cellular logic (Porter's emit)

The three agents are MESH — they expand the same workbook into three
coordinate spaces, each at the right level of abstraction.
"""
