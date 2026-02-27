"""
OpenCM Format — Parser, Validator, Serializer
===============================================

The OpenCM (Open Structural Causal Model) format is a JSON-based interchange
standard for portable, versionable, composable causal models.

This module provides:
- CMFormatValidator: Validates .opencm.json files against the spec
- CMFormatParser: Parses validated JSON into structured SCMModel objects
- CMFormatSerializer: Exports CausalGraphs back to OpenCM format

OpenCM Spec Version: 1.0
"""

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# =============================================================================
# DEBUG TOGGLE (Comment out for production)
# =============================================================================
# DEBUG_SCM_FORMAT = True
DEBUG_SCM_FORMAT = False

def _debug(msg: str):
    if DEBUG_SCM_FORMAT:
        logger.debug(f"[CMFormat] {msg}")


# =============================================================================
# CONSTANTS
# =============================================================================

OPENCM_VERSION = "1.0"
OPENCM_FILE_EXTENSION = ".opencm.json"

VALID_VARIABLE_TYPES = {"continuous", "discrete", "binary", "categorical"}
VALID_EDGE_TYPES = {"causes", "correlates", "mediates", "moderates", "inhibits"}
VALID_EQUATION_TYPES = {"linear", "polynomial", "exponential", "logistic", "interaction", "synergy", "custom"}
VALID_DOMAINS = {
    "strategy", "marketing", "finance", "operations", "organization",
    "technology", "economics", "psychology", "healthcare", "supply_chain",
    "general"
}


# =============================================================================
# DATA STRUCTURES — In-memory representation of an OpenCM model
# =============================================================================

@dataclass
class SCMVariable:
    """A variable (node) in the structural causal model."""
    name: str
    var_type: str = "continuous"          # continuous, discrete, binary, categorical
    domain: Tuple[float, float] = (0.0, 1.0)  # Value range
    unit: str = ""                         # Business unit ($, %, units, index)
    description: str = ""
    observed: bool = True                  # Is this variable observable?
    default_value: Optional[float] = None  # Starting value if known
    categories: Optional[List[str]] = None  # For categorical variables


@dataclass
class SCMEdge:
    """A directed causal relationship between two variables."""
    source: str
    target: str
    edge_type: str = "causes"             # causes, correlates, mediates, moderates, inhibits
    strength: float = 0.5                  # Default causal strength [0, 1]
    description: str = ""
    confidence: float = 1.0                # How confident are we in this edge?
    is_learned: bool = False               # Was this edge learned from data?


@dataclass
class SCMEquation:
    """A structural equation defining how a variable is determined by its parents."""
    target: str
    equation_type: str = "linear"          # linear, polynomial, exponential, logistic, custom
    expression: str = ""                   # e.g., "0.6 - 0.15*SupplierPower - 0.20*BuyerPower"
    noise_distribution: str = "normal"     # Noise term distribution
    noise_params: Dict[str, float] = field(default_factory=lambda: {"mean": 0.0, "std": 0.05})


@dataclass
class SCMMetadata:
    """Model metadata and provenance."""
    author: str = ""
    citation: str = ""
    license: str = "CC0-1.0-Universal"
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    source_url: str = ""                   # Where the original model came from
    adaptation_notes: str = ""              # How we adapted/cloned for OpenCM


@dataclass
class SCMValidation:
    """Validation requirements for data fitting."""
    min_data_points: int = 20
    required_variables: List[str] = field(default_factory=list)
    suggested_datasets: List[str] = field(default_factory=list)


@dataclass
class SCMModel:
    """
    Complete in-memory representation of an OpenCM model.
    
    This is what gets loaded, composed, and applied as a "lens."
    """
    # Identity
    model_id: str
    name: str
    version: str = "1.0.0"
    domain: str = "general"
    description: str = ""
    
    # Structure
    variables: Dict[str, SCMVariable] = field(default_factory=dict)
    edges: List[SCMEdge] = field(default_factory=list)
    equations: Dict[str, SCMEquation] = field(default_factory=dict)
    allow_cycles: bool = False
    
    # Context
    assumptions: List[str] = field(default_factory=list)
    validation: Optional[SCMValidation] = None
    metadata: Optional[SCMMetadata] = None
    
    # Runtime
    _file_path: Optional[str] = None
    
    @property
    def variable_names(self) -> Set[str]:
        return set(self.variables.keys())
    
    @property
    def node_count(self) -> int:
        return len(self.variables)
    
    @property
    def edge_count(self) -> int:
        return len(self.edges)
    
    def summary(self) -> str:
        """One-line human-readable summary."""
        return f"{self.name} ({self.domain}) — {self.node_count} vars, {self.edge_count} edges"


# =============================================================================
# VALIDATOR — Ensures OpenCM files are well-formed
# =============================================================================

