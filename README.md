# ax-quilt v0.3.0

> The cellular spreadsheet orchestrator — mesh between Quilt cells and Docker/Kubernetes/Go/anything-with-IO.

**Insight** (Casey's doctrine): A cell is **ANY IO object** — Docker container, K8s pod, Go binary, file, embedded quilt, network endpoint, sensor, queue. Cells compose in **spreadsheet-like ranges** (rows, columns, 2D grids, named ranges, pipelines, broadcasts). The designer agent works at the cellular level using **natural language**, while the porter agent converts that NL into **backend manifests** (Docker Compose, K8s, Go code, etc.).

Two agents cooperate:
- **Designer Agent**: cellular/spreadsheet view, NL interface
- **Porter Agent**: backend porting — emits Docker, K8s, Go

This is the **mesh layer** between Quilt's cellular architecture and existing infrastructure.

## First-person orientation & double-entry bookkeeping

Every cell sees itself as the **origin** of its own little universe. It picks its own **X** and **Y** axes, where each axis is a tensor of whatever dimension makes sense for the cell's job:

| Cell | X axis | Y axis | Z axis (optional) |
|------|--------|--------|-------------------|
| `image_resizer` | `width_pixels` (int) | `height_pixels` (int) | `channel` (rgb) |
| `text_tokenizer` | `token_id` (int) | `position` (int) | `embedding_dim` (float) |
| `time_series_db` | `timestamp` (int) | `metric` (string) | `value` (float) |
| `audio_sampler` | `sample_index` (int) | `channel` (int) | — |
| `kv_store` | `key_hash` (int) | `value_bytes` (bytes) | — |
| `jaccard_chord` | `claim_a` (string) | `claim_b` (string) | `similarity` (float) |

The cell **owns its orientation**. The spreadsheet isn't a global grid — it's a **patchwork of private coordinate systems** that the cells choose themselves.

### Double-entry bookkeeping for flows

A flow between two cells is a **double-entry transaction**:

```
source cell: CREDIT (output port debits a value)
target cell: DEBIT  (input port credits the same value)
```

The spreadsheet is the **ledger**. Every cell's outputs must balance with its connected cells' inputs. If they don't, the workbook doesn't validate.

This is exactly how accounting works: every transaction has two sides, and the books must balance. The same invariant gives ax-quilt workbooks their consistency.

### Why this matters — the Rubik's cube analogy

A Rubik's cube teaches group theory (the symmetric group S₈₈₈,₉₆₀,⁰⁰⁰ — 4.3 × 10¹⁹ configurations) **without ever writing an equation**. You learn the permutation algebra by feel: twists, swaps, cycles, order.

**First-person orientation does the same thing for spreadsheet plumbing.**

When you make a cell choose its own X and Y axes, you're saying: "this cell lives in its own private 2D world." When you connect it to another cell, you're saying: "their two worlds relate by some permutation."

A spreadsheet formula like `=A1+B2` is secretly a **permutation group operation** — adding two values from different coordinates. A pivot table is secretly a **symmetry operation** — relabeling axes. A VLOOKUP is secretly a **group action** — applying a transformation to find a coset.

By giving each cell its own axes, we let the **Designer Agent** think in spreadsheet math (rows, columns, lookups) while the **Porter Agent** translates those intuitions into actual permutation group operations on tensors — without the agent ever needing to write out the formal group theory.

The result: **permutation group mathematics becomes visual and intuitive**, the way a Rubik's cube makes 19-quintillion configurations childishly explorable.

### Cells that self-organize

Because each cell owns its orientation, it can also **declare how it sorts itself**:

```python
wb.add_cell(Cell(
    id="time_series_db",
    io_type=IOType.DATABASE,
    orientation=Orientation(
        x_axis=Axis(name="timestamp", dtype=PortKind.INT, monotonic=True),
        y_axis=Axis(name="metric", dtype=PortKind.STRING, sorted=True),
    ),
    self_sort="ascending_timestamp",  # the cell knows how to sort itself
    formula="time-indexed metric store; sorted by timestamp ascending",
))
```

The cell:
- Knows it's sorted by timestamp
- Knows its Y axis is alphabetically sorted by metric name
- Can describe itself in spreadsheet terms ("rows are timestamps, columns are metrics")
- Lets the Porter Agent pick the right database index (B-tree on timestamp, B-tree on metric)

### How the Porter Agent uses this

When porting a workbook, the Porter Agent reads the **orientation** of each cell and:

1. **Picks the right backend primitive**:
   - X=int, Y=int, monotonic → B-tree index
   - X=int, Y=int, dense → array slice
   - X=string, Y=any → hash map
   - X=tensor, Y=tensor → matrix multiplication
2. **Optimizes flow connections**:
   - If source Y = target X, that's a **direct join** — no transformation needed
   - If source X = target X, that's a **transpose** — Porter emits a `transpose` step
   - If source X = target Y, that's a **swap** — Porter emits a `swap` step
3. **Validates double-entry balance**:
   - Every source output must have a matching target input
   - If unbalanced, Porter refuses to emit and reports the imbalance

### Example: an image pipeline's implicit permutations

A 5-cell image pipeline:

```
fetcher → validator → resizer → db
                      ↓
                    file
```

Each cell has its own axes:

| Cell | X | Y | What flows in/out |
|------|---|---|---|
| fetcher | (no inputs) | url × response_bytes | bytes go to validator |
| validator | image_width × image_height | format × valid | valid → resizer |
| resizer | new_width × new_height | channel | image → db, file |
| db | image_id × metadata_key | value | metadata stored |
| file | filename × offset | byte | bytes stored |

The flow `validator → resizer` is a **permutation**:
- validator.Y = (format, valid) → resizer.X = (new_width, new_height)
- The Porter emits: `if valid: extract dims; transpose (format, valid) → (width, height) for resize`

The Designer Agent never thinks about this. It just says "validator feeds resizer." The Porter handles the **connective tissue** — the permutation that makes the dimensions line up.

This is the **child's play** Casey described: the agent moves cells around the spreadsheet like Rubik's cube faces, and the algebra works itself out.

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
