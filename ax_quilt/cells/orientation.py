"""First-person orientation — each cell's private coordinate system.

Inspired by Casey's doctrine: "a cell to sort the spreadsheet and even
define the x and y with different axises of tensors for whatever it's
job is. this way, the cell can group and organize it's own relationships
to other cells."

Every cell sees itself as the origin of its own universe. It picks its
own X and Y axes (and optionally Z), each axis being a tensor of
whatever dimension makes sense for the cell's job.

This enables all sorts of advanced permutation group mathematics powers
intuitively and visually, the way a Rubik's cube teaches group theory
without chalkboard formalism.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any

from .cell import PortKind


@dataclass
class Axis:
    """One axis of a cell's first-person orientation.

    Each axis has:
    - A name (what it represents)
    - A dtype (what kind of values live on this axis)
    - Optional sort order (the cell knows how it's sorted)
    - Optional monotonicity (does the axis only increase/decrease?)
    """
    name: str
    dtype: PortKind
    sorted: bool = False
    sort_order: str = "ascending"  # ascending / descending
    monotonic: bool = False

    def to_dict(self) -> Dict:
        return {
            "name": self.name, "dtype": self.dtype.value,
            "sorted": self.sorted, "sort_order": self.sort_order,
            "monotonic": self.monotonic,
        }


@dataclass
class Orientation:
    """A cell's first-person orientation — its private coordinate system.

    Each cell sees itself as the origin of its own universe.
    It picks its own X and Y axes (and optionally Z), each axis being
    a tensor of whatever dimension makes sense for the cell's job.

    The Porter Agent reads orientations to optimize backend plumbing:
    - X=int, Y=int, monotonic → B-tree index
    - X=int, Y=int, dense → array slice
    - X=string, Y=any → hash map
    - X=tensor, Y=tensor → matrix multiplication
    """
    x_axis: Axis
    y_axis: Optional[Axis] = None
    z_axis: Optional[Axis] = None
    self_sort: str = ""  # NL: how the cell sorts itself

    def to_dict(self) -> Dict:
        return {
            "x_axis": self.x_axis.to_dict(),
            "y_axis": self.y_axis.to_dict() if self.y_axis else None,
            "z_axis": self.z_axis.to_dict() if self.z_axis else None,
            "self_sort": self.self_sort,
        }

    def axes(self) -> List[Axis]:
        """Return all axes in order."""
        out = [self.x_axis]
        if self.y_axis:
            out.append(self.y_axis)
        if self.z_axis:
            out.append(self.z_axis)
        return out

    def is_sortable(self) -> bool:
        """Is this cell self-sorting (i.e., sorted on at least one axis)?"""
        return any(a.sorted or a.monotonic for a in self.axes())


# ─── Sort order & permutation operations ─────────────────────

def axis_permutation(src: Axis, dst: Axis) -> str:
    """Describe the permutation between two axes.

    Returns a string like:
    - "identity" (same name + dtype + sort)
    - "transpose" (swap X and Y)
    - "swap_dtype" (same name but different dtype)
    - "rename" (different name)
    """
    if src.name == dst.name and src.dtype == dst.dtype:
        return "identity"
    if src.name == dst.name:
        return "swap_dtype"
    return "rename"


def describe_self_sort(cell) -> str:
    """Generate an NL description of how a cell sorts itself."""
    if not cell.orientation:
        return ""
    o: Orientation = cell.orientation
    parts = []
    for axis in o.axes():
        if axis.sorted:
            parts.append(f"sorted on {axis.name} ({axis.sort_order})")
        if axis.monotonic:
            parts.append(f"monotonic on {axis.name}")
    if parts:
        return "; ".join(parts)
    if o.self_sort:
        return o.self_sort
    return "no explicit sort"
