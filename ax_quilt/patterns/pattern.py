"""Patterns (L3 Constructs) — the highest level of abstraction.

Inspired by AWS CDK's L1/L2/L3 construct layers.

L1 = a single cell (raw IO object)
L2 = a workbook (composed cells with opinionated defaults)
L3 = a pattern (a workbook + validation + post-processing for a specific use case)

A pattern is what you reuse. Industry patterns like
`IndustrialAuditPattern` are pre-validated workbooks that solve a
specific problem. The builder (Designer Agent) uses them as primitives.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable

from ..cells.cell import (
    Cell, Port, PortKind, IOType, Range, RangeLayout, Flow, Workbook,
)


@dataclass
class Pattern:
    """An L3 pattern — a reusable, validated workbook for a specific use case.

    A pattern is what builders reach for when they say "I want to do X."
    X = "audit an industrial pipeline" → IndustrialAuditPattern
    X = "process images from a URL" → ImagePipelinePattern
    X = "feed canon into multiple consumers" → CanonFeedPattern
    """
    name: str
    description: str
    builder: Callable[[], Workbook]  # function that produces the workbook
    defaults: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    validators: List[Callable[[Workbook], List[str]]] = field(default_factory=list)
    mixins: List[str] = field(default_factory=list)  # mixin names to apply

    def build(self) -> Workbook:
        """Build the pattern's workbook."""
        wb = self.builder()
        wb.metadata["pattern"] = self.name
        return wb

    def validate(self, wb: Workbook) -> List[str]:
        """Run all pattern validators on a workbook."""
        issues = []
        for validator in self.validators:
            issues.extend(validator(wb))
        return issues


# ─── Built-in patterns ──────────────────────────────────────

def industrial_audit_builder() -> Workbook:
    """Industrial audit pipeline pattern: PLC → embed → oracle → audit → alert."""
    wb = Workbook(
        name="industrial-audit",
        flow_description=(
            "Industrial PLC tags flow through semantic embedding, "
            "JEV oracle gates canon-worthy readings, and tamper-evident "
            "invoice cells record every transformation. Alerts appear on "
            "the homelab display wall."
        ),
    )
    wb.add_cell(Cell(
        id="plc_sensor",
        io_type=IOType.SENSOR,
        inputs=[],
        outputs=[
            Port(name="tag_value", kind=PortKind.FLOAT, description="PLC tag reading"),
            Port(name="timestamp", kind=PortKind.INT, description="when sampled"),
        ],
        formula="reads a PLC tag every 100ms; emits the value + timestamp",
        backing={"plc_host": "192.168.1.10", "tag": "TEMP_REACTOR_01"},
    ))
    wb.add_cell(Cell(
        id="vector_embedder",
        io_type=IOType.CUSTOM,
        inputs=[Port(name="value", kind=PortKind.FLOAT),
                 Port(name="ts", kind=PortKind.INT)],
        outputs=[Port(name="vector", kind=PortKind.TENSOR, description="1024-d embedding")],
        formula="embeds (value, ts) into 1024-d vector for similarity queries",
        backing={"library": "substrate-vectors", "dims": 1024},
    ))
    wb.add_cell(Cell(
        id="jev_oracle",
        io_type=IOType.NETWORK,
        inputs=[Port(name="claim", kind=PortKind.STRING)],
        outputs=[
            Port(name="verdict", kind=PortKind.STRING),
            Port(name="confidence", kind=PortKind.FLOAT),
        ],
        formula="asks JEV oracle whether this reading is canon-worthy (anomaly or expected)",
        backing={"endpoint": "https://api.typesafe.ai/v1/jev"},
    ))
    wb.add_cell(Cell(
        id="invoice_audit",
        io_type=IOType.FILE,
        inputs=[Port(name="input_hash", kind=PortKind.STRING),
                 Port(name="output_hash", kind=PortKind.STRING)],
        outputs=[Port(name="receipt_id", kind=PortKind.STRING)],
        formula="appends input→output diff to Merkle-chained audit log",
        backing={"path": "/audit/invoices.jsonl", "hash_chain": "merkle"},
    ))
    wb.add_cell(Cell(
        id="alert_display",
        io_type=IOType.NETWORK,
        inputs=[Port(name="alert", kind=PortKind.JSON)],
        outputs=[],
        formula="renders anomaly alerts on homelab LED wall",
        backing={"display_endpoint": "http://homelab.local/api/alerts"},
    ))
    wb.add_range(Range(
        id="pipeline", cell_ids=["plc_sensor", "vector_embedder", "invoice_audit", "alert_display"],
        layout=RangeLayout.PIPELINE,
        description="the canonical PLC → audit → alert flow",
    ))
    wb.add_flow(Flow(from_cell="plc_sensor", from_port="tag_value",
                      to_cell="vector_embedder", to_port="value"))
    wb.add_flow(Flow(from_cell="plc_sensor", from_port="tag_value",
                      to_cell="invoice_audit", to_port="input_hash"))
    wb.add_flow(Flow(from_cell="vector_embedder", from_port="vector",
                      to_cell="jev_oracle", to_port="claim"))
    wb.add_flow(Flow(from_cell="vector_embedder", from_port="vector",
                      to_cell="invoice_audit", to_port="output_hash"))
    wb.add_flow(Flow(from_cell="jev_oracle", from_port="verdict",
                      to_cell="alert_display", to_port="alert"))
    return wb


