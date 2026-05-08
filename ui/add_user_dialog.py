import tkinter as tk
from tkinter import ttk, messagebox

from models.user import UserModel


class AddUserDialog(tk.Toplevel):
    """Modal dialog for adding a new user."""

    ROLES = ["Cashier", "Admin"]

    def __init__(self, parent, db, on_save=None):
        super().__init__(parent)
        self.db = db
        self.user_model = UserModel(db)
        self.on_save = on_save

        self.title("Add New User")
        self.geometry("820x620")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.entries = {}
        self._build_ui()

        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.wait_window(self)

    def _build_ui(self):
        frame = ttk.Frame(self, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Add New User", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 15)
        )

        fields = [
            ("Full Name", "full_name"),
            ("Username", "username"),
            ("Email", "email"),
            ("Password", "password"),
            ("Confirm Password", "confirm_password"),
        ]

        for i, (label, key) in enumerate(fields, start=1):
            ttk.Label(frame, text=label + ":").grid(
                row=i, column=0, sticky="w", padx=5, pady=6
            )
            var = tk.StringVar()
            entry = ttk.Entry(frame, textvariable=var, width=30)
            if "password" in key.lower():
                entry.configure(show="*")
            entry.grid(row=i, column=1, padx=5, pady=6)
            self.entries[key] = var

        # Role
        row_idx = len(fields) + 1
        ttk.Label(frame, text="Role:").grid(
            row=row_idx, column=0, sticky="w", padx=5, pady=6
        )
        self.role_var = tk.StringVar(value="Cashier")
        ttk.Combobox(
            frame, textvariable=self.role_var, values=self.ROLES,
            state="readonly", width=27
        ).grid(row=row_idx, column=1, padx=5, pady=6)

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=row_idx + 1, column=0, columnspan=2, pady=(20, 0))

        ttk.Button(btn_frame, text="Save", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=10)

    def _save(self):
        full_name = self.entries["full_name"].get().strip()
        username = self.entries["username"].get().strip()
        email = self.entries["email"].get().strip()
        password = self.entries["password"].get()
        confirm = self.entries["confirm_password"].get()
        role = self.role_var.get()

        if not all([full_name, username, email, password]):
            messagebox.showwarning("Required", "All fields are required.", parent=self)
            return

        if password != confirm:
            messagebox.showwarning("Mismatch", "Passwords do not match.", parent=self)
            return

        if len(password) < 6:
            messagebox.showwarning("Weak Password", "Password must be at least 6 characters.", parent=self)
            return

        try:
            self.user_model.add(username, email, password, full_name, role)
            messagebox.showinfo("Success", f"User '{username}' created.", parent=self)
            if self.on_save:
                self.on_save()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)
