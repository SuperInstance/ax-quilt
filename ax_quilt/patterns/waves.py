"""Sync Waves (ArgoCD pattern) — order cell application.

`argocd.argoproj.io/sync-wave`-style integer annotations that control
apply order. Lower waves apply first.

Negative waves apply before default (e.g., -1 = setup, -2 = CRDs).
Default = 0.
Positive waves apply after default (e.g., 1, 2, ...).

Combined with PreSync / Sync / PostSync phases, you get transactional
deployment pipelines.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List

from ..cells.cell import Cell, Workbook


class SyncPhase(str, Enum):
    """When a cell applies within a sync operation."""
    PRE_SYNC = "PreSync"     # before main sync
    SYNC = "Sync"            # during main sync
    POST_SYNC = "PostSync"   # after main sync complete


@dataclass
class Wave:
    """A sync wave — an ordered batch of cells."""
    wave: int  # -2 (lowest) to N (highest); default 0
    phase: SyncPhase = SyncPhase.SYNC
    description: str = ""


def assign_waves(workbook: Workbook) -> Dict[str, Wave]:
    """Assign sync waves to cells based on dependency order.

    Cells with no dependencies → wave 0.
    Cells that depend on others → wave = (max dependency wave) + 1.

    Returns a dict mapping cell_id → Wave.
    """
    waves: Dict[str, Wave] = {}

    # Build dependency graph
    deps: Dict[str, List[str]] = {cid: [] for cid in workbook.cells}
    for flow in workbook.flows:
        deps[flow.to_cell].append(flow.from_cell)

    # Topological ordering
    def compute_wave(cid: str, _seen: set = None) -> int:
        if _seen is None:
            _seen = set()
        if cid in _seen:
            return 0  # cycle
        _seen.add(cid)
        if cid in waves:
            return waves[cid].wave
        max_dep = 0
        for dep in deps.get(cid, []):
            if dep in workbook.cells:
                max_dep = max(max_dep, compute_wave(dep, _seen) + 1)
        return max_dep

    for cid in workbook.cells:
        w = Wave(wave=compute_wave(cid), phase=SyncPhase.SYNC,
                 description=f"auto-assigned wave for {cid}")
        waves[cid] = w

    return waves


def apply_wave(workbook: Workbook, cell_id: str, wave: int,
                phase: SyncPhase = SyncPhase.SYNC,
                description: str = "") -> None:
    """Apply a specific wave to a cell (override the auto-assignment)."""
    if cell_id not in workbook.cells:
        return
    cell = workbook.cells[cell_id]
    cell.metadata["sync_wave"] = wave
    cell.metadata["sync_phase"] = phase.value
    if description:
        cell.metadata["sync_description"] = description


def order_by_wave(workbook: Workbook) -> List[str]:
    """Return cell_ids in sync order (lowest wave first)."""
    waves = assign_waves(workbook)
    return sorted(waves.keys(), key=lambda cid: waves[cid].wave)


def wave_report(workbook: Workbook) -> str:
    """Generate a human-readable wave report."""
    waves = assign_waves(workbook)
    by_wave: Dict[int, List[str]] = {}
    for cid, w in waves.items():
        by_wave.setdefault(w.wave, []).append(f"[{w.phase.value}] {cid}")

    lines = [f"=== Sync Wave Plan for {workbook.name} ==="]
    for w in sorted(by_wave.keys()):
        cells_str = ", ".join(by_wave[w])
        lines.append(f"Wave {w}: {cells_str}")
    return "\n".join(lines)
