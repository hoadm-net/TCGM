"""Abstract base class for all dataset adapters."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd

from tcgm.schema import Node, Edge, ProvenanceRecord, Query


class BaseAdapter(ABC):
    """Convert a raw dataset into the four canonical TCGM Parquet tables.

    Subclasses must implement :meth:`build` which populates four lists:
      self.nodes, self.edges, self.provenance, self.queries
    """

    DATASET_TAG: str = ""   # override in subclass, e.g. "lmev2"

    def __init__(self, data_root: Path, output_dir: Path) -> None:
        self.data_root = Path(data_root)
        self.output_dir = Path(output_dir)
        self.nodes: List[Node] = []
        self.edges: List[Edge] = []
        self.provenance: List[ProvenanceRecord] = []
        self.queries: List[Query] = []

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------

    @abstractmethod
    def build(self) -> None:
        """Populate self.nodes / edges / provenance / queries in place."""

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> Dict[str, Path]:
        """Write four Parquet files; return mapping name -> path."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        paths: Dict[str, Path] = {}

        tables = {
            "nodes":      [n.to_dict() for n in self.nodes],
            "edges":      [e.to_dict() for e in self.edges],
            "provenance": [p.to_dict() for p in self.provenance],
            "queries":    [q.to_dict() for q in self.queries],
        }
        for name, records in tables.items():
            df = pd.DataFrame(records)
            out = self.output_dir / f"{name}.parquet"
            df.to_parquet(out, index=False)
            paths[name] = out

        return paths

    # ------------------------------------------------------------------
    # Validation  (subclasses may override / extend)
    # ------------------------------------------------------------------

    def validate(self) -> Dict:
        """Run basic structural checks; return a validation report dict."""
        report: Dict = {"dataset": self.DATASET_TAG, "errors": [], "warnings": [], "stats": {}}

        node_ids = {n.node_id for n in self.nodes}
        report["stats"]["node_count"] = len(node_ids)
        report["stats"]["edge_count"] = len(self.edges)
        report["stats"]["provenance_count"] = len(self.provenance)
        report["stats"]["query_count"] = len(self.queries)

        # Check duplicate node IDs
        all_ids = [n.node_id for n in self.nodes]
        if len(all_ids) != len(node_ids):
            report["errors"].append("Duplicate node_ids detected")

        # Check all edge endpoints exist
        missing_endpoints: List[str] = []
        for e in self.edges:
            if e.src_id not in node_ids:
                missing_endpoints.append(f"edge src missing: {e.src_id}")
            if e.dst_id not in node_ids:
                missing_endpoints.append(f"edge dst missing: {e.dst_id}")
        if missing_endpoints:
            report["errors"].extend(missing_endpoints[:20])  # cap at 20

        # Check provenance target_ids point to known nodes or queries
        # Query provenance records are valid even though query_ids are not in node_ids.
        query_ids = {q.query_id for q in self.queries}
        prov_targets = {p.target_id for p in self.provenance}
        orphan_prov = prov_targets - node_ids - query_ids
        if orphan_prov:
            report["warnings"].append(
                f"{len(orphan_prov)} provenance records point to unknown nodes/queries"
            )

        report["ok"] = len(report["errors"]) == 0
        return report

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    def run(self) -> Tuple[Dict[str, Path], Dict]:
        """build + save + validate; return (paths, validation_report)."""
        self.build()
        paths = self.save()
        report = self.validate()

        val_path = self.output_dir / "validation.json"
        with open(val_path, "w") as fh:
            json.dump(report, fh, indent=2)

        return paths, report
