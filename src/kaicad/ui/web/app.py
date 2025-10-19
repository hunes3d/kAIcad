from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from flask import Flask, flash, jsonify, render_template, request

# Import from kaicad package
from kaicad.core.inspector import (
    find_component_by_reference,
    find_components_by_pattern,
    format_inspection_report,
    get_component_connections,
    inspect_hierarchical_design,
    inspect_net_connections,
    inspect_schematic,
    search_components,
)
from kaicad.core.models import get_default_model, get_real_model_name, is_model_supported, list_supported_models
from kaicad.core.planner import plan_from_prompt
from kaicad.schema.plan import Plan
from kaicad.kicad.tasks import export_netlist, export_pdf, run_erc
from kaicad.core.writer import apply_plan
from skip.eeschema import schematic as sch  # type: ignore

load_dotenv()

# Configure template folder to be in the web package
template_folder = Path(__file__).parent / "templates"

# Project root for state storage files
project_root = Path.cwd()

app = Flask(__name__, template_folder=str(template_folder))

# Initialize CSRF protection at module level
csrf = None
try:
    from flask_wtf.csrf import CSRFProtect

    csrf = CSRFProtect()
except ImportError:
    print("WARNING: flask-wtf not installed. CSRF protection disabled.", file=__import__("sys").stderr)

# Track if app has been configured
_app_configured = False


# Security configuration is deferred to create_app() to avoid import-time failures
def _configure_security(app: Flask) -> None:
    global _app_configured

    # Only configure once
    if _app_configured:
        return

    secret_key = os.getenv("FLASK_SECRET_KEY")
    flask_env = os.getenv("FLASK_ENV", "production")
    if not secret_key or secret_key == "dev-secret":
        if flask_env != "development":
            raise RuntimeError(
                "FATAL: FLASK_SECRET_KEY is not set or using insecure default.\n"
                "Set a secure random key:\n"
                "  export FLASK_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')\n"
                "Or for development only:\n"
                "  export FLASK_ENV=development"
            )
        else:
            print("WARNING: Using default secret key in development mode", file=__import__("sys").stderr)
            secret_key = "dev-secret-" + __import__("secrets").token_hex(16)
    app.secret_key = secret_key

    # Configure Flask-WTF to accept CSRF tokens from both form fields and headers (for AJAX)
    app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken"]
    app.config["WTF_CSRF_TIME_LIMIT"] = None  # No expiration for development

    # Initialize CSRF protection with app (only once)
    if csrf is not None:
        csrf.init_app(app)

    _app_configured = True


# Configure app at module import time (tests set FLASK_ENV before importing)
_configure_security(app)

# State storage files (separated by concern)
RECENT_PROJECTS_FILE = project_root / ".recent_projects.json"
API_KEY_FILE = project_root / ".api_key.json"
CHAT_HISTORY_FILE = project_root / ".chat_history.json"
PLAN_HISTORY_FILE = project_root / ".plan_history.json"
CURRENT_PROJECT_FILE = project_root / ".current_project.json"


def _load_current_project() -> Optional[str]:
    """Load the currently active project path"""
    if CURRENT_PROJECT_FILE.exists():
        try:
            data = json.loads(CURRENT_PROJECT_FILE.read_text())
            return data.get("project_path")
        except Exception as e:
            print(f"[ERROR] Failed to load current project: {e}", file=__import__("sys").stderr)
    return os.getenv("KAICAD_PROJECT", "")


def _save_current_project(project_path: str) -> None:
    """Save the currently active project path"""
    try:
        CURRENT_PROJECT_FILE.write_text(json.dumps({"project_path": project_path}, indent=2))
        os.environ["KAICAD_PROJECT"] = project_path
    except Exception as e:
        print(f"[ERROR] Failed to save current project: {e}", file=__import__("sys").stderr)


def _load_chat_history() -> List[dict]:
    """Load chat history from file"""
    if CHAT_HISTORY_FILE.exists():
        try:
            return json.loads(CHAT_HISTORY_FILE.read_text())
        except Exception as e:
            print(f"[ERROR] Failed to load chat history: {e}", file=__import__("sys").stderr)
            return []
    return []


def _save_chat_history(history: List[dict]) -> None:
    """Save chat history to file"""
    try:
        CHAT_HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception as e:
        print(f"[ERROR] Failed to save chat history: {e}", file=__import__("sys").stderr)


