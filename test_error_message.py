"""
Quick test to demonstrate the improved error message for component creation.
Run this to see the helpful error message when Symbol.from_lib is not available.
"""

from pathlib import Path
from tempfile import TemporaryDirectory

from skip.eeschema import schematic as sch

from kaicad.core.planner import plan_from_prompt
from kaicad.core.writer import apply_plan

# Create a minimal test schematic
MINIMAL_SCHEMATIC = """(kicad_sch
  (version 20231120)
  (generator "eeschema")
  (uuid "00000000-0000-0000-0000-000000000000")
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)
"""

def test_component_creation_error():
    """Demonstrate the improved error message"""
    with TemporaryDirectory() as tmpdir:
        sch_path = Path(tmpdir) / "test.kicad_sch"
        sch_path.write_text(MINIMAL_SCHEMATIC)
        
        # Load schematic
        doc = sch.Schematic(str(sch_path))
        
        # Try to plan and apply - this will fail but with a helpful message
        print("=" * 80)
        print("Testing component creation (this will fail with helpful error message)")
        print("=" * 80)
        print()
        
        # Note: In real usage, you'd use plan_from_prompt() which requires OpenAI API
        # For this demo, we'll create a plan manually
        from kaicad.schema.plan import Plan
        
        plan = Plan(
            plan_version=1,
            ops=[
                {"op": "add_component", "ref": "D1", "symbol": "Device:LED", "value": "RED", "at": [100, 50]},
                {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80, 50]},
                {"op": "add_component", "ref": "C1", "symbol": "Device:C", "value": "100nF", "at": [120, 50]},
            ]
        )
        
        # Apply the plan
        result = apply_plan(doc, plan)
        
        # Display results
        print(f"\nResult: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Diagnostics: {len(result.diagnostics)} messages\n")
        
        for diag in result.diagnostics:
            symbol = "❌" if diag.severity == "error" else "⚠️" if diag.severity == "warning" else "ℹ️"
            print(f"{symbol} [{diag.stage}] {diag.ref or ''}: {diag.message}")
            if diag.suggestion:
                print(f"   💡 Suggestion: {diag.suggestion}")
            print()
        
        print("=" * 80)
        print("EXPLANATION:")
        print("=" * 80)
        print()
        print("The error message now clearly explains:")
        print("1. Why component creation fails (kicad-skip 0.2.5 limitation)")
        print("2. What the workaround is (add components manually in KiCad first)")
        print("3. What operations ARE supported (wiring, labels)")
        print()
        print("See docs/known-issues.md for detailed workarounds and examples.")
        print()

if __name__ == "__main__":
    test_component_creation_error()
