"""Porter Agent — converts workbooks to backend manifests.

The Porter Agent:
- Takes a Workbook (cellular spreadsheet)
- Emits Docker compose, K8s manifests, or Go code
- Optimizes for the target backend
- Bridges Quilt's cellular abstraction with real infrastructure

This is the MESH layer — it knows about Docker, K8s, Go, files, etc.
"""
from typing import Dict, List

from ..cells.cell import (
    Cell, Range, Workbook, Flow, Port, PortKind, IOType,
)


class PorterAgent:
    """The Porter Agent — converts workbooks to backend manifests."""

    def __init__(self, name: str = "porter"):
        self.name = name

    def port_to_docker(self, workbook: Workbook) -> Dict:
        """Emit a Docker Compose manifest for the workbook."""
        services = {}
        networks = {"axnet": {"driver": "bridge"}}
        volumes = {}

        for cid, cell in workbook.cells.items():
            if cell.io_type == IOType.DOCKER:
                services[cid] = self._cell_to_docker_service(cell)
            elif cell.io_type == IOType.KUBERNETES:
                services[cid] = self._cell_to_k8s_service(cell)
            elif cell.io_type == IOType.GO_BINARY:
                services[cid] = self._cell_to_go_service(cell)
            elif cell.io_type == IOType.DATABASE:
                services[cid] = self._cell_to_db_service(cell)
            elif cell.io_type == IOType.NETWORK:
                services[cid] = self._cell_to_network_service(cell)
            elif cell.io_type == IOType.FILE:
                # Files are volumes
                path = cell.backing.get("path", f"/data/{cid}")
                volumes[f"{cid}-vol"] = {"driver": "local"}
                # And mount to dependent cells
                self._mount_volume_to_services(workbook, cid, path, services)

        # Wire up the network connections via flow
        for flow in workbook.flows:
            self._wire_docker_flow(services, flow)

        return {
            "version": "3.8",
            "services": services,
            "networks": networks,
            "volumes": volumes,
        }

    def port_to_kubernetes(self, workbook: Workbook) -> Dict:
        """Emit Kubernetes manifests for the workbook."""
        manifests = []
        for cid, cell in workbook.cells.items():
            manifest = self._cell_to_k8s_manifest(cell)
            if manifest:
                manifests.append(manifest)

        # Wire via Services
        services = []
        for flow in workbook.flows:
            services.append(self._flow_to_k8s_service(workbook, flow))

        return {
            "deployments": manifests,
            "services": services,
        }

    def port_to_go(self, workbook: Workbook) -> Dict:
        """Emit Go source code that wires the workbook."""
        files = {}

        for cid, cell in workbook.cells.items():
            if cell.io_type == IOType.GO_BINARY:
                files[f"{cid}.go"] = self._cell_to_go_source(cell)

        # Generate main.go that wires all cells together
        files["main.go"] = self._generate_go_main(workbook)
        files["go.mod"] = self._generate_go_mod(workbook)

        return files

    # ─── Docker helpers ─────────────────────────────────────

    def _cell_to_docker_service(self, cell: Cell) -> Dict:
        image = cell.backing.get("image", f"ax-quilt/{cell.id}:latest")
        env = cell.backing.get("env", {})
        ports = cell.backing.get("ports", [])
        return {
            "image": image,
            "environment": env,
            "ports": ports,
            "networks": ["axnet"],
            "labels": {
                "ax-quilt.cell.id": cell.id,
                "ax-quilt.cell.formula": cell.formula,
                "ax-quilt.io-type": cell.io_type.value,
            },
        }

    def _cell_to_k8s_service(self, cell: Cell) -> Dict:
        return {
            "image": cell.backing.get("image", f"ax-quilt/{cell.id}:latest"),
            "deploy": True,
        }

    def _cell_to_go_service(self, cell: Cell) -> Dict:
        return {
            "build": {
                "context": cell.backing.get("build_context", "."),
                "dockerfile": cell.backing.get("dockerfile", "Dockerfile"),
            },
            "networks": ["axnet"],
        }

    def _cell_to_db_service(self, cell: Cell) -> Dict:
        engine = cell.backing.get("engine", "postgres")
        image_map = {
            "postgres": "postgres:15",
            "mysql": "mysql:8",
            "mongo": "mongo:7",
            "redis": "redis:7",
        }
        return {
            "image": image_map.get(engine, "postgres:15"),
            "environment": cell.backing.get("env", {}),
            "volumes": [f"{cell.id}-data:/var/lib/postgresql/data"],
            "networks": ["axnet"],
        }

    def _cell_to_network_service(self, cell: Cell) -> Dict:
        return {
            "image": "alpine:latest",
            "command": ["sleep", "infinity"],
            "networks": ["axnet"],
            "labels": {"ax-quilt.role": "network-endpoint"},
        }

    def _mount_volume_to_services(self, workbook: Workbook, file_cell_id: str,
                                   path: str, services: Dict) -> None:
        """Find cells that consume this file's output and mount it."""
        for flow in workbook.flows:
            if flow.from_cell == file_cell_id:
                target_svc = services.get(flow.to_cell)
                if target_svc:
                    target_svc.setdefault("volumes", []).append(
                        f"{file_cell_id}-vol:{path}"
                    )

    def _wire_docker_flow(self, services: Dict, flow: Flow) -> None:
        """Wire a flow into Docker dependencies/links."""
        src = services.get(flow.from_cell)
        dst = services.get(flow.to_cell)
        if dst is None:
            return
        if src:
            dst.setdefault("depends_on", []).append(flow.from_cell)
        # Add link for port-based connection
        if src and "ports" in src:
            dst.setdefault("environment", {})[
                f"AX_QUILT_{flow.from_cell.upper()}_PORT"
            ] = "8000"

    # ─── K8s helpers ────────────────────────────────────────

    def _cell_to_k8s_manifest(self, cell: Cell) -> Dict:
        if cell.io_type in (IOType.DOCKER, IOType.GO_BINARY):
            return {
                "apiVersion": "apps/v1",
                "kind": "Deployment",
                "metadata": {"name": cell.id, "labels": {
                    "ax-quilt/cell": cell.id,
                    "ax-quilt/formula": cell.formula[:63],
                }},
                "spec": {
                    "replicas": cell.backing.get("replicas", 1),
                    "selector": {"matchLabels": {"ax-quilt/cell": cell.id}},
                    "template": {
                        "metadata": {"labels": {"ax-quilt/cell": cell.id}},
                        "spec": {
                            "containers": [{
                                "name": cell.id,
                                "image": cell.backing.get(
                                    "image", f"ax-quilt/{cell.id}:latest"
                                ),
                                "ports": [{"containerPort": p}
                                           for p in cell.backing.get("ports", [8000])],
                            }]
                        }
                    }
                }
            }
        return {}

    def _flow_to_k8s_service(self, workbook: Workbook, flow: Flow) -> Dict:
        return {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{flow.from_cell}-{flow.to_cell}"},
            "spec": {
                "selector": {"ax-quilt/cell": flow.from_cell},
                "ports": [{"port": 8000, "targetPort": 8000}],
            },
        }

    # ─── Go helpers ─────────────────────────────────────────

    def _cell_to_go_source(self, cell: Cell) -> str:
        """Generate Go source for a Go-binary cell."""
        return f"""// Package {cell.id} implements the cell: {cell.formula}
// Generated by ax-quilt Porter Agent
package {cell.id}

import (
\t"encoding/json"
\t"fmt"
\t"io"
\t"net/http"
)

type Input struct {{
{self._port_struct(cell.inputs)}
}}

type Output struct {{
{self._port_struct(cell.outputs)}
}}

// Run executes the cell's logic.
func Run(input Input) (Output, error) {{
\t// Cell formula: {cell.formula}
\toutput := Output{{}}
\t// TODO: implement cell logic here
\treturn output, nil
}}

// ServeHTTP exposes the cell as an HTTP endpoint.
func ServeHTTP(w http.ResponseWriter, r *http.Request) {{
\tbody, err := io.ReadAll(r.Body)
\tif err != nil {{
\t\thttp.Error(w, err.Error(), http.StatusBadRequest)
\t\treturn
\t}}
\tvar input Input
\tif err := json.Unmarshal(body, &input); err != nil {{
\t\thttp.Error(w, err.Error(), http.StatusBadRequest)
\t\treturn
\t}}
\toutput, err := Run(input)
\tif err != nil {{
\t\thttp.Error(w, err.Error(), http.StatusInternalServerError)
\t\treturn
\t}}
\tw.Header().Set("Content-Type", "application/json")
\tjson.NewEncoder(w).Encode(output)
}}

func main() {{
\thttp.HandleFunc("/", ServeHTTP)
\tfmt.Println("{cell.id} listening on :8000")
\thttp.ListenAndServe(":8000", nil)
}}
"""

    def _port_struct(self, ports: List) -> str:
        lines = []
        for p in ports:
            go_type = self._port_kind_to_go(p.kind)
            lines.append(f"\t{p.name.capitalize()} {go_type} `json:\"{p.name}\"`")
        return "\n".join(lines) if lines else "// (no ports)"

    def _port_kind_to_go(self, kind: PortKind) -> str:
        return {
            PortKind.STRING: "string",
            PortKind.INT: "int64",
            PortKind.FLOAT: "float64",
            PortKind.BOOL: "bool",
            PortKind.JSON: "json.RawMessage",
            PortKind.BYTES: "[]byte",
            PortKind.IMAGE: "[]byte",
            PortKind.AUDIO: "[]byte",
            PortKind.TENSOR: "[]float64",
            PortKind.STREAM: "io.Reader",
            PortKind.ANY: "interface{}",
        }.get(kind, "interface{}")

    def _generate_go_main(self, workbook: Workbook) -> str:
        """Generate main.go that wires all cells together."""
        cells_str = ", ".join(workbook.cells.keys())
        flows_str = "\n".join(
            f"\t// {f.from_cell}.{f.from_port} → {f.to_cell}.{f.to_port}"
            for f in workbook.flows
        )
        return f"""// main.go — ax-quilt workbook: {workbook.name}
// Purpose: {workbook.flow_description}
// Generated by ax-quilt Porter Agent
package main

import (
\t"fmt"
)

func main() {{
\tfmt.Println("ax-quilt workbook: {workbook.name}")
\tfmt.Println("Purpose: {workbook.flow_description}")
\tfmt.Println("Cells: {cells_str}")
\tfmt.Println("Flows:")
{flows_str}
\t// Wire cells via their HTTP endpoints
\t// Each cell listens on :8000
\t// Connections:
{self._flow_wiring(workbook)}
}}
"""

    def _flow_wiring(self, workbook: Workbook) -> str:
        lines = []
        for f in workbook.flows:
            lines.append(
                f'\tgo proxy("{f.from_cell}", ":8000", '
                f'"{f.to_cell}", ":8000", "/{f.from_port}", "/{f.to_port}")'
            )
        return "\n".join(lines) if lines else "\t// (no flows)"

    def _generate_go_mod(self, workbook: Workbook) -> str:
        return f"""module ax-quilt/{workbook.name}

go 1.21
"""