def _load_plan_history() -> List[dict]:
    """Load plan generation history from file"""
    if PLAN_HISTORY_FILE.exists():
        try:
            return json.loads(PLAN_HISTORY_FILE.read_text())
        except Exception as e:
            print(f"[ERROR] Failed to load plan history: {e}", file=__import__("sys").stderr)
            return []
    return []


def _save_plan_history(history: List[dict]) -> None:
    """Save plan generation history to file"""
    try:
        PLAN_HISTORY_FILE.write_text(json.dumps(history, indent=2))
    except Exception as e:
        print(f"[ERROR] Failed to save plan history: {e}", file=__import__("sys").stderr)


def _load_api_key() -> Optional[str]:
    """Load API key from file"""
    if API_KEY_FILE.exists():
        try:
            data = json.loads(API_KEY_FILE.read_text())
            return data.get("key")
        except:
            return None
    # Fallback to environment variable
    return os.getenv("OPENAI_API_KEY")


def _save_api_key(api_key: str) -> None:
    """Save API key to file"""
    API_KEY_FILE.write_text(json.dumps({"key": api_key}, indent=2))
    # Also set in environment for current session
    os.environ["OPENAI_API_KEY"] = api_key


def _mask_api_key(api_key: Optional[str]) -> str:
    """Mask API key for display"""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return api_key[:7] + "****" + api_key[-4:]


def _load_recent_projects() -> List[dict]:
    """Load recent projects from file"""
    if RECENT_PROJECTS_FILE.exists():
        try:
            data = json.loads(RECENT_PROJECTS_FILE.read_text())
            # Handle old format (list of strings) and new format (list of dicts)
            if data and isinstance(data[0], str):
                # Convert old format to new format
                return [{"path": p, "name": Path(p).stem} for p in data]
            return data
        except:
            return []
    return []


def _save_recent_project(project_path: str, project_name: str) -> None:
    """Save a project to recent projects list"""
    recent = _load_recent_projects()
    new_entry = {"path": project_path, "name": project_name}

    # Remove if already exists to avoid duplicates
    recent = [p for p in recent if p.get("path") != project_path]

    # Add to front
    recent.insert(0, new_entry)
    # Keep only last 10
    recent = recent[:10]
    RECENT_PROJECTS_FILE.write_text(json.dumps(recent, indent=2))


def _launch_kicad(sch_path: Path) -> bool:
    """Launch KiCad with the specified schematic"""
    try:
        if os.name == "nt":  # Windows
            # Try common KiCad installation paths
            kicad_paths = [
                r"C:\Program Files\KiCad\8.0\bin\kicad.exe",
                r"C:\Program Files\KiCad\7.0\bin\kicad.exe",
                r"C:\Program Files (x86)\KiCad\8.0\bin\kicad.exe",
                r"C:\Program Files (x86)\KiCad\7.0\bin\kicad.exe",
            ]
            kicad_exe = None
            for path in kicad_paths:
                if Path(path).exists():
                    kicad_exe = path
                    break

            if kicad_exe:
                subprocess.Popen([kicad_exe, str(sch_path)], shell=False)
                return True
            else:
                # Try to launch using file association
                os.startfile(str(sch_path))
                return True
        else:  # Unix-like
            subprocess.Popen(["kicad", str(sch_path)], shell=False)
            return True
    except Exception as e:
        print(f"Failed to launch KiCad: {e}")
        return False


def _discover_schematic(proj: Path) -> Optional[Path]:
    """Discover schematic file from a .kicad_pro file, .kicad_sch file, or directory"""
    try:
        # If it's already a .kicad_sch file, return it directly
        if proj.is_file() and proj.suffix == ".kicad_sch":
            return proj
        # If it's a .kicad_pro file, look for .kicad_sch with same name
        elif proj.is_file() and proj.suffix == ".kicad_pro":
            # If it's a .kicad_pro file, look for .kicad_sch with same name
            sch_path = proj.with_suffix(".kicad_sch")
            if sch_path.exists():
                return sch_path
            # If not found, look for any .kicad_sch in the same directory
            return next(proj.parent.glob("*.kicad_sch"))
        elif proj.is_dir():
            # If it's a directory, look for any .kicad_sch
            return next(proj.glob("*.kicad_sch"))
        return None
    except StopIteration:
        return None