def image_pipeline_builder() -> Workbook:
    """Image processing pipeline: network → go validator → docker resizer → db + file."""
    wb = Workbook(
        name="image-pipeline",
        flow_description="Fetches an image, validates it, resizes it, stores metadata and the resized image",
    )
    wb.add_cell(Cell(
        id="A1", io_type=IOType.NETWORK, inputs=[],
        outputs=[Port(name="image", kind=PortKind.IMAGE)],
        formula="fetches an image from a URL and emits the image bytes",
        backing={"endpoint": "https://api.example.com/image"},
    ))
    wb.add_cell(Cell(
        id="A2", io_type=IOType.GO_BINARY,
        inputs=[Port(name="image", kind=PortKind.IMAGE)],
        outputs=[Port(name="valid", kind=PortKind.BOOL),
                  Port(name="error", kind=PortKind.STRING, optional=True)],
        formula="validates image format and dimensions",
    ))
    wb.add_cell(Cell(
        id="A3", io_type=IOType.DOCKER,
        inputs=[Port(name="image", kind=PortKind.IMAGE)],
        outputs=[Port(name="resized", kind=PortKind.IMAGE)],
        formula="resizes the image to 256x256 preserving aspect ratio",
        backing={"image": "ax-quilt/resizer:v1"},
    ))
    wb.add_cell(Cell(
        id="A4", io_type=IOType.DATABASE,
        inputs=[Port(name="metadata", kind=PortKind.JSON)],
        outputs=[Port(name="id", kind=PortKind.STRING)],
        formula="stores image metadata in postgres and returns the record id",
        backing={"engine": "postgres"},
    ))
    wb.add_cell(Cell(
        id="A5", io_type=IOType.FILE,
        inputs=[Port(name="content", kind=PortKind.IMAGE)],
        outputs=[],
        formula="stores the resized image as a file on shared volume",
        backing={"path": "/data/resized.jpg"},
    ))
    wb.add_range(Range(
        id="pipeline",
        cell_ids=["A1", "A2", "A3", "A4", "A5"],
        layout=RangeLayout.PIPELINE,
        description="the image processing pipeline",
    ))
    wb.add_flow(Flow(from_cell="A1", from_port="image", to_cell="A2", to_port="image"))
    wb.add_flow(Flow(from_cell="A1", from_port="image", to_cell="A3", to_port="image"))
    wb.add_flow(Flow(from_cell="A2", from_port="valid", to_cell="A3", to_port="image"))
    wb.add_flow(Flow(from_cell="A3", from_port="resized", to_cell="A4", to_port="metadata"))
    wb.add_flow(Flow(from_cell="A3", from_port="resized", to_cell="A5", to_port="content"))
    return wb


