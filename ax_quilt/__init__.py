"""ax-quilt — cellular spreadsheet orchestrator.

A cell is ANY IO object. Cells compose in spreadsheet-like ranges.
Two agents cooperate: Designer (NL, cellular view) + Porter (backend manifests).

Three layers of abstraction (AWS CDK-inspired):
- L1: Cell (a single IO object)
- L2: Workbook (composed cells with opinionated defaults)
- L3: Pattern (a reusable, validated workbook for a specific use case)

Public API:
    from ax_quilt import (
        # L1 — cells
        Cell, Port, Range, Flow, Workbook,
        IOType, PortKind, RangeLayout,
        # L2 — agents
        DesignerAgent, PorterAgent,
        # L3 — patterns
        Pattern, get_pattern, list_patterns,
        # Sync waves (ArgoCD-style)
        assign_waves, order_by_wave, wave_report,
        # Mixins
        apply_mixin, apply_mixins,
    )
"""
from .cells.cell import (
    IOType, PortKind, Port, Cell, Range, RangeLayout, Flow, Workbook,
)
from .agents.designer import DesignerAgent
from .agents.porter import PorterAgent
from .patterns.pattern import (
    Pattern, PATTERNS, get_pattern, list_patterns,
)
from .patterns.waves import (
    Wave, SyncPhase, assign_waves, apply_wave, order_by_wave, wave_report,
)
from .patterns.mixins import (
    MIXINS, apply_mixin, apply_mixins,
)


__version__ = "0.3.0"


__all__ = [
    "__version__",
    "IOType", "PortKind", "Port", "Cell", "Range", "RangeLayout", "Flow", "Workbook",
    "DesignerAgent", "PorterAgent",
    "Pattern", "PATTERNS", "get_pattern", "list_patterns",
    "Wave", "SyncPhase", "assign_waves", "apply_wave", "order_by_wave", "wave_report",
    "MIXINS", "apply_mixin", "apply_mixins",
]
