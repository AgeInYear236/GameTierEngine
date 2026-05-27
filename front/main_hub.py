import sys
import os
import subprocess
import tkinter as tk
from tkinter import messagebox
import api_client
from login_manager import AuthWindow

# CONFIGURATION: Указываем напрямую файлы сценариев Python
CALCULATOR_SCRIPT = "game_calculator.py"
VIEWER_SCRIPT = "tier_list_viewer.py"


class GameHubLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🎮 Game Evaluation & Tier List Hub")
        self.root.geometry("500x500")
        self.root.configure(bg="#141414")
        self.root.resizable(True, True)
        if os.path.exists("/app_icon.ico"):
            self.root.iconbitmap("/app_icon.ico")

        # Header
        self.header_frame = tk.Frame(self.root, bg="#1e1e1e", pady=20)
        self.header_frame.pack(fill="x")
        tk.Label(self.header_frame, text="GAME RANKING ENGINE", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="#00ffcc").pack()
        tk.Label(self.header_frame, text="Central Management Suite", font=("Arial", 10, "italic"), bg="#1e1e1e", fg="#888888").pack(pady=(2, 0))

        self.lbl_user_status = tk.Label(
            self.root, text="Not logged in", font=("Arial", 10, "bold"), 
            bg="#1a1a1a", fg="#888888"
        )
        self.lbl_user_status.pack(anchor="nw", padx=10, pady=5)

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

        # Buttons
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

        self.check_login_status()

    def check_login_status(self):
        user = api_client.get_current_user()
        if user:
            self.lbl_user_status.config(
                text=f"Logged in as: {user}", 
                fg="#00ffcc"
            )
        self.root.after(1000, self.check_login_status)

    def open_user_directory(self):
        from user_directory import UserDirectory
        UserDirectory(self.root)

    def open_explorer(self):
        from game_explorer import GameExplorer
        GameExplorer(self.root)

    def open_auth(self):
        AuthWindow(self.root, lambda: self.lbl_status.config(text="✅ Authenticated.", fg="#00ffcc"))

    def launch_script(self, script_name, description):
        """Запускает дочерний скрипт .py в отдельном процессе Python, передавая токен авторизации."""
        # Находим папку, где лежит ТЕКУЩИЙ файл лаунчера
        base_path = os.path.dirname(os.path.abspath(__file__))
        target_script_path = os.path.join(base_path, script_name)

        # Проверяем, существует ли файл скрипта вообще
        if not os.path.exists(target_script_path):
            messagebox.showerror(
                "Launcher Error", 
                f"Не удалось найти файл подсистемы:\n{script_name}\n\nОжидался путь: {target_script_path}"
            )
            return

        self.lbl_status.config(text=f"🚀 Запуск {description}...", fg="#00ffcc")
        self.root.update_idletasks()

        token_arg = api_client.TOKEN if api_client.TOKEN else "None"

        try:
            # ЧИСТЫЙ ЗАПУСК ЧЕРЕЗ ТЕКУЩИЙ ИНТЕРПРЕТАТОР PYTHON:
            # Выполняет команду вида: python path/to/script.py <token>
            subprocess.Popen([sys.executable, target_script_path, token_arg])
                
            self.lbl_status.config(text=f"✅ {description} успешно запущен.", fg="#aaaaaa")
        except Exception as e:
            messagebox.showerror("Execution Fault", f"Ошибка инициализации процесса:\n{e}")

    def launch_with_auth(self, script_name, description):
        """Проверяет токен перед запуском скрипта."""
        if api_client.TOKEN is None:
            # Если не авторизован, сначала показываем окно логина
            AuthWindow(self.root, lambda: self.launch_script(script_name, description))
        else:
            # Если уже залогинен — запускаем скрипт сразу
            self.launch_script(script_name, description)

    def launch_calculator(self):
        self.launch_with_auth(CALCULATOR_SCRIPT, "Game Calculator Menu")

    def launch_viewer(self):
        self.launch_with_auth(VIEWER_SCRIPT, "Visual Tier List Board")


if __name__ == "__main__":
    root = tk.Tk()
    app = GameHubLauncher(root)
    root.mainloop()