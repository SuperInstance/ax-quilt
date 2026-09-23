"""ax-quilt — cellular spreadsheet orchestrator.

A cell is ANY IO object. Cells compose in spreadsheet-like ranges.
THREE agents cooperate:
  - Designer   (NL, cellular view)
  - Porter     (backend manifests: Docker/K8s/Go)
  - Projection (last-mile UI/HW/engine: ESP32/NMEA/React/Bevy/...)

Each cell has FIRST-PERSON ORIENTATION (its own X/Y/Z axes) and
self-organizes via DOUBLE-ENTRY BOOKKEEPING (every flow has two sides).

Three layers of abstraction (AWS CDK-inspired):
- L1: Cell (a single IO object) + Orientation (its private axes)
- L2: Workbook (composed cells with opinionated defaults)
- L3: Pattern (a reusable, validated workbook for a specific use case)

Public API:
    from ax_quilt import (
        # L1 — cells + orientation
        Cell, Port, Range, Flow, Workbook,
        Orientation, Axis,  # first-person cell coordinates
        IOType, PortKind, RangeLayout,
        # L2 — three agents
        DesignerAgent, PorterAgent, ProjectionAgent,
        ProjectionTarget, TEMPLATES, THREE_AGENT_DOCTRINE,
        # L3 — patterns
        Pattern, get_pattern, list_patterns,
        # Sync waves (ArgoCD-style)
        assign_waves, order_by_wave, wave_report,
        # Mixins
        apply_mixin, apply_mixins,
        # Zoom levels
        zoom_in, zoom_out,
    )
"""
from .cells.cell import (
    IOType, PortKind, Port, Cell, Range, RangeLayout, Flow, Workbook,
)
from .cells.orientation import (
    Axis, Orientation, axis_permutation, describe_self_sort,
)
from .agents.designer import DesignerAgent
from .agents.porter import PorterAgent
from .agents.projection import (
    ProjectionAgent, ProjectionTarget, A2UIComponent, A2UITemplate,
    TEMPLATES, THREE_AGENT_DOCTRINE,
)
from .patterns.pattern import (
    Pattern, PATTERNS, get_pattern, list_patterns,
)
from .patterns.waves import (
    Wave, SyncPhase, assign_waves, apply_wave, order_by_wave, wave_report,
)
from .patterns.mixins import (
    MIXINS, apply_mixin, apply_mixins,
)
from .zoom import (
    IntraCellView, InterCellView, SurfaceView, zoom_in, zoom_out,
)


__version__ = "0.4.0"


__all__ = [
    "__version__",
    "IOType", "PortKind", "Port", "Cell", "Range", "RangeLayout", "Flow", "Workbook",
    "Axis", "Orientation", "axis_permutation", "describe_self_sort",  # first-person orientation
    "DesignerAgent", "PorterAgent",
    "Pattern", "PATTERNS", "get_pattern", "list_patterns",
    "Wave", "SyncPhase", "assign_waves", "apply_wave", "order_by_wave", "wave_report",
    "MIXINS", "apply_mixin", "apply_mixins",
]
