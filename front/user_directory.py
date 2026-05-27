import tkinter as tk
from tkinter import ttk, messagebox
import requests
import api_client

class UserDirectory:
    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("System Users Directory")
        self.window.geometry("400x500")
        self.window.attributes("-topmost", True)
        self.window.transient(parent)
        self.window.configure(bg="#1a1a1a")

        tk.Label(
            self.window, 
            text="Registered Users", 
            font=("Arial", 14, "bold"), 
            bg="#1a1a1a", 
            fg="#00ffcc"
        ).pack(pady=(15, 5))
        
        tk.Label(
            self.window, 
            text="💡 Double-click any user to inspect their Tier List Board", 
            font=("Arial", 9, "italic"), 
            bg="#1a1a1a", 
            fg="#888888"
        ).pack(pady=(0, 10))

        # Stylize the Treeview Table to match dark UI layout
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#252525", fieldbackground="#252525", foreground="white", rowheight=28)
        style.configure("Treeview.Heading", background="#333333", foreground="#00ffcc", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[("selected", "#007acc")])
        
        # Create a treeview table
        self.tree = ttk.Treeview(self.window, columns=("User", "Games"), show="headings")
        self.tree.heading("User", text="Username")
        self.tree.heading("Games", text="Rated Games")
        self.tree.column("User", width=200, anchor="w")
        self.tree.column("Games", width=120, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=15, pady=10)

        # BIND DOUBLE CLICK EVENT
        self.tree.bind("<Double-1>", self.on_user_double_click)

        self.load_data()

    def load_data(self):
        try:
            response = requests.get(f"{api_client.BASE_URL}/users_stats", timeout=5)
            if response.status_code == 200:
                for user in response.json():
                    self.tree.insert("", "end", values=(user['username'], user['game_count']))
        except Exception as e:
            print(f"Error fetching stats: {e}")

    def on_user_double_click(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
            
        selected_item = selected_items[0]
        clicked_username = self.tree.item(selected_item)['values'][0]
        
        # Import your TierListViewer here to avoid circular dependencies
        from tier_list_viewer import TierListViewer
        
        # Create a new top-level window instance
        viewer_window = tk.Toplevel(self.window)
        viewer_window.attributes("-topmost", True)
        
        # Instantiate your custom viewer, sending the target profile directly to init parameters
        app = TierListViewer(viewer_window, selected_profile=clicked_username)