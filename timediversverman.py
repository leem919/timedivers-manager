import os
import json
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tempfile
import shutil
import subprocess
import scraper
import asyncio
import threading
import sys
import ctypes

# Configuration
CONFIG_FILE = "config.json"
MANIFEST_FILE = "manifests.json"
PRIMARY_DEPOTS = [553851, 553853, 553854]
APP_ID = 553850

# Helper Functions
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"common_folder": "", "username": "", "remember_password": False, "active_version": "steam"}

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def load_manifests():
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, "r") as f:
            return json.load(f)
    return {}

def save_manifests(manifests):
    with open(MANIFEST_FILE, "w") as f:
        json.dump(manifests, f, indent=4)

def format_version_name(date_str):
    return f"Helldivers 2_v{date_str}"

def get_active_folder_path(config):
    return os.path.join(config["common_folder"], "Helldivers 2")

def merge_manifests(manifests):
    return {date: entry for date, entry in manifests.items()}

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

icon_stable = os.path.join(os.getenv("APPDATA"), "timedivers_manager", "meridia.ico")
os.makedirs(os.path.dirname(icon_stable), exist_ok=True)
if not os.path.exists(icon_stable):
    shutil.copy(resource_path("meridia.ico"), icon_stable)


# GUI
class VersionManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        icon_path = resource_path("meridia.ico")
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Warning: Could not set icon: {e}")
        self.title("Timedivers Manager")
        self.geometry("750x550")
        self.deiconify()
        self.bg = "#1e1b29"
        self.fg = "#ffffff"
        self.accent = "#9b59b6"
        default_font = ("Segoe UI", 10)
        self.configure(bg=self.bg)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", background=self.accent, foreground=self.fg, font=default_font, padding=6)
        style.map("TButton", background=[("active", "#b67fd3")], foreground=[("disabled", "#666666")])
        style.configure("TLabel", background=self.bg, foreground=self.fg, font=default_font)
        style.configure("TEntry", fieldbackground="#2c2c3c", foreground=self.fg, insertcolor=self.fg)
        style.configure("TFrame", background=self.bg)
        style.configure("TCheckbutton", background=self.bg, foreground=self.fg, font=default_font)

        self.config_data = load_config()
        self.manifests = merge_manifests(load_manifests())
        save_manifests(self.manifests)
        self.listbox_index_to_version = {}

        self.create_widgets()
        self.refresh_version_list()

    def restart_app(self):
        subprocess.Popen([sys.executable, os.path.abspath(sys.argv[0])])
        # Exit current instance
        sys.exit(0)

    def create_widgets(self):
        top_frame = ttk.Frame(self, style="TFrame")
        top_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(top_frame, text="Steam Common Folder:").grid(row=0, column=0, sticky="w")
        self.folder_var = tk.StringVar(value=self.config_data.get("common_folder", ""))
        folder_entry = ttk.Entry(top_frame, textvariable=self.folder_var, width=50)
        folder_entry.grid(row=0, column=1, padx=5)
        ttk.Button(top_frame, text="Browse", command=self.browse_folder).grid(row=0, column=2)

        ttk.Label(top_frame, text="Steam Username:").grid(row=1, column=0, sticky="w")
        self.username_var = tk.StringVar(value=self.config_data.get("username", ""))
        ttk.Entry(top_frame, textvariable=self.username_var, width=50).grid(row=1, column=1, padx=5)

        self.remember_var = tk.BooleanVar(value=self.config_data.get("remember_password", True))
        ttk.Checkbutton(top_frame, text="Remember Password for Downloads", variable=self.remember_var).grid(row=1, column=2)

        middle_frame = ttk.Frame(self, style="TFrame")
        middle_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ttk.Label(middle_frame, text="Available Versions:").pack(anchor="w")
        self.version_listbox = tk.Listbox(
            middle_frame, height=20,
            bg="#2c2c3c", fg=self.fg, selectbackground=self.accent,
            font=("Segoe UI", 10)
        )
        self.version_listbox.pack(fill="both", expand=True, padx=2, pady=2)

        bottom_frame = ttk.Frame(self, style="TFrame")
        bottom_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(bottom_frame, text="Download Version", command=self.download_version).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Set Active Version", command=self.switch_version).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Delete Version", command=self.delete_version).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Update List", command=self.run_scraper).pack(side="right", padx=5)

    # Folder/Version Management
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.config_data["common_folder"] = folder
            save_config(self.config_data)
            self.refresh_version_list()

    def refresh_version_list(self):
        self.version_listbox.delete(0, tk.END)
        self.listbox_index_to_version.clear()
        active_version = self.config_data.get("active_version", "")

        steam_folder = os.path.join(self.config_data.get("common_folder", ""), "Helldivers 2_steam")
        display_name = "Steam Version"
        downloaded_tag = "(downloaded) " if os.path.exists(steam_folder) else ""
        active_tag = "(active) " if active_version == "steam" else ""
        display_name = f"{downloaded_tag}{active_tag}{display_name}"
        self.version_listbox.insert(tk.END, display_name)
        self.listbox_index_to_version[0] = "steam"

        dates = [v for v in self.manifests.keys() if v != "steam"]
        dates_sorted = sorted(dates, key=lambda x: x, reverse=True)
        for version in dates_sorted:
            folder_path = os.path.join(self.config_data.get("common_folder", ""), format_version_name(version))
            downloaded_tag = "(downloaded) " if os.path.exists(folder_path) else ""
            active_tag = "(active) " if version == active_version else ""
            patch_title = self.manifests.get(version, {}).get("patch_title", "")
            title_suffix = f"- {patch_title}" if patch_title else ""
            display_name = f"{downloaded_tag}{active_tag}{version} {title_suffix}"
            idx = self.version_listbox.size()
            self.version_listbox.insert(tk.END, display_name)
            self.listbox_index_to_version[idx] = version

    # Download / Switch / Delete
    def download_version(self):
        self.config_data["username"] = self.username_var.get()
        self.config_data["remember_password"] = self.remember_var.get()
        save_config(self.config_data)
        selection = self.version_listbox.curselection()
        if not selection:
            return

        version_name = self.listbox_index_to_version[selection[0]]
        if version_name == "steam":
            messagebox.showwarning("Download Not Allowed", "Use the Steam client for the Steam version.")
            return
        if version_name == self.config_data.get("active_version"):
            messagebox.showwarning("Download Not Allowed", "Cannot download the currently active version.")
            return

        folder_path = os.path.join(self.config_data["common_folder"], format_version_name(version_name))
        os.makedirs(folder_path, exist_ok=True)
        username = self.username_var.get()

        with tempfile.NamedTemporaryFile("w", delete=False, suffix=".bat") as f:
            for depot in PRIMARY_DEPOTS:
                manifest_id = self.manifests.get(version_name, {}).get(str(depot), "UNKNOWN")
                if manifest_id == "UNKNOWN":
                    print(f"Warning: Manifest ID unknown for depot {depot} on version {version_name}")
                    continue
                cmd = f'DepotDownloader.exe -app {APP_ID} -depot {depot} -manifest {manifest_id} -username "{username}" -dir "{folder_path}"'
                if self.remember_var.get():
                    cmd += " -remember-password"
                f.write(cmd + "\n")
            f.write("exit\n")
            batch_path = f.name

        subprocess.Popen(["cmd.exe", "/c", batch_path], creationflags=subprocess.CREATE_NEW_CONSOLE)
        self.refresh_version_list()

    def switch_version(self):
        selection = self.version_listbox.curselection()
        if not selection:
            return
        version_name = self.listbox_index_to_version[selection[0]]
        active_folder = get_active_folder_path(self.config_data)
        common = self.config_data["common_folder"]
        target_folder = os.path.join(common, format_version_name(version_name) if version_name != "steam" else "Helldivers 2_steam")

        if active_folder == target_folder:
            return

        if os.path.exists(active_folder):
            current_active_name = self.config_data.get("active_version")
            new_name = os.path.join(common, "Helldivers 2_steam" if current_active_name == "steam" else format_version_name(current_active_name))
            if os.path.exists(new_name):
                messagebox.showwarning("Rename Conflict", f"Cannot rename current active folder, {new_name} already exists.")
                return
            os.rename(active_folder, new_name)

        if not os.path.exists(target_folder):
            messagebox.showerror("Missing Folder", f"Target version folder {target_folder} does not exist.")
            return

        os.rename(target_folder, active_folder)
        self.config_data["active_version"] = version_name
        save_config(self.config_data)
        self.refresh_version_list()

    def delete_version(self):
        selection = self.version_listbox.curselection()
        if not selection:
            return
        version_name = self.listbox_index_to_version[selection[0]]

        if version_name == "steam":
            messagebox.showwarning("Delete Not Allowed", "Cannot delete the Steam version.")
            return
        if version_name == self.config_data.get("active_version"):
            messagebox.showwarning("Delete Not Allowed", "Cannot delete the currently active version.")
            return

        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete version '{version_name}'?"
        )
        if not confirm:
            return

        folder_to_delete = os.path.join(self.config_data["common_folder"], format_version_name(version_name))
        if not os.path.exists(folder_to_delete):
            messagebox.showerror("Missing Folder", f"Folder {folder_to_delete} does not exist.")
            return

        shutil.rmtree(folder_to_delete)
        self.refresh_version_list()


    def run_scraper(self):
        confirm = messagebox.askyesno(
            "Manifest Scraper",
            "Microsoft Edge will be used for the scraping process, it will be restarted in debug mode. "
            "Please open Microsoft Edge, navigate to steamdb.info, and make sure you are logged into your Steam account "
            "with the 'Remember Me' option checked. Continue?"
        )
        if not confirm:
            return

        def worker():
            asyncio.run(scraper.main())
            # Schedule restart on main thread
            self.after(0, self.restart_app)

        threading.Thread(target=worker, daemon=True).start()


# Entrypoint
if __name__ == "__main__":
    app = VersionManagerApp()
    app.mainloop()
