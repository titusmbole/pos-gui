import os
import tkinter as tk
from tkinter import ttk
import pygubu


# Hardcoded credentials – replace with DB auth later
VALID_USERNAME = "admin"
VALID_PASSWORD = "admin"

UI_DIR = os.path.join(os.path.dirname(__file__), "xml")


class LoginWindow:
    """Login screen loaded from XML via pygubu."""

    def __init__(self, on_success):
        """
        on_success: callback invoked (with no args) after successful login.
        """
        self.on_success = on_success

        self.root = tk.Tk()
        self.root.title("POS System - Login")
        self.root.geometry("500x450")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")

        # Build UI from XML
        self.builder = pygubu.Builder()
        self.builder.add_from_file(os.path.join(UI_DIR, "login.ui"))
        self.main_frame = self.builder.get_object("login_frame", self.root)

        # Get widget references
        self.username_entry = self.builder.get_object("username_entry")
        self.password_entry = self.builder.get_object("password_entry")
        self.error_label = self.builder.get_object("error_label")

        # Connect callbacks
        self.builder.connect_callbacks(self)

        # Bind Enter key
        self.root.bind("<Return>", lambda e: self.on_login())

        # Focus username field
        self.username_entry.focus_set()

        self._center_window()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_label.configure(text="Please enter username and password")
            return

        if username == VALID_USERNAME and password == VALID_PASSWORD:
            self.error_label.configure(text="")
            self.root.destroy()
            self.on_success()
        else:
            self.error_label.configure(text="Invalid username or password")
            self.password_entry.delete(0, "end")

    def run(self):
        self.root.mainloop()