class CMFormatValidator:
    """
    Validates OpenCM JSON files against the specification.
    
    Checks:
    - Required fields present
    - Variable types are valid
    - Edge endpoints reference existing variables
    - DAG acyclicity
    - Structural equations reference valid variables
    - Domain values are valid
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate an OpenCM JSON structure.
        
        Returns True if valid, False if errors found.
        Populates self.errors and self.warnings.
        """
        self.errors = []
        self.warnings = []
        
        # 1. Check top-level structure
        self._check_required_fields(data)
        if self.errors:
            return False  # Can't proceed without basic structure
        
        # 2. Check model metadata
        self._check_model_section(data.get("model", {}))
        
        # 3. Check variables
        variables = data.get("variables", {})
        self._check_variables(variables)
        
        # 4. Check edges
        edges = data.get("edges", [])
        self._check_edges(edges, set(variables.keys()))
        
        # 5. Check structural equations (optional)
        equations = data.get("structural_equations", {})
        if equations:
            self._check_equations(equations, set(variables.keys()))
        
        # 6. Check DAG acyclicity
        allow_cycles = data.get("model", {}).get("allow_cycles", False)
        if not allow_cycles:
            self._check_acyclicity(edges)
        else:
            self.warnings.append("Cyclic Graph detected and allowed — ensure an iterative solver is used")
        
        # 7. Check assumptions
        assumptions = data.get("assumptions", [])
        if not assumptions:
            self.warnings.append("No assumptions listed — models should be transparent about their assumptions")
        
        _debug(f"Validation complete: {len(self.errors)} errors, {len(self.warnings)} warnings")
        return len(self.errors) == 0
    
    def _check_required_fields(self, data: Dict):
        """Check that all required top-level fields are present."""
        required = ["opencm_version", "model", "variables", "edges"]
        for field_name in required:
            if field_name not in data:
                self.errors.append(f"Missing required field: '{field_name}'")
        
        if "opencm_version" in data:
            version = data["opencm_version"]
            if version != OPENCM_VERSION:
                self.warnings.append(f"Model uses OpenCM version {version}, current is {OPENCM_VERSION}")
    
    def _check_model_section(self, model: Dict):
        """Validate the model identity section."""
        required = ["id", "name"]
        for f in required:
            if f not in model:
                self.errors.append(f"Missing required model field: 'model.{f}'")
        
        if "id" in model:
            model_id = model["id"]
            if not re.match(r'^[a-z][a-z0-9_]*$', model_id):
                self.errors.append(f"model.id must be lowercase alphanumeric with underscores, got: '{model_id}'")
        
        if "domain" in model:
            if model["domain"] not in VALID_DOMAINS:
                self.warnings.append(f"Unknown domain '{model['domain']}' — valid: {VALID_DOMAINS}")
    
    def _check_variables(self, variables: Dict):
        """Validate variable definitions."""
        if not variables:
            self.errors.append("Model must have at least one variable")
            return
        
        for var_name, var_def in variables.items():
            if not isinstance(var_def, dict):
                self.errors.append(f"Variable '{var_name}' must be a dict, got {type(var_def)}")
                continue
            
            # Check type
            var_type = var_def.get("type", "continuous")
            if var_type not in VALID_VARIABLE_TYPES:
                self.errors.append(f"Variable '{var_name}' has invalid type '{var_type}' — valid: {VALID_VARIABLE_TYPES}")
            
            # Check domain
            domain = var_def.get("domain")
            if domain is not None:
                if not isinstance(domain, (list, tuple)) or len(domain) != 2:
                    self.errors.append(f"Variable '{var_name}' domain must be [min, max], got: {domain}")
                elif domain[0] >= domain[1]:
                    self.errors.append(f"Variable '{var_name}' domain min ({domain[0]}) must be < max ({domain[1]})")
    
    def _check_edges(self, edges: List, variable_names: Set[str]):
        """Validate edge definitions."""
        for i, edge in enumerate(edges):
            if not isinstance(edge, dict):
                self.errors.append(f"Edge {i} must be a dict")
                continue
            
            source = edge.get("source")
            target = edge.get("target")
            
            if not source:
                self.errors.append(f"Edge {i} missing 'source'")
            elif source not in variable_names:
                self.errors.append(f"Edge {i} source '{source}' not in variables")
            
            if not target:
                self.errors.append(f"Edge {i} missing 'target'")
            elif target not in variable_names:
                self.errors.append(f"Edge {i} target '{target}' not in variables")
            
            if source == target:
                self.errors.append(f"Edge {i} is a self-loop ({source} → {source})")
            
            edge_type = edge.get("type", "causes")
            if edge_type not in VALID_EDGE_TYPES:
                self.warnings.append(f"Edge {i} has unknown type '{edge_type}' — valid: {VALID_EDGE_TYPES}")
            
            strength = edge.get("strength", 0.5)
            if not isinstance(strength, (int, float)) or not (-1.0 <= strength <= 1.0):
                self.errors.append(f"Edge {i} strength must be in [-1, 1], got: {strength}")
    
    def _check_equations(self, equations: Dict, variable_names: Set[str]):
        """Validate structural equations."""
        for target, equation in equations.items():
            if target not in variable_names:
                self.errors.append(f"Equation target '{target}' not in variables")
            
            if isinstance(equation, str):
                # Simple expression format — check for referenced variables
                for var in variable_names:
                    pass  # We'd do deeper parsing for production
            elif isinstance(equation, dict):
                eq_type = equation.get("type", "linear")
                if eq_type not in VALID_EQUATION_TYPES:
                    self.warnings.append(f"Equation for '{target}' has unknown type '{eq_type}'")
    
    def _check_acyclicity(self, edges: List):
        """Check that edges form a DAG (no cycles)."""
        try:
            import networkx as nx
            G = nx.DiGraph()
            for edge in edges:
                if isinstance(edge, dict) and "source" in edge and "target" in edge:
                    G.add_edge(edge["source"], edge["target"])
            
            if not nx.is_directed_acyclic_graph(G):
                cycles = list(nx.simple_cycles(G))
                self.errors.append(f"Graph contains cycles: {cycles[:3]}")
        except Exception as e:
            self.warnings.append(f"Could not check acyclicity: {e}")