@app.route("/debug_schematic", methods=["GET"])
def debug_schematic():
    """Debug endpoint to check schematic loading status"""
    try:
        last_proj = _load_current_project()
        debug_info = {
            "current_project_setting": last_proj,
            "project_exists": False,
            "discovered_schematic": None,
            "error": None,
        }

        if last_proj:
            proj = Path(last_proj).expanduser().resolve()
            debug_info["resolved_path"] = str(proj)
            debug_info["project_exists"] = proj.exists()
            debug_info["is_file"] = proj.is_file()
            debug_info["is_dir"] = proj.is_dir()

            if proj.exists():
                try:
                    sch_path = _discover_schematic(proj)
                    if sch_path:
                        debug_info["discovered_schematic"] = str(sch_path)
                        debug_info["schematic_exists"] = sch_path.exists()
                        debug_info["schematic_size"] = sch_path.stat().st_size

                        # Try to load it
                        try:
                            doc = sch.Schematic(str(sch_path))
                            symbols = list(doc.symbol)
                            debug_info["symbols_count"] = len(symbols)
                            debug_info["load_success"] = True
                        except Exception as e:
                            debug_info["load_error"] = str(e)
                            debug_info["load_success"] = False
                    else:
                        debug_info["discovery_error"] = "No .kicad_sch file found"
                except Exception as e:
                    debug_info["discovery_error"] = str(e)
        else:
            debug_info["error"] = "No project path configured"

        return jsonify(debug_info)
    except Exception as e:
        return jsonify({"error": str(e)})


@app.route("/generate_description", methods=["POST"])
def generate_description():
    """Use AI to generate or expand a plan description"""
    try:
        data = request.get_json()
        user_input = data.get("input", "").strip()
        api_key = _load_api_key()

        if not api_key:
            return jsonify({"success": False, "message": "API key not configured"})

        if not user_input:
            return jsonify({"success": False, "message": "Please provide some input text"})

        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        # Get the model from request or use default
        model = data.get("model", get_default_model())

        # Validate model
        if not is_model_supported(model):
            return jsonify(
                {
                    "success": False,
                    "message": f"Model '{model}' is not supported. Supported models: {', '.join(list_supported_models())}",
                }
            )

        # Get real model name (handle aliases)
        model = get_real_model_name(model)

        prompt = f"""Convert this brief idea into a detailed, technical KiCad schematic plan description.
Be specific about component types, values, and connections.

User's idea: {user_input}

Provide a clear, actionable description for implementing this in KiCad (2-3 sentences max):"""

        completion = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a KiCad expert. Convert brief circuit ideas into precise technical descriptions with component specs.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=200,
            temperature=0.7,
        )

        description = completion.choices[0].message.content.strip()
        return jsonify({"success": True, "description": description})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route("/send_chat", methods=["POST"])
