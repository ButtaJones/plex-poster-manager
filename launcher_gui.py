#!/usr/bin/env python3
"""
Plex Poster Manager GUI Launcher
Provides a modern GUI to launch and manage both backend and frontend servers.
"""

try:
    import customtkinter as ctk
    from tkinter import filedialog, messagebox
    CTK_AVAILABLE = True
except ImportError:
    # Fallback to regular tkinter if CustomTkinter not available
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    CTK_AVAILABLE = False

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

        # Auto-start if configured
        if self.config.get("auto_start_servers", False):
            self.root.after(2000, self.auto_start)

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
            "auto_detect_url": True,
            "auto_start_servers": False
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

        # Auto-start checkbox
        self.auto_start_var = tk.BooleanVar(value=self.config.get("auto_start_servers", False))
        ttk.Checkbutton(config_frame, text="🚀 Auto-start servers on launch",
                       variable=self.auto_start_var).grid(row=5, column=0, sticky="w", pady=5)

        # Save Config Button
        ttk.Button(config_frame, text="💾 Save Configuration",
                   command=self.save_configuration).grid(row=6, column=0, pady=5)

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

        self.update_button = ttk.Button(control_frame, text="🔄 Check for Updates",
                                         command=self.check_for_updates)
        self.update_button.pack(side="left", padx=5, fill="x", expand=True)

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
        """Test Plex token validity using PlexAPI."""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("No Token", "Please enter a Plex token to test.")
            return

        self.log("Testing Plex token...")

        try:
            # Test by trying to connect to Plex server
            from plexapi.server import PlexServer

            plex_url = self.url_var.get().strip() or "http://localhost:32400"
            plex = PlexServer(plex_url, token)

            # If we got here, connection worked!
            self.log(f"✓ Token valid! Connected to: {plex.friendlyName}")
            self.log(f"  Server version: {plex.version}")
            messagebox.showinfo("Success",
                              f"Token is valid!\n\n"
                              f"Connected to: {plex.friendlyName}\n"
                              f"Version: {plex.version}")
        except Exception as e:
            error_msg = str(e)
            self.log(f"✗ Token test failed: {error_msg}")

            if "401" in error_msg or "Unauthorized" in error_msg:
                messagebox.showerror("Invalid Token",
                                    "Token is invalid or expired.\n\n"
                                    "Please get a new token from:\n"
                                    "https://support.plex.tv/articles/204059436")
            elif "Connection" in error_msg or "timeout" in error_msg.lower():
                messagebox.showerror("Connection Failed",
                                    f"Could not connect to Plex server at:\n{plex_url}\n\n"
                                    "Make sure Plex Media Server is running.")
            else:
                messagebox.showerror("Error", f"Token test failed:\n\n{error_msg}")

    def save_configuration(self):
        """Save current configuration."""
        self.config["plex_url"] = self.url_var.get().strip()
        self.config["plex_token"] = self.token_var.get().strip()
        self.config["auto_start_servers"] = self.auto_start_var.get()

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
        needs_update = []

        # Check Python venv
        if not VENV_PYTHON.exists():
            self.log("✗ Python virtual environment not found!")
            needs_setup.append("Backend virtual environment")

        # Check node_modules
        if not (FRONTEND_DIR / "node_modules").exists():
            self.log("✗ Frontend dependencies not installed!")
            needs_setup.append("Frontend dependencies")
        else:
            # Check if package.json has newer dependencies than what's installed
            # This catches cases like lucide-react being added after npm install
            package_json = FRONTEND_DIR / "package.json"
            if package_json.exists():
                try:
                    import json
                    with open(package_json, 'r') as f:
                        pkg_data = json.load(f)

                    # Check if lucide-react (new in v2.1.0) is installed
                    lucide_path = FRONTEND_DIR / "node_modules" / "lucide-react"
                    if "lucide-react" in pkg_data.get("dependencies", {}) and not lucide_path.exists():
                        self.log("⚠ New dependencies detected (lucide-react icons)")
                        needs_update.append("Frontend dependencies (new packages)")
                except Exception as e:
                    self.log(f"  (Could not check package.json: {e})")

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

        if needs_update:
            self.status_label.config(text="● Updates Available", foreground="orange")

            # Offer automatic update
            msg = "New dependencies detected:\n\n"
            msg += "\n".join(f"  • {item}" for item in needs_update)
            msg += "\n\nThis happens after pulling updates from GitHub."
            msg += "\n\nWould you like to install them now? (takes ~30 seconds)"

            if messagebox.askyesno("Update Dependencies", msg):
                return self.update_frontend_dependencies()
            else:
                self.log("\n⚠ WARNING: App may not work without new dependencies!")
                self.log("  Run manually: cd frontend && npm install")
                return False

        self.log("✓ All dependencies found and up to date")
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

    def update_frontend_dependencies(self):
        """Update frontend dependencies (run npm install)."""
        self.log("\n" + "=" * 60)
        self.log("UPDATING FRONTEND DEPENDENCIES")
        self.log("=" * 60)
        self.log("\n📦 Installing new packages from package.json...")
        self.status_label.config(text="● Installing packages...", foreground="orange")

        try:
            result = subprocess.run(
                [NPM_CMD, "install"],
                cwd=str(FRONTEND_DIR),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                self.log(f"✗ Failed to install dependencies: {result.stderr}")
                messagebox.showerror("Update Failed",
                                   f"Failed to install dependencies:\n\n{result.stderr}")
                self.status_label.config(text="● Update Failed", foreground="red")
                return False

            self.log("✓ Frontend dependencies updated successfully")
            self.log("\n" + "=" * 60)
            self.log("✓ UPDATE COMPLETE!")
            self.log("=" * 60 + "\n")

            self.status_label.config(text="● Ready", foreground="green")
            messagebox.showinfo("Success",
                              "Dependencies installed successfully!\n\n"
                              "If servers are running, please restart them\n"
                              "to use the new packages.")
            return True

        except Exception as e:
            self.log(f"✗ Error updating dependencies: {e}")
            messagebox.showerror("Error", f"Failed to update dependencies:\n\n{e}")
            self.status_label.config(text="● Update Failed", foreground="red")
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

    def auto_start(self):
        """Auto-start servers if configured and dependencies are ready."""
        if self.check_dependencies():
            self.log("\n🚀 Auto-starting servers (configured in settings)...\n")
            self.start_servers()

    def check_for_updates(self):
        """Check GitHub for latest release and offer to update."""
        self.log("\n🔍 Checking for updates...")

        try:
            # Fetch latest release from GitHub API
            url = "https://api.github.com/repos/ButtaJones/plex-poster-manager/releases/latest"
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            latest_release = response.json()
            latest_version = latest_release.get('tag_name', 'unknown')
            release_name = latest_release.get('name', latest_version)
            release_body = latest_release.get('body', 'No changelog available.')
            release_url = latest_release.get('html_url', '')

            # Get current version from git (if available)
            try:
                current_version_result = subprocess.run(
                    ["git", "describe", "--tags", "--abbrev=0"],
                    cwd=str(PROJECT_ROOT),
                    capture_output=True,
                    text=True
                )
                current_version = current_version_result.stdout.strip() if current_version_result.returncode == 0 else "unknown"
            except:
                current_version = "unknown"

            self.log(f"✓ Current version: {current_version}")
            self.log(f"✓ Latest version: {latest_version}")

            # Check if update is available
            if current_version == latest_version:
                self.log("✓ You're up to date!")
                messagebox.showinfo(
                    "No Updates Available",
                    f"You're already running the latest version!\n\n"
                    f"Current: {current_version}\n"
                    f"Latest: {latest_version}"
                )
            else:
                # Show update dialog with changelog
                self.show_update_dialog(current_version, latest_version, release_name, release_body, release_url)

        except requests.exceptions.RequestException as e:
            self.log(f"✗ Failed to check for updates: {e}")
            messagebox.showerror(
                "Update Check Failed",
                f"Could not check for updates:\n\n{str(e)}\n\n"
                "Please check your internet connection or try again later."
            )
        except Exception as e:
            self.log(f"✗ Error checking for updates: {e}")
            messagebox.showerror("Error", f"An error occurred:\n\n{str(e)}")

    def show_update_dialog(self, current, latest, name, changelog, url):
        """Show update available dialog with changelog."""
        # Create custom dialog
        dialog = tk.Toplevel(self.root)
        dialog.title("Update Available")
        dialog.geometry("600x500")
        dialog.resizable(True, True)

        # Title
        title_label = ttk.Label(dialog, text=f"New Version Available: {latest}", font=("", 14, "bold"))
        title_label.pack(pady=(20, 10))

        subtitle_label = ttk.Label(dialog, text=f"Current version: {current}")
        subtitle_label.pack(pady=(0, 20))

        # Changelog frame
        changelog_frame = ttk.LabelFrame(dialog, text="What's New", padding="10")
        changelog_frame.pack(padx=20, pady=(0, 20), fill="both", expand=True)

        changelog_text = scrolledtext.ScrolledText(changelog_frame, wrap=tk.WORD, height=15)
        changelog_text.pack(fill="both", expand=True)
        changelog_text.insert(1.0, changelog)
        changelog_text.config(state="disabled")

        # Buttons frame
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=(0, 20))

        def update_now():
            dialog.destroy()
            self.perform_update(url)

        def skip_version():
            dialog.destroy()
            self.log(f"ℹ Skipped version {latest}")

        def remind_later():
            dialog.destroy()
            self.log("ℹ Update reminder dismissed")

        update_btn = ttk.Button(button_frame, text="Update Now", command=update_now, style="Accent.TButton")
        update_btn.pack(side="left", padx=5)

        skip_btn = ttk.Button(button_frame, text="Skip This Version", command=skip_version)
        skip_btn.pack(side="left", padx=5)

        later_btn = ttk.Button(button_frame, text="Remind Me Later", command=remind_later)
        later_btn.pack(side="left", padx=5)

        # Center dialog
        dialog.transient(self.root)
        dialog.grab_set()

    def perform_update(self, release_url):
        """Perform git pull to update the application."""
        self.log("\n📥 Updating application...")

        try:
            # Check if git is available
            result = subprocess.run(
                ["git", "pull"],
                cwd=str(PROJECT_ROOT),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                self.log("✓ Update successful!")
                self.log(result.stdout)

                messagebox.showinfo(
                    "Update Successful",
                    "Application updated successfully!\n\n"
                    "Please restart the launcher to use the new version.\n\n"
                    "Don't forget to run 'npm install' in the frontend folder if there were dependency changes!"
                )

                # Trigger dependency check for new packages
                self.check_dependencies()
            else:
                self.log(f"✗ Update failed: {result.stderr}")
                messagebox.showerror(
                    "Update Failed",
                    f"Failed to update:\n\n{result.stderr}\n\n"
                    f"You can manually update by visiting:\n{release_url}"
                )
        except Exception as e:
            self.log(f"✗ Error updating: {e}")
            messagebox.showerror(
                "Update Error",
                f"Could not update application:\n\n{str(e)}\n\n"
                f"You can manually download the latest version from:\n{release_url}"
            )

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