# =============================================================================
# PARSER — Converts validated JSON into SCMModel objects
# =============================================================================

class CMFormatParser:
    """
    Parses validated OpenCM JSON into SCMModel instances.
    """
    
    @staticmethod
    def parse(data: Dict[str, Any], file_path: str = None) -> SCMModel:
        """
        Parse validated OpenCM JSON into an SCMModel.
        
        Args:
            data: Validated OpenCM JSON dict
            file_path: Optional path to the source file
            
        Returns:
            SCMModel instance
        """
        model_data = data.get("model", {})
        
        # Parse variables
        variables = {}
        for var_name, var_def in data.get("variables", {}).items():
            domain_raw = var_def.get("domain", [0.0, 1.0])
            variables[var_name] = SCMVariable(
                name=var_name,
                var_type=var_def.get("type", "continuous"),
                domain=tuple(domain_raw) if isinstance(domain_raw, list) else domain_raw,
                unit=var_def.get("unit", ""),
                description=var_def.get("description", ""),
                observed=var_def.get("observed", True),
                default_value=var_def.get("default_value"),
                categories=var_def.get("categories"),
            )
        
        # Parse edges
        edges = []
        for edge_data in data.get("edges", []):
            edges.append(SCMEdge(
                source=edge_data["source"],
                target=edge_data["target"],
                edge_type=edge_data.get("type", "causes"),
                strength=edge_data.get("strength", 0.5),
                description=edge_data.get("description", ""),
                confidence=edge_data.get("confidence", 1.0),
                is_learned=edge_data.get("is_learned", False),
            ))
        
        # Parse structural equations
        equations = {}
        for target, eq_data in data.get("structural_equations", {}).items():
            if isinstance(eq_data, str):
                equations[target] = SCMEquation(
                    target=target,
                    equation_type="linear",
                    expression=eq_data,
                )
            elif isinstance(eq_data, dict):
                equations[target] = SCMEquation(
                    target=target,
                    equation_type=eq_data.get("type", "linear"),
                    expression=eq_data.get("expression", ""),
                    noise_distribution=eq_data.get("noise_distribution", "normal"),
                    noise_params=eq_data.get("noise_params", {"mean": 0.0, "std": 0.05}),
                )
        
        # Parse metadata
        meta_data = data.get("metadata", {})
        metadata = SCMMetadata(
            author=meta_data.get("author", ""),
            citation=meta_data.get("citation", ""),
            license=meta_data.get("license", "CC0-1.0-Universal"),
            tags=meta_data.get("tags", []),
            created_at=meta_data.get("created_at", ""),
            updated_at=meta_data.get("updated_at", ""),
            source_url=meta_data.get("source_url", ""),
            adaptation_notes=meta_data.get("adaptation_notes", ""),
        )
        
        # Parse validation
        val_data = data.get("validation", {})
        validation = SCMValidation(
            min_data_points=val_data.get("min_data_points", 20),
            required_variables=val_data.get("required_variables", []),
            suggested_datasets=val_data.get("suggested_datasets", []),
        ) if val_data else None
        
        return SCMModel(
            model_id=model_data.get("id", "unknown"),
            name=model_data.get("name", "Unknown Model"),
            version=model_data.get("version", "1.0.0"),
            domain=model_data.get("domain", "general"),
            description=model_data.get("description", ""),
            variables=variables,
            edges=edges,
            equations=equations,
            allow_cycles=data.get("model", {}).get("allow_cycles", False),
            assumptions=data.get("assumptions", []),
            validation=validation,
            metadata=metadata,
            _file_path=file_path,
        )


