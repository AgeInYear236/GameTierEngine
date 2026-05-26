import tkinter as tk
from tkinter import messagebox
import api_client

class AuthWindow:
    def __init__(self, parent, on_success):
        self.window = tk.Toplevel(parent)
        self.window.title("Authentication")
        self.window.geometry("300x250")

        tk.Label(self.window, text="Username:").pack(pady=(10, 0))
        self.entry_user = tk.Entry(self.window)
        self.entry_user.pack()

        tk.Label(self.window, text="Password:").pack(pady=(10, 0))
        self.entry_pass = tk.Entry(self.window, show="*")
        self.entry_pass.pack()

        # Buttons for Login and Register
        tk.Button(self.window, text="Login", command=lambda: self.handle_auth("login")).pack(pady=10)
        tk.Button(self.window, text="Register", command=lambda: self.handle_auth("register")).pack()

        self.on_success = on_success

    def handle_auth(self, mode):
        username = self.entry_user.get()
        password = self.entry_pass.get()
        
        # Logic to either register or login
        if mode == "register":
            # Add a POST /register call to your api_client
            success, msg = api_client.register(username, password)
            if success: messagebox.showinfo("Success", "Registered! Now login.")
            else: messagebox.showerror("Error", msg)
        else:
            success, msg = api_client.login(username, password)
            if success:
                messagebox.showinfo("Success", "Logged in!")
                self.window.destroy()
                self.on_success()
            else:
                messagebox.showerror("Error", msg)