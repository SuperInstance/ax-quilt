"""Designer Agent — works at the cellular/spreadsheet level with NL.

The Designer Agent:
- Receives high-level intent in NL
- Creates cells with IO types
- Sets up ranges and flows
- Validates port compatibility
- Speaks NL to the user

It does NOT know about Docker/K8s/Go. It only knows about cells and flows.
"""
from typing import Dict, List, Optional

from ..cells.cell import (
    Cell, Range, RangeLayout, Flow, Workbook, Port, PortKind, IOType,
)


class DesignerAgent:
    """The Designer Agent — high-level cellular composition."""

    def __init__(self, name: str = "designer"):
        self.name = name
        self.workbooks: Dict[str, Workbook] = {}

    def create_workbook(self, name: str, flow_description: str = "") -> Workbook:
        """Start a new workbook with a NL description of what it does."""
        wb = Workbook(name=name, flow_description=flow_description)
        self.workbooks[name] = wb
        return wb

    def suggest_cells(self, intent: str) -> List[Dict]:
        """Given NL intent, suggest cells (the Designer proposes a topology).

        This is a simple heuristic — in production, an LLM would do this.
        Returns a list of cell specifications the user can accept/reject.
        """
        intent_lower = intent.lower()
        suggestions = []

        # Common patterns:
        if "fetch" in intent_lower or "download" in intent_lower:
            suggestions.append({
                "id": "fetcher",
                "io_type": IOType.NETWORK.value,
                "inputs": [],
                "outputs": [{"name": "response", "kind": PortKind.JSON.value,
                              "description": "the fetched data"}],
                "formula": "fetches data from an external endpoint and emits JSON",
            })
        if "transform" in intent_lower or "process" in intent_lower:
            suggestions.append({
                "id": "transformer",
                "io_type": IOType.DOCKER.value,
                "inputs": [{"name": "input", "kind": PortKind.JSON.value}],
                "outputs": [{"name": "output", "kind": PortKind.JSON.value}],
                "formula": "transforms input data via a Docker container",
            })
        if "store" in intent_lower or "save" in intent_lower:
            suggestions.append({
                "id": "storer",
                "io_type": IOType.DATABASE.value,
                "inputs": [{"name": "data", "kind": PortKind.JSON.value}],
                "outputs": [],
                "formula": "stores data in a database",
            })
        if "validate" in intent_lower or "check" in intent_lower:
            suggestions.append({
                "id": "validator",
                "io_type": IOType.GO_BINARY.value,
                "inputs": [{"name": "input", "kind": PortKind.ANY.value}],
                "outputs": [
                    {"name": "valid", "kind": PortKind.BOOL.value},
                    {"name": "errors", "kind": PortKind.STRING.value, "optional": True},
                ],
                "formula": "validates input against a schema, emits valid/errors",
            })

        return suggestions

    def apply_suggestion(self, workbook: Workbook, suggestion: Dict) -> Cell:
        """Apply a suggestion to a workbook, creating the cell."""
        cell = Cell(
            id=suggestion["id"],
            io_type=IOType(suggestion["io_type"]),
            inputs=[Port(name=p["name"], kind=PortKind(p["kind"]),
                          description=p.get("description", ""))
                     for p in suggestion["inputs"]],
            outputs=[Port(name=p["name"], kind=PortKind(p["kind"]),
                           description=p.get("description", ""))
                      for p in suggestion["outputs"]],
            formula=suggestion["formula"],
        )
        workbook.add_cell(cell)
        return cell

    def create_range(self, workbook: Workbook, range_id: str,
                     cell_ids: List[str], layout: str,
                     description: str) -> Range:
        """Create a semantic range (spreadsheet-style grouping)."""
        rng = Range(
            id=range_id,
            cell_ids=cell_ids,
            layout=RangeLayout(layout),
            description=description,
        )
        workbook.add_range(rng)
        return rng

    def connect(self, workbook: Workbook, from_cell: str, from_port: str,
                to_cell: str, to_port: str, description: str = "") -> bool:
        """Connect two cells via their ports."""
        src = workbook.cells.get(from_cell)
        dst = workbook.cells.get(to_cell)
        if not src or not dst:
            return False
        # Verify port exists
        if not any(p.name == from_port for p in src.outputs):
            return False
        if not any(p.name == to_port for p in dst.inputs):
            return False
        workbook.add_flow(Flow(
            from_cell=from_cell, from_port=from_port,
            to_cell=to_cell, to_port=to_port,
            description=description,
        ))
        return True

    def describe(self, workbook: Workbook) -> str:
        """Produce a NL description of the workbook (what a user would see)."""
        lines = [f"Workbook: {workbook.name}"]
        if workbook.flow_description:
            lines.append(f"Purpose: {workbook.flow_description}")
        lines.append(f"Cells: {len(workbook.cells)}")
        for cid, cell in workbook.cells.items():
            lines.append(f"  [{cid}] {cell.io_type.value}: {cell.formula}")
        lines.append(f"Ranges: {len(workbook.ranges)}")
        for rid, rng in workbook.ranges.items():
            lines.append(f"  [{rid}] {rng.layout.value}: {rng.description}")
            lines.append(f"      cells: {', '.join(rng.cell_ids)}")
        lines.append(f"Flows: {len(workbook.flows)}")
        for f in workbook.flows:
            lines.append(f"  {f.from_cell}.{f.from_port} → {f.to_cell}.{f.to_port}")
        return "\n".join(lines)
