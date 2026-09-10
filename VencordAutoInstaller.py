import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import tkinter as tk
from tkinter import ttk


DOWNLOAD_URL = "https://github.com/Vencord/Installer/releases/latest/download/VencordInstallerCli.exe"


class Installer:
    def __init__(self, root):
        self.root = root
        self.root.title("Vencord Installer")
        self.root.geometry("520x230")
        self.root.resizable(False, False)
        self.root.configure(bg="#111214")

        self.status = tk.StringVar(value="Preparing installation...")
        self.percent = tk.StringVar(value="0%")
        self.progress = tk.DoubleVar(value=0)

        tk.Label(
            root,
            text="Vencord Installer",
            font=("Segoe UI", 20, "bold"),
            fg="#ffffff",
            bg="#111214"
        ).pack(pady=(28, 8))

        tk.Label(
            root,
            textvariable=self.status,
            font=("Segoe UI", 10),
            fg="#b5bac1",
            bg="#111214"
        ).pack()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Vencord.Horizontal.TProgressbar",
            troughcolor="#242629",
            background="#5865F2",
            bordercolor="#242629",
            lightcolor="#5865F2",
            darkcolor="#5865F2"
        )

        ttk.Progressbar(
            root,
            style="Vencord.Horizontal.TProgressbar",
            variable=self.progress,
            maximum=100,
            length=420
        ).pack(pady=(22, 7))

        tk.Label(
            root,
            textvariable=self.percent,
            font=("Segoe UI", 9),
            fg="#72767d",
            bg="#111214"
        ).pack()

        self.root.after(300, self.start)

    def update(self, status=None, progress=None):
        def apply():
            if status is not None:
                self.status.set(status)

            if progress is not None:
                self.progress.set(progress)
                self.percent.set(f"{int(progress)}%")

        self.root.after(0, apply)

    def close_discord(self):
        self.update("Closing Discord...", 5)

        subprocess.run(
            ["taskkill", "/F", "/IM", "Discord.exe"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        time.sleep(2)

    def download(self):
        self.update("Downloading latest Vencord installer...", 15)

        temp_dir = tempfile.mkdtemp(prefix="vencord_installer_")
        cli_path = os.path.join(temp_dir, "VencordInstallerCli.exe")

        request = urllib.request.Request(
            DOWNLOAD_URL,
            headers={
                "User-Agent": "VencordAutoInstaller"
            }
        )

        with urllib.request.urlopen(request) as response:
            total = response.headers.get("Content-Length")

            if total:
                total = int(total)

            downloaded = 0

            with open(cli_path, "wb") as file:
                while True:
                    chunk = response.read(1024 * 256)

                    if not chunk:
                        break

                    file.write(chunk)
                    downloaded += len(chunk)

                    if total:
                        percent = downloaded / total * 30 + 15
                        self.update(
                            "Downloading latest Vencord installer...",
                            min(percent, 45)
                        )

        return cli_path, temp_dir

    def install(self, cli_path):
        self.update("Starting Vencord installation...", 50)

        process = subprocess.Popen(
            [
                cli_path,
                "-install",
                "-branch",
                "auto"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW
        )

        self.update("Detecting Discord installation...", 55)

        for line in process.stdout:
            line = line.strip()

            if not line:
                continue

            lower = line.lower()

            if "downloading" in lower:
                self.update("Downloading Vencord files...", 65)

            elif "patch" in lower or "patching" in lower:
                self.update("Patching Discord...", 80)

            elif "install" in lower:
                self.update("Installing Vencord...", 75)

            elif "success" in lower:
                self.update("Finishing installation...", 95)

        return process.wait()

    def cleanup(self, temp_dir):
        self.update("Cleaning temporary files...", 97)

        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    def finish(self, success):
        if success:
            self.update("Vencord installed successfully!", 100)
        else:
            self.update("Vencord installation failed.", 100)

        self.root.after(2000, self.root.destroy)

    def run(self):
        temp_dir = None

        try:
            self.close_discord()

            cli_path, temp_dir = self.download()

            return_code = self.install(cli_path)

            self.cleanup(temp_dir)

            self.finish(return_code == 0)

        except Exception as error:
            print(error)

            if temp_dir:
                self.cleanup(temp_dir)

            self.update("Installation failed.", 100)
            self.root.after(3000, self.root.destroy)

    def start(self):
        threading.Thread(
            target=self.run,
            daemon=True
        ).start()


if __name__ == "__main__":
    root = tk.Tk()
    Installer(root)
    root.mainloop()
