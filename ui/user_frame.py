import tkinter as tk
from tkinter import ttk, messagebox

from models.user import UserModel
from models.session import session
from ui.table import Table
from ui.add_user_dialog import AddUserDialog


class UserFrame(ttk.Frame):
    """User management screen (Admin only)."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.user_model = UserModel(db)

        self._build_ui()
        self._load_users()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Toolbar ───────────────────────────────────────────────
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        ttk.Button(toolbar, text="+ Add User", command=self._add).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Edit", command=self._edit).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Reset Password", command=self._reset_password).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Deactivate", command=self._deactivate).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Activate", command=self._activate).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Delete", command=self._delete).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Refresh", command=self._load_users).pack(side="right", padx=5)

        # ── Table ─────────────────────────────────────────────────
        self.table = Table(self, columns=[
            {"key": "id", "label": "Id", "width": 50, "anchor": "center", "stretch": False},
            {"key": "full_name", "label": "Full Name", "width": 180, "anchor": "w", "stretch": True},
            {"key": "username", "label": "Username", "width": 130, "anchor": "w", "stretch": True},
            {"key": "email", "label": "Email", "width": 220, "anchor": "w", "stretch": True},
            {"key": "role", "label": "Role", "width": 90, "anchor": "center", "stretch": False},
            {"key": "status", "label": "Status", "width": 90, "anchor": "center", "stretch": False},
            {"key": "created_at", "label": "Created", "width": 160, "anchor": "w", "stretch": False},
        ])
        self.table.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # ── Actions ───────────────────────────────────────────────

    def _add(self):
        AddUserDialog(self.winfo_toplevel(), self.db, on_save=self._load_users)

    def _edit(self):
        row = self.table.get_selected()
        if not row:
            messagebox.showwarning("Select", "Select a user first.")
            return
        self._open_edit_dialog(row)

    def _open_edit_dialog(self, user_row):
        dlg = tk.Toplevel(self.winfo_toplevel())
        dlg.title("Edit User")
        dlg.geometry("820x620")
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Edit User", font=("Segoe UI", 14, "bold")).grid(
            row=0, column=0, columnspan=2, pady=(0, 15)
        )

        entries = {}
        for i, (label, key) in enumerate([
            ("Full Name", "full_name"),
            ("Username", "username"),
            ("Email", "email"),
        ], start=1):
            ttk.Label(frame, text=label + ":").grid(row=i, column=0, sticky="w", padx=5, pady=6)
            var = tk.StringVar(value=user_row.get(key, ""))
            ttk.Entry(frame, textvariable=var, width=30).grid(row=i, column=1, padx=5, pady=6)
            entries[key] = var

        ttk.Label(frame, text="Role:").grid(row=4, column=0, sticky="w", padx=5, pady=6)
        role_var = tk.StringVar(value=user_row.get("role", "Cashier"))
        ttk.Combobox(frame, textvariable=role_var, values=["Admin", "Cashier"],
                     state="readonly", width=27).grid(row=4, column=1, padx=5, pady=6)

        def save():
            fn = entries["full_name"].get().strip()
            un = entries["username"].get().strip()
            em = entries["email"].get().strip()
            rl = role_var.get()
            if not all([fn, un, em]):
                messagebox.showwarning("Required", "All fields are required.", parent=dlg)
                return
            try:
                self.user_model.update(user_row["id"], un, em, fn, rl)
                messagebox.showinfo("Success", "User updated.", parent=dlg)
                self._load_users()
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="Save", command=save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side="left", padx=10)

    def _reset_password(self):
        row = self.table.get_selected()
        if not row:
            messagebox.showwarning("Select", "Select a user first.")
            return

        dlg = tk.Toplevel(self.winfo_toplevel())
        dlg.title("Reset Password")
        dlg.geometry("680x320")
        dlg.resizable(False, False)
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text=f"Reset password for: {row['username']}",
                  font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 15))

        ttk.Label(frame, text="New Password:").grid(row=1, column=0, sticky="w", padx=5, pady=6)
        pw_var = tk.StringVar()
        ttk.Entry(frame, textvariable=pw_var, show="*", width=25).grid(row=1, column=1, padx=5, pady=6)

        ttk.Label(frame, text="Confirm:").grid(row=2, column=0, sticky="w", padx=5, pady=6)
        confirm_var = tk.StringVar()
        ttk.Entry(frame, textvariable=confirm_var, show="*", width=25).grid(row=2, column=1, padx=5, pady=6)

        def save():
            pw = pw_var.get()
            cf = confirm_var.get()
            if not pw:
                messagebox.showwarning("Required", "Enter a password.", parent=dlg)
                return
            if pw != cf:
                messagebox.showwarning("Mismatch", "Passwords do not match.", parent=dlg)
                return
            if len(pw) < 6:
                messagebox.showwarning("Weak", "Password must be at least 6 characters.", parent=dlg)
                return
            try:
                self.user_model.change_password(row["id"], pw)
                messagebox.showinfo("Success", "Password reset.", parent=dlg)
                dlg.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e), parent=dlg)

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(btn_frame, text="Reset", command=save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=dlg.destroy).pack(side="left", padx=10)

    def _deactivate(self):
        row = self.table.get_selected()
        if not row:
            return
        if row["id"] == session.user_id:
            messagebox.showwarning("Error", "Cannot deactivate yourself.")
            return
        if messagebox.askyesno("Confirm", f"Deactivate user '{row['username']}'?"):
            try:
                self.user_model.deactivate(row["id"])
                messagebox.showinfo("Done", "User deactivated.")
                self._load_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _activate(self):
        row = self.table.get_selected()
        if not row:
            return
        try:
            self.db.execute_query(
                "UPDATE users SET is_active=TRUE WHERE id=%s", (row["id"],)
            )
            messagebox.showinfo("Done", "User activated.")
            self._load_users()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        row = self.table.get_selected()
        if not row:
            return
        if row["id"] == session.user_id:
            messagebox.showwarning("Error", "Cannot delete yourself.")
            return
        if messagebox.askyesno("Confirm", f"Permanently delete user '{row['username']}'?"):
            try:
                self.db.execute_query("DELETE FROM users WHERE id=%s", (row["id"],))
                messagebox.showinfo("Done", "User deleted.")
                self._load_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ── Helpers ───────────────────────────────────────────────

    def _load_users(self):
        try:
            users = self.user_model.get_all()
            data = [
                {
                    "id": u["id"],
                    "full_name": u["full_name"],
                    "username": u["username"],
                    "email": u["email"],
                    "role": u["role"],
                    "status": "Active" if u["is_active"] else "Inactive",
                    "created_at": str(u["created_at"]),
                }
                for u in users
            ]
            self.table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", str(e))
