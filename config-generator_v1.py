# Copyright (c) 2026 Hiromasa Shikata
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import math
import os

class ConfigGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("SyringeGUI Config-Generator v1.0")
        self.root.geometry("670x850")
        self.root.resizable(True, True)

        self.axes = ["X", "Y", "Z"]
        self.sync_all = tk.BooleanVar(value=False)
        self.vars = {}

        for ax in self.axes:
            self.vars[ax] = {
                "mode": tk.StringVar(value="direct"),
                "step_angle": tk.StringVar(value="1.8"),
                "microstep": tk.StringVar(value="32"),
                "gear_ratio": tk.StringVar(value="1.0"),
                "pitch_mode": tk.StringVar(value="direct"),
                "pitch_direct": tk.StringVar(value="2.0"),
                "pitch_len": tk.StringVar(value="10.0"),
                "pitch_threads": tk.StringVar(value="5"),
                "calc_pitch_val": tk.StringVar(value="---"),
                "steps_mm_direct": tk.StringVar(value="6400"),
                "max_rate": tk.StringVar(value="200.0"),
                "accel": tk.StringVar(value="50.0"),
                "max_travel": tk.StringVar(value="130.0"),
                "invert": tk.BooleanVar(value=False),
                "calc_frame": None, 
                "dir_frame": None,
                "calc_result_label": None
            }

            keys_to_trace = [
                "step_angle", "microstep", "gear_ratio", "pitch_direct", 
                "pitch_len", "pitch_threads", "mode", "pitch_mode",
                "steps_mm_direct", "max_rate"
            ]
            for key in keys_to_trace:
                self.vars[ax][key].trace_add("write", lambda *args, a=ax: self.update_axis_mode_states(a))

        self.syringe_list = []
        self.sy_name = tk.StringVar()
        self.sy_vol = tk.StringVar()
        self.sy_len = tk.StringVar()

        self.create_widgets()
        
        
    def create_widgets(self):
        main_canvas = tk.Canvas(self.root)
        scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollable_frame = ttk.Frame(main_canvas)
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.notebook = ttk.Notebook(scrollable_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.tab_axes = ttk.Frame(self.notebook)   # Tab1
        self.tab_config = ttk.Frame(self.notebook) # Tab2
        self.notebook.add(self.tab_axes, text=" 1. Pump Settings ")
        self.notebook.add(self.tab_config, text=" 2. Syringe Registration & Save ")

        # UI for Tab1
        ttk.Label(self.tab_axes, text="     - This App can generate the config file(.JSON) for SyringeGUI.\n     - Setting information from existing config files can also be modified.").pack(pady=2, anchor="w")
        ttk.Button(self.tab_axes, text="Load Existing Config File", command=self.load_json).pack(pady=5)

        sync_frame = ttk.LabelFrame(self.tab_axes, text="Global Settings", padding=10)
        sync_frame.pack(fill="x", padx=10, pady=5)
        ttk.Checkbutton(sync_frame, text="Copy Pump X settings to Y and Z", variable=self.sync_all, command=self.handle_sync).pack(anchor="w")

        self.axis_frames = {}
        for ax in self.axes:
            f = ttk.LabelFrame(self.tab_axes, text=f"Pump {ax} Settings", padding=10)
            f.pack(fill="x", padx=10, pady=5)
            self.axis_frames[ax] = f
            self.build_axis_ui(ax, f)

        # UI for Tab2
        sy_frame = ttk.LabelFrame(self.tab_config, text="Syringe Database", padding=10)
        sy_frame.pack(fill="x", padx=10, pady=5)
        
        input_f = ttk.Frame(sy_frame)
        input_f.pack(fill="x")
        ttk.Label(input_f, text="Name:").grid(row=0, column=0)
        ttk.Entry(input_f, textvariable=self.sy_name, width=15).grid(row=0, column=1)
        ttk.Label(input_f, text="Vol (mL):").grid(row=0, column=2)
        ttk.Entry(input_f, textvariable=self.sy_vol, width=7).grid(row=0, column=3)
        ttk.Label(input_f, text="Len (mm):").grid(row=0, column=4)
        ttk.Entry(input_f, textvariable=self.sy_len, width=7).grid(row=0, column=5)
        
        btn_f = ttk.Frame(sy_frame)
        btn_f.pack(pady=5)
        ttk.Button(btn_f, text="Add Syringe", command=self.add_syringe).pack(side="left", padx=5)
        ttk.Button(btn_f, text="Delete Selected", command=self.delete_syringe).pack(side="left", padx=5)
        
        ttk.Button(self.tab_config, text="Genarate New Config File", command=self.save_json_as).pack(pady=20)
        
        self.sy_tree = ttk.Treeview(sy_frame, columns=("Vol", "Coeff"), height=8)
        self.sy_tree.heading("#0", text="Name")
        self.sy_tree.heading("Vol", text="Volume (mL)")
        self.sy_tree.heading("Coeff", text="Coeff (mL/mm)")
        self.sy_tree.column("#0", width=150)
        self.sy_tree.column("Vol", width=80)
        self.sy_tree.column("Coeff", width=100)
        self.sy_tree.pack(fill="x")

    def toggle_mode_frame(self, current_mode, target_frame, active_value):
        if active_value == "NONE":
            state = "disabled"
        else:
            state = "normal" if current_mode.get() == active_value else "disabled"
        
        for child in target_frame.winfo_children():
            try:
                self.set_state_recursive(child, state)
            except:
                pass

    def build_axis_ui(self, ax, frame):
        v = self.vars[ax]
        mode_frame = ttk.Frame(frame)
        mode_frame.pack(fill="x")
        
        update_cmd = lambda a=ax: self.update_axis_mode_states(a)
        
        ttk.Label(mode_frame, text="Choose a method to specify [Steps/mm] value.").pack(side="top", anchor="w")
        ttk.Radiobutton(mode_frame, text="Input Value      ", value="direct", variable=v["mode"], command=update_cmd).pack(side="left")
        ttk.Radiobutton(mode_frame, text="Calculate Value (Steps A-D)", value="calc", variable=v["mode"], command=update_cmd).pack(side="left")

        dir_frame = ttk.Frame(frame, padding=(20, 5, 5, 5))
        dir_frame.pack(fill="x")
        self.vars[ax]["dir_frame"] = dir_frame
        ttk.Entry(dir_frame, textvariable=v["steps_mm_direct"], width=10).grid(row=0, column=0)
        ttk.Label(dir_frame, text="Steps/mm").grid(row=0, column=1, sticky="w")

        
        calc_frame = ttk.Frame(frame, padding=(20, 5, 5, 5))
        calc_frame.pack(fill="x")
        self.vars[ax]["calc_frame"] = calc_frame
        
        ttk.Label(calc_frame, text="A. Step Angle of Stepper Motor:").grid(row=0, column=0, columnspan=2, sticky="w")
        for i, ang in enumerate(["0.9", "1.8", "18"]):
            ttk.Radiobutton(calc_frame, text=f"{ang}°", value=ang, variable=v["step_angle"]).grid(row=1, column=i, sticky="w")

        ttk.Label(calc_frame, text="B. Microstepping:").grid(row=2, column=0, columnspan=2, pady=(5,0), sticky="w")
        for i, microstep in enumerate(["1", "2", "4", "8", "16", "32", "64", "128"]):
            ttk.Radiobutton(calc_frame, text=f"1/{microstep}", value=microstep, variable=v["microstep"], width=12).grid(row=(3 if i<=3 else 4), column=(i if i<=3 else i-4), sticky="w")

        ttk.Label(calc_frame, text="C. Gear Ratio").grid(row=5, column=0, columnspan=2, pady=(5,0), sticky="w")
        ttk.Label(calc_frame, text="Motor : Screw = ").grid(row=6, column=0, sticky="e")
        ttk.Entry(calc_frame, textvariable=v["gear_ratio"], width=8, justify="right").grid(row=6, column=1, sticky="e")
        ttk.Label(calc_frame, text=" : 1    *e.g. 1:1 [no gear]; 5:1 planetary gear").grid(row=6, column=2, columnspan=2, sticky="w")

        ttk.Label(calc_frame, text="D. Lead Screw Pitch (mm/rotation):").grid(row=7, column=0, columnspan=2, pady=(5,0), sticky="w")
        ttk.Radiobutton(calc_frame, text="Input Value", value="direct", variable=v["pitch_mode"]).grid(row=8, column=0, columnspan=2, sticky="w")
        ttk.Entry(calc_frame, textvariable=v["pitch_direct"], width=8).grid(row=8, column=1, sticky="w")
        
        ttk.Radiobutton(calc_frame, text="Calculate Value", value="count", variable=v["pitch_mode"]).grid(row=9, column=0, columnspan=2, sticky="w")
        ttk.Label(calc_frame, text="Threads: ").grid(row=9, column=1, sticky="e")
        ttk.Entry(calc_frame, textvariable=v["pitch_threads"], width=8).grid(row=9, column=2, sticky="w")
        ttk.Label(calc_frame, text="Calculated val.").grid(row=9, column=3, sticky="w")
        ttk.Label(calc_frame, text="Length (mm): ").grid(row=10, column=1, sticky="e")
        ttk.Entry(calc_frame, textvariable=v["pitch_len"], width=8).grid(row=10, column=2, sticky="w")
        self.vars[ax]["calc_pitch_val"] = ttk.Label(calc_frame, text="---")
        self.vars[ax]["calc_pitch_val"].grid(row=10, column=3, sticky="w")
        
        ttk.Label(calc_frame, text="    *Count the number of screw threads within a specific length (mm).").grid(row=11, column=0, columnspan=4, sticky="w")

        self.vars[ax]["calc_result_label"] = ttk.Label(calc_frame, text="Calculated Steps/mm: ---")
        self.vars[ax]["calc_result_label"].grid(row=12, column=0, columnspan=4, pady=(5,0), sticky="w")
        self.update_axis_mode_states(ax)
        

        safe_frame = ttk.Frame(frame, padding=(0, 5, 0, 0))
        safe_frame.pack(fill="x")
        ttk.Label(safe_frame, text="Max Rate (mm/min):").grid(row=0, column=0, columnspan=2, sticky="w")
        ttk.Entry(safe_frame, textvariable=v["max_rate"], width=8).grid(row=0, column=2)
        ttk.Label(safe_frame, text="*Optimal: close to theoretical value").grid(row=0, column=3, sticky="w")
        
        ttk.Label(safe_frame, text="Accel (mm/sec^2):").grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Entry(safe_frame, textvariable=v["accel"], width=8).grid(row=1, column=2)
        ttk.Label(safe_frame, text="*Typical: 10~50").grid(row=1, column=3, sticky="w")
        
        ttk.Label(safe_frame, text="Max Travel distance (mm):").grid(row=2, column=0, columnspan=2, sticky="w")
        ttk.Entry(safe_frame, textvariable=v["max_travel"], width=8).grid(row=2, column=2)
        ttk.Label(safe_frame, text="*Distance that slider can move").grid(row=2, column=3, sticky="w")
        
        ttk.Checkbutton(safe_frame, text="Invert Direction without Wiring Modification  *Default: disabled", variable=v["invert"]).grid(row=3, column=0, columnspan=4, pady=(5,0), sticky="w")
        
        update_cmd()
        
    def update_axis_mode_states(self, ax):
        v = self.vars[ax]
        
        if self.sync_all.get() and ax != "X":
            self.toggle_mode_frame(v["mode"], v["calc_frame"], "NONE")
            self.toggle_mode_frame(v["mode"], v["dir_frame"], "NONE")
        else:
            self.toggle_mode_frame(v["mode"], v["calc_frame"], "calc")
            self.toggle_mode_frame(v["mode"], v["dir_frame"], "direct")

        pitch_val = self.calculate_pitch(ax)
        if "calc_pitch_val" in v:
            if pitch_val > 0:
                v["calc_pitch_val"].config(text=f"{pitch_val:.3f}", foreground="black" if v["mode"].get() == "calc" else "gray")
            else:
                v["calc_pitch_val"].config(text="---", foreground="black" if v["mode"].get() == "calc" else "gray")

        steps = self.calculate_steps(ax)
        
        if "calc_result_label" in v:
            if steps > 0:
                limit_20khz = 20000 * 60 / steps
                threshold = limit_20khz * 0.1
                
                result_text = f"Calculated Steps/mm: {steps:.3f}\n"
                result_text += f"Theoretical Max rate at 20 kHz (Arduino Uno): {limit_20khz:.1f} mm/min"
                
                try:
                    current_max = float(v["max_rate"].get())
                    if current_max > limit_20khz + threshold:
                        color = "red"
                        result_text += " [Max rate > Limit]"
                    elif current_max >= limit_20khz and current_max <= limit_20khz + threshold:
                        color = "green"
                        result_text += " [Max rate: Optimal]"
                    else:
                        color = "blue"
                        result_text += " [Max rate < Limit]"
                except:
                    color = "blue"

                v["calc_result_label"].config(text=result_text, foreground=color)
            else:
                v["calc_result_label"].config(text="Calculated Steps/mm: ---")
        
        pitch = self.calculate_pitch(ax)
        
        if  "calc_pitch_val" in v and v["calc_pitch_val"]:
            if pitch > 0:
                v["calc_pitch_val"].config(text=f"= {pitch:.3f}")
            else:
                v["calc_pitch_val"].config(text="---")

    def calculate_pitch(self, ax):
        v = self.vars[ax]
        try:
            if v["pitch_mode"].get() == "direct":
                return float(v["pitch_direct"].get())
            else:
                p_len = float(v["pitch_len"].get())
                p_threads = float(v["pitch_threads"].get())
                return p_len / p_threads if p_threads > 0 else 0.0
        except (ValueError, ZeroDivisionError):
            return 0.0

    def calculate_steps(self, ax):
        v = self.vars[ax]
        try:
            if v["mode"].get() == "calc":
                pitch = self.calculate_pitch(ax)
                    
                if pitch <= 0: return 0.0
                
                gear_ratio = float(v["gear_ratio"].get())
                angle = float(v["step_angle"].get())
                m_step = float(v["microstep"].get())
                
                steps = (360.0 / angle) * m_step * gear_ratio / pitch
                return steps
            else:
                val = v["steps_mm_direct"].get()
                return float(val) if val else 0.0
        except (ValueError, ZeroDivisionError):
            return 0.0

    def handle_sync(self):
        self.update_ui_states()
        for ax in self.axes:
            self.update_axis_mode_states(ax)

    def update_ui_states(self):
        sync_active = self.sync_all.get()
        for ax in self.axes:
            is_disabled = sync_active and (ax != "X")
            state_val = "disabled" if is_disabled else "normal"
            self.set_state_recursive(self.axis_frames[ax], state_val)

    def set_state_recursive(self, widget, state):
        try:
            widget.configure(state=state)
        except tk.TclError:
            pass
        
        for child in widget.winfo_children():
            self.set_state_recursive(child, state)

    def add_syringe(self):
        try:
            name = self.sy_name.get().strip()
            vol = float(self.sy_vol.get())
            length = float(self.sy_len.get())
            if not name:
                messagebox.showwarning("Warning", "Please enter a syringe name.")
                return
            coeff = vol / length
            self.syringe_list.append((name, vol, coeff))
            self.sy_tree.insert("", "end", text=name, values=(vol, f"{coeff:.8f}"))
            self.sy_name.set(""); self.sy_vol.set(""); self.sy_len.set("")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers.")
            
    def delete_syringe(self):
        selected_item = self.sy_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a syringe to delete.")
            return
        
        for item in selected_item:
            # Delete item from Treeview
            item_text = self.sy_tree.item(item, "text")
            self.sy_tree.delete(item)
            # Delete the item from self.syringe_list
            self.syringe_list = [s for s in self.syringe_list if s[0] != item_text]
            
    def save_json_as(self):
        if not self.syringe_list:
            if not messagebox.askyesno("Confirm", "Syringe database is empty. Do you want to proceed?"):
                return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile="config.json",  # Default file name
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration File"
        )
        
        if not file_path:
            return

        try:
            actual_filename = os.path.basename(file_path)
            invert_mask = 0
            res_settings = {}

            for i, ax in enumerate(self.axes):
                steps = self.calculate_steps(ax)
                v = self.vars[ax]
                
                res_settings[f"${100+i}"] = f"{steps:.3f}"
                res_settings[f"${110+i}"] = f"{v['max_rate'].get()}"
                res_settings[f"${120+i}"] = f"{v['accel'].get()}"
                res_settings[f"${130+i}"] = f"{v['max_travel'].get()}"
                
                # $3 setting
                if v["invert"].get():
                    invert_mask += (2**i)

            config_data = {
                "config_file_name": actual_filename,
                "_comment-syringe": "values = volume (mL) / syringe length (mm)",
                "syringes": {s[0]: s[2] for s in self.syringe_list},
                "_comment-grbl_settings": "values in $100-102, $110-112, $120-122, $130-132",
                "grbl_settings": {
                    **res_settings, 
                    "$3": str(invert_mask)
                }
            }

            # Save JSON file in the selected path
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
            
            messagebox.showinfo("Success", f"Configuration saved successfully to:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Save Error", f"An error occurred while saving:\n{e}")
            
    def load_json(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # load Syringe info
            self.syringe_list = []
            # Clear Treeview
            for item in self.sy_tree.get_children():
                self.sy_tree.delete(item)
            
            if "syringes" in data:
                for name, coeff in data["syringes"].items():
                    self.syringe_list.append((name, 0.0, coeff)) 
                    self.sy_tree.insert("", "end", text=name, values=("(imported)", f"{coeff:.8f}"))

            # Load GRBL settings
            if "grbl_settings" in data:
                gs = data["grbl_settings"]
                # $100-$102 (Steps/mm)
                for i, ax in enumerate(self.axes):
                    key = f"${100+i}"
                    if key in gs:
                        self.vars[ax]["mode"].set("direct")
                        self.vars[ax]["steps_mm_direct"].set(gs[key])
                    
                    # $110-$112 (Max rate)
                    key_rate = f"${110+i}"
                    if key_rate in gs: self.vars[ax]["max_rate"].set(gs[key_rate])
                    
                    # $120-$122 (Accel)
                    key_accel = f"${120+i}"
                    if key_accel in gs: self.vars[ax]["accel"].set(gs[key_accel])

                # $3 (Invert direction)
                if "$3" in gs:
                    mask = int(gs["$3"])
                    self.vars["X"]["invert"].set(bool(mask & 1))
                    self.vars["Y"]["invert"].set(bool(mask & 2))
                    self.vars["Z"]["invert"].set(bool(mask & 4))

            messagebox.showinfo("Success", "Config loaded successfully!")
            # Upadate UI
            for ax in self.axes: self.update_axis_mode_states(ax)

        except Exception as e:
            messagebox.showerror("Load Error", f"Could not read file: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ConfigGenerator(root)
    root.mainloop()