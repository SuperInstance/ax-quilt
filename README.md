# ax-quilt v0.2.0

> The cellular spreadsheet orchestrator — mesh between Quilt cells and Docker/Kubernetes/Go/anything-with-IO.

**Insight** (Casey's doctrine): A cell is **ANY IO object** — Docker container, K8s pod, Go binary, file, embedded quilt, network endpoint, sensor, queue. Cells compose in **spreadsheet-like ranges** (rows, columns, 2D grids, named ranges, pipelines, broadcasts). The designer agent works at the cellular level using **natural language**, while the porter agent converts that NL into **backend manifests** (Docker Compose, K8s, Go code, etc.).

Two agents cooperate:
- **Designer Agent**: cellular/spreadsheet view, NL interface
- **Porter Agent**: backend porting — emits Docker, K8s, Go

This is the **mesh layer** between Quilt's cellular architecture and existing infrastructure.

## Concept

```
   ┌────────────────────┐    NL flow     ┌────────────────────┐
   │  Designer Agent    │ ─────────────► │   Workbook         │
   │  (cellular view)   │                │   (the spreadsheet)│
   │                    │                │   - cells          │
   │  "fetch, validate, │                │   - ranges         │
   │   transform,       │                │   - flows          │
   │   store"           │                │   - NL descriptions│
   └────────────────────┘                └────────────────────┘
                                                   │
                                                   ▼ porter
                                ┌──────────────────────────────────┐
                                │  Porter Agent (backend manifests) │
                                │  - Docker Compose                │
                                │  - Kubernetes manifests          │
                                │  - Go source code                │
                                │  - (anything with IO)            │
                                └──────────────────────────────────┘
                                                   │
                                                   ▼ runs on
                                ┌──────────────────────────────────┐
                                │  Mesh runtime                    │
                                │  - Docker daemon                 │
                                │  - K8s cluster                   │
                                │  - Go binaries                   │
                                │  - Files, queues, sensors        │
                                └──────────────────────────────────┘
```

## What is a Cell?

Anything with input/output:

| IO Type | Description |
|---------|-------------|
| `docker` | Docker container |
| `kubernetes` | K8s pod/deployment |
| `go_binary` | Go executable |
| `file` | File handle or stream |
| `embedded_quilt` | A workbook nested in a cell |
| `network` | HTTP/gRPC endpoint |
| `sensor` | Hardware sensor |
| `actuator` | Hardware actuator |
| `queue` | Message queue (Redis/Kafka/NATS) |
| `database` | DB connection |
| `custom` | User-defined |

Cells have **typed ports** (string/int/float/bool/json/bytes/image/audio/tensor/stream) and a **natural-language formula** describing what they do.

## What is a Range?

A semantic grouping of cells, like spreadsheet ranges:

| Layout | Example | Meaning |
|--------|---------|---------|
| `row` | A1, A2, A3 | Sequential cells in a row |
| `column` | A1, B1, C1 | Stacked cells in a column |
| `grid` | A1:C3 | 2D block |
| `named` | `MyValidators` | Named range |
| `pipeline` | A1→A2→A3 | Linear pipeline |
| `broadcast` | A→{B,C,D} | Fan-out |
| `set` | {A1, A2} | Unordered group |

## Install / Run

```bash
# From the workspace
python3 -m ax_quilt version

# Design from NL intent
python3 -m ax_quilt design "fetch, validate, transform, store image data"

# Validate a workbook
python3 -m ax_quilt validate examples/image-pipeline.json

# Port to Docker Compose
python3 -m ax_quilt docker examples/image-pipeline.json -o docker.json

# Port to Kubernetes
python3 -m ax_quilt k8s examples/image-pipeline.json -o k8s.json

# Port to Go source
python3 -m ax_quilt go examples/image-pipeline.json -o ./my-go-app
```

## Python API

```python
from ax_quilt import (
    Workbook, Cell, Port, PortKind, IOType,
    Range, RangeLayout, Flow, DesignerAgent, PorterAgent,
)

# Designer mode
designer = DesignerAgent()
wb = designer.create_workbook("my-pipeline", "fetches, validates, stores data")

# Add cells
wb.add_cell(Cell(
    id="fetcher",
    io_type=IOType.NETWORK,
    inputs=[],
    outputs=[Port(name="data", kind=PortKind.JSON)],
    formula="fetches data from an endpoint",
))
wb.add_cell(Cell(
    id="validator",
    io_type=IOType.GO_BINARY,
    inputs=[Port(name="input", kind=PortKind.JSON)],
    outputs=[Port(name="valid", kind=PortKind.BOOL)],
    formula="validates the input data",
))

# Connect via flow
designer.connect(wb, "fetcher", "data", "validator", "input")

# Group via range
wb.add_range(Range(
    id="pipeline",
    cell_ids=["fetcher", "validator"],
    layout=RangeLayout.PIPELINE,
    description="the data pipeline",
))

# Porter mode
porter = PorterAgent()
docker_manifest = porter.port_to_docker(wb)
k8s_manifest = porter.port_to_kubernetes(wb)
go_files = porter.port_to_go(wb)
```

## Tests

```bash
python3 run_tests.py    # 23/23 passing
```

## Example

`examples/image-pipeline.json` shows a 5-cell image processing pipeline:
- A1: `network` cell fetches image
- A2: `go_binary` cell validates
- A3: `docker` cell resizes
- A4: `database` cell stores metadata
- A5: `file` cell holds the resized image

Same workbook ports to:
- `examples/image-pipeline.docker.json` (4 services, 1 volume)
- `examples/image-pipeline.k8s.json` (2 deployments, 5 services)
- `examples/go-output/` (3 Go files: main.go, A2.go, go.mod)

## Bedrock Doctrines

- `cells_are_scars` — every cell is a record of an IO contract
- `witness_log_is_prediction` — workbook ports predict the runtime topology
- `canon_gate_is_chord` — workbook is canon when Designer + Porter agree
- `oracle_is_heard` — NL flow description is heard, not parsed
- `substrate_quantum` — a cell is a verb, not a noun
- `polyformalism_canary` — same canary across all porter outputs

## Casey Mesh Doctrine (origin)

> "Cells can be containers in one agent's abstraction and within the container it could be a traditional application or it could be an embedded quilt. The same for any kind of object with an IO."

The Designer Agent and Porter Agent are the two faces of this doctrine:
- Designer Agent: cells are **abstractions** with NL formulas
- Porter Agent: cells become **concrete backends** (Docker/K8s/Go/files)
- The mesh: a single workbook ports to ANY backend that supports IO

## Versioning

- v0.1.0: Quilt-only local Python orchestrator (replaced original ax.io/v1alpha1)
- v0.2.0: Cellular spreadsheet orchestrator — mesh with Docker/K8s/Go/files
