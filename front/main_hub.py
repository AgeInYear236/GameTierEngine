import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import api_client
from login_manager import AuthWindow

# CONFIGURATION: Point directly to the companion EXEs that will sit in the same folder
CALCULATOR_EXE = "game_calculator.py"
VIEWER_EXE = "tier_list_viewer.py"


class GameHubLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Game Evaluation & Tier List Hub")
        self.root.geometry("500x500")
        self.root.configure(bg="#141414")
        self.root.resizable(True, True)

        # Header
        self.header_frame = tk.Frame(self.root, bg="#1e1e1e", pady=20)
        self.header_frame.pack(fill="x")
        tk.Label(self.header_frame, text="GAME RANKING ENGINE", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00ffcc").pack()
        tk.Label(self.header_frame, text="Central Management Suite", font=("Arial", 10, "italic"), bg="#1e1e1e", fg="#888888").pack(pady=(2, 0))

        # Buttons Container
        self.button_container = tk.Frame(self.root, bg="#141414", pady=30)
        self.button_container.pack(fill="both", expand=True, padx=40)

        self.btn_calc = tk.Button(
            self.button_container, text="➕ Rank & Log New Game Entry", font=("Arial", 12, "bold"),
            bg="#2b2b2b", fg="white", activebackground="#007acc", activeforeground="white",
            bd=1, relief="solid", pady=15, command=self.launch_calculator
        )
        self.btn_calc.pack(fill="x", pady=10)

        self.btn_viewer = tk.Button(
            self.button_container, text="🏆 Open Tier List Board", font=("Arial", 12, "bold"),
            bg="#2b2b2b", fg="white", activebackground="#27ae60", activeforeground="white",
            bd=1, relief="solid", pady=15, command=self.launch_viewer
        )
        self.btn_viewer.pack(fill="x", pady=10)

        # Status Bar
        self.status_bar = tk.Frame(self.root, bg="#1e1e1e", pady=8, padx=10)
        self.status_bar.pack(fill="x", side="bottom")
        self.lbl_status = tk.Label(self.status_bar, text="Ready to launch subsystems.", font=("Arial", 9), bg="#1e1e1e", fg="#aaaaaa")
        self.lbl_status.pack(side="left")

        # Inside your GameHubLauncher class __init__:
        self.btn_auth = tk.Button(
        self.button_container, text="👤 Login / Register Account", font=("Arial", 10),
            bg="#007f22", fg="white", command=self.open_auth
        )
        self.btn_auth.pack(fill="x", pady=(0, 20))

        self.btn_users = tk.Button(
        self.button_container, text="👥 View All Users", font=("Arial", 12, "bold"),
            bg="#2b2b2b", fg="white", command=self.open_user_directory
        )
        self.btn_users.pack(fill="x", pady=10)

        self.btn_explore = tk.Button(
        self.button_container, text="🔍 Explore Games", font=("Arial", 12),
            bg="#4a4a4a", fg="white", command=self.open_explorer
        )
        self.btn_explore.pack(fill="x", pady=10)

    def open_user_directory(self):
        from user_directory import UserDirectory
        UserDirectory(self.root)

    def open_explorer(self):
        from game_explorer import GameExplorer
        GameExplorer(self.root)

    def open_auth(self):
        AuthWindow(self.root, lambda: self.lbl_status.config(text="✅ Authenticated.", fg="#00ffcc"))

    def launch_exe(self, exe_name, description):
        """Launches a compiled companion executable sitting right next to this file."""
        # Detect the exact folder where this launcher EXE is currently sitting
        base_path = os.path.dirname(sys.argv[0]) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
        target_exe_path = os.path.join(base_path, exe_name)

        # If running raw in your IDE/Code Editor, look for the .py fallback instead
        if not getattr(sys, 'frozen', False):
            py_fallback = exe_name.replace(".exe", ".py")
            target_exe_path = os.path.join(base_path, py_fallback)

        if not os.path.exists(target_exe_path):
            messagebox.showerror("Launcher Error", f"Could not locate subsystem module:\n{exe_name}\n\nExpected at: {target_exe_path}")
            return

        self.lbl_status.config(text=f"🚀 Launching {description}...", fg="#00ffcc")
        self.root.update_idletasks()

        token_arg = api_client.TOKEN if api_client.TOKEN else "None"

        try:
            # Open the target executable (or raw script fallback) as a separate Windows process
            if getattr(sys, 'frozen', False):
                subprocess.Popen([target_exe_path, token_arg])
            else:
                subprocess.Popen([sys.executable, target_exe_path, token_arg])
                
            self.lbl_status.config(text=f"✅ {description} opened.", fg="#aaaaaa")
        except Exception as e:
            messagebox.showerror("Execution Fault", f"Failed to initialize process window:\n{e}")

    def launch_with_auth(self, exe_name, description):
        """Helper to ensure login before launching any EXE."""
        if api_client.TOKEN is None:
            # If not logged in, open the login window first
            # The callback 'lambda' ensures we launch the target ONLY after success
            LoginWindow(self.root, lambda: self.launch_exe(exe_name, description))
        else:
            # Already logged in, launch immediately
            self.launch_exe(exe_name, description)

    def launch_calculator(self):
        self.launch_with_auth(CALCULATOR_EXE, "Game Calculator Menu")

    def launch_viewer(self):
        self.launch_with_auth(VIEWER_EXE, "Visual Tier List Board")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHubLauncher(root)
    root.mainloop()