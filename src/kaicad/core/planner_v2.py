"""
Enhanced AI planner for KiCad schematic operations using schema-first approach.

This module replaces the basic planner.py with improved:
- Settings integration (no direct env var access)
- Better prompt engineering with KiCad context
- Component library awareness
- Grid-aware placement
- Structured error handling
"""

import json
import logging
from typing import Optional

from kaicad.config.settings import Settings
from kaicad.core.model_registry import ModelRegistry
from kaicad.schema.plan import PLAN_SCHEMA_VERSION, Diagnostic, Plan, PlanResult

logger = logging.getLogger(__name__)

# KiCad schematic grid size in mm (default 1.27mm = 50 mils)
KICAD_GRID_MM = 1.27


def _snap_to_grid(x: float, y: float, grid: float = KICAD_GRID_MM) -> tuple[float, float]:
    """Snap coordinates to KiCad grid."""
    return (round(x / grid) * grid, round(y / grid) * grid)


def _demo_plan() -> Plan:
    """Return a simple demo plan (LED + resistor circuit)."""
    demo = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "220", "at": [80.01, 50.8], "rot": 0},
            {"op": "add_component", "ref": "D1", "symbol": "Device:LED", "value": "RED", "at": [101.6, 50.8], "rot": 0},
            {"op": "wire", "from": "R1:2", "to": "D1:1"},
            {"op": "label", "net": "VCC", "at": [76.2, 50.8]},
            {"op": "label", "net": "GND", "at": [106.68, 50.8]},
        ],
    }
    return Plan.model_validate(demo)


# System prompt with comprehensive KiCad context
SYSTEM_PROMPT = """You are an expert KiCad schematic planning assistant. Your job is to generate valid schematic operation plans in JSON format.

## KiCad Schema Rules

### Operations (ops)
You can use these operations:

1. **add_component**: Add a component to the schematic
   - ref: Component reference (e.g., "R1", "C2", "U1")
   - symbol: Library symbol in format "LibraryName:ComponentName" (e.g., "Device:R", "Device:C", "MCU_ST_STM32F1:STM32F103C8Tx")
   - value: Component value (e.g., "10k", "100nF", "STM32F103")
   - at: [x, y] position in mm (will be snapped to 1.27mm grid)
   - rot: Rotation in degrees (0, 90, 180, 270)
   - fields: Optional dict of custom fields

2. **wire**: Connect two component pins
   - from: Source as "REF:PIN" (e.g., "R1:1" means R1 pin 1)
   - to: Target as "REF:PIN" (e.g., "R2:2")

3. **label**: Add net label
   - net: Net name (e.g., "VCC", "GND", "SDA")
   - at: [x, y] position in mm

### Common KiCad Symbols
- Device:R - Resistor (pins: 1, 2)
- Device:C - Capacitor (pins: 1, 2)  
- Device:LED - LED (pins: 1=anode/A, 2=cathode/K)
- Device:D - Diode (pins: 1=K, 2=A)
- Connector:Conn_01x02_Pin - 2-pin connector (pins: 1, 2)
- power:GND - Ground symbol (pin: 1)
- power:VCC - VCC power symbol (pin: 1)

### Reference Designators
- R = Resistor (R1, R2, ...)
- C = Capacitor (C1, C2, ...)
- D = Diode/LED (D1, D2, ...)
- U = IC (U1, U2, ...)
- J = Connector (J1, J2, ...)
- Q = Transistor (Q1, Q2, ...)

### Placement Guidelines
- Space components 15-25mm apart
- Use 1.27mm grid (KiCad default)
- Common ranges: X: 50-200mm, Y: 50-150mm
- Keep related components close together

### Output Format
Return ONLY valid JSON matching this structure:
{
  "plan_version": 1,
  "ops": [
    {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80.01, 50.8], "rot": 0},
    {"op": "wire", "from": "R1:2", "to": "D1:1"},
    {"op": "label", "net": "VCC", "at": [76.2, 50.8]}
  ]
}

Do NOT include explanations, markdown, or anything other than the JSON object.
"""