def send_chat():
    """Handle chat messages via AJAX"""
    try:
        print("[DEBUG] Received chat request")
        data = request.get_json()
        message = data.get("message", "").strip()
        chat_model = data.get("chat_model", "gpt-4")  # Use gpt-4 as default for chat

        # Validate model
        if not is_model_supported(chat_model):
            return jsonify(
                {
                    "success": False,
                    "error": f"Model '{chat_model}' is not supported. Supported models: {', '.join(list_supported_models())}",
                }
            )

        # Get real model name (handle aliases)
        chat_model = get_real_model_name(chat_model)

        print(f"[DEBUG] Message: {message[:50]}... Model: {chat_model}")

        if not message:
            return jsonify({"success": False, "message": "Empty message"})

        api_key = _load_api_key()
        if not api_key:
            print("[DEBUG] No API key found")
            return jsonify({"success": False, "message": "API key not configured"})

        print("[DEBUG] Loading chat history")
        # Load chat history and add user message
        chat_history = _load_chat_history()
        chat_history.append({"role": "user", "content": message})

        # Get project context from persistent storage
        last_proj = _load_current_project()
        sch_name = None
        project_name = None
        sch_path = None
        schematic_info = None

        print(f"[DEBUG] Current project: {last_proj}")

        if last_proj:
            try:
                proj = Path(last_proj).expanduser().resolve()
                print(f"[DEBUG] Resolved project path: {proj}")
                print(f"[DEBUG] Path exists: {proj.exists()}")
                print(f"[DEBUG] Is file: {proj.is_file()}")
                print(f"[DEBUG] Is directory: {proj.is_dir()}")

                if proj.exists():
                    sch_path = _discover_schematic(proj)
                    print(f"[DEBUG] Discovered schematic: {sch_path}")

                    if sch_path:
                        sch_name = sch_path.name
                        project_name = sch_path.stem
                        print(f"[DEBUG] Schematic name: {sch_name}, Project: {project_name}")

                        # If user is asking about the schematic, load actual data
                        inspect_keywords = [
                            "inspect",
                            "analyze",
                            "check",
                            "review",
                            "look at",
                            "examine",
                            "show me",
                            "hierarchy",
                            "hierarchical",
                            "sheets",
                            "net",
                            "connection",
                            "connected",
                        ]

                        # Check for specific component reference patterns (C2, R47, U1, etc.)
                        component_ref_pattern = r"\b([RCLUQDJKTP]\d+)\b"
                        ref_matches = re.findall(component_ref_pattern, message, re.IGNORECASE)

                        # Check for net name queries
                        net_keywords = ["net ", "network ", "signal "]
                        asking_about_net = any(kw in message.lower() for kw in net_keywords)

                        if (
                            any(keyword in message.lower() for keyword in inspect_keywords)
                            or ref_matches
                            or asking_about_net
                        ):
                            try:
                                print(f"[DEBUG] Inspecting schematic: {sch_path}")

                                # Check for specific component reference queries
                                if ref_matches:
                                    print(f"[DEBUG] Found component references: {ref_matches}")
                                    component_details = []
                                    for ref in ref_matches[:5]:  # Limit to first 5 refs
                                        comp_info = find_component_by_reference(sch_path, ref)
                                        if comp_info and "error" not in comp_info:
                                            component_details.append(comp_info)

                                    if component_details:
                                        schematic_info = {
                                            "type": "component_lookup",
                                            "components": component_details,
                                            "query_refs": ref_matches,
                                        }
                                        print(f"[DEBUG] Found {len(component_details)} components")
                                    else:
                                        schematic_info = {
                                            "type": "component_lookup",
                                            "error": f"Components {', '.join(ref_matches)} not found",
                                            "query_refs": ref_matches,
                                        }

                                # Check for net connection queries
                                elif asking_about_net:
                                    # Try to extract net name from message
                                    # Look for quoted strings or common net names
                                    net_name = None
                                    if '"' in message:
                                        parts = message.split('"')
                                        if len(parts) >= 2:
                                            net_name = parts[1]

                                    if net_name:
                                        net_info = inspect_net_connections(sch_path, net_name)
                                        schematic_info = {
                                            "type": "net_inspection",
                                            "net": net_info,
                                            "net_name": net_name,
                                        }
                                        print(f"[DEBUG] Inspected net: {net_name}")
                                    else:
                                        # Just do regular inspection and include net list
                                        inspection = inspect_schematic(sch_path)
                                        schematic_info = {
                                            "type": "nets_list",
                                            "nets": inspection.get("nets", []),
                                            "net_count": len(inspection.get("nets", [])),
                                        }

                                # Check if user is asking about hierarchical sheets specifically
                                elif "hierarch" in message.lower() or "sheet" in message.lower():
                                    inspection = inspect_hierarchical_design(sch_path)

                                    # Format hierarchical design info
                                    if inspection["root"].get("success"):
                                        schematic_info = {
                                            "is_hierarchical": len(inspection["root"].get("hierarchy", [])) > 0,
                                            "root_stats": inspection["root"]["stats"],
                                            "sheets": inspection["root"].get("hierarchy", []),
                                            "symbols_count": inspection["root"]["stats"]["total_components"],
                                            "symbols": inspection["root"]["components"][:20],
                                            "subsheets_info": {},
                                        }

                                        # Add subsheet information
                                        for sheet_name, sheet_data in inspection["subsheets"].items():
                                            if sheet_data.get("success"):
                                                schematic_info["subsheets_info"][sheet_name] = {
                                                    "components": sheet_data["stats"]["total_components"],
                                                    "nets": sheet_data["stats"]["total_nets"],
                                                }
                                    else:
                                        schematic_info = {
                                            "error": inspection["root"].get("error"),
                                            "path": str(sch_path),
                                        }
                                else:
                                    # Regular inspection
                                    inspection = inspect_schematic(sch_path)

                                    if inspection.get("success"):
                                        schematic_info = {
                                            "is_hierarchical": len(inspection.get("hierarchy", [])) > 0,
                                            "stats": inspection["stats"],
                                            "sheets": inspection.get("hierarchy", []),
                                            "symbols_count": inspection["stats"]["total_components"],
                                            "symbols": inspection["components"][:20],
                                            "nets": inspection["nets"][:15],
                                            "labels": inspection.get("labels", [])[:10],
                                        }
                                    else:
                                        schematic_info = {"error": inspection.get("error"), "path": str(sch_path)}

                                print(f"[DEBUG] Inspection complete: {schematic_info.get('symbols_count', 0)} symbols")

                            except Exception as e:
                                print(f"[DEBUG] Failed to inspect schematic: {e}")
                                import traceback

                                traceback.print_exc()
                                schematic_info = {"error": str(e), "path": str(sch_path)}
                    else:
                        print(f"[DEBUG] No schematic discovered from path: {proj}")
                else:
                    print(f"[DEBUG] Project path does not exist: {proj}")
            except Exception as e:
                print(f"[DEBUG] Error processing project path: {e}")
                import traceback

                traceback.print_exc()

        # Build system prompt
        system_prompt = """You are an expert KiCad electronics engineer. Be CONCISE and FUNCTIONAL - no fluff or redundant explanations.

Current context:"""
        if sch_name:
            system_prompt += f"\n- Schematic: {sch_name}"
            system_prompt += f"\n- Project: {project_name}"

            if schematic_info:
                if "error" in schematic_info:
                    system_prompt += f"\n- ⚠️ Schematic could not be loaded: {schematic_info['error']}"
                    system_prompt += f"\n- File path attempted: {schematic_info.get('path', 'unknown')}"
                    system_prompt += "\n- Tell user to verify: 1) path is correct in Settings, 2) file exists, 3) it's a valid .kicad_sch file"
                elif schematic_info.get("type") == "component_lookup":
                    # User asked about specific component(s)
                    if schematic_info.get("components"):
                        system_prompt += "\n\n📍 Component Details Requested:"
                        for comp in schematic_info["components"]:
                            system_prompt += f"\n- {comp['reference']}: {comp['value']}"
                            system_prompt += f"\n  Symbol: {comp['symbol']}"
                            if comp.get("footprint"):
                                system_prompt += f"\n  Footprint: {comp['footprint']}"
                            if comp.get("properties"):
                                props = [f"{k}={v}" for k, v in list(comp["properties"].items())[:3]]
                                if props:
                                    system_prompt += f"\n  Properties: {', '.join(props)}"
                            if comp.get("connections"):
                                system_prompt += f"\n  Connected to {len(comp['connections'])} nets: {', '.join(comp['connections'][:5])}"
                        system_prompt += "\n\n➡️ Provide technical details about these specific components"
                    else:
                        system_prompt += (
                            f"\n- ⚠️ Components not found: {', '.join(schematic_info.get('query_refs', []))}"
                        )
                        system_prompt += "\n- Tell user: Component references are case-insensitive. List available components if needed."
                elif schematic_info.get("type") == "net_inspection":
                    # User asked about a specific net
                    net_info = schematic_info["net"]
                    if net_info.get("success"):
                        system_prompt += f"\n\n🔌 Net '{schematic_info['net_name']}' Details:"
                        system_prompt += f"\n- Connected components: {len(net_info['connections'])}"
                        for conn in net_info["connections"][:10]:
                            system_prompt += f"\n  - {conn['component']}: pin {conn['pin_number']} ({conn['pin_name']})"
                        system_prompt += "\n\n➡️ Explain this net's function and connections"
                    else:
                        system_prompt += f"\n- ⚠️ Net '{schematic_info['net_name']}' not found"
                        system_prompt += f"\n- Available nets: {', '.join(net_info.get('available_nets', [])[:10])}"
                elif schematic_info.get("type") == "nets_list":
                    # User asked about nets in general
                    system_prompt += "\n\n🔌 Network Analysis:"
                    system_prompt += f"\n- Total nets: {schematic_info['net_count']}"
                    system_prompt += f"\n- Net names: {', '.join(schematic_info['nets'][:15])}"
                    system_prompt += "\n\n➡️ Provide overview of the circuit's net structure"
                else:
                    system_prompt += f"\n- Components: {schematic_info['symbols_count']}"

                    # Hierarchical design info
                    if schematic_info.get("is_hierarchical"):
                        system_prompt += (
                            f"\n- 🏗️ Hierarchical design with {len(schematic_info.get('sheets', []))} sub-sheets"
                        )
                        if schematic_info.get("sheets"):
                            system_prompt += "\n- Sheets: " + ", ".join(
                                [f"{s['name']}" for s in schematic_info["sheets"]]
                            )
                        if schematic_info.get("subsheets_info"):
                            for sheet_name, info in schematic_info["subsheets_info"].items():
                                system_prompt += (
                                    f"\n  - {sheet_name}: {info['components']} components, {info['nets']} nets"
                                )

                    # Component list
                    if schematic_info.get("symbols"):
                        system_prompt += "\n- Parts: " + ", ".join(
                            [f"{s['ref']}={s['value']}" for s in schematic_info["symbols"][:10]]
                        )

                    # Nets and labels
                    if schematic_info.get("nets"):
                        system_prompt += f"\n- Nets: {', '.join(schematic_info['nets'][:8])}"
                    if schematic_info.get("labels"):
                        system_prompt += f"\n- Labels: {len(schematic_info['labels'])} net labels present"
        else:
            system_prompt += "\n- ⚠️ No schematic loaded"
            system_prompt += (
                "\n- Tell user: Go to Settings tab → Set project path to .kicad_pro or .kicad_sch file → Save Settings"
            )

        system_prompt += """

Rules:
- Get straight to the point - no introductions or conclusions
- Give actionable answers only - component specs, values, connections
- Use technical terminology - assume user knows electronics
- No phrases like "I can help", "Let me explain", "In summary"
- No asking for files/uploads - user has direct KiCad access
- When suggesting circuits: provide exact component values, part numbers, and pin connections
- Skip theoretical background unless specifically asked
- If schematic is loaded, analyze the ACTUAL components shown above
- Don't give generic instructions - give specific advice based on the loaded schematic"""

        # Get AI response
        from openai import OpenAI

        client = OpenAI(api_key=api_key)

        messages_to_send = [{"role": "system", "content": system_prompt}] + chat_history

        completion = client.chat.completions.create(model=chat_model, messages=messages_to_send)

        assistant_message = completion.choices[0].message.content
        chat_history.append({"role": "assistant", "content": assistant_message})

        print(f"[DEBUG] Got response: {assistant_message[:100]}...")

        # Save updated history
        _save_chat_history(chat_history)

        print("[DEBUG] Sending success response")
        return jsonify({"success": True, "user_message": message, "assistant_message": assistant_message})

    except Exception as e:
        print(f"[DEBUG] Error in send_chat: {e}")
        import traceback

        traceback.print_exc()
        return jsonify({"success": False, "message": str(e)})


