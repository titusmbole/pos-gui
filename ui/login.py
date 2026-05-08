import tkinter as tk
from tkinter import ttk

from models.user import UserModel
from models.session import session


class LoginWindow:
    """Login screen – authenticates against the users table."""

    def __init__(self, db, on_success):
        """
        db: Database instance (already connected)
        on_success: callback invoked after successful login
        """
        self.db = db
        self.user_model = UserModel(db)
        self.on_success = on_success

        self.root = tk.Tk()
        self.root.title("POS System - Login")
        self.root.geometry("800x750")
        self.root.resizable(False, False)

        style = ttk.Style()
        style.theme_use("clam")

        self._build_ui()
        self._center_window()

    def _build_ui(self):
        outer = ttk.Frame(self.root, padding=40)
        outer.pack(fill="both", expand=True)

        ttk.Frame(outer).pack(expand=True, fill="both")

        card = ttk.LabelFrame(outer, text="Login", padding=30)
        card.pack(padx=100, pady=10)

        ttk.Label(card, text="POS System", font=("Arial", 22, "bold"), anchor="center").pack(
            fill="x", pady=(0, 20)
        )
        ttk.Label(card, text="Sign in to continue", anchor="center").pack(
            fill="x", pady=(0, 20)
        )

        ttk.Label(card, text="Username", anchor="w").pack(fill="x", pady=(5, 2))
        self.username_entry = ttk.Entry(card, width=30)
        self.username_entry.pack(fill="x", pady=(0, 10))

        ttk.Label(card, text="Password", anchor="w").pack(fill="x", pady=(5, 2))
        self.password_entry = ttk.Entry(card, width=30, show="\u2022")
        self.password_entry.pack(fill="x", pady=(0, 5))

        self.error_var = tk.StringVar(value=" ")
        ttk.Label(card, textvariable=self.error_var, foreground="red", anchor="center").pack(
            fill="x", pady=5
        )

        ttk.Button(card, text="Login", command=self._on_login).pack(
            fill="x", pady=(10, 5), ipady=5
        )

        ttk.Label(card, text="\u00a9 2026 POS System", anchor="center", foreground="gray").pack(
            fill="x", pady=(15, 0)
        )

        ttk.Frame(outer).pack(expand=True, fill="both")

        self.root.bind("<Return>", lambda e: self._on_login())
        self.username_entry.focus_set()

    def _center_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (w // 2)
        y = (self.root.winfo_screenheight() // 2) - (h // 2)
        self.root.geometry(f"+{x}+{y}")

    def _on_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.error_var.set("Please enter username and password")
            return

        user = self.user_model.authenticate(username, password)
        if user:
            session.login(user)
            self.error_var.set("")
            self.root.destroy()
            self.on_success()
        else:
            self.error_var.set("Invalid username or password")
            self.password_entry.delete(0, "end")

    def run(self):
        self.root.mainloop()