def canon_feed_builder() -> Workbook:
    """Canon feed: quilt-canon-search → quilt-canon-iterator → broadcast fan-out."""
    wb = Workbook(
        name="canon-feed",
        flow_description=(
            "Searches canon for keywords, iterates matching canon pieces, "
            "and broadcasts the feed to multiple consumers (web, agent, archive)."
        ),
    )
    wb.add_cell(Cell(
        id="canon_search", io_type=IOType.NETWORK, inputs=[],
        outputs=[Port(name="hits", kind=PortKind.JSON)],
        formula="searches the quilt-canon-search index for matching canon pieces",
        backing={"endpoint": "quilt-canon-search:8000"},
    ))
    wb.add_cell(Cell(
        id="canon_iterator", io_type=IOType.GO_BINARY,
        inputs=[Port(name="hits", kind=PortKind.JSON)],
        outputs=[Port(name="pieces", kind=PortKind.JSON, optional=False)],
        formula="iterates the search hits and emits each canon piece",
    ))
    wb.add_cell(Cell(
        id="web_consumer", io_type=IOType.NETWORK,
        inputs=[Port(name="piece", kind=PortKind.JSON)],
        outputs=[],
        formula="renders canon pieces to the web feed",
    ))
    wb.add_cell(Cell(
        id="agent_consumer", io_type=IOType.NETWORK,
        inputs=[Port(name="piece", kind=PortKind.JSON)],
        outputs=[],
        formula="delivers canon pieces to agent pool via SSE",
    ))
    wb.add_cell(Cell(
        id="archive_consumer", io_type=IOType.FILE,
        inputs=[Port(name="piece", kind=PortKind.JSON)],
        outputs=[],
        formula="archives canon pieces to JSONL archive file",
        backing={"path": "/var/canon/archive.jsonl"},
    ))
    wb.add_flow(Flow(from_cell="canon_search", from_port="hits", to_cell="canon_iterator", to_port="hits"))
    wb.add_flow(Flow(from_cell="canon_iterator", from_port="pieces", to_cell="web_consumer", to_port="piece"))
    wb.add_flow(Flow(from_cell="canon_iterator", from_port="pieces", to_cell="agent_consumer", to_port="piece"))
    wb.add_flow(Flow(from_cell="canon_iterator", from_port="pieces", to_cell="archive_consumer", to_port="piece"))
    return wb


def validate_image_pipeline(wb: Workbook) -> List[str]:
    """Validator for image-pipeline pattern: must have exactly one of each kind."""
    issues = []
    kinds = [c.io_type for c in wb.cells.values()]
    if kinds.count(IOType.NETWORK) < 1:
        issues.append("image-pipeline needs at least one NETWORK cell (fetcher)")
    if kinds.count(IOType.GO_BINARY) < 1:
        issues.append("image-pipeline needs at least one GO_BINARY cell (validator)")
    if kinds.count(IOType.DOCKER) < 1:
        issues.append("image-pipeline needs at least one DOCKER cell (resizer)")
    return issues


def validate_industrial_audit(wb: Workbook) -> List[str]:
    """Validator for industrial-audit pattern."""
    issues = []
    if "plc_sensor" not in wb.cells:
        issues.append("industrial-audit needs a plc_sensor cell")
    if "invoice_audit" not in wb.cells:
        issues.append("industrial-audit needs an invoice_audit cell")
    return issues


# ─── Registry ────────────────────────────────────────────────

PATTERNS: Dict[str, Pattern] = {
    "industrial-audit": Pattern(
        name="industrial-audit",
        description="Industrial PLC → audit pipeline with JEV oracle gating",
        builder=industrial_audit_builder,
        tags=["audit", "industrial", "iot", "plc"],
        validators=[validate_industrial_audit],
        mixins=["canary", "witness"],
    ),
    "image-pipeline": Pattern(
        name="image-pipeline",
        description="Image fetching + validation + resize + storage",
        builder=image_pipeline_builder,
        tags=["image", "media", "etl"],
        validators=[validate_image_pipeline],
        mixins=["canary"],
    ),
    "canon-feed": Pattern(
        name="canon-feed",
        description="Canon search + iterate + broadcast to multiple consumers",
        builder=canon_feed_builder,
        tags=["canon", "feed", "federation"],
        mixins=["canary", "polyformality"],
    ),
}


def get_pattern(name: str) -> Optional[Pattern]:
    """Get a pattern by name."""
    return PATTERNS.get(name)


def list_patterns() -> List[str]:
    """List all available pattern names."""
    return sorted(PATTERNS.keys())
