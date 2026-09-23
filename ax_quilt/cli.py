"""CLI for ax-quilt."""
import argparse
import json
import sys
from pathlib import Path

from . import (
    Workbook, DesignerAgent, PorterAgent, Cell, Port, PortKind, IOType,
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

    sub.add_parser("version").set_defaults(func=cmd_version)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
