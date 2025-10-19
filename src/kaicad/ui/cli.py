import json
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table
from skip.eeschema import schematic as sch  # type: ignore

from kaicad.core.planner import plan_from_prompt
from kaicad.schema.plan import Plan
from kaicad.kicad.tasks import export_netlist, export_pdf, run_erc
from kaicad.core.writer import apply_plan

try:
    # Load environment from .env if present
    from dotenv import load_dotenv  # type: ignore

    load_dotenv()
except Exception:
    # Optional dependency; safe to continue without .env loading
    pass

console = Console()


def print_diagnostics(diagnostics):
    """Print diagnostics in a formatted table"""
    if not diagnostics:
        return

    table = Table(title="Diagnostics")
    table.add_column("Stage", style="cyan")
    table.add_column("Level", style="yellow")
    table.add_column("Ref", style="green")
    table.add_column("Message", style="white")
    table.add_column("Suggestion", style="blue")

    for d in diagnostics:
        level_style = "red" if d.severity == "error" else "yellow" if d.severity == "warning" else "green"
        table.add_row(
            d.stage, f"[{level_style}]{d.severity}[/{level_style}]", d.ref or "—", d.message, d.suggestion or "—"
        )

    console.print(table)


def apply_and_validate(sch_path: Path, plan: Plan, dry_run: bool = False):
    """Apply plan to schematic with validation and optional dry-run mode"""
    original = sch_path.read_text(encoding="utf-8")
    doc = sch.Schematic(str(sch_path))
    result = apply_plan(doc, plan)

    # Show diagnostics
    print_diagnostics(result.diagnostics)

    if not result.success:
        console.print("[red]Plan application failed with errors. Schematic not modified.[/red]")
        sys.exit(1)  # Exit with error code

    if dry_run:
        console.print("[yellow]DRY RUN: Changes not written to file.[/yellow]")
        console.print(f"[cyan]Would modify refs: {', '.join(result.affected_refs)}[/cyan]")
        return

    bak = sch_path.with_suffix(".kicad_sch.bak")
    bak.write_text(original, encoding="utf-8")
    doc.to_file(str(sch_path))

    console.print(f"[green]Applied plan successfully. Modified refs: {', '.join(result.affected_refs)}[/green]")
    run_erc(sch_path)
    export_netlist(sch_path)
    export_pdf(sch_path)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="kAIcad CLI - AI-powered KiCad schematic editor")
    parser.add_argument("--project", type=str, help="Project folder containing .kicad_sch file")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without applying changes")
    parser.add_argument("--prompt", type=str, help="Direct prompt for plan generation (non-interactive)")
    args = parser.parse_args()

    # Determine project folder
    if args.project:
        proj = Path(args.project).expanduser().resolve()
    else:
        proj = Path(Prompt.ask("Project folder")).expanduser().resolve()

    try:
        sch_path = next(proj.glob("*.kicad_sch"))
    except StopIteration:
        console.print("[red]No .kicad_sch found in the provided folder.[/red]")
        sys.exit(1)

    console.print(f"[cyan]Loaded schematic: {sch_path.name}[/cyan]")

    # Non-interactive mode with --prompt
    if args.prompt:
        plan_result = plan_from_prompt(args.prompt)

        if plan_result.diagnostics:
            console.print("\n[bold cyan]Planner Diagnostics:[/bold cyan]")
            print_diagnostics(plan_result.diagnostics)

        if plan_result.has_errors():
            console.print("[red]Plan generation failed with errors.[/red]")
            sys.exit(1)

        console.print("\n[bold]Generated Plan:[/bold]")
        console.print(json.dumps(plan_result.plan.model_dump(by_alias=True), indent=2))

        if not args.dry_run:
            if not Confirm.ask("Apply?", default=True):
                sys.exit(0)

        apply_and_validate(sch_path, plan_result.plan, dry_run=args.dry_run)
        sys.exit(0)

    # Interactive mode
    while True:
        cmd = Prompt.ask("[A]dd ops, [F]ix ERC (re-run), [Q]uit").strip().lower()
        if cmd == "q":
            break
        if cmd == "a":
            prompt = Prompt.ask("Describe change")
            plan_result = plan_from_prompt(prompt)

            # Show planner diagnostics first
            if plan_result.diagnostics:
                console.print("\n[bold cyan]Planner Diagnostics:[/bold cyan]")
                print_diagnostics(plan_result.diagnostics)

            if plan_result.has_errors():
                console.print("[red]Plan generation failed with errors.[/red]")
                continue

            # Show the plan
            console.print(json.dumps(plan_result.plan.model_dump(by_alias=True), indent=2))
            if Confirm.ask("Apply?"):
                apply_and_validate(sch_path, plan_result.plan, dry_run=args.dry_run)
        elif cmd == "f":
            run_erc(sch_path)
            console.print("[green]ERC re-run complete.[/green]")
        time.sleep(0.1)


if __name__ == "__main__":
    main()
