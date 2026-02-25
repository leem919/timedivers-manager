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

def is_junction(path):
    try:
        FILE_ATTRIBUTE_REPARSE_POINT = 0x400
        attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
        if attrs == -1:
            return False
        return bool(attrs & FILE_ATTRIBUTE_REPARSE_POINT)
    except Exception:
        return False

def create_junction(link_path, target_path):
    result = subprocess.run(
        ["cmd.exe", "/c", "mklink", "/J", link_path, target_path],
        check=True, capture_output=True, text=True
    )
    return result

def remove_junction(path):
    os.rmdir(path)

def open_explorer(path):
    subprocess.Popen(["explorer", os.path.normpath(path)])


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

        self.migrate_to_junction()
        self.create_widgets()
        self.refresh_version_list()

    def migrate_to_junction(self):
        common = self.config_data.get("common_folder", "")
        if not common:
            return

        active_folder = os.path.join(common, "Helldivers 2")
        active_version = self.config_data.get("active_version", "steam")
        versioned_name = (
            "Helldivers 2_steam"
            if active_version == "steam"
            else format_version_name(active_version)
        )
        versioned_path = os.path.join(common, versioned_name)

        if is_junction(active_folder):
            return

        if not os.path.isdir(active_folder) and os.path.isdir(versioned_path):
            try:
                create_junction(active_folder, versioned_path)
            except Exception as e:
                messagebox.showerror(
                    "Migration Failed",
                    f"The versioned folder exists but junction creation failed:\n{e}\n\n"
                    f"Try running the app as administrator."
                )
            return

        if os.path.isdir(active_folder):
            proceed = messagebox.askyesno(
                "One-Time Setup",
                f"In order to enable junction-based version switching, a one-time migration is needed. "
                f"This reduces potential errors when unable to switch versions.\n\n"
                f"The following will happen:\n\n"
                f"  • 'Helldivers 2' will be renamed to '{versioned_name}'\n"
                f"  • A junction named 'Helldivers 2' will be created in its place\n\n"
                f"The game will continue to work exactly as before. "
                f"This only needs to be done once.\n\n"
                f"Proceed?"
            )
            if not proceed:
                sys.exit(0)
            if os.path.exists(versioned_path):
                messagebox.showwarning(
                    "Migration Warning",
                    f"Both of these folders exist as real directories:\n\n"
                    f"  {active_folder}\n"
                    f"  {versioned_path}\n\n"
                    f"Please manually remove or merge the duplicate, then restart."
                )
                return

            try:
                os.rename(active_folder, versioned_path)
            except OSError:
                messagebox.showinfo(
                    "One-Time Setup Required",
                    f"A one-time folder migration to use junction points is required "
                    f"for version switching, as this reduces potential switching errors.\n\n"
                    f"Windows is preventing the app from renaming the folder automatically.\n\n"
                    f"Please do this manually in File Explorer:\n\n"
                    f"  Rename:  Helldivers 2\n"
                    f"  To:      {versioned_name}\n\n"
                    f"The folder is located in:\n  {common}\n\n"
                    f"Then restart Timedivers. This only needs to be done once.\n\n"
                    f"The junction will be created after restarting the app."
                )
                open_explorer(common)
                return

            try:
                create_junction(active_folder, versioned_path)
            except Exception as e:
                try:
                    os.rename(versioned_path, active_folder)
                except Exception:
                    pass
                messagebox.showerror(
                    "Migration Failed",
                    f"The folder was renamed successfully but junction creation failed:\n{e}\n\n"
                    f"The rename has been undone. Try running the app as administrator."
                )
                open_explorer(common)

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
        self.sort_downloaded_first = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            middle_frame,
            text="Sort by Downloaded",
            variable=self.sort_downloaded_first,
            command=self.refresh_version_list
        ).pack(anchor="w", pady=(0, 5))
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
        ttk.Button(bottom_frame, text="Revert Folders", command=self.revert_to_vanilla).pack(side="left", padx=5)
        ttk.Button(bottom_frame, text="Update List", command=self.run_scraper).pack(side="right", padx=5)

    # Folder/Version Management
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_var.set(folder)
            self.config_data["common_folder"] = folder
            save_config(self.config_data)
            self.refresh_version_list()
            self.migrate_to_junction()

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
        if self.sort_downloaded_first.get():
            def sort_key(v):
                folder_path = os.path.join(self.config_data.get("common_folder", ""), format_version_name(v))
                is_downloaded = os.path.exists(folder_path)
                return (not is_downloaded, -int(v.replace("-", "")) if v.replace("-", "").isdigit() else 0)
            dates_sorted = sorted(dates, key=sort_key)
        else:
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

    # Download / Switch / Delete / Revert
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
        common = self.config_data["common_folder"]
        active_folder = get_active_folder_path(self.config_data)  

        target_folder = os.path.join(
            common,
            "Helldivers 2_steam" if version_name == "steam" else format_version_name(version_name)
        )

        if not os.path.exists(target_folder):
            messagebox.showerror("Missing Folder", f"Target version folder does not exist:\n{target_folder}")
            return

        if os.path.exists(active_folder) or is_junction(active_folder):
            try:
                remove_junction(active_folder)
            except Exception as e:
                messagebox.showerror(
                    "Switch Failed",
                    f"Could not remove the existing junction at:\n{active_folder}\n\n{e}"
                )
                return

        try:
            create_junction(active_folder, target_folder)
        except Exception as e:
            messagebox.showerror(
                "Switch Failed",
                f"Could not create junction to:\n{target_folder}\n\n{e}"
            )
            return

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

    def revert_to_vanilla(self):
        confirm = messagebox.askyesno(
            "Revert Folders",
            "This will:\n\n"
            "  • Remove the junction\n"
            "  • Rename 'Helldivers 2_steam' back to 'Helldivers 2'\n\n"
            "Any downloaded old version folders will be left on disk, "
            "you can delete them manually to reclaim disk space.\n\n"
            "Steam will manage Helldivers 2 normally after this.\n\n"
            "Continue?"
        )
        if not confirm:
            return

        common = self.config_data.get("common_folder", "")
        if not common:
            messagebox.showerror("Revert Failed", "No Steam common folder is configured.")
            return

        active_folder = os.path.join(common, "Helldivers 2")
        steam_versioned = os.path.join(common, "Helldivers 2_steam")

        active_version = self.config_data.get("active_version", "steam")
        if active_version != "steam":
            if not os.path.exists(steam_versioned):
                messagebox.showerror(
                    "Revert Failed",
                    f"Cannot revert: the Steam version folder does not exist:\n{steam_versioned}\n\n"
                    f"You need the Steam version present to revert."
                )
                return
            if is_junction(active_folder) or os.path.exists(active_folder):
                try:
                    remove_junction(active_folder)
                except Exception as e:
                    messagebox.showerror("Revert Failed", f"Could not remove junction:\n{e}")
                    return
            try:
                create_junction(active_folder, steam_versioned)
            except Exception as e:
                messagebox.showerror("Revert Failed", f"Could not point junction at Steam version:\n{e}")
                return

        if is_junction(active_folder) or os.path.exists(active_folder):
            try:
                remove_junction(active_folder)
            except Exception as e:
                messagebox.showerror("Revert Failed", f"Could not remove junction:\n{e}")
                return

        if not os.path.exists(steam_versioned):
            messagebox.showerror(
                "Revert Failed",
                f"Steam version folder not found:\n{steam_versioned}\n\n"
                f"The junction has been removed but the folder could not be renamed. "
                f"Please rename it manually in File Explorer:\n"
                f"  From: Helldivers 2_steam\n"
                f"  To:   Helldivers 2"
            )
            open_explorer(common)
            return

        try:
            os.rename(steam_versioned, active_folder)
        except OSError as e:
            messagebox.showerror(
                "Revert Failed",
                f"Could not rename the Steam folder back to 'Helldivers 2':\n{e}\n\n"
                f"Please rename it manually in File Explorer:\n"
                f"  From: Helldivers 2_steam\n"
                f"  To:   Helldivers 2"
            )
            open_explorer(common)
            return

        messagebox.showinfo(
            "Revert Complete",
            "Your folder setup has been restored.\n\n"
            "Note: any old version folders are still on disk, "
            "you can delete them manually from your Steam common folder to reclaim the space."
        )
        sys.exit(0)

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
            self.after(0, self._scraper_done)

        threading.Thread(target=worker, daemon=True).start()

    def _scraper_done(self):
        messagebox.showinfo(
            "Scraping Complete",
            "The manifest list has been updated.\n\n"
            "Please restart the version manager to load the new manifests."
        )
        sys.exit(0)


# Entrypoint
if __name__ == "__main__":
    app = VersionManagerApp()
    app.mainloop()