"""ax-quilt zoom levels — inter/intra-cellular view for the maintainer.

Casey's directive: "the maintainer can pop up the cells for easy updates,
improvements and fixes. or they can turn around to the backend and see the
raw code for each porting between cells (inter-cellular-logic) or zoom in
on a cell to see it's intra-cellular-logic."

Three zoom levels:
  1. Surface view       — workbook (Designer view)
  2. Inter-cellular     — flow between cells (Porter view)
  3. Intra-cellular     — code inside one cell (Projection + IDE view)

Zoom operations preserve identity — the same cell at different scales
of observation.
"""
from __future__ import annotations
import os
import json
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

try:
    from .cells.cell import Cell, Flow, Workbook, IOType
except ImportError:
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from cells.cell import Cell, Flow, Workbook, IOType


@dataclass
class IntraCellView:
    """Zoom level 3: inside a single cell.

    Shows the cell's raw source code, its dependencies, and its IO
    wiring. The maintainer can edit the source here and the cell
    re-deploys.
    """
    cell: Cell
    source_code: str = ""
    dependencies: List[str] = field(default_factory=list)
    io_wiring: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""

    def to_dict(self) -> Dict:
        return {
            "cell_id": self.cell.id,
            "cell_name": self.cell.metadata.get("name") or self.cell.id,
            "io_type": self.cell.io_type.value,
            "kind": self.cell.metadata.get("cell_kind") or self.cell.formula or "",
            "source_code": self.source_code,
            "dependencies": self.dependencies,
            "io_wiring": self.io_wiring,
            "orientation": self.cell.orientation.to_dict() if self.cell.orientation else None,
            "notes": self.notes,
        }

    def to_html(self) -> str:
        return f"""<div class="ax-quilt-intra" data-cell-id="{self.cell.id}">
  <h3>{self.cell.metadata.get("name") or self.cell.id} <small>({self.cell.io_type.value})</small></h3>
  <pre><code>{self.source_code}</code></pre>
  <details><summary>IO wiring</summary><pre>{json.dumps(self.io_wiring, indent=2)}</pre></details>
  <details><summary>Dependencies</summary><ul>{''.join(f'<li>{d}</li>' for d in self.dependencies)}</ul></details>
  <p class="notes">{self.notes}</p>
</div>"""


@dataclass
class InterCellView:
    """Zoom level 2: between cells (inter-cellular logic).

    Shows the wiring between two cells: the source cell, the target cell,
    the flow, the Porter's emitted glue code (e.g. HTTP proxy, queue topic,
    serial port, etc.).
    """
    source_cell: Cell
    target_cell: Cell
    flow: Flow
    porter_glue: str = ""
    projection_glue: str = ""
    transport: str = "in-process"  # in-process | http | queue | file | serial | gpio | mqtt

    def to_dict(self) -> Dict:
        return {
            "source": self.source_cell.id,
            "target": self.target_cell.id,
            "transport": self.transport,
            "flow": self.flow.to_dict() if hasattr(self.flow, "to_dict") else {},
            "porter_glue": self.porter_glue,
            "projection_glue": self.projection_glue,
        }

    def to_html(self) -> str:
        return f"""<div class="ax-quilt-inter" data-flow="{self.source_cell.id}→{self.target_cell.id}">
  <div class="flow-arrow">{(self.source_cell.metadata.get("name") or self.source_cell.id)} → {(self.target_cell.metadata.get("name") or self.target_cell.id)}</div>
  <p><b>Transport:</b> {self.transport}</p>
  <details open><summary>Porter glue (inter-cellular logic)</summary><pre><code>{self.porter_glue}</code></pre></details>
  <details><summary>Projection glue (last-mile)</summary><pre><code>{self.projection_glue}</code></pre></details>
</div>"""


@dataclass
class SurfaceView:
    """Zoom level 1: the workbook itself (Designer view).

    Shows the spreadsheet: cells as named ranges, flows as references.
    This is what the Designer Agent emits and what the maintainer sees
    at the highest level.
    """
    workbook: Workbook

    def to_dict(self) -> Dict:
        return {
            "name": self.workbook.name,
            "description": self.workbook.flow_description,
            "cells": {cid: c.to_dict() for cid, c in self.workbook.cells.items()},
            "flows": [f.to_dict() if hasattr(f, "to_dict") else {} for f in self.workbook.flows],
        }

    def to_html(self) -> str:
        rows = "".join(
            f"<tr><td>{c.metadata.get('name') or c.id}</td><td>{c.metadata.get('cell_kind') or c.formula or '?'}</td><td>{c.io_type.value}</td></tr>"
            for c in self.workbook.cells.values()
        )
        return f"""<div class="ax-quilt-surface">
  <h1>{self.workbook.name}</h1>
  <p>{self.workbook.flow_description or ''}</p>
  <table class="cells"><thead><tr><th>Cell</th><th>Kind</th><th>IO</th></tr></thead><tbody>{rows}</tbody></table>
</div>"""


# ─── Zoom navigation ──────────────────────────────────────

def zoom_in(workbook: Workbook, target: str) -> Dict[str, Any]:
    """Zoom in on a cell OR a flow.

    If `target` is a cell id → IntraCellView
    If `target` is "cell1→cell2" → InterCellView
    Otherwise → SurfaceView of the whole workbook
    """
    if target in workbook.cells:
        return IntraCellView(cell=workbook.cells[target]).to_dict()
    if "→" in target:
        src, tgt = target.split("→", 1)
        flow = next(
            (f for f in workbook.flows
             if getattr(f, "from_cell", None) == src and getattr(f, "to_cell", None) == tgt),
            None,
        )
        if flow and src in workbook.cells and tgt in workbook.cells:
            return InterCellView(
                source_cell=workbook.cells[src],
                target_cell=workbook.cells[tgt],
                flow=flow,
            ).to_dict()
    return SurfaceView(workbook=workbook).to_dict()


def zoom_out(workbook: Workbook) -> Dict[str, Any]:
    """Surface view (zoom out all the way)."""
    return SurfaceView(workbook=workbook).to_dict()
