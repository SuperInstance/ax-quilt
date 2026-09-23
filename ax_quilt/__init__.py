"""ax-quilt — cellular spreadsheet orchestrator.

A cell is ANY IO object. Cells compose in spreadsheet-like ranges.
Two agents cooperate: Designer (NL, cellular view) + Porter (backend manifests).

Public API:
    from ax_quilt import (
        Cell, Port, Range, Flow, Workbook,
        IOType, PortKind, RangeLayout,
        DesignerAgent, PorterAgent,
    )
"""
from .cells.cell import (
    IOType, PortKind, Port, Cell, Range, RangeLayout, Flow, Workbook,
)
from .agents.designer import DesignerAgent
from .agents.porter import PorterAgent


__version__ = "0.2.0"


__all__ = [
    "__version__",
    "IOType", "PortKind", "Port", "Cell", "Range", "RangeLayout", "Flow", "Workbook",
    "DesignerAgent", "PorterAgent",
]