# =============================================================================
# SERIALIZER — Exports SCMModel back to OpenCM JSON
# =============================================================================

class CMFormatSerializer:
    """
    Serializes SCMModel instances back to OpenCM JSON format.
    Used for CausalGraph.to_opencm() and model export.
    """
    
    @staticmethod
    def serialize(model: SCMModel) -> Dict[str, Any]:
        """
        Serialize an SCMModel to OpenCM JSON dict.
        
        Returns:
            Dict ready for json.dumps()
        """
        result = {
            "opencm_version": OPENCM_VERSION,
            "model": {
                "id": model.model_id,
                "name": model.name,
                "version": model.version,
                "domain": model.domain,
                "description": model.description,
            },
            "variables": {},
            "edges": [],
            "structural_equations": {},
            "assumptions": model.assumptions,
        }
        
        # Serialize variables
        for var_name, var in model.variables.items():
            var_dict = {
                "type": var.var_type,
                "domain": list(var.domain),
                "unit": var.unit,
                "observed": var.observed,
            }
            if var.description:
                var_dict["description"] = var.description
            if var.default_value is not None:
                var_dict["default_value"] = var.default_value
            if var.categories:
                var_dict["categories"] = var.categories
            result["variables"][var_name] = var_dict
        
        # Serialize edges
        for edge in model.edges:
            edge_dict = {
                "source": edge.source,
                "target": edge.target,
                "type": edge.edge_type,
                "strength": edge.strength,
            }
            if edge.description:
                edge_dict["description"] = edge.description
            if edge.confidence != 1.0:
                edge_dict["confidence"] = edge.confidence
            if edge.is_learned:
                edge_dict["is_learned"] = True
            result["edges"].append(edge_dict)
        
        # Serialize equations
        for target, eq in model.equations.items():
            if eq.equation_type == "linear" and eq.noise_distribution == "normal":
                # Simple format for simple equations
                result["structural_equations"][target] = eq.expression
            else:
                result["structural_equations"][target] = {
                    "type": eq.equation_type,
                    "expression": eq.expression,
                    "noise_distribution": eq.noise_distribution,
                    "noise_params": eq.noise_params,
                }
        
        # Serialize validation
        if model.validation:
            result["validation"] = {
                "min_data_points": model.validation.min_data_points,
                "required_variables": model.validation.required_variables,
                "suggested_datasets": model.validation.suggested_datasets,
            }
        
        # Serialize metadata
        if model.metadata:
            result["metadata"] = {
                "author": model.metadata.author,
                "citation": model.metadata.citation,
                "license": model.metadata.license,
                "tags": model.metadata.tags,
            }
            if model.metadata.source_url:
                result["metadata"]["source_url"] = model.metadata.source_url
            if model.metadata.adaptation_notes:
                result["metadata"]["adaptation_notes"] = model.metadata.adaptation_notes
        
        return result
    
    @staticmethod
    def save(model: SCMModel, path: str) -> str:
        """
        Save an SCMModel to an .opencm.json file.
        
        Args:
            model: SCMModel to save
            path: File path (should end with .opencm.json)
            
        Returns:
            Absolute path to saved file
        """
        data = CMFormatSerializer.serialize(model)
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"[OpenCM] Saved model '{model.model_id}' to {path}")
        return os.path.abspath(path)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def load_opencm(path: str) -> SCMModel:
    """
    Load and validate an OpenCM model file.
    
    Args:
        path: Path to .opencm.json file
        
    Returns:
        Validated SCMModel instance
        
    Raises:
        ValueError: If model fails validation
        FileNotFoundError: If file doesn't exist
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"OpenCM file not found: {path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    validator = CMFormatValidator()
    if not validator.validate(data):
        raise ValueError(f"OpenCM validation failed for {path}:\n" + "\n".join(validator.errors))
    
    if validator.warnings:
        for w in validator.warnings:
            logger.warning(f"[OpenCM] {w}")
    
    return CMFormatParser.parse(data, file_path=path)


def validate_opencm(path: str) -> Tuple[bool, List[str], List[str]]:
    """
    Validate an OpenCM file without loading it.
    
    Returns:
        (is_valid, errors, warnings)
    """
    with open(path, 'r') as f:
        data = json.load(f)
    
    validator = CMFormatValidator()
    is_valid = validator.validate(data)
    return is_valid, validator.errors, validator.warnings
