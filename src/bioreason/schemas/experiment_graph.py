"""
Typed schemas for ExperimentGraph: structured topological representation of biological experiments,
units of replication, data flows, transformations, batch assignments, and model partitions.
"""

from enum import Enum
from typing import List, Dict, Any, Optional, Set
import hashlib
import json
from pydantic import BaseModel, Field, ConfigDict


class NodeType(str, Enum):
    # Hierarchy Levels
    SITE = "site"
    CENTER = "center"
    COHORT = "cohort"
    DONOR = "donor"
    PATIENT = "patient"
    SUBJECT = "subject"
    SAMPLE = "sample"
    ALIQUOT = "aliquot"
    REGION = "region"
    SPOT = "spot"
    IMAGE_TILE = "image_tile"
    CELL = "cell"
    OBSERVATION = "observation"
    TIMEPOINT = "timepoint"
    EVENT = "event"
    # Technical & Assay Units
    BATCH = "batch"
    LANE = "lane"
    PLATE = "plate"
    RUN = "run"
    ASSAY = "assay"
    TREATMENT = "treatment"
    PHENOTYPE = "phenotype"
    COVARIATE = "covariate"
    # Computational & Workflow Units
    TRANSFORMATION = "transformation"
    FEATURE_SELECTION = "feature_selection"
    MODEL = "model"
    PARTITION = "partition"


