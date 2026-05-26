import tkinter as tk
from tkinter import ttk
import requests
import api_client

class GameExplorer:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Global Game Library")
        self.window.geometry("400x500")

        tk.Label(self.window, text="Search for a game:").pack(pady=5)
        self.entry = tk.Entry(self.window)
        self.entry.pack(fill="x", padx=10)
        self.entry.bind("<KeyRelease>", self.search)

        self.listbox = tk.Listbox(self.window)
        self.listbox.pack(fill="both", expand=True, padx=10, pady=10)
        self.listbox.bind("<<ListboxSelect>>", self.show_stats)

        self.results = []

    def search(self, event):
        query = self.entry.get()
        if len(query) < 2: return
        
        response = requests.get(f"{api_client.BASE_URL}/search_games?q={query}")
        self.results = response.json()
        self.listbox.delete(0, tk.END)
        for game in self.results:
            self.listbox.insert(tk.END, game['name'])

    def show_stats(self, event):
        idx = self.listbox.curselection()
        if not idx: return
        game = self.results[idx[0]]
        tk.messagebox.showinfo("Stats", f"{game['name']}\nAverage Score: {game['avg_score']}\nRated by {game['count']} users.")