@app.route("/", methods=["GET", "POST"])
def index():
    # Persist last used project folder in persistent file
    last_proj = _load_current_project()
    project = last_proj
    plan_json = None
    plan_obj: Optional[Plan] = None
    sch_name = None
    project_name = None
    recent_projects = _load_recent_projects()
    chat_history = _load_chat_history()

    # API key management
    api_key = _load_api_key()
    has_api_key = bool(api_key)
    api_key_masked = _mask_api_key(api_key) if api_key else ""

    # Model selection (hot-swappable)
    available_models = ["gpt-5", "gpt-5-mini", "gpt-5-nano"]
    chat_models = ["gpt-5-pro", "gpt-5", "gpt-5-mini", "gpt-5-nano"]
    current_model = request.form.get("model", os.getenv("OPENAI_MODEL", "gpt-5-mini"))
    current_chat_model = request.form.get("chat_model", os.getenv("OPENAI_CHAT_MODEL", "gpt-5"))

    # Try to detect schematic on initial page load
    if project:
        proj = Path(project).expanduser().resolve()
        if proj.exists():
            sch_path = _discover_schematic(proj)
            if sch_path:
                sch_name = sch_path.name
                project_name = sch_path.stem
                # Update project to be the .kicad_pro path if it was a directory
                if proj.is_dir():
                    pro_file = sch_path.with_suffix(".kicad_pro")
                    if pro_file.exists():
                        project = str(pro_file)

    if request.method == "POST":
        action = request.form.get("action")

        # Handle API key save action
        if action == "save_key":
            new_api_key = request.form.get("api_key", "").strip()
            if new_api_key and not new_api_key.startswith("sk-****"):
                _save_api_key(new_api_key)
                api_key = new_api_key
                has_api_key = True
                api_key_masked = _mask_api_key(api_key)
                flash("API key saved successfully", "success")
            else:
                flash("Please enter a valid API key", "error")
            return render_template(
                "index.html",
                project=project,
                recent_projects=recent_projects,
                available_models=available_models,
                current_model=current_model,
                chat_models=chat_models,
                current_chat_model=current_chat_model,
                has_api_key=has_api_key,
                api_key_masked=api_key_masked,
                project_name=project_name,
                sch_name=sch_name,
                chat_history=chat_history,
            )

        project = request.form.get("project") or project
        proj = Path(project).expanduser().resolve()
        sch_path = _discover_schematic(proj)
        if not sch_path:
            flash("No .kicad_sch found. Please select a valid .kicad_pro file or project folder.", "error")
            return render_template(
                "index.html",
                project=project,
                recent_projects=recent_projects,
                available_models=available_models,
                current_model=current_model,
                chat_models=chat_models,
                current_chat_model=current_chat_model,
                has_api_key=has_api_key,
                api_key_masked=api_key_masked,
                project_name=project_name,
                sch_name=sch_name,
                chat_history=chat_history,
            )
        sch_name = sch_path.name
        project_name = sch_path.stem

        # Update project to be the .kicad_pro path if it exists
        pro_file = sch_path.with_suffix(".kicad_pro")
        if pro_file.exists():
            project = str(pro_file)

        # Save to recent projects
        _save_recent_project(project, project_name)
        recent_projects = _load_recent_projects()

        if action == "chat":
            # Handle chat message
            chat_message = request.form.get("chat_message", "").strip()
            if chat_message:
                # Add user message to history
                chat_history.append({"role": "user", "content": chat_message})

                # Get AI response
                try:
                    from openai import OpenAI

                    client = OpenAI(api_key=api_key)

                    # Use the chat model selection
                    chat_model_to_use = current_chat_model

                    # Build system prompt with context
                    system_prompt = """You are an expert KiCad electronics engineer. Be CONCISE and FUNCTIONAL - no fluff or redundant explanations.

Current context:"""
                    if sch_name:
                        system_prompt += f"\n- Schematic: {sch_name}"
                        system_prompt += f"\n- Project: {project_name}"
                    else:
                        system_prompt += "\n- No schematic loaded yet."

                    system_prompt += """

Rules:
- Get straight to the point - no introductions or conclusions
- Give actionable answers only - component specs, values, connections
- Use technical terminology - assume user knows electronics
- No phrases like "I can help", "Let me explain", "In summary"
- No asking for files/uploads - user has direct KiCad access
- When suggesting circuits: provide exact component values, part numbers, and pin connections
- Skip theoretical background unless specifically asked"""

                    # Always prepend system message for context
                    messages_to_send = [{"role": "system", "content": system_prompt}] + chat_history

                    completion = client.chat.completions.create(model=chat_model_to_use, messages=messages_to_send)

                    assistant_message = completion.choices[0].message.content
                    chat_history.append({"role": "assistant", "content": assistant_message})

                    _save_chat_history(chat_history)
                    # Don't flash for chat to keep it more conversational
                except Exception as e:
                    flash(f"Chat error: {e}", "error")
        elif action == "clear_chat":
            # Clear chat history
            chat_history = []
            _save_chat_history(chat_history)
            flash("Chat history cleared", "success")
        elif action == "load_schematic":
            # Load schematic content and display it
            if sch_path:
                try:
                    doc = sch.Schematic(str(sch_path))
                    # You could display schematic info here
                    flash(f"Schematic loaded: {sch_name}", "success")
                except Exception as e:
                    flash(f"Failed to load schematic: {e}", "error")
            else:
                flash("No schematic detected. Configure project in Settings first.", "error")
        elif action == "detect":
            # Just detect and display - no other action needed
            flash(f"Detected schematic: {sch_name}", "success")
            _save_current_project(project)
        elif action == "launch":
            # Launch KiCad with the schematic
            if _launch_kicad(sch_path):
                flash(f"Launched KiCad with {sch_name}", "success")
            else:
                flash("Failed to launch KiCad. Please open the schematic manually.", "error")
            # Save last project choice
            _save_current_project(project)
        elif action == "plan":
            # Check API key before planning
            if not has_api_key:
                flash("API key required for AI features. Please save your OpenAI API key.", "error")
                return render_template(
                    "index.html",
                    project=project,
                    plan_json=plan_json,
                    sch_name=sch_name,
                    available_models=available_models,
                    current_model=current_model,
                    chat_models=chat_models,
                    current_chat_model=current_chat_model,
                    recent_projects=recent_projects,
                    has_api_key=has_api_key,
                    api_key_masked=api_key_masked,
                    project_name=project_name,
                    chat_history=chat_history,
                )

            prompt = request.form.get("prompt", "")

            # Hot-swap model selection and set API key
            # Warn if user selected gpt-5-pro for plan generation
            model_to_use = current_model
            if current_model == "gpt-5-pro":
                flash("Note: gpt-5-pro is only available for chat. Using gpt-5 for plan generation.", "warning")
                model_to_use = "gpt-5"

            os.environ["OPENAI_MODEL"] = model_to_use
            os.environ["OPENAI_API_KEY"] = api_key

            plan_result = plan_from_prompt(prompt)

            # Show planner diagnostics
            if plan_result.diagnostics:
                for d in plan_result.diagnostics:
                    level = "error" if d.severity == "error" else "warning" if d.severity == "warning" else "success"
                    msg = f"[{d.stage}] {d.message}"
                    if d.ref:
                        msg = f"{d.ref}: {msg}"
                    if d.suggestion:
                        msg += f" → {d.suggestion}"
                    flash(msg, level)

            plan_json = json.dumps(plan_result.plan.model_dump(by_alias=True), indent=2)
            # Save last project choice
            _save_current_project(str(proj))
        elif action == "apply":
            try:
                plan_json_str = request.form.get("plan_json", "{}")
                data = json.loads(plan_json_str)
                plan_obj = Plan.model_validate(data)
            except Exception as e:
                flash(f"Invalid plan JSON: {e}", "error")
                return render_template(
                    "index.html",
                    project=project,
                    plan_json=plan_json,
                    available_models=available_models,
                    current_model=current_model,
                    chat_models=chat_models,
                    current_chat_model=current_chat_model,
                    recent_projects=recent_projects,
                    has_api_key=has_api_key,
                    api_key_masked=api_key_masked,
                    project_name=project_name,
                    sch_name=sch_name,
                    chat_history=chat_history,
                )
            try:
                # Apply plan and run checks/exports
                original = sch_path.read_text(encoding="utf-8")
                doc = sch.Schematic(str(sch_path))
                result = apply_plan(doc, plan_obj)

                # Show diagnostics
                if result.diagnostics:
                    for d in result.diagnostics:
                        level = (
                            "error" if d.severity == "error" else "warning" if d.severity == "warning" else "success"
                        )
                        msg = f"[{d.stage}] {d.message}"
                        if d.ref:
                            msg = f"{d.ref}: {msg}"
                        if d.suggestion:
                            msg += f" (Suggestion: {d.suggestion})"
                        flash(msg, level)

                if not result.success:
                    flash("Plan application failed. See errors above.", "error")
                    return render_template(
                        "index.html",
                        project=project,
                        plan_json=plan_json,
                        sch_name=sch_name,
                        available_models=available_models,
                        current_model=current_model,
                        chat_models=chat_models,
                        current_chat_model=current_chat_model,
                        recent_projects=recent_projects,
                        has_api_key=has_api_key,
                        api_key_masked=api_key_masked,
                        project_name=project_name,
                        chat_history=chat_history,
                    )

                bak = sch_path.with_suffix(".kicad_sch.bak")
                bak.write_text(original, encoding="utf-8")
                doc.to_file(str(sch_path))
                run_erc(sch_path)
                export_netlist(sch_path)
                export_pdf(sch_path)
                flash(f"Plan applied successfully. Modified: {', '.join(result.affected_refs)}", "success")
            except Exception as e:
                flash(f"Apply failed: {e}", "error")

    return render_template(
        "index.html",
        project=project,
        plan_json=plan_json,
        sch_name=sch_name,
        available_models=available_models,
        current_model=current_model,
        chat_models=chat_models,
        current_chat_model=current_chat_model,
        recent_projects=recent_projects,
        has_api_key=has_api_key,
        api_key_masked=api_key_masked,
        project_name=project_name,
        chat_history=chat_history,
    )


def create_app() -> Flask:
    _configure_security(app)
    return app


def main():
    """Entry point for kaicad-web console script"""
    import argparse

    parser = argparse.ArgumentParser(description="kAIcad Web GUI")
    parser.add_argument("--serve", action="store_true", help="Production serve mode (requires secure secret)")
    parser.add_argument("--dev", action="store_true", help="Development mode (allows default secret)")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "5173")), help="Port to bind to")
    args = parser.parse_args()

    # Security check is now handled at app initialization
    if args.serve and not args.dev:
        print(f"[kAIcad Web] Starting in production mode on {args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=False)
    else:
        mode = "development (--dev)" if args.dev else "development (default)"
        print(f"[kAIcad Web] Starting in {mode} on http://{args.host}:{args.port}")
        app.run(host=args.host, port=args.port, debug=True)


if __name__ == "__main__":
    main()
