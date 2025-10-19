from typing import Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field

# Schema version for migration tracking
PLAN_SCHEMA_VERSION = 1


class Diagnostic(BaseModel):
    """
    Structured diagnostic message for errors, warnings, and info.
    Used to surface issues from planner/writer stages to UIs.
    """

    stage: Literal["planner", "writer", "validator", "web"] = Field(
        ..., description="Stage where diagnostic was generated"
    )
    severity: Literal["error", "warning", "info"] = Field(..., description="Severity level")
    ref: Optional[str] = Field(None, description="Component reference if applicable (e.g., 'R1')")
    message: str = Field(..., description="Human-readable diagnostic message")
    suggestion: Optional[str] = Field(None, description="Suggested fix or next step")


class PlanResult(BaseModel):
    """
    Result of planning operation, including the plan and any diagnostics.
    Allows planner to return warnings without failing.
    """

    plan: "Plan"
    diagnostics: List[Diagnostic] = Field(default_factory=list, description="Warnings and errors")

    def has_errors(self) -> bool:
        """Check if any diagnostics are errors"""
        return any(d.severity == "error" for d in self.diagnostics)

    def has_warnings(self) -> bool:
        """Check if any diagnostics are warnings"""
        return any(d.severity == "warning" for d in self.diagnostics)


class ApplyResult(BaseModel):
    """
    Result of applying a plan, including any diagnostics from the writer.
    """

    success: bool = Field(..., description="Whether the plan was applied successfully")
    diagnostics: List[Diagnostic] = Field(default_factory=list, description="Warnings and errors")
    affected_refs: List[str] = Field(default_factory=list, description="Component refs that were modified")

    def has_errors(self) -> bool:
        """Check if any diagnostics are errors"""
        return any(d.severity == "error" for d in self.diagnostics)

    def has_warnings(self) -> bool:
        """Check if any diagnostics are warnings"""
        return any(d.severity == "warning" for d in self.diagnostics)


class AddComponent(BaseModel):
    op: Literal["add_component"]
    ref: str = Field(..., description="Component reference designator (e.g., 'R1')")
    symbol: str = Field(..., description="Library symbol (e.g., 'Device:R')")
    value: str = Field(..., description="Component value (e.g., '1k', 'RED')")
    at: Tuple[float, float] = Field(..., description="Position in mm, will snap to grid")
    rot: int = Field(0, description="Rotation in degrees (0, 90, 180, 270)")
    fields: Dict[str, str] = Field(default_factory=dict, description="Additional fields")


class Wire(BaseModel):
    op: Literal["wire"]
    from_: str = Field(alias="from", description="Source pin as REF:PIN (e.g., 'R1:1')")
    to: str = Field(..., description="Target pin as REF:PIN (e.g., 'R2:2')")

    # Allow population by field name (from_) in addition to alias ("from")
    model_config = ConfigDict(populate_by_name=True)


class Label(BaseModel):
    op: Literal["label"]
    net: str = Field(..., description="Net name")
    at: Tuple[float, float] = Field(..., description="Position in mm, will snap to grid")


Op = Union[AddComponent, Wire, Label]


class Plan(BaseModel):
    """
    A plan describes a sequence of schematic operations.
    Version 1: Supports add_component, wire, and label operations.
    """

    plan_version: int = Field(PLAN_SCHEMA_VERSION, description="Schema version for migrations")
    ops: List[Op] = Field(..., description="Ordered list of operations to apply")
    constraints: Dict[str, object] = Field(default_factory=dict, description="Optional metadata")

    # Be permissive when validating JSON produced without aliases
    model_config = ConfigDict(populate_by_name=True)


# Public API
__all__ = [
    "PLAN_SCHEMA_VERSION",
    "Diagnostic",
    "PlanResult",
    "ApplyResult",
    "AddComponent",
    "Wire",
    "Label",
    "Plan",
]
