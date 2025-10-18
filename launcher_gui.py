#!/usr/bin/env python3
"""
Plex Poster Manager GUI Launcher
Provides a simple GUI to launch and manage both backend and frontend servers.
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import json
import signal
import platform
import webbrowser
from pathlib import Path
import time
import requests

# Determine project root
PROJECT_ROOT = Path(__file__).parent.absolute()
BACKEND_DIR = PROJECT_ROOT / "backend"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
CONFIG_FILE = PROJECT_ROOT / "config.json"

# Platform-specific paths
if platform.system() == "Windows":
    VENV_PYTHON = BACKEND_DIR / "venv" / "Scripts" / "python.exe"
    NPM_CMD = "npm.cmd"
else:
    VENV_PYTHON = BACKEND_DIR / "venv" / "bin" / "python"
    NPM_CMD = "npm"


class PlexPosterManagerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Plex Poster Manager Launcher")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)

        # Process handles
        self.backend_process = None
        self.frontend_process = None

        # Configuration
        self.config = self.load_config()

        # Setup UI
        self.setup_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Check dependencies
        self.root.after(100, self.check_dependencies)

    def load_config(self):
        """Load configuration from file."""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading config: {e}")
                return self.get_default_config()
        return self.get_default_config()

    def get_default_config(self):
        """Get default configuration."""
        return {
            "plex_url": "http://localhost:32400",
            "plex_token": "",
            "backup_directory": str(PROJECT_ROOT / "backups"),
            "thumbnail_size": [300, 450],
            "auto_detect_url": True
        }

    def save_config(self):
        """Save configuration to file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.log("✓ Configuration saved successfully")
            return True
        except Exception as e:
            self.log(f"✗ Error saving configuration: {e}")
            messagebox.showerror("Error", f"Failed to save configuration: {e}")
            return False

    def setup_ui(self):
        """Set up the user interface."""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

        # Title
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        title_label = ttk.Label(title_frame, text="🎬 Plex Poster Manager",
                                font=("Helvetica", 18, "bold"))
        title_label.pack(side="left")

        # Status indicator
        self.status_label = ttk.Label(title_frame, text="● Ready",
                                       foreground="gray", font=("Helvetica", 12))
        self.status_label.pack(side="right")

        # --- Configuration Section ---
        config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding="10")
        config_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        # Plex Server URL
        ttk.Label(config_frame, text="Plex Server URL:").grid(row=0, column=0, sticky="w", pady=5)

        url_frame = ttk.Frame(config_frame)
        url_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        config_frame.grid_columnconfigure(0, weight=1)

        self.url_var = tk.StringVar(value=self.config.get("plex_url", "http://localhost:32400"))
        url_entry = ttk.Entry(url_frame, textvariable=self.url_var, width=50)
        url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Button(url_frame, text="Auto-Detect", command=self.auto_detect_url).pack(side="left")

        # Plex Token (REQUIRED for v2.0)
        token_label_frame = ttk.Frame(config_frame)
        token_label_frame.grid(row=2, column=0, sticky="w", pady=5)

        ttk.Label(token_label_frame, text="Plex Token (REQUIRED):").pack(side="left")
        ttk.Label(token_label_frame, text="⚠️ Required for v2.0 API mode",
                  foreground="red", font=("Helvetica", 9, "bold")).pack(side="left", padx=5)

        token_frame = ttk.Frame(config_frame)
        token_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5))

        self.token_var = tk.StringVar(value=self.config.get("plex_token", ""))
        self.token_show_var = tk.BooleanVar(value=False)

        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var,
                                      show="*", width=50)
        self.token_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        ttk.Checkbutton(token_frame, text="Show", variable=self.token_show_var,
                        command=self.toggle_token_visibility).pack(side="left", padx=2)
        ttk.Button(token_frame, text="Test Token", command=self.test_token).pack(side="left")

        # Token help text with link
        token_help_frame = ttk.Frame(config_frame)
        token_help_frame.grid(row=4, column=0, sticky="w", pady=(0, 10))

        token_help = ttk.Label(token_help_frame,
                              text="How to get token:",
                              foreground="gray", font=("Helvetica", 8))
        token_help.pack(side="left")

        token_link = ttk.Label(token_help_frame,
                              text="https://support.plex.tv/articles/204059436",
                              foreground="blue", font=("Helvetica", 8), cursor="hand2")
        token_link.pack(side="left", padx=5)
        token_link.bind("<Button-1>", lambda e: webbrowser.open("https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/"))

        # Save Config Button
        ttk.Button(config_frame, text="💾 Save Configuration",
                   command=self.save_configuration).grid(row=5, column=0, pady=5)

        # --- Control Section ---
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.start_button = ttk.Button(control_frame, text="▶ Launch Servers",
                                        command=self.start_servers, style="Accent.TButton")
        self.start_button.pack(side="left", padx=5, fill="x", expand=True)

        self.stop_button = ttk.Button(control_frame, text="⏹ Stop Servers",
                                       command=self.stop_servers, state="disabled")
        self.stop_button.pack(side="left", padx=5, fill="x", expand=True)

        self.browser_button = ttk.Button(control_frame, text="🌐 Open Browser",
                                          command=self.open_browser, state="disabled")
        self.browser_button.pack(side="left", padx=5, fill="x", expand=True)

        # --- Log Output Section ---
        log_frame = ttk.LabelFrame(main_frame, text="Server Output", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky="nsew", pady=(0, 10))

        main_frame.grid_rowconfigure(3, weight=1)

        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD,
                                                   height=15, font=("Courier", 10))
        self.log_text.pack(fill="both", expand=True)

        # --- Status Bar ---
        status_bar = ttk.Frame(main_frame)
        status_bar.grid(row=4, column=0, columnspan=2, sticky="ew")

        self.backend_status = ttk.Label(status_bar, text="Backend: Stopped",
                                         foreground="gray")
        self.backend_status.pack(side="left", padx=10)

        self.frontend_status = ttk.Label(status_bar, text="Frontend: Stopped",
                                          foreground="gray")
        self.frontend_status.pack(side="left", padx=10)

    def log(self, message):
        """Add message to log output."""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()

    def auto_detect_url(self):
        """Auto-detect Plex server URL."""
        self.log("Detecting Plex server...")

        # Try common local URLs
        common_urls = [
            "http://localhost:32400",
            "http://127.0.0.1:32400"
        ]

        for url in common_urls:
            try:
                response = requests.get(f"{url}/identity", timeout=2)
                if response.status_code == 200:
                    self.url_var.set(url)
                    self.log(f"✓ Found Plex server at: {url}")
                    messagebox.showinfo("Success", f"Found Plex server at:\n{url}")
                    return
            except:
                continue

        self.log("✗ Could not auto-detect Plex server.")
        messagebox.showwarning("Auto-Detect",
                              "Could not find Plex server automatically.\n\n"
                              "Make sure Plex Media Server is running,\n"
                              "then enter the URL manually (e.g., http://localhost:32400)")

    def toggle_token_visibility(self):
        """Toggle Plex token visibility."""
        if self.token_show_var.get():
            self.token_entry.config(show="")
        else:
            self.token_entry.config(show="*")

    def test_token(self):
        """Test Plex token validity."""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a Plex token to test.")
            return

        self.log("Testing Plex token...")

        try:
            response = requests.get("https://plex.tv/api/v2/user",
                                    headers={"X-Plex-Token": token},
                                    timeout=10)

            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get("username", "Unknown")
                self.log(f"✓ Token valid! Logged in as: {username}")
                messagebox.showinfo("Success", f"Token is valid!\nLogged in as: {username}")
            else:
                self.log(f"✗ Invalid token (Status: {response.status_code})")
                messagebox.showerror("Error", "Invalid Plex token.")
        except Exception as e:
            self.log(f"✗ Error testing token: {e}")
            messagebox.showerror("Error", f"Failed to test token:\n{e}")

    def save_configuration(self):
        """Save current configuration."""
        self.config["plex_url"] = self.url_var.get().strip()
        self.config["plex_token"] = self.token_var.get().strip()

        # Validate token is provided
        if not self.config["plex_token"]:
            messagebox.showwarning("Token Required",
                                  "Plex token is REQUIRED for v2.0!\n\n"
                                  "The app uses the Plex API and needs your token.\n\n"
                                  "Click the blue link above to learn how to get it.")
            return

        if self.save_config():
            messagebox.showinfo("Success", "Configuration saved successfully!")

    def check_dependencies(self):
        """Check if dependencies are installed, offer to install if missing."""
        self.log("Checking dependencies...")

        needs_setup = []

        # Check Python venv
        if not VENV_PYTHON.exists():
            self.log("✗ Python virtual environment not found!")
            needs_setup.append("Backend virtual environment")

        # Check node_modules
        if not (FRONTEND_DIR / "node_modules").exists():
            self.log("✗ Frontend dependencies not installed!")
            needs_setup.append("Frontend dependencies")

        if needs_setup:
            self.status_label.config(text="● Missing Dependencies", foreground="red")

            # Offer automatic setup
            msg = "First-time setup required:\n\n"
            msg += "\n".join(f"  • {item}" for item in needs_setup)
            msg += "\n\nThis will take 2-3 minutes."
            msg += "\n\nWould you like to install dependencies automatically?"

            if messagebox.askyesno("First Time Setup", msg):
                return self.run_first_time_setup()
            else:
                self.log("\nManual setup required:")
                if "Backend virtual environment" in needs_setup:
                    self.log("  1. cd backend && python -m venv venv")
                    self.log("  2. pip install -r backend/requirements.txt")
                if "Frontend dependencies" in needs_setup:
                    self.log("  3. cd frontend && npm install")
                return False

        self.log("✓ All dependencies found")
        return True

    def run_first_time_setup(self):
        """Run automated first-time setup."""
        self.log("\n" + "=" * 60)
        self.log("FIRST TIME SETUP - This may take a few minutes")
        self.log("=" * 60)

        try:
            # Create venv if needed
            if not VENV_PYTHON.exists():
                self.log("\n📦 Creating Python virtual environment...")
                self.status_label.config(text="● Setting up backend...", foreground="orange")

                result = subprocess.run(
                    [sys.executable, "-m", "venv", "venv"],
                    cwd=str(BACKEND_DIR),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    self.log(f"✗ Failed to create venv: {result.stderr}")
                    messagebox.showerror("Setup Failed", f"Failed to create virtual environment:\n{result.stderr}")
                    return False

                self.log("✓ Virtual environment created")

                # Install Python dependencies
                self.log("\n📦 Installing backend dependencies...")

                if platform.system() == "Windows":
                    pip_exe = BACKEND_DIR / "venv" / "Scripts" / "pip.exe"
                else:
                    pip_exe = BACKEND_DIR / "venv" / "bin" / "pip"

                result = subprocess.run(
                    [str(pip_exe), "install", "-r", "requirements.txt"],
                    cwd=str(BACKEND_DIR),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    self.log(f"✗ Failed to install backend dependencies: {result.stderr}")
                    messagebox.showerror("Setup Failed", f"Failed to install backend dependencies:\n{result.stderr}")
                    return False

                self.log("✓ Backend dependencies installed")

            # Install Node dependencies if needed
            if not (FRONTEND_DIR / "node_modules").exists():
                self.log("\n📦 Installing frontend dependencies (this takes longest)...")
                self.status_label.config(text="● Setting up frontend...", foreground="orange")

                result = subprocess.run(
                    [NPM_CMD, "install"],
                    cwd=str(FRONTEND_DIR),
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    self.log(f"✗ Failed to install frontend dependencies: {result.stderr}")
                    messagebox.showerror("Setup Failed", f"Failed to install frontend dependencies:\n{result.stderr}")
                    return False

                self.log("✓ Frontend dependencies installed")

            self.log("\n" + "=" * 60)
            self.log("✓ SETUP COMPLETE! You can now launch the servers.")
            self.log("=" * 60 + "\n")

            self.status_label.config(text="● Ready", foreground="green")
            messagebox.showinfo("Setup Complete",
                               "All dependencies installed successfully!\n\n"
                               "You can now click 'Launch Servers' to start.")
            return True

        except Exception as e:
            self.log(f"\n✗ Setup failed with error: {e}")
            messagebox.showerror("Setup Failed", f"An error occurred during setup:\n{e}")
            self.status_label.config(text="● Setup Failed", foreground="red")
            return False

    def start_servers(self):
        """Start both backend and frontend servers."""
        if not self.check_dependencies():
            messagebox.showerror("Missing Dependencies",
                                 "Please install dependencies first.\nSee log for details.")
            return

        self.log("=" * 60)
        self.log("Starting servers...")
        self.log("=" * 60)

        # Start backend
        self.log("\n[Backend] Starting Flask server...")
        try:
            self.backend_process = subprocess.Popen(
                [str(VENV_PYTHON), "app.py"],
                cwd=str(BACKEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            self.backend_status.config(text="Backend: Running", foreground="green")
            self.log("✓ Backend started")

            # Start reading backend output in thread
            threading.Thread(target=self.read_backend_output, daemon=True).start()
        except Exception as e:
            self.log(f"✗ Failed to start backend: {e}")
            messagebox.showerror("Error", f"Failed to start backend:\n{e}")
            return

        # Wait a bit for backend to initialize
        time.sleep(2)

        # Start frontend
        self.log("\n[Frontend] Starting React dev server...")
        try:
            env = os.environ.copy()
            env["BROWSER"] = "none"  # Prevent auto-opening browser

            self.frontend_process = subprocess.Popen(
                [NPM_CMD, "start"],
                cwd=str(FRONTEND_DIR),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                env=env
            )
            self.frontend_status.config(text="Frontend: Running", foreground="green")
            self.log("✓ Frontend started")

            # Start reading frontend output in thread
            threading.Thread(target=self.read_frontend_output, daemon=True).start()
        except Exception as e:
            self.log(f"✗ Failed to start frontend: {e}")
            messagebox.showerror("Error", f"Failed to start frontend:\n{e}")
            self.stop_servers()
            return

        # Update UI
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.browser_button.config(state="normal")
        self.status_label.config(text="● Running", foreground="green")

        self.log("\n" + "=" * 60)
        self.log("✓ Both servers are running!")
        self.log("Backend: http://localhost:5000")
        self.log("Frontend: http://localhost:3000")
        self.log("=" * 60 + "\n")

        # Auto-open browser after a delay
        self.root.after(5000, self.open_browser)

    def read_backend_output(self):
        """Read backend process output."""
        try:
            for line in iter(self.backend_process.stdout.readline, ''):
                if line:
                    self.log(f"[Backend] {line.rstrip()}")
        except Exception as e:
            self.log(f"[Backend] Output stream closed: {e}")

    def read_frontend_output(self):
        """Read frontend process output."""
        try:
            for line in iter(self.frontend_process.stdout.readline, ''):
                if line:
                    # Filter out some verbose npm output
                    line_clean = line.rstrip()
                    if line_clean and not line_clean.startswith("webpack"):
                        self.log(f"[Frontend] {line_clean}")
        except Exception as e:
            self.log(f"[Frontend] Output stream closed: {e}")

    def stop_servers(self):
        """Stop both servers."""
        self.log("\nStopping servers...")

        # Stop frontend
        if self.frontend_process:
            try:
                self.log("[Frontend] Stopping...")
                if platform.system() == "Windows":
                    self.frontend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.frontend_process.pid), signal.SIGTERM)
                self.frontend_process.wait(timeout=5)
                self.frontend_status.config(text="Frontend: Stopped", foreground="gray")
                self.log("✓ Frontend stopped")
            except Exception as e:
                self.log(f"✗ Error stopping frontend: {e}")
            self.frontend_process = None

        # Stop backend
        if self.backend_process:
            try:
                self.log("[Backend] Stopping...")
                if platform.system() == "Windows":
                    self.backend_process.terminate()
                else:
                    os.killpg(os.getpgid(self.backend_process.pid), signal.SIGTERM)
                self.backend_process.wait(timeout=5)
                self.backend_status.config(text="Backend: Stopped", foreground="gray")
                self.log("✓ Backend stopped")
            except Exception as e:
                self.log(f"✗ Error stopping backend: {e}")
            self.backend_process = None

        # Update UI
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.browser_button.config(state="disabled")
        self.status_label.config(text="● Stopped", foreground="gray")

        self.log("✓ All servers stopped\n")

    def open_browser(self):
        """Open the app in default browser."""
        webbrowser.open("http://localhost:3000")
        self.log("✓ Opened browser to http://localhost:3000")

    def on_closing(self):
        """Handle window closing."""
        if self.backend_process or self.frontend_process:
            if messagebox.askokcancel("Quit", "Servers are still running. Stop and quit?"):
                self.stop_servers()
                self.root.destroy()
        else:
            self.root.destroy()


def main():
    """Main entry point."""
    root = tk.Tk()

    # Set theme (works on macOS/Windows)
    style = ttk.Style()
    if "aqua" in style.theme_names():
        style.theme_use("aqua")
    elif "vista" in style.theme_names():
        style.theme_use("vista")

    app = PlexPosterManagerLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
