"""CLI for ax-quilt."""
import argparse
import json
import sys
from pathlib import Path

from . import (
    Workbook, DesignerAgent, PorterAgent, ProjectionAgent, ProjectionTarget,
    TEMPLATES, THREE_AGENT_DOCTRINE,
    zoom_in, zoom_out,
    Cell, Port, PortKind, IOType,
    Range, RangeLayout, Flow, __version__, canary,
)


def cmd_describe(args):
    """Describe a workbook in NL (what the Designer Agent sees)."""
    wb = Workbook.load(args.workbook)
    designer = DesignerAgent()
    print(designer.describe(wb))


def cmd_docker(args):
    """Port a workbook to Docker Compose."""
    wb = Workbook.load(args.workbook)
    porter = PorterAgent()
    manifest = porter.port_to_docker(wb)
    if args.output:
        Path(args.output).write_text(json.dumps(manifest, indent=2))
        print(f"Docker manifest saved to {args.output}")
    else:
        print(json.dumps(manifest, indent=2))


def cmd_k8s(args):
    """Port a workbook to Kubernetes manifests."""
    wb = Workbook.load(args.workbook)
    porter = PorterAgent()
    manifest = porter.port_to_kubernetes(wb)
    if args.output:
        Path(args.output).write_text(json.dumps(manifest, indent=2))
        print(f"K8s manifest saved to {args.output}")
    else:
        print(json.dumps(manifest, indent=2))


def cmd_go(args):
    """Port a workbook to Go source code."""
    wb = Workbook.load(args.workbook)
    porter = PorterAgent()
    files = porter.port_to_go(wb)
    out_dir = Path(args.output or ".")
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (out_dir / name).write_text(content)
        print(f"  Wrote {name}")


def cmd_validate(args):
    """Validate a workbook."""
    wb = Workbook.load(args.workbook)
    issues = wb.validate()
    if not issues:
        print(f"✓ Workbook {wb.name} is valid")
        print(f"  {len(wb.cells)} cells, {len(wb.ranges)} ranges, {len(wb.flows)} flows")
    else:
        print(f"✗ Workbook {wb.name} has {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")


def cmd_version(args):
    """Show version."""
    print(f"ax-quilt v{__version__}")
    print(f"Canary: {canary()}")
    print(f"\nThree agents: Designer, Porter, Projection")
    print(f"Projection templates: {', '.join(TEMPLATES.keys())}")


def cmd_project(args):
    """Project a workbook to a last-mile target (UI/HW/engine)."""
    wb = Workbook.load(args.workbook)
    agent = ProjectionAgent(template=args.template)
    # Map target string to enum
    try:
        target = ProjectionTarget(args.target)
    except ValueError:
        print(f"Unknown target: {args.target}")
        print(f"Available: {[t.value for t in ProjectionTarget]}")
        sys.exit(1)
    out = agent.project(wb, target)
    if args.output:
        # If output is a directory and we have multiple files (Go / Bevy), write all
        out_path = Path(args.output)
        if out_path.suffix:
            # Single file
            if "arduino_ino" in out:
                out_path.write_text(out["arduino_ino"])
            elif "nmea_bridge" in out:
                out_path.write_text(out["nmea_bridge"])
            elif "htmx_html" in out:
                out_path.write_text(out["htmx_html"])
            elif "tui" in out:
                out_path.write_text(out["tui"])
            elif "gpio_py" in out:
                out_path.write_text(out["gpio_py"])
            elif "bevy_rust" in out:
                out_path.write_text(out["bevy_rust"])
            elif "engine_source" in out:
                out_path.write_text(out["engine_source"])
            elif "frontend_source" in out:
                out_path.write_text(out["frontend_source"])
            elif "a2ui" in out:
                out_path.write_text(json.dumps(out["a2ui"], indent=2))
            elif "mqtt_config" in out:
                out_path.write_text(json.dumps(out["mqtt_config"], indent=2))
            elif "webhook_routes" in out:
                out_path.write_text(json.dumps(out["webhook_routes"], indent=2))
            else:
                out_path.write_text(json.dumps(out, indent=2))
            print(f"Projection saved to {args.output}")
        else:
            out_path.mkdir(parents=True, exist_ok=True)
            for k, v in out.items():
                (out_path / k).write_text(v)
                print(f"  Wrote {k}")
    else:
        # Print first key's value or full dict
        if len(out) == 1:
            k, v = next(iter(out.items()))
            print(v)
        else:
            print(json.dumps(out, indent=2))


