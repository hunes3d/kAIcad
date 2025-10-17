import json
import os
import threading
from pathlib import Path
from typing import Optional, List

try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv()
except Exception:
    pass

import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

from .schema import Plan
from .planner import plan_from_prompt
from .writer_skip import apply_plan
from .tasks import run_erc, export_netlist, export_pdf
from skip.eeschema import schematic as sch  # type: ignore
from .settings import Settings


def _discover_schematic(proj: Path) -> Optional[Path]:
    try:
        return next(proj.glob("*.kicad_sch"))
    except StopIteration:
        return None


class SidecarApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("kAIcad Sidecar")
        self.root.geometry("1100x760")

        # State
        self.settings = Settings.load()
        self.settings.apply_env()
        self.project_var = tk.StringVar(value=os.getenv("KAICAD_PROJECT", self.settings.default_project))
        self.sch_path: Optional[Path] = None
        self.attachments: List[str] = []

        # Top: Project selection and model selection
        top = tk.Frame(root)
        top.pack(fill=tk.X, padx=10, pady=10)
        # Settings button (top-left)
        tk.Button(top, text="⚙ Settings", command=self.open_settings).pack(side=tk.LEFT)
        
        # Model selection dropdown (hot-swappable)
        tk.Label(top, text="  Model:").pack(side=tk.LEFT, padx=(10, 0))
        self.model_var = tk.StringVar(value=self.settings.openai_model)
        model_options = [
            "gpt-5",
            "gpt-5-mini",
            "gpt-5-nano"
        ]
        self.model_dropdown = tk.OptionMenu(top, self.model_var, *model_options, command=self.on_model_change)
        self.model_dropdown.config(width=15)
        self.model_dropdown.pack(side=tk.LEFT, padx=6)
        
        tk.Label(top, text="  Project:").pack(side=tk.LEFT, padx=(10, 0))
        self.project_entry = tk.Entry(top, textvariable=self.project_var, width=50)
        self.project_entry.pack(side=tk.LEFT, padx=6)
        tk.Button(top, text="Browse", command=self.on_browse).pack(side=tk.LEFT)
        tk.Button(top, text="Detect", command=self.on_detect).pack(side=tk.LEFT, padx=6)

        self.sch_label_var = tk.StringVar(value="Detected schematic: —")
        tk.Label(root, textvariable=self.sch_label_var)
        self.sch_label = tk.Label(root, textvariable=self.sch_label_var)
        self.sch_label.pack(anchor="w", padx=12)

        # Middle: Prompt and Plan side by side
        mid = tk.Frame(root)
        mid.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        left = tk.Frame(mid)
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tk.Label(left, text="Describe change:").pack(anchor="w")
        self.prompt_text = scrolledtext.ScrolledText(left, height=10)
        self.prompt_text.pack(fill=tk.BOTH, expand=True)
        attach_row = tk.Frame(left)
        attach_row.pack(fill=tk.X, pady=4)
        tk.Button(attach_row, text="Attach files…", command=self.on_attach_files).pack(side=tk.LEFT)
        self.attach_label_var = tk.StringVar(value="No files attached")
        tk.Label(attach_row, textvariable=self.attach_label_var).pack(side=tk.LEFT, padx=6)
        tk.Button(left, text="Generate Plan", command=self.on_generate).pack(anchor="e", pady=6)

        right = tk.Frame(mid)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        tk.Label(right, text="Plan JSON:").pack(anchor="w")
        self.plan_text = scrolledtext.ScrolledText(right)
        self.plan_text.pack(fill=tk.BOTH, expand=True)
        apply_row = tk.Frame(right)
        apply_row.pack(fill=tk.X, pady=6)
        self.apply_btn = tk.Button(apply_row, text="Apply Plan + ERC/Netlist/PDF", command=self.on_apply)
        self.apply_btn.pack(side=tk.RIGHT)

        # Bottom: Logs and actions
        bottom = tk.Frame(root)
        bottom.pack(fill=tk.BOTH, expand=False, padx=10, pady=10)
        self.log = scrolledtext.ScrolledText(bottom, height=8, state=tk.DISABLED)
        self.log.pack(fill=tk.BOTH, expand=True)

        actions = tk.Frame(root)
        actions.pack(fill=tk.X, padx=10, pady=(0, 10))
        tk.Button(actions, text="Re-run ERC", command=self.on_rerun_erc).pack(side=tk.LEFT)

        # Initial detect and docking
        self.on_detect()
        self.dock_right()

    def logln(self, msg: str):
        self.log.configure(state=tk.NORMAL)
        self.log.insert(tk.END, msg + "\n")
        self.log.configure(state=tk.DISABLED)
        self.log.see(tk.END)

    def on_browse(self):
        folder = filedialog.askdirectory(initialdir=self.project_var.get() or str(Path.cwd()))
        if folder:
            self.project_var.set(folder)
            os.environ["KAICAD_PROJECT"] = folder
            self.on_detect()

    def on_detect(self):
        proj = Path(self.project_var.get()).expanduser().resolve()
        sch = _discover_schematic(proj)
        self.sch_path = sch
        if sch:
            self.sch_label_var.set(f"Detected schematic: {sch.name}")
            self.logln(f"Loaded schematic: {sch}")
        else:
            self.sch_label_var.set("Detected schematic: —")
            self.logln("No .kicad_sch found in the provided folder.")
    
    def on_model_change(self, selected_model: str):
        """Hot-swap the model selection"""
        os.environ["OPENAI_MODEL"] = selected_model
        self.logln(f"Switched to model: {selected_model}")

    def on_generate(self):
        prompt = self.prompt_text.get("1.0", tk.END).strip()
        if not prompt:
            messagebox.showinfo("kAIcad", "Please enter a prompt.")
            return

        def worker():
            try:
                # Use the currently selected model from dropdown (hot-swappable)
                current_model = self.model_var.get()
                os.environ["OPENAI_MODEL"] = current_model
                self.root.after(0, lambda: self.logln(f"Generating plan with {current_model}..."))
                
                enriched = prompt
                if self.attachments:
                    previews = []
                    for p in self.attachments[:5]:
                        try:
                            text = Path(p).read_text(encoding="utf-8", errors="ignore")
                            text = text[:2000]
                            previews.append(f"--- file: {Path(p).name} ---\n{text}")
                        except Exception:
                            previews.append(f"--- file: {Path(p).name} ---\n<unreadable>")
                    enriched += "\n\nAttached files (previews):\n" + "\n\n".join(previews)
                self.set_busy(True)
                plan_result = plan_from_prompt(enriched)
                
                # Log planner diagnostics
                if plan_result.diagnostics:
                    for d in plan_result.diagnostics:
                        level_str = d.severity.upper()
                        ref_str = f"[{d.ref}] " if d.ref else ""
                        msg = f"[{d.stage}] {level_str}: {ref_str}{d.message}"
                        if d.suggestion:
                            msg += f" → {d.suggestion}"
                        self.root.after(0, lambda m=msg: self.logln(m))
                
                self.root.after(0, lambda: self.plan_text_replace(json.dumps(plan_result.plan.model_dump(), indent=2)))
                self.root.after(0, lambda: self.logln("Plan generated."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("kAIcad", f"Plan generation failed: {e}"))
            finally:
                self.root.after(0, lambda: self.set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def plan_text_replace(self, text: str):
        self.plan_text.delete("1.0", tk.END)
        self.plan_text.insert("1.0", text)

    def on_apply(self):
        if not self.sch_path:
            messagebox.showwarning("kAIcad", "No schematic detected. Choose a project folder with a .kicad_sch.")
            return
        try:
            data = json.loads(self.plan_text.get("1.0", tk.END))
            plan = Plan.model_validate(data)
        except Exception as e:
            messagebox.showerror("kAIcad", f"Invalid plan JSON: {e}")
            return

        self.apply_btn.configure(state=tk.DISABLED)

        def worker():
            try:
                self.root.after(0, lambda: self.set_busy(True))
                original = self.sch_path.read_text(encoding="utf-8")
                doc = sch.Schematic(str(self.sch_path))
                result = apply_plan(doc, plan)
                
                # Log diagnostics
                for d in result.diagnostics:
                    level = "ERROR" if d.severity == "error" else "WARN" if d.severity == "warning" else "INFO"
                    ref_str = f"[{d.ref}] " if d.ref else ""
                    msg = f"[{d.stage}] {level}: {ref_str}{d.message}"
                    if d.suggestion:
                        msg += f" → {d.suggestion}"
                    self.root.after(0, lambda m=msg: self.logln(m))
                
                if not result.success:
                    self.root.after(0, lambda: messagebox.showerror("kAIcad", "Plan application failed. See log for details."))
                    return
                
                bak = self.sch_path.with_suffix(".kicad_sch.bak")
                bak.write_text(original, encoding="utf-8")
                doc.to_file(str(self.sch_path))
                self.root.after(0, lambda: self.logln(f"Applied plan. Modified: {', '.join(result.affected_refs)}"))
                self.root.after(0, lambda: self.logln("Running ERC/Netlist/PDF..."))
                run_erc(self.sch_path)
                export_netlist(self.sch_path)
                export_pdf(self.sch_path)
                self.root.after(0, lambda: self.logln("Done. ERC report, netlist, and PDF generated."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("kAIcad", f"Apply failed: {e}"))
            finally:
                self.root.after(0, lambda: self.apply_btn.configure(state=tk.NORMAL))
                self.root.after(0, lambda: self.set_busy(False))

        threading.Thread(target=worker, daemon=True).start()

    def on_rerun_erc(self):
        if not self.sch_path:
            messagebox.showwarning("kAIcad", "No schematic detected.")
            return

        def worker():
            try:
                self.root.after(0, lambda: self.logln("Re-running ERC..."))
                run_erc(self.sch_path)
                self.root.after(0, lambda: self.logln("ERC re-run complete."))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("kAIcad", f"ERC failed: {e}"))

        threading.Thread(target=worker, daemon=True).start()

    # QoL: dock to right of screen if enabled
    def dock_right(self):
        if not self.settings.dock_right:
            return
        try:
            self.root.update_idletasks()
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            x = sw - w - 40
            y = 40
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        except Exception:
            pass

    def on_attach_files(self):
        files = filedialog.askopenfilenames(title="Select files to attach", initialdir=self.project_var.get())
        if files:
            self.attachments = list(files)
            if len(self.attachments) > 3:
                shown = ", ".join(Path(p).name for p in self.attachments[:3]) + f" +{len(self.attachments)-3} more"
            else:
                shown = ", ".join(Path(p).name for p in self.attachments)
            self.attach_label_var.set(shown)
            self.logln(f"Attached {len(self.attachments)} file(s)")

    def set_busy(self, busy: bool):
        try:
            if busy:
                self.root.config(cursor="watch")
            else:
                self.root.config(cursor="")
            self.root.update_idletasks()
        except Exception:
            pass

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("420x320")

        def row(lbl: str):
            f = tk.Frame(win)
            f.pack(fill=tk.X, padx=10, pady=6)
            tk.Label(f, text=lbl, width=16, anchor="w").pack(side=tk.LEFT)
            return f

        r1 = row("OpenAI API Key")
        key_var = tk.StringVar(value=self.settings.openai_api_key)
        key_entry = tk.Entry(r1, textvariable=key_var, show="•", width=40)
        key_entry.pack(side=tk.LEFT)

        r2 = row("Model")
        model_var = tk.StringVar(value=self.settings.openai_model)
        model_entry = tk.Entry(r2, textvariable=model_var, width=40)
        model_entry.pack(side=tk.LEFT)

        r3 = row("Temperature")
        temp_var = tk.StringVar(value=str(self.settings.openai_temperature))
        temp_entry = tk.Entry(r3, textvariable=temp_var, width=10)
        temp_entry.pack(side=tk.LEFT)

        r4 = row("Dock Right")
        dock_var = tk.BooleanVar(value=self.settings.dock_right)
        tk.Checkbutton(r4, variable=dock_var).pack(side=tk.LEFT)

        r5 = row("Default Project")
        proj_var = tk.StringVar(value=self.project_var.get())
        proj_entry = tk.Entry(r5, textvariable=proj_var, width=40)
        proj_entry.pack(side=tk.LEFT)
        tk.Button(r5, text="Browse", command=lambda: proj_var.set(filedialog.askdirectory(initialdir=proj_var.get() or str(Path.cwd())) or proj_var.get())).pack(side=tk.LEFT, padx=6)

        # Test KiCad CLI button
        def test_kicad_cli():
            import subprocess
            try:
                result = subprocess.run(["kicad-cli", "--version"], capture_output=True, text=True, timeout=3)
                if result.returncode == 0:
                    messagebox.showinfo("KiCad CLI Test", f"✓ KiCad CLI found!\nVersion: {result.stdout.strip()}")
                else:
                    messagebox.showerror("KiCad CLI Test", f"✗ KiCad CLI error:\n{result.stderr}")
            except FileNotFoundError:
                messagebox.showerror("KiCad CLI Test", "✗ kicad-cli not found in PATH.\n\nAdd KiCad bin directory to your system PATH.")
            except Exception as e:
                messagebox.showerror("KiCad CLI Test", f"✗ Test failed:\n{e}")

        test_frame = tk.Frame(win)
        test_frame.pack(fill=tk.X, padx=10, pady=6)
        tk.Button(test_frame, text="Test KiCad CLI", command=test_kicad_cli).pack()

        btns = tk.Frame(win)
        btns.pack(fill=tk.X, padx=10, pady=10)
        def save_and_close():
            try:
                self.settings.openai_api_key = key_var.get().strip()
                self.settings.openai_model = model_var.get().strip() or self.settings.openai_model
                self.settings.openai_temperature = float(temp_var.get()) if temp_var.get() else 0.0
                self.settings.dock_right = bool(dock_var.get())
                self.settings.default_project = proj_var.get().strip() or self.settings.default_project
                self.settings.save()
                self.settings.apply_env()
                os.environ["KAICAD_PROJECT"] = self.settings.default_project
                self.project_var.set(self.settings.default_project)
                self.dock_right()
                messagebox.showinfo("kAIcad", "Settings saved.")
                win.destroy()
            except Exception as e:
                messagebox.showerror("kAIcad", f"Failed to save settings: {e}")
        tk.Button(btns, text="Save", command=save_and_close).pack(side=tk.RIGHT)
        tk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=6)


def main():
    root = tk.Tk()
    SidecarApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
