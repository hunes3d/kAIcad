import json
import os

from .models import get_default_model, get_real_model_name, validate_model_for_json
from .schema import PLAN_SCHEMA_VERSION, Diagnostic, Plan, PlanResult


def _demo_plan() -> Plan:
    demo = {
        "plan_version": PLAN_SCHEMA_VERSION,
        "ops": [
            {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80, 50], "rot": 0},
            {"op": "add_component", "ref": "D1", "symbol": "Device:LED", "value": "RED", "at": [120, 50], "rot": 0},
            {"op": "wire", "from": "R1:2", "to": "D1:A"},
            {"op": "label", "net": "LED_K", "at": [120, 46]},
        ],
    }
    return Plan.model_validate(demo)


def plan_from_prompt(prompt: str) -> PlanResult:
    """Generate a Plan from a natural language prompt using OpenAI if available.

    Fallbacks:
    - If no OPENAI_API_KEY or any error occurs -> return a small demo plan.
    - Attempts structured output via Responses API with json_schema; falls back to Chat Completions JSON mode.

    Returns PlanResult with diagnostics for any warnings during planning.

    Environment variables:
    - OPENAI_API_KEY: Required for AI planning
    - OPENAI_MODEL: Model name (default: gpt-5-mini)
    - OPENAI_TEMPERATURE: Sampling temperature (default: 0.0)

    Note: KAI_MODEL is deprecated, use OPENAI_MODEL instead
    """
    diagnostics = []

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[planner] No OPENAI_API_KEY found, returning demo plan")
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="warning",
                message="No OPENAI_API_KEY set, using demo plan",
                suggestion="Set OPENAI_API_KEY environment variable for AI-powered planning",
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    # Choose model (env override supported, KAI_MODEL deprecated but still checked)
    model = os.getenv("OPENAI_MODEL") or os.getenv("KAI_MODEL", get_default_model())

    # Warn if using deprecated KAI_MODEL
    if os.getenv("KAI_MODEL") and not os.getenv("OPENAI_MODEL"):
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="warning",
                message="KAI_MODEL is deprecated, use OPENAI_MODEL instead",
                suggestion="Set OPENAI_MODEL environment variable",
            )
        )

    # Validate model supports JSON mode
    is_valid, error_msg = validate_model_for_json(model)
    if not is_valid:
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="error",
                message=error_msg,
                suggestion=f"Use a supported model like {get_default_model()}",
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)

    # Get real model name (handles aliases like gpt-5-mini -> gpt-4o-mini)
    real_model = get_real_model_name(model)
    if real_model != model:
        print(f"[planner] Using model: {model} (aliased to {real_model})")
    else:
        print(f"[planner] Using model: {model}")

    model = real_model  # Use real name for API calls

    # Construct minimal JSON schema from Pydantic for structured output
    schema = Plan.model_json_schema()

    # Try Responses API with JSON schema first
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        try:
            resp = client.responses.create(
                model=model,
                input=[
                    {
                        "role": "system",
                        "content": (
                            "You are a KiCad schematic planning assistant. "
                            "Given a user request for schematic edits, output ONLY a JSON object that matches the provided JSON schema exactly. "
                            "Do not include explanations. Coordinates are in schematic units (mm-ish)."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
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
            # Extract text (SDK returns content[0].text in Responses API)
            content = None
            try:
                # Newer SDK
                content = resp.output_text  # type: ignore[attr-defined]
            except Exception:
                # Fallback parse
                if hasattr(resp, "output") and resp.output and hasattr(resp.output[0], "content"):
                    parts = resp.output[0].content
                    if parts and hasattr(parts[0], "text"):
                        content = parts[0].text
            if not content:
                raise RuntimeError("Empty response content from Responses API")
            data = json.loads(content)
            plan = Plan.model_validate(data)
            diagnostics.append(
                Diagnostic(
                    stage="planner",
                    severity="info",
                    message=f"Generated plan with {len(plan.ops)} operations using {model}",
                )
            )
            return PlanResult(plan=plan, diagnostics=diagnostics)
        except Exception:
            # Fall through to Chat Completions JSON mode
            pass
    except Exception:
        # openai package old or not available; we'll try chat completions path
        pass

    # Try Chat Completions with JSON output
    try:
        from openai import OpenAI  # type: ignore

        client = OpenAI(api_key=api_key)
        sys_prompt = (
            "You are a KiCad schematic planning assistant. "
            "Return ONLY a JSON object conforming to this schema: \n" + json.dumps(schema)
        )

        # Build completion parameters
        completion_params = {
            "model": model,
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt},
            ],
            "response_format": {"type": "json_object"},  # models that support JSON mode
        }

        # Only add temperature if explicitly set in environment (some models don't support it)
        temperature = os.getenv("OPENAI_TEMPERATURE")
        if temperature is not None:
            try:
                completion_params["temperature"] = float(temperature)
            except ValueError:
                pass

        completion = client.chat.completions.create(**completion_params)
        content = completion.choices[0].message.content
        data = json.loads(content)
        plan = Plan.model_validate(data)
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="info",
                message=f"Generated plan with {len(plan.ops)} operations using {model} (chat mode)",
            )
        )
        return PlanResult(plan=plan, diagnostics=diagnostics)
    except Exception as e:
        diagnostics.append(
            Diagnostic(
                stage="planner",
                severity="warning",
                message=f"OpenAI API error, using demo plan: {e}",
                suggestion="Check OPENAI_API_KEY and network connectivity",
            )
        )
        return PlanResult(plan=_demo_plan(), diagnostics=diagnostics)