def plan_from_prompt(
    prompt: str,
    settings: Optional[Settings] = None,
    model_override: Optional[str] = None
) -> PlanResult:
    """
    Generate a Plan from natural language prompt using OpenAI.

    This is the v2 planner with improved:
    - Settings integration (no direct env var access)
    - Better prompt engineering
    - Structured error handling

    Args:
        prompt: Natural language description of schematic changes
        settings: Settings object (loads from config if not provided)
        model_override: Optional model name to override settings

    Returns:
        PlanResult with plan and diagnostics

    Fallback behavior:
        - No API key -> demo plan with warning
        - API error -> demo plan with warning
        - Invalid JSON -> demo plan with error diagnostic
    """
    diagnostics: list[Diagnostic] = []

    # Load settings if not provided
    if settings is None:
        try:
            settings = Settings.load()
        except Exception as e:
            logger.error(f"Failed to load settings: {e}")
            diagnostics.append(
                Diagnostic(
                    stage="planner",
                    severity="error",
                    message=f"Failed to load settings: {e}",
                    suggestion="Check your configuration file and keyring setup"
                )
            )
            return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    # Check for API key
    if not settings.openai_api_key:
        logger.warning("No OpenAI API key configured, returning demo plan")
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="warning",
                message="No OpenAI API key configured",
                suggestion="Set OPENAI_API_KEY environment variable or configure in settings"
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    # Determine model to use
    model = model_override or settings.openai_model
    registry = ModelRegistry()

    # Validate model exists
    if not registry.is_valid_model(model):
        available = registry.get_available_models()
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="error",
                message=f"Invalid model: {model}",
                suggestion=f"Use one of: {', '.join(available[:5])}"
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    logger.info(f"Planning with model: {model}, temperature: {settings.openai_temperature}")

    # Get JSON schema for structured output
    schema = Plan.model_json_schema()

    # Try OpenAI Responses API (newer) with structured output
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        try:
            # Attempt Responses API (SDK v1.60.0+)
            response = client.responses.create(
                model=model,
                input=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "kAIcadPlan",
                        "schema": schema,
                        "strict": True,
                    },
                },
            )

            # Extract response content
            content = None
            if hasattr(response, "output_text"):
                content = response.output_text
            elif hasattr(response, "output") and response.output:
                if hasattr(response.output[0], "content"):
                    parts = response.output[0].content
                    if parts and hasattr(parts[0], "text"):
                        content = parts[0].text

            if not content:
                raise RuntimeError("Empty response from OpenAI Responses API")

            data = json.loads(content)
            plan = Plan.model_validate(data)

            diagnostics.append(
                Diagnostic(
                    stage="planner",
                    severity="info",
                    message=f"Generated {len(plan.ops)} operations using {model} (Responses API)"
                )
            )
            return PlanResult(plan=plan, diagnostics=diagnostics)

        except Exception as responses_error:
            logger.debug(f"Responses API failed: {responses_error}, falling back to Chat Completions")

    except ImportError:
        logger.warning("OpenAI package not installed, cannot plan")
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="error",
                message="OpenAI package not installed",
                suggestion="Install with: pip install openai"
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    # Fallback to Chat Completions API with JSON mode
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.openai_api_key)

        # Build completion request
        completion_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},
            "temperature": settings.openai_temperature,
        }

        completion = client.chat.completions.create(**completion_params)
        content = completion.choices[0].message.content

        if not content:
            raise RuntimeError("Empty response from OpenAI Chat API")

        data = json.loads(content)
        plan = Plan.model_validate(data)

        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="info",
                message=f"Generated {len(plan.ops)} operations using {model} (Chat API)"
            )
        )
        return PlanResult(plan=plan, diagnostics=diagnostics)

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse OpenAI response as JSON: {e}")
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="error",
                message=f"Invalid JSON response from OpenAI: {e}",
                suggestion="Try a different model or check your prompt"
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="warning",
                message=f"OpenAI API error: {str(e)[:100]}",
                suggestion="Check API key, model availability, and network connectivity"
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)
