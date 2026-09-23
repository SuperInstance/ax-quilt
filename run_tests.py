"""Test suite for ax-quilt v0.2.0 — cellular spreadsheet orchestrator."""
import json
import sys
import tempfile
from pathlib import Path

from ax_quilt import (
    __version__, canary,
    Cell, Port, PortKind, IOType, Range, RangeLayout, Flow, Workbook,
    DesignerAgent, PorterAgent,
    Pattern, get_pattern, list_patterns,
    assign_waves, order_by_wave, wave_report,
    apply_mixin, apply_mixins,
)
from ax_quilt.canary import canary as canary_func


results = []
failures = []


def test(name, func):
    try:
        func()
        results.append((name, "PASS"))
    except AssertionError as e:
        results.append((name, f"FAIL: {e}"))
        failures.append(name)
    except Exception as e:
        results.append((name, f"ERROR: {type(e).__name__}: {e}"))
        failures.append(name)


# ─── Canary & version ───────────────────────────────────────

def t_canary():
    assert canary_func() == "0x24a555471370b18d"


def t_version():
    assert __version__ == "0.3.0"


# ─── Cell tests ─────────────────────────────────────────────

def t_cell_minimal():
    c = Cell(
        id="A1",
        io_type=IOType.DOCKER,
        inputs=[],
        outputs=[Port(name="out", kind=PortKind.STRING)],
        formula="does something",
    )
    issues = c.validate()
    assert not issues, f"Cell should be valid: {issues}"


def t_cell_no_id_invalid():
    c = Cell(
        id="",
        io_type=IOType.DOCKER,
        inputs=[],
        outputs=[Port(name="out", kind=PortKind.STRING)],
        formula="x",
    )
    issues = c.validate()
    assert any("id" in i for i in issues)


def t_cell_no_io_invalid():
    c = Cell(
        id="X",
        io_type=IOType.DOCKER,
        inputs=[],
        outputs=[],
        formula="x",
    )
    issues = c.validate()
    assert any("input or output" in i for i in issues)


def t_cell_to_dict():
    c = Cell(
        id="A1",
        io_type=IOType.GO_BINARY,
        inputs=[Port(name="in", kind=PortKind.JSON)],
        outputs=[Port(name="out", kind=PortKind.JSON)],
        formula="transforms",
    )
    d = c.to_dict()
    assert d["id"] == "A1"
    assert d["io_type"] == "go_binary"
    assert len(d["inputs"]) == 1
    assert len(d["outputs"]) == 1


# ─── Workbook tests ─────────────────────────────────────────

def t_workbook_create():
    wb = Workbook(name="test", flow_description="a test")
    assert wb.name == "test"
    assert len(wb.cells) == 0


def t_workbook_add_cell():
    wb = Workbook(name="x")
    cell = Cell(
        id="A1",
        io_type=IOType.DOCKER,
        inputs=[],
        outputs=[Port(name="out", kind=PortKind.STRING)],
        formula="x",
    )
    wb.add_cell(cell)
    assert "A1" in wb.cells