class EdgeRelation(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    NESTED_WITHIN = "NESTED_WITHIN"
    PAIRED_WITH = "PAIRED_WITH"
    MEASURED_AT = "MEASURED_AT"
    PROCESSED_BY = "PROCESSED_BY"
    ASSIGNED_TO = "ASSIGNED_TO"
    TRANSFORMED_BY = "TRANSFORMED_BY"
    SPLIT_INTO = "SPLIT_INTO"
    TRAINED_ON = "TRAINED_ON"
    EVALUATED_ON = "EVALUATED_ON"
    CONFOUNDED_WITH = "CONFOUNDED_WITH"


class GraphNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str = Field(description="Unique node identifier within the graph (e.g., subj_01, cell_01, batch_A, model_rf)")
    node_type: NodeType = Field(description="Semantic type of experimental entity or operation")
    label: str = Field(description="Human-readable descriptive label")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary domain properties (e.g. organism, organ, timepoint)")


class GraphEdge(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source_id: str = Field(description="Identifier of source node")
    target_id: str = Field(description="Identifier of target node")
    relation: EdgeRelation = Field(description="Directional semantic relation (source -> relation -> target)")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Metadata or edge attributes")


class ExperimentGraph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str = Field(description="Unique experiment graph identifier")
    name: str = Field(description="Descriptive study title or workflow summary")
    nodes: List[GraphNode] = Field(default_factory=list, description="All entities and processing steps")
    edges: List[GraphEdge] = Field(default_factory=list, description="All directional relations")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Experiment-level metadata")

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        for n in self.nodes:
            if n.node_id == node_id:
                return n
        return None

    def get_outgoing_edges(self, source_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.source_id == source_id]

    def get_incoming_edges(self, target_id: str) -> List[GraphEdge]:
        return [e for e in self.edges if e.target_id == target_id]

    def find_nodes_by_type(self, node_type: NodeType) -> List[GraphNode]:
        return [n for n in self.nodes if n.node_type == node_type]

    def get_ancestor_nodes(self, node_id: str, visited: Optional[Set[str]] = None) -> Set[str]:
        """Recursively retrieves all ancestor node IDs via DERIVED_FROM or NESTED_WITHIN relations."""
        if visited is None:
            visited = set()
        ancestors = set()
        for edge in self.get_outgoing_edges(node_id):
            if edge.relation in [EdgeRelation.DERIVED_FROM, EdgeRelation.NESTED_WITHIN]:
                target = edge.target_id
                if target not in visited:
                    visited.add(target)
                    ancestors.add(target)
                    ancestors.update(self.get_ancestor_nodes(target, visited))
        return ancestors

    def compute_structural_fingerprint(self) -> str:
        """
        Computes an invariant topological signature based on node types, degree distributions,
        and directional edge relations for cross-study structural comparison and contamination detection.
        """
        type_counts = {}
        for n in self.nodes:
            type_counts[n.node_type.value] = type_counts.get(n.node_type.value, 0) + 1

        edge_relations = {}
        for e in self.edges:
            rel = e.relation.value
            edge_relations[rel] = edge_relations.get(rel, 0) + 1

        sig_data = {
            "node_types": sorted(type_counts.items()),
            "edge_relations": sorted(edge_relations.items()),
            "num_nodes": len(self.nodes),
            "num_edges": len(self.edges),
        }
        encoded = json.dumps(sig_data, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def check_partition_leakage(self) -> List[str]:
        """
        Detects topological leakage: checks if test/validation partition nodes share
        preprocessing transformations, feature selections, or augmentations with training nodes.
        """
        issues = []
        train_partitions = [n.node_id for n in self.nodes if n.node_type == NodeType.PARTITION and "train" in n.label.lower()]
        test_partitions = [n.node_id for n in self.nodes if n.node_type == NodeType.PARTITION and ("test" in n.label.lower() or "val" in n.label.lower())]

        transform_nodes = [n.node_id for n in self.nodes if n.node_type in [NodeType.TRANSFORMATION, NodeType.FEATURE_SELECTION]]

        for t_node in transform_nodes:
            # Check if t_node receives incoming edges from both train and test partitions / samples
            incoming = self.get_incoming_edges(t_node)
            incoming_sources = {e.source_id for e in incoming}

            has_test = any(ts in incoming_sources for ts in test_partitions)
            has_train = any(tr in incoming_sources for tr in train_partitions)

            if has_test and has_train:
                issues.append(f"LEAKAGE_DETECTED: Node '{t_node}' processes data from both train and test partitions globally before splitting.")

        return issues

    def check_pseudoreplication_topology(self) -> List[str]:
        """
        Detects topological pseudoreplication: checks whether multiple observation nodes derived
        from the same subject node are split across train/test partitions or treated as independent subjects.
        """
        issues = []
        biological_unit_types = [NodeType.SUBJECT, NodeType.PATIENT, NodeType.DONOR, NodeType.COHORT]
        subject_nodes = [n for n in self.nodes if n.node_type in biological_unit_types]

        for subj in subject_nodes:
            # Find all observations derived from or nested within this subject
            derived_obs = set()
            for edge in self.edges:
                if edge.target_id == subj.node_id and edge.relation in [EdgeRelation.DERIVED_FROM, EdgeRelation.NESTED_WITHIN]:
                    derived_obs.add(edge.source_id)

            # Check if derived observations are assigned to multiple distinct partitions
            partitions_assigned = set()
            for obs in derived_obs:
                for edge in self.get_outgoing_edges(obs):
                    if edge.relation in [EdgeRelation.ASSIGNED_TO, EdgeRelation.SPLIT_INTO]:
                        target_node = self.get_node(edge.target_id)
                        if target_node and target_node.node_type == NodeType.PARTITION:
                            partitions_assigned.add(target_node.label)

            if len(partitions_assigned) > 1:
                issues.append(
                    f"PSEUDOREPLICATION_LEAKAGE: Observations from single biological entity '{subj.node_id}' "
                    f"are split across multiple partitions: {sorted(partitions_assigned)}."
                )

        return issues

    def check_ancestry_partition_leakage(self) -> List[str]:
        """
        Multi-hop ancestry leakage detection: detects if any two observations in distinct partitions
        share a common higher-order biological ancestor (e.g. same patient, same tumor, same donor).
        """
        issues = []
        partition_observations: Dict[str, Set[str]] = {}

        for edge in self.edges:
            if edge.relation in [EdgeRelation.ASSIGNED_TO, EdgeRelation.SPLIT_INTO]:
                target_node = self.get_node(edge.target_id)
                if target_node and target_node.node_type == NodeType.PARTITION:
                    part_name = target_node.label
                    if part_name not in partition_observations:
                        partition_observations[part_name] = set()
                    partition_observations[part_name].add(edge.source_id)

        part_names = list(partition_observations.keys())
        for i in range(len(part_names)):
            for j in range(i + 1, len(part_names)):
                p1, p2 = part_names[i], part_names[j]
                # If one is train and one is test/val
                if ("train" in p1.lower() and ("test" in p2.lower() or "val" in p2.lower())) or \
                   ("train" in p2.lower() and ("test" in p1.lower() or "val" in p1.lower())):
                    obs1 = partition_observations[p1]
                    obs2 = partition_observations[p2]

                    for o1 in obs1:
                        anc1 = self.get_ancestor_nodes(o1)
                        for o2 in obs2:
                            anc2 = self.get_ancestor_nodes(o2)
                            common_ancestors = anc1.intersection(anc2)
                            if common_ancestors:
                                issues.append(
                                    f"ANCESTRY_LEAKAGE: Node '{o1}' in partition '{p1}' and node '{o2}' in partition '{p2}' "
                                    f"share biological ancestor entities: {sorted(common_ancestors)}."
                                )
        return issues