def cmd_zoom(args):
    """Zoom into a workbook (surface), cell (intra), or flow (inter)."""
    wb = Workbook.load(args.workbook)
    if not args.target:
        print(json.dumps(zoom_out(wb), indent=2))
    else:
        print(json.dumps(zoom_in(wb, args.target), indent=2))


def cmd_design(args):
    """Design a workbook from NL intent (Designer Agent mode)."""
    designer = DesignerAgent()
    wb = designer.create_workbook(name=args.name, flow_description=args.intent)
    suggestions = designer.suggest_cells(args.intent)
    print(f"Designer Agent analyzing intent: '{args.intent}'")
    print(f"Suggested {len(suggestions)} cells:")
    for s in suggestions:
        print(f"  - {s['id']}: {s['io_type']} — {s['formula']}")
        cell = designer.apply_suggestion(wb, s)
    print(f"\nWorkbook: {wb.name}")
    print(designer.describe(wb))

    if args.output:
        wb.save(args.output)
        print(f"\nSaved to {args.output}")


def main():
    p = argparse.ArgumentParser(description="ax-quilt — cellular spreadsheet orchestrator")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_d = sub.add_parser("design", help="Design a workbook from NL intent")
    p_d.add_argument("intent", help="NL description of what the workbook should do")
    p_d.add_argument("--name", default="workbook", help="Workbook name")
    p_d.add_argument("--output", help="Save to file")
    p_d.set_defaults(func=cmd_design)

    p_dsc = sub.add_parser("describe", help="Describe a workbook in NL")
    p_dsc.add_argument("workbook", help="Path to workbook JSON")
    p_dsc.set_defaults(func=cmd_describe)

    p_v = sub.add_parser("validate", help="Validate a workbook")
    p_v.add_argument("workbook")
    p_v.set_defaults(func=cmd_validate)

    p_dk = sub.add_parser("docker", help="Port to Docker Compose")
    p_dk.add_argument("workbook")
    p_dk.add_argument("--output", "-o", help="Output file")
    p_dk.set_defaults(func=cmd_docker)

    p_k8s = sub.add_parser("k8s", help="Port to Kubernetes")
    p_k8s.add_argument("workbook")
    p_k8s.add_argument("--output", "-o", help="Output file")
    p_k8s.set_defaults(func=cmd_k8s)

    p_go = sub.add_parser("go", help="Port to Go source")
    p_go.add_argument("workbook")
    p_go.add_argument("--output", "-o", default=".", help="Output directory")
    p_go.set_defaults(func=cmd_go)

    p_proj = sub.add_parser("project", help="Project a workbook to last-mile target (UI/HW/engine)")
    p_proj.add_argument("workbook")
    p_proj.add_argument("target", help="Target: esp32_arduino, comport_nmea, htmx_fragment, "
                                       "react_component, bevy_rust, terminal_dashboard, gpio_python, "
                                       "comport_nmea, mqtt_publisher, webhook_http, ...")
    p_proj.add_argument("--template", "-t", help="A2UI template name (e.g. autopilot_dashboard)")
    p_proj.add_argument("--output", "-o", help="Output file")
    p_proj.set_defaults(func=cmd_project)

    p_zoom = sub.add_parser("zoom", help="Zoom into a cell (intra) or flow (inter) of a workbook")
    p_zoom.add_argument("workbook")
    p_zoom.add_argument("target", help="Cell id, or 'src→tgt' for a flow, or empty for surface view")
    p_zoom.set_defaults(func=cmd_zoom)

    sub.add_parser("version").set_defaults(func=cmd_version)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
