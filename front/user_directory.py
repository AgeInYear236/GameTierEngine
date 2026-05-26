import tkinter as tk
from tkinter import ttk
import requests
import api_client

class UserDirectory:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("System Users Directory")
        self.window.geometry("300x400")

        tk.Label(self.window, text="Registered Users", font=("Arial", 12, "bold")).pack(pady=10)
        
        # Create a treeview table
        self.tree = ttk.Treeview(self.window, columns=("User", "Games"), show="headings")
        self.tree.heading("User", text="Username")
        self.tree.heading("Games", text="Rated Games")
        self.tree.column("Games", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.load_data()

    def load_data(self):
        try:
            response = requests.get(f"{api_client.BASE_URL}/users_stats")
            if response.status_code == 200:
                for user in response.json():
                    self.tree.insert("", "end", values=(user['username'], user['game_count']))
        except Exception as e:
            print(f"Error fetching stats: {e}")