"""ax-quilt: the cellular spreadsheet orchestrator.

A cell is ANY IO object — Docker container, Kubernetes pod, Go binary,
file, embedded quilt, network endpoint, sensor, etc. Cells compose in
spreadsheet-like ranges (rows, columns, 2D grids, named ranges) and
inter-work via natural-language flow descriptions.

The system has two cooperating agents:
1. Designer Agent: works at the cellular/spreadsheet level using NL
2. Porter Agent: converts NL flows → backend manifests (Docker, K8s, Go)

This module defines the core types.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple


# ─── IO types ─────────────────────────────────────────────────

class IOType(str, Enum):
    """The kinds of cells ax-quilt can represent.

    Anything with input/output is a valid cell. This is the mesh:
    - Compute platforms (docker, kubernetes, go)
    - Data substrates (file, embedded_quilt, network)
    - Edge devices (sensor, actuator)
    - Composition (embedded_quilt = a cell that's also a workbook)
    """
    DOCKER = "docker"           # Docker container
    KUBERNETES = "kubernetes"   # K8s pod/deployment
    GO_BINARY = "go_binary"     # Go executable
    FILE = "file"               # File handle / stream
    EMBEDDED_QUILT = "embedded_quilt"  # A workbook in a workbook
    NETWORK = "network"         # HTTP/gRPC/TCP endpoint
    SENSOR = "sensor"           # Hardware sensor
    ACTUATOR = "actuator"       # Hardware actuator
    QUEUE = "queue"             # Message queue (Redis/Kafka/NATS)
    DATABASE = "database"       # DB connection
    CUSTOM = "custom"           # User-defined


class PortKind(str, Enum):
    """Port data types — like spreadsheet column types."""
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    JSON = "json"
    BYTES = "bytes"
    IMAGE = "image"
    AUDIO = "audio"
    TENSOR = "tensor"
    STREAM = "stream"
    ANY = "any"


# ─── Cell definition ────────────────────────────────────────

@dataclass
class Port:
    """A typed input or output on a cell."""
    name: str
    kind: PortKind
    description: str = ""
    optional: bool = False


@dataclass
class Cell:
    """An IO object in the workbook.

    A cell has:
    - A unique id (like A1, B2 in a spreadsheet)
    - An IO type (what kind of object it is)
    - Inputs and outputs (typed ports)
    - A natural-language formula (what this cell does)
    - Optional backend-specific config (image, replicas, etc.)
    """
    id: str
    io_type: IOType
    inputs: List[Port]
    outputs: List[Port]
    formula: str  # NL description of what this cell does
    backing: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "io_type": self.io_type.value,
            "inputs": [{"name": p.name, "kind": p.kind.value,
                         "description": p.description, "optional": p.optional}
                        for p in self.inputs],
            "outputs": [{"name": p.name, "kind": p.kind.value,
                          "description": p.description, "optional": p.optional}
                         for p in self.outputs],
            "formula": self.formula,
            "backing": self.backing,
            "metadata": self.metadata,
        }

    def validate(self) -> List[str]:
        """Validate cell structure. Returns list of issues."""
        issues = []
        if not self.id:
            issues.append("Cell id is required")
        if not self.io_type:
            issues.append(f"Cell {self.id}: io_type required")
        if not self.formula:
            issues.append(f"Cell {self.id}: formula (NL description) required")
        # A cell must have at least one input or one output
        if not self.inputs and not self.outputs:
            issues.append(f"Cell {self.id}: must have at least one input or output")
        return issues


# ─── Range (grouping) ───────────────────────────────────────

class RangeLayout(str, Enum):
    """How cells are arranged in a range — like spreadsheet ranges."""
    ROW = "row"           # Cells in a row (A1, A2, A3)
    COLUMN = "column"     # Cells in a column (A1, B1, C1)
    GRID = "grid"         # 2D grid (A1:C3)
    NAMED = "named"       # Named range (MyValidators)
    PIPELINE = "pipeline"  # Linear pipeline (sequential)
    BROADCAST = "broadcast"  # Fan-out / fan-in
    SET = "set"           # Unordered group


@dataclass
class Range:
    """A semantic grouping of cells.

    Like spreadsheet ranges (A1:B3) but with semantic meaning.
    Ranges can be: rows, columns, 2D grids, named ranges, pipelines, etc.
    """
    id: str
    cell_ids: List[str]
    layout: RangeLayout
    description: str  # NL: "these are the input validators"
    formulas: Dict[str, str] = field(default_factory=dict)  # cell_id -> flow

    def validate(self, cells: Dict[str, Cell]) -> List[str]:
        issues = []
        for cid in self.cell_ids:
            if cid not in cells:
                issues.append(f"Range {self.id}: cell {cid} does not exist")
        return issues


# ─── Workbook (the spreadsheet of cells) ─────────────────────

@dataclass
class Flow:
    """A directed edge between cells — how data flows."""
    from_cell: str
    from_port: str
    to_cell: str
    to_port: str
    description: str = ""


@dataclass
class Workbook:
    """A complete cellular spreadsheet — the workbook.

    This is the artifact the Designer Agent works with.
    Cells, ranges, flows, NL flow descriptions.
    """
    name: str
    cells: Dict[str, Cell] = field(default_factory=dict)
    ranges: Dict[str, Range] = field(default_factory=dict)
    flows: List[Flow] = field(default_factory=list)
    flow_description: str = ""  # global NL: "this workbook does X by Y"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_cell(self, cell: Cell) -> None:
        self.cells[cell.id] = cell

    def add_range(self, range_: Range) -> None:
        self.ranges[range_.id] = range_

    def add_flow(self, flow: Flow) -> None:
        self.flows.append(flow)

    def validate(self) -> List[str]:
        """Validate the whole workbook."""
        issues = []
        for cell in self.cells.values():
            issues.extend(cell.validate())
        for rng in self.ranges.values():
            issues.extend(rng.validate(self.cells))
        for flow in self.flows:
            if flow.from_cell not in self.cells:
                issues.append(f"Flow: from_cell {flow.from_cell} not in cells")
            if flow.to_cell not in self.cells:
                issues.append(f"Flow: to_cell {flow.to_cell} not in cells")
        return issues

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "cells": {cid: c.to_dict() for cid, c in self.cells.items()},
            "ranges": {rid: {
                "id": r.id, "cell_ids": r.cell_ids,
                "layout": r.layout.value, "description": r.description,
                "formulas": r.formulas,
            } for rid, r in self.ranges.items()},
            "flows": [{
                "from_cell": f.from_cell, "from_port": f.from_port,
                "to_cell": f.to_cell, "to_port": f.to_port,
                "description": f.description,
            } for f in self.flows],
            "flow_description": self.flow_description,
            "metadata": self.metadata,
        }

    def save(self, path: str) -> None:
        """Save workbook to JSON."""
        import json
        from pathlib import Path
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))

    @classmethod
    def load(cls, path: str) -> "Workbook":
        """Load workbook from JSON."""
        import json
        from pathlib import Path as _Path
        data = json.loads(_Path(path).read_text())

        wb = cls(name=data["name"], flow_description=data.get("flow_description", ""))
        for cid, c in data["cells"].items():
            wb.cells[cid] = Cell(
                id=c["id"],
                io_type=IOType(c["io_type"]),
                inputs=[Port(name=p["name"], kind=PortKind(p["kind"]),
                              description=p.get("description", ""),
                              optional=p.get("optional", False))
                         for p in c["inputs"]],
                outputs=[Port(name=p["name"], kind=PortKind(p["kind"]),
                               description=p.get("description", ""),
                               optional=p.get("optional", False))
                          for p in c["outputs"]],
                formula=c["formula"],
                backing=c.get("backing", {}),
                metadata=c.get("metadata", {}),
            )
        for rid, r in data["ranges"].items():
            wb.ranges[rid] = Range(
                id=r["id"], cell_ids=r["cell_ids"],
                layout=RangeLayout(r["layout"]),
                description=r["description"],
                formulas=r.get("formulas", {}),
            )
        for f in data["flows"]:
            wb.flows.append(Flow(
                from_cell=f["from_cell"], from_port=f["from_port"],
                to_cell=f["to_cell"], to_port=f["to_port"],
                description=f.get("description", ""),
            ))
        return wb
