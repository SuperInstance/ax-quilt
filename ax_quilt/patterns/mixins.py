"""Mixins — cross-cutting features applied to any cell/workbook.

AWS CDK-style `.with()` mixins. Apply a mixin to add features
without changing the underlying cell definition.

Built-in mixins:
- canary: adds the polyformalism canary to all cells
- witness: wraps all cells in a witness log
- polyformality: adds chord verification gates
- observability: adds metrics + logging
"""
from dataclasses import dataclass
from typing import Callable, Dict, List

from ..cells.cell import Cell, Workbook


def mixin_canary(cell: Cell) -> Cell:
    """Add the polyformalism canary to a cell."""
    cell.metadata["canary"] = "0x24a555471370b18d"
    return cell


def mixin_witness(cell: Cell) -> Cell:
    """Mark a cell as producing witness log entries."""
    cell.metadata["witness"] = True
    cell.metadata["witness_log_path"] = f"/workspace/research/{cell.id}-witness.jsonl"
    return cell


def mixin_polyformality(cell: Cell) -> Cell:
    """Require chord verification (N-of-M polyformality) on cell output."""
    cell.metadata["polyformality_required"] = True
    cell.metadata["polyformality_threshold"] = 0.5
    return cell


def mixin_observability(cell: Cell) -> Cell:
    """Add metrics + tracing to a cell."""
    cell.metadata["metrics"] = True
    cell.metadata["trace"] = True
    cell.metadata["otel_endpoint"] = "http://otel-collector:4317"
    return cell


MIXINS: Dict[str, Callable[[Cell], Cell]] = {
    "canary": mixin_canary,
    "witness": mixin_witness,
    "polyformality": mixin_polyformality,
    "observability": mixin_observability,
}


def apply_mixin(cell: Cell, mixin_name: str) -> Cell:
    """Apply a named mixin to a cell."""
    mixin = MIXINS.get(mixin_name)
    if mixin:
        return mixin(cell)
    return cell


def apply_mixins(workbook: Workbook, mixin_names: List[str]) -> Workbook:
    """Apply multiple mixins to every cell in a workbook."""
    for cell in workbook.cells.values():
        for name in mixin_names:
            apply_mixin(cell, name)
    return workbook
