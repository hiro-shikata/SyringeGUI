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
from tkinter import ttk, filedialog, messagebox
import serial
from serial.tools import list_ports
import time
import threading
import datetime
import re
import csv
import math
import json
import os


# =========================
## Version info
# =========================
def show_version_info():
    messagebox.showinfo(
        "About SyringeGUI",
        "SyringeGUI v2.4.1\n\n"
        "This software is released under the MIT License.\n\n"
        "Copyright (c) 2026 \n Hiromasa Shikata"
    )


# =========================
## Setup - making folder to save Log and CSV files
# =========================
data_base_dir = os.path.expanduser("~/SyringeGUI_Data/CONFIG")
if not os.path.exists(data_base_dir):
    os.makedirs(data_base_dir)
CONFIG_LOG = os.path.join(data_base_dir, "last_config.txt") # Config log recording the latest used JOSON file
DEFAULT_JSON = "default_config.json"   # Default config file

save_dir = os.path.expanduser("~/SyringeGUI_Data")
current_csv_filename = None
current_config_path = DEFAULT_JSON

# Loading the last session log to set directoryf
if os.path.exists(CONFIG_LOG):
    try:
        with open(CONFIG_LOG, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if len(lines) >= 3:
                save_dir = lines[2]
    except Exception as e:
        print(f"Early config read error: {e}")

# Fix the directory for saving Log
session_log_dir = save_dir 
current_time = datetime.datetime.now().strftime('%Y%m%d_%H%M%S') # order: year month day
log_filename = os.path.join(session_log_dir, f"pump_log_{current_time}.txt")

# Settings for CSV & Log files
def select_save_directory():
    global save_dir, dir_label_var
    selected = filedialog.askdirectory(initialdir=save_dir, title="Select Location to Save CSV & Log Files.")
    if selected:
        save_dir = selected
        
        if 'dir_label_var' in globals() and dir_label_var:
            dir_label_var.set(f"CSV Save Dir: {save_dir}\nLog Save Dir (Fixed): {session_log_dir}")
            
        print(f"Save directory changed to: {save_dir}")
        log(f">> Save directory changed to: {save_dir}")
        save_last_session_info()
        
        messagebox.showinfo(
            "Save Directory Changed", 
            f"Save directory for CSV file imediately changed to {save_dir},\n"
            f"while Log file is still stored in the last directory.\n"
            f"Restart is required for applying the settings to Log."
        )
        
        dir_label_var.set(f"Current Directory:\n {save_dir}")
        print(f"Save directory changed to: {save_dir}")
        log(f">>Save directory changed to: {save_dir}")
        messagebox.showinfo("Save Directory Changed", f"Save Directory changed to:\n{save_dir}")
        init_csv_file()
        save_last_session_info()


def init_csv_file():
    global current_csv_filename, dir_label_var
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    current_csv_filename = os.path.join(save_dir, f"experiment_settings_{current_time}.csv")
    
    try:
        with open(current_csv_filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Timestamp", "Pump", "Syringe", "Flow_(uL/min)", "Start (sec)", "End (sec)", "Duration (sec)"])
        log(f">> New CSV file created at: {current_csv_filename}")
    except Exception as e:
        print(f"CSV Init Error: {e}")


def log_to_csv(axis, syringe, flow, t_start, t_end, duration):
    global current_csv_filename
    if current_csv_filename is None or not os.path.exists(current_csv_filename):
        init_csv_file()
       
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open(current_csv_filename, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([now, axis, syringe, flow, t_start, t_end, duration])
    except Exception as e:
        print(f"CSV Append Error: {e}")

# Settings for Log file
log_filename = os.path.join(session_log_dir, f"pump_log_{current_time}.txt")


# =========================
## Global Settings
# =========================

# Default Grbl settings in app, if not selected a new config file.
DEFAULT_CONFIG = {
    "config_file_name": "Internal_Default",
    "syringes": {
        "1 mL (Zelostat)": 0.01769912,
        "2.5 mL (Terumo)": 0.06313131,
        "10 mL (Terumo)": 0.195503421
    },
    "grbl_settings": {
        "$1": "255", "$3": "0",
        "$100": "6400", "$101": "6400", "$102": "6400",
        "$110": "250.000", "$111": "250.000", "$112": "250.000",
        "$120": "50.000",   "$121": "50.000",   "$122": "50.000",
        "$130": "130.000", "$131": "130.000", "$132": "130.000"
    }
}

# Default settings for limitation
TOTAL_MAX_HZ = 20000.0 # Practical limitation of steps/sec generated by Arduino Uno/Nano
STEPS_PER_MM = 6398.537 # software default
AUTO_LIMIT_MM_MIN = 187.5 # software default

def update_machine_limits():
    global STEPS_PER_MM, AUTO_LIMIT_MM_MIN

    # Get info of $100 (steps/mm) from JSON file
    settings = current_config.get("grbl_settings", {})
    STEPS_PER_MM = float(settings.get("$100", 6398.537))
    
    # rate(mm/min) = (Hz * 60) / steps_per_mm
    AUTO_LIMIT_MM_MIN = (TOTAL_MAX_HZ * 60) / STEPS_PER_MM
    
    log(f">> [Safety] Dynamic Limit calculated: {AUTO_LIMIT_MM_MIN:.2f} mm/min (at 20kHz)")


# =========================
# Global values
# =========================
SYRINGES = {}

ser_lock = threading.Lock()

raw_recipe = []

mx_raw = 0.0
my_raw = 0.0
mz_raw = 0.0
saved_offset_x = 0.0
saved_offset_y = 0.0
saved_offset_z = 0.0
current_wpos_x = 0.0
current_wpos_y = 0.0
current_wpos_z = 0.0
canvas_x = None
canvas_y = None

axis_map = {}

# Unit option and Conversion
FLOW_UNIT_OPTIONS = ["µL/min", "µL/sec", "mL/min"]
FLOW_UNIT_CONV = {
    "µL/min": 1.0,
    "µL/sec": 60.0,    # 1 µL/sec = 60 µL/min
    "mL/min": 1000.0   # 1 mL/min = 1000 µL/min
}

DUR_UNIT_OPTIONS = ["sec", "min", "hr"]
DUR_UNIT_CONV = {
    "sec": 1.0,
    "min": 60.0,
    "hr": 3600.0
}

VOL_UNIT_OPTIONS = ["µL", "mL"]
VOL_UNIT_CONV = {
    "µL": 1.0,
    "mL": 1000.0
}


def handle_flow_unit_change(axis):
    info = axis_map.get(axis)
    if not info:
        return
        
    entry = info["flow_entry"]
    old_unit = info["last_flow_unit"]
    new_unit = info["flow_unit"].get()

    try:
        current_val = float(entry.get())
        val_in_ul_min = current_val * FLOW_UNIT_CONV[old_unit]
        new_val = val_in_ul_min / FLOW_UNIT_CONV[new_unit]
        
        entry.delete(0, tk.END)
        entry.insert(0, f"{new_val:.3f}")
        
        info["last_flow_unit"] = new_unit
        
    except (ValueError, KeyError):
        info["last_flow_unit"] = new_unit


def handle_duration_unit_change(axis):
    info = axis_map.get(axis)
    if not info:
        return
        
    entry = info["time_entry"]
    old_unit = info["last_dur_unit"]
    new_unit = info["dur_unit"].get()

    try:
        current_val = float(entry.get())
        val_in_sec = current_val * DUR_UNIT_CONV[old_unit]
        new_val = val_in_sec / DUR_UNIT_CONV[new_unit]
        
        entry.delete(0, tk.END)
        entry.insert(0, f"{new_val:.2f}")
        
        info["last_dur_unit"] = new_unit
        
    except (ValueError, KeyError):
        info["last_dur_unit"] = new_unit


def handle_vol_unit_change(axis):
    info = axis_map.get(axis)
    if not info:
        return
    entry = info["vol_entry"]
    old_unit = info["last_vol_unit"]
    new_unit = info["vol_unit"].get()

    try:
        current_val = float(entry.get())
        val_in_ul = current_val * VOL_UNIT_CONV[old_unit]
        new_val = val_in_ul / VOL_UNIT_CONV[new_unit]
        
        entry.delete(0, tk.END)
        entry.insert(0, f"{new_val:.3f}")
        
        info["last_vol_unit"] = new_unit
        
    except (ValueError, KeyError):
        info["last_vol_unit"] = new_unit


# Store info on PATH for the latest JSON file and PORT in "last_config.txt".
def save_last_session_info():
    try:
        with open(CONFIG_LOG, "w", encoding="utf-8") as f:
            # Use DEFAULT_JSON, If current_config_path is empty
            path_to_save = current_config_path if current_config_path else DEFAULT_JSON
            f.write(f"{path_to_save}\n{port_var.get()}\n{save_dir}")
    except Exception as e:
        print(f"Failed to save session: {e}")

# Get the latest path. If no path, return the default.
def get_last_config_path():
    if os.path.exists(CONFIG_LOG):
        with open(CONFIG_LOG, "r", encoding="utf-8") as f:
            line = f.readline().strip()
            if os.path.exists(line):
                return line
    return DEFAULT_JSON
    
def load_initial_config():
    global current_config, SYRINGES, current_config_path, config_name_var, dir_label_var, save_dir
    last_port = ""
    current_config_path = DEFAULT_JSON
    
    if os.path.exists(CONFIG_LOG):
        try:
            with open(CONFIG_LOG, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
                if len(lines) >= 1:
                    current_config_path = lines[0]
                if len(lines) >= 2:
                    last_port = lines[1]
                if len(lines) >= 3:
                    save_dir = lines[2]
#                    log(f">> Last Save Directory Selected: {save_dir}")
                    if 'dir_label_var' in globals() and dir_label_var:
                        dir_label_var.set(f"Current Directory:\n {save_dir}")
                    
        except Exception as e:
            print(f"Error reading last_config: {e}")
    
    # Load JSON file
    target_json = current_config_path if current_config_path else DEFAULT_JSON
    if os.path.exists(target_json):
        try:
            with open(target_json, "r", encoding="utf-8") as cf:
                current_config = json.load(cf)
                update_machine_limits()
                SYRINGES = current_config.get("syringes", DEFAULT_CONFIG["syringes"])
                fname = current_config.get("config_file_name", "Unknown")
                if 'config_name_var' in globals() and config_name_var:
                    config_name_var.set(fname)
                log(f">> Config settings loaded: {target_json}")
                
        # If the JSON is broken, use the default settings.
        except Exception:
                current_config = DEFAULT_CONFIG
                SYRINGES = current_config["syringes"]
    # If the JSON is not available, use the default settings.
    else:
        current_config = DEFAULT_CONFIG
        SYRINGES = current_config["syringes"]
    
    return last_port

#init_csv_file()
load_initial_config()

def update_syringe_list():
    syringe_names = list(SYRINGES.keys())
    
    for axis, info in axis_map.items():
        try:
            combo = info.get("syringe_combo")
            if combo:
                combo['values'] = syringe_names
                if info["syringe"].get() not in syringe_names:
                    info["syringe"].set(syringe_names[0])
        except Exception as e:
            print(f"Error updating syringe list for Pump {axis}: {e}")

def select_config_file():
    global current_config, SYRINGES, current_config_path
    file_path = filedialog.askopenfilename(
        title="Select Configuration File",
        filetypes=[("JSON files", "*.json")]
    )
    
    if file_path:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                new_config = json.load(f)
            
            current_config = new_config
            
            update_machine_limits()
            
            SYRINGES = current_config["syringes"]
            current_config_path = file_path
            save_last_session_info()
            
            # Refresh display of UI and tabs
            config_name_var.set(current_config.get("config_file_name", file_path.split("/")[-1]))
            
            update_syringe_list()
            refresh_settings_tab_list()

            messagebox.showinfo("Success", f"Loaded: {config_name_var.get()}")
            log(f">> Switched config to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {e}")


# Refresh the syringe lists in the tab
def refresh_settings_tab_list():
    try:
        for widget in syringe_list_frame.winfo_children():
            widget.destroy()
        
        for name, coeff in SYRINGES.items():
            ttk.Label(syringe_list_frame, text=f"{name}: {coeff}").pack(anchor="w")
            
        log(">> Settings tab syringe list refreshed.")
    except (NameError, tk.TclError):
        pass

# Synchronize Grbl settings according to JSON file
def sync_hardware_settings():
    if not ser or not ser.is_open:
        messagebox.showwarning("Warning", "Please connect to Serial first!")
        return
    
    if messagebox.askyesno("Confirm", "Write settings to Grbl EEPROM?"):
        log(">> Starting Hardware Sync...")
        grbl_dict = current_config.get("grbl_settings", {})
        
        for param, value in grbl_dict.items():
            cmd = f"{param}={value}"
            send(cmd)
            time.sleep(0.1)
            
        log(">> Hardware Sync Completed.")
        messagebox.showinfo("Success", "Grbl settings updated!")

# serial connection
def detect_serial_ports():
    ports = list_ports.comports()
    return [p.device for p in ports]

ser = None
ser_lock = threading.Lock()
connect_button = None

def connect_serial():
    global ser, connect_button
    port = port_var.get()
    baudrate = int(baud_var.get())
    
    if 'connect_button' not in globals() or connect_button is None:
        pass

    try:
        ser = serial.Serial(port, baudrate, timeout=0.5)
        time.sleep(2)
        ser.flushInput()
        
        save_last_session_info()
        
        log(f">> Connected to {port} at {baudrate} baud")
        
        if 'connect_button' in globals() and connect_button is not None:
            connect_button.config(state="disabled")
        
    except Exception as e:
        log(f">> Connection failed: {e}")
        
    if ser in globals() and ser.is_open:
        fname = current_config.get("config_file_name", "Unknown")
        log(f">> Connected. Configuration '{fname}' is ready to sync.")


# Browse recipe for programmed movement
def browse_recipe():
    global raw_recipe
    file_path = filedialog.askopenfilename(
        title="Please select a recipe file",
        filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt")]
    )
    
    if file_path:
        try:
            temp_recipe = []
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"): continue
                    
                    clean_line = line.replace("(", "").replace(")", "").replace('"', "").replace("'", "")
                    row = clean_line.split(",")
                    
                    if len(row) < 4: continue
                    
                    axis = row[0].strip().upper()
                    start = float(row[1])
                    end = float(row[2])
                    flow = float(row[3])
                    temp_recipe.append((axis, start, end, flow))
            
            raw_recipe = temp_recipe
            
            for i in tree.get_children():
                tree.delete(i)
            
            for r in raw_recipe:
                tree.insert("", "end", values=r)
            
            recipe_label.config(text=f"Selected: {file_path.split('/')[-1]}")
            log(f">> Success: {len(raw_recipe)} steps loaded.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Loading failed: {e}")

        update_recipe_graph(raw_recipe)
            
            
# Illustrate recipe
def update_recipe_graph(recipe_data=None):
    global canvas_x, canvas_y, canvas_z, raw_recipe
    canvas_x = globals().get("canvas_x")
    canvas_y = globals().get("canvas_y")
    canvas_z = globals().get("canvas_z")

    if canvas_x is None or canvas_y is None or canvas_z is None:
        return

    canvas_x.delete("all")
    canvas_y.delete("all")
    canvas_z.delete("all")

    if not raw_recipe:
        return

    max_time = max([row[2] for row in raw_recipe]) if raw_recipe else 1
    
    max_flow = max([abs(row[3]) for row in raw_recipe]) if raw_recipe else 1
    if max_flow == 0: max_flow = 1

    def calculate_total_volumes(recipe):
        vols = {"X": 0.0, "Y": 0.0, "Z": 0.0}
        
        for axis, start, end, flow in recipe:
            duration = end - start
            v_ml = (flow * (duration / 60.0)) / 1000.0
            if axis in vols:
                vols[axis] += v_ml
        return vols["X"], vols["Y"], vols["Z"]

    vol_x, vol_y, vol_z = calculate_total_volumes(raw_recipe)

    w, h = 250, 30 
    center_h = h / 2
    margin_w = 7
    margin_h = 5

    def draw_axis_graph(canvas, axis_name, color, total_vol):
        canvas.create_line(margin_w - 1, h - 2, margin_w - 1, 2, 
                        fill="black", width=1)

        canvas.create_text(margin_w - 1, 5, text="+", anchor="e", font=("Arial", 8))
        canvas.create_text(margin_w - 1, center_h, text="0", anchor="e", font=("Arial", 8))
        canvas.create_text(margin_w - 1, h - 5, text="-", anchor="e", font=("Arial", 8))

        canvas.create_line(margin_w, center_h, w - 5, center_h, fill="black", width=1)
        
        for row in raw_recipe:
            axis, start, end, flow = row
            if axis == axis_name:
                x_start = margin_w + (start / max_time) * (w - margin_w - 5)
                x_end = margin_w + (end / max_time) * (w - margin_w - 5)
                
                y_flow = center_h - (flow / max_flow) * (center_h - margin_h)
                
                canvas.create_rectangle(x_start, center_h, x_end, y_flow, 
                                         fill=color, outline=color, stipple="gray50")
                canvas.create_line(x_start, y_flow, x_end, y_flow, fill=color, width=2)
                
        canvas.create_text(245, 30, text=f"Total: {total_vol:.3f} mL", 
                           anchor="se", font=("Arial", 12, "bold"), fill="black")

    draw_axis_graph(canvas_x, "X", "magenta", vol_x)
    draw_axis_graph(canvas_y, "Y", "cyan", vol_y)
    draw_axis_graph(canvas_z, "Z", "orange", vol_z)


# =========================
## UI Settings
# =========================
root = tk.Tk()
root.title("SyringeGUI")

font_ui = ("Arial", 12)
style = ttk.Style()
style.configure(".", font=("Arial", 12))
style.configure("TNotebook.Tab", font=("Arial, 14"))
style.configure("TLabelframe.Label", font=("Arial", 14))


notebook = ttk.Notebook(root)
notebook.pack(expand=True, fill="both")

tab_manual = ttk.Frame(notebook, padding=10)
tab_programmed = ttk.Frame(notebook, padding=10)
tab_settings = ttk.Frame(notebook, padding=10)

notebook.add(tab_manual, text=" Manual Control ")
notebook.add(tab_programmed, text=" Programmed Control ")
notebook.add(tab_settings, text=" Settings ")

position_var_x = tk.StringVar(value="0.000 mm")
position_var_y = tk.StringVar(value="0.000 mm")
position_var_z = tk.StringVar(value="0.000 mm")

volume_var_x = tk.StringVar(value="0.0 µL")
volume_var_y = tk.StringVar(value="0.0 µL")
volume_var_z = tk.StringVar(value="0.0 µL")

status_var = tk.StringVar()
elapsed_time_var = tk.StringVar(value="Elapsed time: 00:00.0")

# UI for Manual tab
# Frame settings
upper_frame = ttk.Frame(tab_manual)
bottom_frame = ttk.Frame(tab_manual)
upper_frame.pack(side="top", fill="x", anchor="n")
bottom_frame.pack(side="bottom", fill="both", expand=True)


frame_control = ttk.LabelFrame(bottom_frame, text="Control", labelanchor = "n", padding=5)
frame_control.pack(side="left", padx=5, pady=5, anchor="nw")

frame_jog = ttk.LabelFrame(bottom_frame, text="Jog", labelanchor = "n", padding=5)
frame_jog.pack(side="left", padx=5, pady=5, anchor="nw")

frame_log = ttk.LabelFrame(bottom_frame, text="Log & Command", padding=5)
frame_log.pack(side="left", padx=5, pady=5, anchor="nw")


for axis in ["X", "Y", "Z"]:
    low_axis = axis.lower()
    
    entry_var = tk.IntVar(value=1)
    globals()[f"axis_entry_{low_axis}"] = entry_var
    
    cb = tk.Checkbutton(
        upper_frame,
        text=f"Pump {axis}",
        variable=entry_var,
        font=("Arial", 14)
    )
    globals()[f"cb_label_{low_axis}"] = cb
    
    cb =  globals().get(f"cb_label_{low_axis}")
    
    frame = tk.LabelFrame(
        upper_frame, 
        labelwidget=cb, 
        labelanchor="n", 
    )
    frame.pack(side="left", padx=5, pady=5, fill="both", expand=True)
    globals()[f"frame_{low_axis}"] = frame

    entry_var.trace_add("write", lambda *args, v=entry_var, f=frame: toggle_axis_frame(v, f))


# Safety check for rate limitation
def check_dynamic_safety(flow_dict):
    v_list = {axis: 0.0 for axis in axis_map.keys()}
    
    # Check whether the flow of each pump is below 20 kHz limitation
    for axis, flow in flow_dict.items():
        info = axis_map.get(axis)
        if not info:
            continue
        
        is_enabled = info["axis_entry"].get() == 1
        
        if is_enabled and flow != 0:
            c_val = SYRINGES.get(info["syringe"].get(), 1.0)
            
            v = (abs(flow) / 1000.0) / c_val
            v_list[axis] = v
            
            if v > AUTO_LIMIT_MM_MIN:
                return False, f"Pump {axis} rate is over limit!\n Limit: {AUTO_LIMIT_MM_MIN:.1f} mm/min"

    # Check whether the combined flow of pumps is below 20 kHz limitation
    v_sq_sum = sum(v**2 for v in v_list.values())
    v_combined = math.sqrt(v_sq_sum)
    
    if v_combined > AUTO_LIMIT_MM_MIN:
        return False, (f"Generated pulse will get over the pulse limitation (20kHz). \n"
                       f"Combined flow: {v_combined:.1f} mm/min\n"
                       f"System limitated-flow: {AUTO_LIMIT_MM_MIN:.1f} mm/min")

    return True, ""


def toggle_axis_frame(axis_entry, target_frame):
    # When checkbox is out, all menus get disable.
    state = "normal" if axis_entry.get() == 1 else "disabled"
    for child in target_frame.winfo_children():
        try:
            child.configure(state=state)
        except:
            pass


# UI for Settings tab
def setup_settings_tab(parent):
    global config_name_var, syringe_list_frame, port_var, baud_var, connect_button, dir_label_var

    left_frame = ttk.Frame(parent, padding=5)
    left_frame.pack(side="left", fill="y", expand=False)

    config_name_var = tk.StringVar(value=current_config.get("config_file_name", "Default"))
    
    ttk.Label(left_frame, text="Current Configuration:").pack(anchor="w")
    ttk.Label(left_frame, textvariable=config_name_var, font=("Arial", 12, "bold"), foreground="blue").pack(anchor="w", pady=5)
    
    ttk.Button(left_frame, text="Load Different Config JSON", command=select_config_file).pack(fill="x", pady=5)
    ttk.Label(left_frame, text="Only Syringe Profiles will be loaded.", foreground="gray").pack(anchor="w")
    ttk.Label(left_frame, text="Press Sync buttom to apply hardware settings.", foreground="gray").pack(anchor="w")
    
    ttk.Separator(left_frame, orient="horizontal").pack(fill="x", pady=5)
    
    ttk.Label(left_frame, text="Hardware Sync:").pack(anchor="w")
    ttk.Button(left_frame, text="Sync to Grbl EEPROM", command=sync_hardware_settings).pack(fill="x", pady=5)
    
    ttk.Label(left_frame, text="Sync all settings from JSON.", foreground="gray").pack(anchor="w")

    ttk.Separator(left_frame, orient="horizontal").pack(fill="x", pady=5)
    
    ttk.Label(left_frame, text="Save Directory for CSV & Log Files:").pack(anchor="w")
    ttk.Button(left_frame, text="Select Directory", command=select_save_directory).pack(fill="x", pady=5)
    dir_label_var = tk.StringVar(value=f"Current Directory: {save_dir}")
    ttk.Label(left_frame, textvariable=dir_label_var, wraplength=250, foreground="blue").pack(anchor="w")


    right_frame = ttk.Frame(parent, padding=5)
    right_frame.pack(side="left", fill="both", anchor="n", expand=True)
    
    #UI for Serial port settings
    bottom_frame = ttk.LabelFrame(right_frame, text="Serial Port Settings", padding=10)
    bottom_frame.pack(side="top", fill="x", pady=10)
    
    port_var = tk.StringVar(value="")
    baud_var = tk.StringVar(value="115200")
    
    ttk.Label(bottom_frame, text="Port:").grid(row=0, column=0, sticky="w")
    
    port_combo = ttk.Combobox(bottom_frame, textvariable=port_var, values=detect_serial_ports(), width=25)
    port_combo.grid(row=0, column=1, columnspan=3, padx=5, pady=2)
    
    ttk.Label(bottom_frame, text="Baud:").grid(row=1, column=0, sticky="w")
    baud_entry = ttk.Entry(bottom_frame, textvariable=baud_var, width=8)
    baud_entry.grid(row=1, column=1, padx=5, pady=2)
    
    connect_button = ttk.Button(bottom_frame, text="Connect", command=connect_serial)
    connect_button.grid(row=0, column=4, sticky="w")
    
    ttk.Separator(right_frame, orient="horizontal").pack(fill="x", pady=5)
    
    # UI for Syringe List
    syringe_list_frame = ttk.LabelFrame(right_frame, text="Loaded Syringes : volume (mL) / length (mm)", padding=10)
    syringe_list_frame.pack(side="top", fill="x", expand=False)

    # About SyringeGUI
    ttk.Button(right_frame, text="About SyringeGUI", command=show_version_info).pack(side="bottom", pady=5, anchor="e")
    
    refresh_settings_tab_list()
    
setup_settings_tab(tab_settings)


# =========================
# Command Communication between hardware and UI
# =========================
def send(cmd):
    with ser_lock:
        log(f">> {cmd}")
        ser.write((cmd + "\n").encode())
        time.sleep(0.05)
        while ser.in_waiting:
            res = ser.readline().decode(errors='ignore').strip()
            if res:
                log(f">> {res}")


def send_nowait(cmd):
    if ser is not None:
        with ser_lock:
            ser.write((cmd + "\n").encode())
            log(f">> {cmd} (sent)")


def log(msg):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # timestamp: year, day, hr, min, sec
    full_msg = f"{msg}  [{now}]\n"
    
    print(full_msg.strip())
    
    log_widget = globals().get("log_box")
    
    if log_widget:
        log_widget.config(state="normal")      # Write Eabled
        log_widget.insert("end", full_msg) # Insert at end
        log_widget.see("end")                  # Auto scroll
        log_widget.config(state="disabled")    # Return to Read-only

    if 'log_filename' in globals() and log_filename:
        try:
            with open(log_filename, "a", encoding="utf-8") as f:
                f.write(full_msg)
        except Exception as e:
            print(f"Logging error: {e}")


# =========================
## General manipulations
# =========================
def reset_zero():
    global saved_offset_x, saved_offset_y, saved_offset_z
    try:
        saved_offset_x = mx_raw
        saved_offset_y = my_raw
        saved_offset_z = mz_raw
        
        log(f">> Zero set at MPos: {saved_offset_x}, {saved_offset_y}, {saved_offset_z} is now the new 0.000")
    except Exception as e:
        log(f">> Reset Error: {e}")


def stop_motion(axis=None):
    global is_running
    send_nowait("!")
    stop_timer()
    if axis=="X":
        log(">> X STOP")
    elif axis=="Y":
        log(">> Y STOP")
    elif axis=="Z":
        log(">> Y STOP")
    else:
        log(">> ALL STOP")


resume_event = threading.Event()
resume_event.set()
pause_time_for_timer = 0
pause_button = None
resume_button = None

def pause_sequence():
    global accumulated_time, pause_button, resume_button
    if pause_button is None and resume_button is None:
        return
        
    else:
        send_nowait("!")
        resume_event.clear()
    
        accumulated_time += (time.time() - session_start_time)
    
        log(">> Pause Pressed.")
        pause_button.config(state="disabled")
        resume_button.config(state="normal")

def resume_sequence():
    global session_start_time, resume_button, resume_button
    if pause_button is None and resume_button is None:
        return
        
    else:
        send_nowait("~")
    
        session_start_time = time.time()
        resume_event.set()
    
        log(">> Resume Pressed.")
        pause_button.config(state="normal")
        resume_button.config(state="disabled")

def reset_seq_state():
    global is_running, resume_event
    is_running = False    
    resume_event.set()
    
    if 'pause_button' in globals() and pause_button:
        pause_button.config(state="normal")
        
    if 'resume_button' in globals() and resume_button:
        resume_button.config(state="disabled")

    log(">> [System] Planned seq cleared. New seq can be started.")

# =========================
## Grbl reset before RUN/Jog
# =========================
def prepare_run():
    global ser
    if ser is None:
        return
    try:
        ser.write(b'\x18') # Ctrl+X: reset
        time.sleep(0.2) 
        log(">> Grbl Reset")
    except Exception as e:
        log(f">> Prepare Error: {e}")

# =========================
## Timer
# =========================
timer_id = None
start_timestamp = 0
accumulated_time = 0
pause_time_for_timer = 0
session_start_time = 0
is_running = False

def update_timer():
    global timer_id
    if is_running:
        total_elapsed = accumulated_time
        if resume_event.is_set():
            total_elapsed += (time.time() - session_start_time)
        
        minutes = int(total_elapsed // 60)
        seconds = int(total_elapsed % 60)
        milliseconds = int((total_elapsed * 10) % 10)
        
        elapsed_time_var.set(f"Elapsed time: {minutes:02d}:{seconds:02d}.{milliseconds:d}")
        
        timer_id = root.after(100, update_timer)

def reset_timer():
    global accumulated_time, session_start_time, is_running, accumulated_time, timer_id
    if timer_id is not None:
        root.after_cancel(timer_id)
        timer_id = None
        
    accumulated_time = 0
    session_start_time = time.time()
    is_running = True
    update_timer()

def stop_timer():
    global is_running
    is_running = False
    
def resume_timer():
    global start_timestamp, is_running
    if not is_running:
        start_timestamp = time.time()
        is_running = True
        update_timer()

# progress for programmed sequence
def update_progress(elapsed, total_duration):
    global is_running
    if not is_running or total_duration is None or total_duration <= 0:
        return

#    elapsed_sec = time.time() - start_time
    total_min = total_duration / 60

    display_sec = min(elapsed, total_duration)
    
    progress_bar["value"] = display_sec
    percent = (display_sec / total_duration) * 100 if total_duration > 0 else 0
    if total_duration - elapsed < 0.2:
            percent = 100.0
        
    elapsed_min = elapsed / 60
    progress_label.config(text=f"{percent:.1f}% ({elapsed_min:.1f}/{total_min:.1f} min)")


# =========================
# Execute Pumping
# =========================
def run_axis(axis):
    global is_running, ser, session_start_time
    try:
        if ser is None:
            messagebox.showerror("Connection Error", "Serial port is not connected.\nPlease CONNECT to serial port first.")
            log(">> Serial not connected.")
            return

        info = axis_map.get(axis)
        if not info: return
        
        raw_flow = float(info["flow_entry"].get())
        if info["axis_entry"].get() == 0:
            log(f">> Pump {axis} is disabled.")
            return
        
        is_safe, msg = check_dynamic_safety({axis: raw_flow * FLOW_UNIT_CONV[info["flow_unit"].get()]})
        if not is_safe:
            messagebox.showwarning("Safety Limit Error", msg)
            return

        syringe_name = info["syringe"].get()
        coeff = SYRINGES.get(syringe_name, 1.0)
        
        flow_unit = info["flow_unit"].get()
        flow_val_ul_min = raw_flow * FLOW_UNIT_CONV[flow_unit] # uL/min
        flow_val = flow_val_ul_min / 1000   # mL/min

        dur_unit = info["dur_unit"].get()
        raw_dur = float(info["time_entry"].get())
        duration = raw_dur * DUR_UNIT_CONV[dur_unit] # sec

        vol_unit = info["vol_unit"].get()
        raw_vol = float(info["vol_entry"].get())
        vol = raw_vol * VOL_UNIT_CONV[vol_unit] # µL
        
        current_mm = info["curr_pos"]()
        
        feed_rate = abs(flow_val) / coeff # mm/min
        distance = feed_rate * (duration / 60) * (1 if flow_val >=0 else -1) # mm
            
        max_vol = distance * coeff * 1000
        if max_vol > vol + 0.001:
            log(f">> Pump {axis} = Cancelled. Exceeded max volume.")
            return
        
        is_running = True
        prepare_run()
        resume_event.set()
        
        session_start_time = time.time()
        reset_timer()
        
        param_log = f">> [RUN {axis}] Syringe: {syringe_name}, Flow: {flow_val_ul_min} µL/min, Time: {duration} sec"
        log(param_log)
        log_to_csv(axis, syringe_name, flow_val_ul_min, "", "", duration)
        
        send_nowait("G91")
        send_nowait(f"G1 {axis}{distance:.4f} F{feed_rate:.3f}")

        start_wait = time.time()
            
        def check_finish():
            global is_running
            if not is_running or (time.time() - start_wait) >= duration:
                stop_timer()
                log(f">> Pump {axis} = Run Finished.")
            else:
                root.after(100, check_finish)

        check_finish()
            
    except Exception as e:
        log(f">> Error in Pump {axis}: {e}")
        is_running = False
        stop_timer()


def run_all():
    try:
        prepare_run()
        manual_recipe = []
        
        # Get current values on UI and prepare a recipe
        for axis, info in axis_map.items():
            if info["axis_entry"].get() == 1:
                f = float(info["flow_entry"].get()) * FLOW_UNIT_CONV[info["flow_unit"].get()]
                t = float(info["time_entry"].get()) * DUR_UNIT_CONV[info["dur_unit"].get()]

                # readable style by the Engine [ (axis, start, end, flow), ... ]
                if f != 0:
                    manual_recipe.append((axis, 0, t, f))

        if manual_recipe:
            run_smart_sequence(custom_recipe=manual_recipe)
            
    except Exception as e:
        log(f">> Manual Run Error: {e}")

# =========================
## Jog control
# =========================
def on_jog_rate_change(*args):
    try:
        val_str = jog_rate_var.get()
        if not val_str: return
        
        val = float(val_str)
        
        jog_max_rate = AUTO_LIMIT_MM_MIN
        jog_min_rate = jog_max_rate / 100
        
        if jog_min_rate <= val <= jog_max_rate:
            if abs(jog_slider.get() - val) > 0.1:
                jog_slider.set(val)
            
    except (ValueError, NameError):
        pass


def jog(axis, direction):
    info = axis_map.get(axis)
    if not info or info["axis_entry"].get() == 0:
        return

    if ser is None:
        messagebox.showerror("Connection Error", "Serial port is not connected.\nPlease CONNECT to serial port first.")
        log(">> Serial not connected. Cannot jog.")
        return
        
    try:
        prepare_run()

        step = 50        # Max movement by one action（mm）
        F = float(jog_rate_var.get())
        current_mm = info["curr_pos"]()
        coeff = SYRINGES.get(info["syringe"].get(), 1.0)
        
        max_ul = float(info["vol_entry"].get())
        max_mm = max_ul / (coeff * 1000) # calculate max limit distance (mm)
        
        if direction > 0:
            remaining = max_mm - current_mm
            if remaining <= 0:
                log(f">> Pump {axis} at Max Volume")
                return
            actual_step = min(step, remaining)  # select the shortest distance from 50 mm or remaining distance
        else:
            remaining = abs(max_mm) - current_mm
            if remaining <= 0:
                return
            actual_step = min(step, remaining)
        
        if actual_step > 0.001:
            cmd = f"$J=G91 {axis}{direction * actual_step:.4f} F{F}"
            send_nowait(cmd)
        
    except Exception as e:
            log(f">> Error in Jog {axis}: {e}")

def jog_stop(axis):
    info = axis_map.get(axis)
    if not info or info["axis_entry"].get() == 0:
        return

    if ser is None:
        return
    send_nowait("!")
    log(f">> Jog {axis} STOP")

# =========================
## Functions for Programmed Sequence
# =========================
def run_smart_sequence(custom_recipe=None):
    global is_running, ser, raw_recipe
    
    if ser is None or not ser.is_open:
        messagebox.showerror("Connection Error", "Serial port is not connected.\nPlease CONNECT to serial port first.")
        log(">> Serial not connected. Cannot RUN.")
        return
        
    if is_running:
        log(">> [Warning] Sequence is running. Please press ABORT first.")
        return
    
    active_recipe = custom_recipe if custom_recipe is not None else raw_recipe      # recipe from run_all is also integrated.
    
    if not active_recipe:
        messagebox.showwarning("Warning", "No recipe data.")
        return

    is_running = True
    
    try:
        total_duration = max([row[2] for row in active_recipe])        # calculate total duration
        progress_bar["maximum"] = total_duration                       # reset progressbar

        # Check whether flow in all steps is below limit by dry_run
        success, message = execute_recipe_engine(active_recipe, total_duration, dry_run=True)

        if not success:
            is_running = False
            messagebox.showerror("Safety Limit Error", f"This recipe will not be execuated.\n{message}")
            return

        log(">> Safety Check Passed. Starting sequence...")

        reset_timer()

        # Start sequence in another thread
        threading.Thread(
            target=execute_recipe_engine,
            args=(active_recipe, total_duration, False),    # dry_run=False
            daemon=True
        ).start()
        
    except Exception as e:
        log(f">> Sequence Start Error: {e}")
        is_running = False

def execute_recipe_engine(recipe, total_duration, dry_run=False):
    global is_running, ser
    print(f">> Recipe contains {len(recipe)} steps")

    if not dry_run:
        is_running = True
        resume_event.set()
    
    total_duration = max([row[2] for row in recipe]) if recipe else 0

    sorted_points = sorted(list(set([row[1] for row in recipe] + [row[2] for row in recipe])))

    start_time = time.time()
    last_ui_update = 0

    if not dry_run:
        prepare_run()
        log(">> Sequence starting...")
        send_nowait("G91")
    else:
        log(">> Limitation check: Validating recipe limits...")
    
    try:
        for i in range(len(sorted_points) - 1):
            if not dry_run and not is_running: break
                
            t_start = sorted_points[i]
            t_end = sorted_points[i+1]
            duration = t_end - t_start
            if duration <= 0: continue

            # Extract the axis and flow to be activated in each period
            active_flows = {"X": 0.0, "Y": 0.0, "Z": 0.0}
            for axis, s, e, flow in recipe:
                if s <= t_start and e >= t_end:
                    info = axis_map.get(axis)
                    if info and info["axis_entry"].get() == 1:
                        active_flows[axis] = flow
            
            is_safe, msg = check_dynamic_safety(active_flows)
            if not is_safe:
                if dry_run:
                    return False, f"Step {i+1} ({t_start}s): {msg}"
                else:
                    log(f">> [Critical Safety Error] {msg}")
                    return False, msg

            if dry_run:
                continue
            
            while is_running:
                if not resume_event.is_set():
                    ps = time.time()
                    resume_event.wait()
                    start_time += (time.time() - ps)
                    
                elapsed = time.time() - start_time
                if elapsed >= t_start: break
                time.sleep(0.01)

            cmd_parts = []
            feed_sq_sum = 0.0

            for axis, s, e, flow in recipe:
                if not (s <= t_start and e >= t_end):
                    continue
                    
                info = axis_map.get(axis)
                if not info or info["axis_entry"].get() == 0:
                    continue
                    
                syringe_name = info["syringe"].get()
                coeff = SYRINGES.get(syringe_name, 1.0)
                
                log_to_csv(f"Pump {axis}_S{i+1}", syringe_name, flow, t_start, t_end, duration)
                
                v = (abs(flow) / 1000.0) / coeff
                dist = (flow / 1000.0) / coeff * (duration / 60.0)
                
                cmd_parts.append(f"{axis}{dist:.4f}")
                feed_sq_sum += v**2

            if cmd_parts:
                f_combined = math.sqrt(feed_sq_sum)
                cmd = f"G1 {' '.join(cmd_parts)} F{f_combined:.4f}"
                send_nowait(cmd)
                log(f">> [Engine] Step {i+1}: {cmd} ({duration}s)")
            else:
                log(f">> [Engine] Step {i+1}: Wait ({duration}s)")
                
            while is_running:
                if not resume_event.is_set():
                    ps = time.time()
                    resume_event.wait()
                    start_time += (time.time() - ps)
                
                current_elapsed = time.time() - start_time
                
                # Refresh UI
                if time.time() - last_ui_update > 0.2:
                    if start_time is time.time():
                        update_progress(0, total_duration)
                    else:
                        update_progress(current_elapsed, total_duration)
                    last_ui_update = time.time()
                    
                if current_elapsed >= t_end:
                    break
                time.sleep(0.02)
                
        if dry_run:
            return True, "Limitation check passed"
                
    except Exception as e:
        log(f">> Engine Error: {e}")
    finally:
        if not dry_run:
            is_running = False
            stop_timer()
            update_progress(total_duration, total_duration)
            log(f">> Sequence Finished.")
    
    return True, "Success"

# =========================
## Position Monitoring
# =========================
current_wpos_x = 0.0
current_wpos_y = 0.0
current_wpos_z = 0.0

def update_status():
    global mx_raw, my_raw, mz_raw, current_wpos_x, current_wpos_y, current_wpos_z
    while True:
        try:
            if 'ser' not in globals() or ser is None or not ser.is_open:
                time.sleep(1.0)
                continue
                
            with ser_lock:
                ser.write(b"?\n")
            
            time.sleep(0.05)
            
            loop_count = 0
            
            while ser.in_waiting > 0 and loop_count < 10:
                res = ser.readline().decode(errors='ignore').strip()
                loop_count += 1
                
                if "MPos:" in res:
                    m_match = re.search(r"MPos:([-.\d]+),([-.\d]+),([-.\d]+)", res)
                    if m_match:
                        vals = m_match.group(0).replace("MPos:", "").split(",")
                        mx_raw = float(vals[0])
                        my_raw = float(vals[1])
                        mz_raw = float(vals[2])

                        current_wpos_x = mx_raw - saved_offset_x
                        current_wpos_y = my_raw - saved_offset_y
                        current_wpos_z = mz_raw - saved_offset_z

                        if 'pause_button' in globals():
                            root.after(0, update_ui_with_current_pos)
                            
                elif res == "ok":
                    continue
                elif "Grbl 1.1h" in res:
                    continue
                elif res.startswith("<") and res.endswith(">"):
                    continue
                elif res:
                    root.after(0, lambda r=res: log(f">> SERIAL: {r}"))
                    
        except Exception as e:
            print(f"Status Update Error: {e}")
            time.sleep(1.0)
            
        time.sleep(0.2)


def update_ui_with_current_pos():
    try:
        for axis, info in axis_map.items():
            mpos = info["curr_pos"]()
            coeff = SYRINGES[info["syringe"].get()]
            vol_ul = mpos * coeff * 1000
            info["pos_var"].set(f"{mpos:.3f} mm ({vol_ul:.1f} µL)")

    except Exception:
        pass


# =========================
## UI for Manual Control
# =========================
configs = [
    {"id": "X", "frame": globals()["frame_x"], "num": "1"},
    {"id": "Y", "frame": globals()["frame_y"], "num": "2"},
    {"id": "Z", "frame": globals()["frame_z"], "num": "3"},
]

for cfg in configs:
    axis = cfg["id"]

    frame = globals().get(f"frame_{axis.lower()}") 
    axis_entry = globals().get(f"axis_entry_{axis.lower()}")

    # Variables
    syr_var = tk.StringVar(value="1 mL (Zelostat)")
    flow_unit_var = tk.StringVar(value="µL/min")
    dur_unit_var = tk.StringVar(value="sec")
    vol_unit_var = tk.StringVar(value="µL")
    pos_var = globals()[f"position_var_{axis.lower()}"] 

    # Syringe
    if axis == "X": ttk.Label(frame, text="Syringe ").grid(row=0, column=0, sticky="e")
    syr_combo = ttk.Combobox(frame, textvariable=syr_var, values=list(SYRINGES.keys()), width=18)
    syr_combo.grid(row=0, column=1 if axis == "X" else 0, columnspan=2, sticky="w")

    # Flow
    if axis == "X": ttk.Label(frame, text="Flow ").grid(row=1, column=0, sticky="e")
    flow_entry = ttk.Entry(frame, width=10, justify="right")
    flow_entry.insert(0, "100")
    flow_entry.grid(row=1, column=1 if axis == "X" else 0, sticky="w")
    
    flow_unit_combo = ttk.Combobox(frame, textvariable=flow_unit_var, values=["µL/min", "µL/sec", "mL/min"], width=7, state="readonly")
    flow_unit_combo.grid(row=1, column=2 if axis == "X" else 1, sticky="w")
    flow_unit_combo.bind("<<ComboboxSelected>>", lambda e, a=axis: handle_flow_unit_change(a))

    # Help Label
    ttk.Label(frame, text="inject(+), draw(-)").grid(row=2, column=1 if axis == "X" else 0, sticky="n")

    # Duration
    if axis == "X": ttk.Label(frame, text="Duration ").grid(row=3, column=0, sticky="e")
    time_entry = ttk.Entry(frame, width=10, justify="right")
    time_entry.insert(0, "60")
    time_entry.grid(row=3, column=1 if axis == "X" else 0, sticky="w")
    
    dur_unit_combo = ttk.Combobox(frame, textvariable=dur_unit_var, values=DUR_UNIT_OPTIONS, width=7, state="readonly")
    dur_unit_combo.grid(row=3, column=2 if axis == "X" else 1, sticky="w")
    dur_unit_combo.bind("<<ComboboxSelected>>", lambda e, a=axis: handle_duration_unit_change(a))

    # Buttons
    ttk.Button(frame, text=f"▶ RUN {axis}", command=lambda a=axis: threading.Thread(target=run_axis, args=(a,), daemon=True).start()).grid(row=4, column=1 if axis == "X" else 0, rowspan=2, padx=5)
    ttk.Button(frame, text=f"■ STOP {axis}", command=lambda a=axis: stop_motion(a)).grid(row=4, column=2 if axis == "X" else 1, rowspan=2, padx=5)

    # Position
    if axis == "X": ttk.Label(frame, text="Position (Vol)").grid(row=6, column=0, sticky="e")
    ttk.Label(frame, textvariable=pos_var).grid(row=6, column=1 if axis == "X" else 0, columnspan=2)

    # Max Volume
    if axis == "X": ttk.Label(frame, text="Max Vol.").grid(row=7, column=0, sticky="e")
    vol_entry = ttk.Entry(frame, width=10, justify="right")
    vol_entry.insert(0, "1000")
    vol_entry.grid(row=7, column=1 if axis == "X" else 0, sticky="w")
    
    vol_unit_combo = ttk.Combobox(frame, textvariable=vol_unit_var, values=VOL_UNIT_OPTIONS, width=7, state="readonly")
    vol_unit_combo.grid(row=7, column=2 if axis == "X" else 1, sticky="w")
    vol_unit_combo.bind("<<ComboboxSelected>>", lambda e, a=axis: handle_vol_unit_change(a))

    # Restore in dictionary "axis_map"
    axis_map[axis] = {
        "syringe": syr_var,
        "syringe_combo": syr_combo,
        "flow_entry": flow_entry,
        "flow_unit": flow_unit_var,
        "last_flow_unit": flow_unit_var.get(),
        "time_entry": time_entry,
        "dur_unit": dur_unit_var,
        "last_dur_unit": dur_unit_var.get(),
        "vol_entry": vol_entry,
        "vol_unit": vol_unit_var,
        "last_vol_unit": vol_unit_var.get(),
        "pos_var": pos_var,
        "curr_pos": lambda a=axis.lower(): globals()[f"current_wpos_{a}"],
        "axis_entry": axis_entry
    }
    
    if axis_entry and frame:
        axis_entry.trace_add("write", lambda *args, e=axis_entry, f=frame: toggle_axis_frame(e, f))


## Control UI of all pumps
ttk.Button(frame_control, text="▶ RUN ALL", command=lambda: threading.Thread(target=run_all,daemon=True).start()).grid(row=0,column=0, padx=5, pady=2)
ttk.Button(frame_control, text="■ STOP ALL", command=lambda: stop_motion()).grid(row=1,column=0,padx=5, pady=2)

elapsed_label = ttk.Label(frame_control, textvariable=elapsed_time_var, font=("Arial", 12, "bold"))
elapsed_label.grid(row=2, column=0, columnspan=2, pady=2, sticky="w")

ttk.Button(frame_control, text="RESET POSITION", command=reset_zero).grid(row=3,columnspan=2,padx=5, pady=2)


## Jog UI
ttk.Label(frame_jog, text="Rate (mm/min)").grid(row=0, column=1, padx=5, sticky="e")

global jog_rate_var, jog_slider
jog_rate_var = tk.StringVar(value="50.0")
jog_rate_var.trace_add("write", on_jog_rate_change)

jog_entry = ttk.Entry(frame_jog, textvariable=jog_rate_var, width=8, justify="right")
jog_entry.grid(row=0, column=2, sticky="w", padx=5)

jog_max_rate = AUTO_LIMIT_MM_MIN
jog_min_rate = jog_max_rate / 100.0

jog_slider = ttk.Scale(
    frame_jog,
    from_= jog_min_rate,
    to = jog_max_rate,
    orient="vertical",
    command=lambda v: jog_rate_var.set(f"{float(v):.1f}")
)

jog_slider.set(50) # Initial rate of Jog
jog_slider.grid(row=0, column=0, rowspan=4, padx=10)

for i, axis in enumerate(["X", "Y", "Z"], start=1):
    # Jog (-) button
    btn_minus = ttk.Button(frame_jog, text=f"Jog {axis} -")
    btn_minus.grid(row=i, column=1, padx=2, pady=2)
    btn_minus.bind("<ButtonPress>", lambda e, a=axis: jog(a, -1))
    btn_minus.bind("<ButtonRelease>", lambda e, a=axis: jog_stop(a))
    
    #  Jog (+) button
    btn_plus = ttk.Button(frame_jog, text=f"Jog {axis} +")
    btn_plus.grid(row=i, column=2, padx=2, pady=2)
    btn_plus.bind("<ButtonPress>", lambda e, a=axis: jog(a, 1))
    btn_plus.bind("<ButtonRelease>", lambda e, a=axis: jog_stop(a))

    axis_map[axis]["jog_buttons"] = [btn_minus, btn_plus]


def update_button_states(*args):
    for axis, info in axis_map.items():
        new_state = "normal" if info["axis_entry"].get() == 1 else "disabled"
        for btn in info.get("jog_buttons", []):
            btn.config(state=new_state)

for info in axis_map.values():
    info["axis_entry"].trace_add("write", update_button_states)

update_button_states()


# UI for Log and Command
def send_manual(event=None):
    entry_widget = globals().get("cmd_entry_widget")
    if not entry_widget:
        return
        
    cmd = entry_widget.get().strip()
    if not cmd:
        return
    
    log(f">> Manual Send: {cmd}")
    
    ser.write(b'\x18')
    send(cmd)
            
    cmd_entry.delete(0, tk.END)


log_box = tk.Text(frame_log, width=42, height=7, state="disabled", font=("Courier", 12))
log_box.grid(row=0, column=0, rowspan=3, columnspan=3, pady=5, sticky="w")
globals()["log_box"] = log_box

ttk.Label(frame_log, text="Command:").grid(row=4, column=0, sticky="e")
cmd_entry = ttk.Entry(frame_log, width=10)
cmd_entry.grid(row=4, column=1, sticky="w")

globals()["cmd_entry_widget"] = cmd_entry

cmd_entry.bind("<Return>", send_manual)

ttk.Button(frame_log, text="Send", command=send_manual).grid(row=4, column=2, padx=5, sticky="w")


# =========================
## UI for Programmed Sequence
# =========================
def setup_programmed_tab(parent):
    upper_frame = ttk.Frame(parent)
    upper_frame.pack(pady=10, padx=10, fill="x")
    
    file_frame = ttk.LabelFrame(upper_frame, text="File Selection", padding=5)
    file_frame.pack(side="left", fill="y", padx=(0, 10))

    ttk.Button(file_frame, text="Select Recipe CSV", command=browse_recipe).grid(row=0, column=0, sticky="w", padx=5, pady=5)
    global recipe_label
    recipe_label = ttk.Label(file_frame, text="No file selected", font=("Arial", 12, "italic"))
    recipe_label.grid(row=0, column=1, sticky="w", padx=5)
    
    ttk.Label(file_frame, text="Template: [Pump, Start (s), End (s), Flow (µL/min)]").grid(row=1, column=0, columnspan=2, sticky="w", pady=(10, 2))
    ttk.Label(file_frame, text="    raw 1: X, Tx_0, Tx_1, flow_x_1").grid(row=2, column=0, columnspan=2, sticky="w")
    ttk.Label(file_frame, text="    raw 2: X, Tx_1, Tx_2, flow_x_2").grid(row=3, column=0, columnspan=2, sticky="w")
    ttk.Label(file_frame, text="    raw 3: Y, Ty_0, Ty_1, flow_y_1").grid(row=4, column=0, columnspan=2, sticky="w")
    ttk.Label(file_frame, text="*(...) and space should be removed. Only commas must be used.").grid(row=5, column=0, columnspan=2, sticky="w")

    preview_frame = ttk.LabelFrame(upper_frame, text="Recipe Preview", padding=5)
    preview_frame.pack(side="left", fill="both", expand=True)

    global tree
    columns = ("axis", "start", "end", "flow")
    tree = ttk.Treeview(preview_frame, columns=columns, show="headings", height=6)
    
    tree.heading("axis", text="Pump")
    tree.heading("start", text="Start (s)")
    tree.heading("end", text="End (s)")
    tree.heading("flow", text="Flow (µL/min)")
    
    tree.column("axis", width=65, anchor="center")
    tree.column("start", width=70, anchor="center")
    tree.column("end", width=70, anchor="center")
    tree.column("flow", width=75, anchor="center")
    
    tree.pack(side="left", fill="both", expand=True)

    scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    # Execution frame
    control_frame = ttk.LabelFrame(parent, text="Execution", padding=5)
    control_frame.pack(side="left", fill="y", pady=5, padx=5, anchor="n")

    ttk.Button(control_frame, text="▶ START SEQUENCE", 
               command=lambda: threading.Thread(target=run_smart_sequence, daemon=True).start(),
               ).grid(row=0, column=0, columnspan=2, pady=2)
    
    elapsed_label = ttk.Label(control_frame, textvariable=elapsed_time_var, font=("Arial", 12, "bold"))
    elapsed_label.grid(row=1, column=0, columnspan=2, pady=2, sticky="w")
    
    
    global pause_button, resume_button
    pause_button = ttk.Button(control_frame, text="PAUSE", command=pause_sequence)
    pause_button.grid(row=2, column=0, padx=5, pady=2)

    resume_button = ttk.Button(control_frame, text="RESUME", command=resume_sequence)
    resume_button.grid(row=2,column=1, padx=5, pady=2)
    
    reset_button = ttk.Button(control_frame, text="ABORT", command=reset_seq_state)
    reset_button.grid(row=3, column=0, columnspan=2, pady=5, sticky="n")

    # Status frame
    status_frame = ttk.LabelFrame(parent, text="Status", padding=5)
    status_frame.pack(side="left", fill="x", pady=5, padx=10, anchor="n")
    
    ttk.Label(status_frame, text="    Position (Volume)    ").grid(row=0, column=1, columnspan=2)
    for i, axis in enumerate(["X", "Y", "Z"], start=1):
        ttk.Label(status_frame, text=f"Pump {axis}").grid(row=i, column=0, sticky="e")
        ttk.Label(status_frame, textvariable=axis_map[axis]["pos_var"], font=("Arial", 12, "bold")).grid(row=i, column=1, columnspan=2, sticky="n")

    ttk.Button(status_frame, text="RESET POSITION", command=reset_zero).grid(row=4,columnspan=3,padx=5, pady=2)

    # Canvas for graph
    graph_frame = ttk.LabelFrame(parent, text="Visualized Recipe", padding=5)
    graph_frame.pack(side="right", fill="x", padx=5, anchor="n")

    for i, axis in enumerate(["X", "Y", "Z"]):
        ttk.Label(graph_frame, text=axis).grid(row=i, column=0, sticky="w")
        cv = tk.Canvas(graph_frame, width=250, height=30, bg="white", highlightthickness=1)
        cv.grid(row=i, column=1, pady=2)
        axis_map[axis]["canvas"] = cv
        
        if axis == "X": globals()["canvas_x"] = cv
        elif axis == "Y": globals()["canvas_y"] = cv
        elif axis == "Z": globals()["canvas_z"] = cv

    #Progress-bar
    global progress_bar, progress_label
    ttk.Label(graph_frame, text="Time").grid(row=4, column=0, pady=2)
    style = ttk.Style()
    style.configure("green.Horizontal.TProgressbar", background="green", thickness=5)
    progress_bar = ttk.Progressbar(graph_frame, length=240, style="green.Horizontal.TProgressbar", orient="horizontal", mode="determinate")
    progress_bar.grid(row=4, column=1, pady=2, padx=5, columnspan=2, sticky="e")

    # Lable for percentage
    progress_label = tk.Label(graph_frame, text="0% (0.0 / 0.0 min)", font=("Arial", 12))
    progress_label.grid(row=5, column=1, pady=2, sticky="e")

setup_programmed_tab(tab_programmed)

# =========================
## Update status and auto-selection of PORT
# =========================
threading.Thread(target=update_status, daemon=True).start()

last_port_name = load_initial_config()
update_syringe_list()
refresh_settings_tab_list()

if last_port_name:
    available_ports = [p.device for p in list_ports.comports()]
    if last_port_name in available_ports:
        port_var.set(last_port_name)
        log(f">> Attempting auto-connect to {last_port_name}...")
        root.after(500, connect_serial)
    else:
        log(f">> Last port {last_port_name} not found. Please select manually.")

root.mainloop()