def t_workbook_add_range():
    wb = Workbook(name="x")
    wb.add_cell(Cell(id="A1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="A2", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    rng = Range(id="R1", cell_ids=["A1", "A2"],
                layout=RangeLayout.ROW,
                description="a row")
    wb.add_range(rng)
    assert "R1" in wb.ranges


def t_workbook_validate():
    wb = Workbook(name="x", flow_description="test")
    wb.add_cell(Cell(id="A1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="out", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="A2", io_type=IOType.DOCKER,
                     inputs=[Port(name="in", kind=PortKind.STRING)],
                     outputs=[Port(name="out", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A1", from_port="out",
                      to_cell="A2", to_port="in", description="data"))
    issues = wb.validate()
    assert not issues, f"Should be valid: {issues}"


def t_workbook_save_load():
    wb = Workbook(name="test", flow_description="a test")
    wb.add_cell(Cell(id="A1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="out", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="A2", io_type=IOType.DOCKER,
                     inputs=[Port(name="in", kind=PortKind.STRING)],
                     outputs=[Port(name="out", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A1", from_port="out",
                      to_cell="A2", to_port="in"))

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    wb.save(path)
    loaded = Workbook.load(path)
    assert loaded.name == "test"
    assert "A1" in loaded.cells
    assert len(loaded.flows) == 1
    Path(path).unlink()


# ─── Designer agent tests ───────────────────────────────────

def t_designer_create_workbook():
    d = DesignerAgent()
    wb = d.create_workbook("x", "does x")
    assert wb.name == "x"


def t_designer_suggestions():
    d = DesignerAgent()
    suggestions = d.suggest_cells("fetch transform validate store data")
    assert any(s["id"] == "fetcher" for s in suggestions)
    assert any(s["id"] == "transformer" for s in suggestions)
    assert any(s["id"] == "validator" for s in suggestions)
    assert any(s["id"] == "storer" for s in suggestions)


def t_designer_apply_suggestion():
    d = DesignerAgent()
    wb = d.create_workbook("x")
    s = {"id": "test", "io_type": IOType.DOCKER.value,
         "inputs": [], "outputs": [{"name": "o", "kind": "string"}],
         "formula": "test"}
    cell = d.apply_suggestion(wb, s)
    assert cell.id == "test"
    assert "test" in wb.cells


def t_designer_connect():
    d = DesignerAgent()
    wb = d.create_workbook("x")
    wb.add_cell(Cell(id="A", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="B", io_type=IOType.DOCKER,
                     inputs=[Port(name="i", kind=PortKind.STRING)],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    ok = d.connect(wb, "A", "o", "B", "i")
    assert ok
    assert len(wb.flows) == 1


def t_designer_connect_invalid_port():
    d = DesignerAgent()
    wb = d.create_workbook("x")
    wb.add_cell(Cell(id="A", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="B", io_type=IOType.DOCKER,
                     inputs=[Port(name="i", kind=PortKind.STRING)],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    ok = d.connect(wb, "A", "nonexistent", "B", "i")
    assert not ok


def t_designer_describe():
    d = DesignerAgent()
    wb = d.create_workbook("x", "test")
    wb.add_cell(Cell(id="A1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    desc = d.describe(wb)
    assert "Workbook: x" in desc
    assert "A1" in desc


# ─── Porter agent tests ─────────────────────────────────────

def t_porter_docker_basic():
    d = DesignerAgent()
    wb = d.create_workbook("test")
    wb.add_cell(Cell(id="A1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_cell(Cell(id="A2", io_type=IOType.DOCKER,
                     inputs=[Port(name="i", kind=PortKind.STRING)],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A1", from_port="o",
                      to_cell="A2", to_port="i"))

    p = PorterAgent()
    manifest = p.port_to_docker(wb)
    assert "version" in manifest
    assert "A1" in manifest["services"]
    assert "A2" in manifest["services"]
    assert "axnet" in manifest["networks"]


def t_porter_docker_k8s_cell():
    """A KUBERNETES cell becomes a deployable service."""
    d = DesignerAgent()
    wb = d.create_workbook("test")
    wb.add_cell(Cell(id="K1", io_type=IOType.KUBERNETES, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x",
                     backing={"image": "myapp:v1"}))
    p = PorterAgent()
    manifest = p.port_to_docker(wb)
    assert "K1" in manifest["services"]


def t_porter_kubernetes_basic():
    d = DesignerAgent()
    wb = d.create_workbook("test")
    wb.add_cell(Cell(id="K1", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x",
                     backing={"image": "myapp:v1"}))
    p = PorterAgent()
    manifest = p.port_to_kubernetes(wb)
    assert "deployments" in manifest
    assert len(manifest["deployments"]) == 1


def t_porter_go():
    d = DesignerAgent()
    wb = d.create_workbook("test", flow_description="test workbook")
    wb.add_cell(Cell(id="Go1", io_type=IOType.GO_BINARY, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="transforms"))
    p = PorterAgent()
    files = p.port_to_go(wb)
    assert "main.go" in files
    assert "Go1.go" in files
    assert "go.mod" in files
    assert "test workbook" in files["main.go"]


def t_porter_database():
    """A DATABASE cell becomes a DB service."""
    d = DesignerAgent()
    wb = d.create_workbook("test")
    wb.add_cell(Cell(id="db", io_type=IOType.DATABASE, inputs=[],
                     outputs=[Port(name="conn", kind=PortKind.STRING)], formula="stores data",
                     backing={"engine": "postgres"}))
    p = PorterAgent()
    manifest = p.port_to_docker(wb)
    assert "db" in manifest["services"]
    assert "postgres:15" in manifest["services"]["db"]["image"]


def t_porter_file_volume():
    """A FILE cell becomes a volume mounted to dependent cells."""
    d = DesignerAgent()
    wb = d.create_workbook("test")
    wb.add_cell(Cell(id="F1", io_type=IOType.FILE, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.BYTES)], formula="stores file",
                     backing={"path": "/data/file.bin"}))
    wb.add_cell(Cell(id="C1", io_type=IOType.DOCKER,
                     inputs=[Port(name="i", kind=PortKind.BYTES)],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="reads"))
    wb.add_flow(Flow(from_cell="F1", from_port="o", to_cell="C1", to_port="i"))
    p = PorterAgent()
    manifest = p.port_to_docker(wb)
    assert "F1-vol" in manifest["volumes"]


# ─── Pattern (L3) tests ─────────────────────────────────────

def t_list_patterns():
    patterns = list_patterns()
    assert "industrial-audit" in patterns
    assert "image-pipeline" in patterns
    assert "canon-feed" in patterns


def t_get_pattern():
    p = get_pattern("industrial-audit")
    assert p is not None
    assert p.name == "industrial-audit"
    assert "audit" in p.tags


def t_pattern_build():
    p = get_pattern("industrial-audit")
    wb = p.build()
    assert wb.name == "industrial-audit"
    assert "plc_sensor" in wb.cells
    assert "invoice_audit" in wb.cells


def t_pattern_validate():
    p = get_pattern("industrial-audit")
    wb = p.build()
    issues = p.validate(wb)
    assert issues == [], f"Pattern should validate: {issues}"


def t_pattern_to_docker():
    """A pattern's workbook should port to Docker."""
    p = get_pattern("image-pipeline")
    wb = p.build()
    porter = PorterAgent()
    manifest = porter.port_to_docker(wb)
    assert "A1" in manifest["services"]
    assert "A3" in manifest["services"]


# ─── Wave (sync waves) tests ────────────────────────────────

def t_assign_waves_linear():
    """A→B→C should be waves 0, 1, 2."""
    wb = Workbook(name="x")
    for cid in ["A", "B", "C"]:
        wb.add_cell(Cell(id=cid, io_type=IOType.DOCKER, inputs=[],
                          outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A", from_port="o", to_cell="B", to_port="i"))
    wb.add_flow(Flow(from_cell="B", from_port="o", to_cell="C", to_port="i"))
    waves = assign_waves(wb)
    assert waves["A"].wave == 0
    assert waves["B"].wave == 1
    assert waves["C"].wave == 2


def t_assign_waves_diamond():
    """A→B,C→D should be 0, 1, 1, 2."""
    wb = Workbook(name="x")
    for cid in ["A", "B", "C", "D"]:
        wb.add_cell(Cell(id=cid, io_type=IOType.DOCKER, inputs=[],
                          outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A", from_port="o", to_cell="B", to_port="i"))
    wb.add_flow(Flow(from_cell="A", from_port="o", to_cell="C", to_port="i"))
    wb.add_flow(Flow(from_cell="B", from_port="o", to_cell="D", to_port="i"))
    wb.add_flow(Flow(from_cell="C", from_port="o", to_cell="D", to_port="i"))
    waves = assign_waves(wb)
    assert waves["A"].wave == 0
    assert waves["B"].wave == 1
    assert waves["C"].wave == 1
    assert waves["D"].wave == 2


def t_order_by_wave():
    """order_by_wave returns cells in topological order."""
    wb = Workbook(name="x")
    for cid in ["A", "B", "C", "D"]:
        wb.add_cell(Cell(id=cid, io_type=IOType.DOCKER, inputs=[],
                          outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    wb.add_flow(Flow(from_cell="A", from_port="o", to_cell="B", to_port="i"))
    wb.add_flow(Flow(from_cell="A", from_port="o", to_cell="C", to_port="i"))
    wb.add_flow(Flow(from_cell="B", from_port="o", to_cell="D", to_port="i"))
    order = order_by_wave(wb)
    # A must come before B/C, D must come last
    assert order.index("A") < order.index("B")
    assert order.index("A") < order.index("C")


# ─── Mixin tests ─────────────────────────────────────────────

def t_mixin_canary():
    cell = Cell(id="x", io_type=IOType.DOCKER, inputs=[],
                 outputs=[Port(name="o", kind=PortKind.STRING)], formula="x")
    apply_mixin(cell, "canary")
    assert cell.metadata["canary"] == "0x24a555471370b18d"


def t_mixin_witness():
    cell = Cell(id="x", io_type=IOType.DOCKER, inputs=[],
                 outputs=[Port(name="o", kind=PortKind.STRING)], formula="x")
    apply_mixin(cell, "witness")
    assert cell.metadata["witness"] is True
    assert "witness_log_path" in cell.metadata


def t_apply_mixins_to_workbook():
    wb = Workbook(name="x")
    wb.add_cell(Cell(id="A", io_type=IOType.DOCKER, inputs=[],
                     outputs=[Port(name="o", kind=PortKind.STRING)], formula="x"))
    apply_mixins(wb, ["canary", "witness"])
    assert wb.cells["A"].metadata["canary"] == "0x24a555471370b18d"
    assert wb.cells["A"].metadata["witness"] is True


# ─── Run tests ──────────────────────────────────────────────

test("test_canary", t_canary)
test("test_version", t_version)
test("test_cell_minimal", t_cell_minimal)
test("test_cell_no_id_invalid", t_cell_no_id_invalid)
test("test_cell_no_io_invalid", t_cell_no_io_invalid)
test("test_cell_to_dict", t_cell_to_dict)
test("test_workbook_create", t_workbook_create)
test("test_workbook_add_cell", t_workbook_add_cell)
test("test_workbook_add_range", t_workbook_add_range)
test("test_workbook_validate", t_workbook_validate)
test("test_workbook_save_load", t_workbook_save_load)
test("test_designer_create_workbook", t_designer_create_workbook)
test("test_designer_suggestions", t_designer_suggestions)
test("test_designer_apply_suggestion", t_designer_apply_suggestion)
test("test_designer_connect", t_designer_connect)
test("test_designer_connect_invalid_port", t_designer_connect_invalid_port)
test("test_designer_describe", t_designer_describe)
test("test_porter_docker_basic", t_porter_docker_basic)
test("test_porter_docker_k8s_cell", t_porter_docker_k8s_cell)
test("test_porter_kubernetes_basic", t_porter_kubernetes_basic)
test("test_porter_go", t_porter_go)
test("test_porter_database", t_porter_database)
test("test_porter_file_volume", t_porter_file_volume)

# Pattern (L3) tests
test("test_list_patterns", t_list_patterns)
test("test_get_pattern", t_get_pattern)
test("test_pattern_build", t_pattern_build)
test("test_pattern_validate", t_pattern_validate)
test("test_pattern_to_docker", t_pattern_to_docker)

# Wave tests
test("test_assign_waves_linear", t_assign_waves_linear)
test("test_assign_waves_diamond", t_assign_waves_diamond)
test("test_order_by_wave", t_order_by_wave)

# Mixin tests
test("test_mixin_canary", t_mixin_canary)
test("test_mixin_witness", t_mixin_witness)
test("test_apply_mixins_to_workbook", t_apply_mixins_to_workbook)

print("\n=== ax-quilt v0.3.0 test results ===")
for name, status in results:
    print(f"  {status:60} {name}")

print(f"\n{len(results) - len(failures)}/{len(results)} passed")
if failures:
    sys.exit(1)
