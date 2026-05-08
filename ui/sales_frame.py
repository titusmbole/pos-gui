import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from models.sale import SaleModel


class SalesFrame(ttk.Frame):
    """View sales history and daily summary."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.sale_model = SaleModel(db)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Summary bar ──────────────────────────────────────────
        summary_frame = ttk.LabelFrame(self, text="Daily Summary")
        summary_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        self.summary_var = tk.StringVar(value="Sales: 0 | Revenue: $0.00")
        ttk.Label(
            summary_frame, textvariable=self.summary_var, font=("Arial", 13)
        ).pack(side="left", padx=10, pady=5)

        ttk.Button(summary_frame, text="Refresh", command=self._load).pack(
            side="right", padx=10
        )

        # ── Sales table ──────────────────────────────────────────
        cols = ("id", "total", "payment", "date")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=60, anchor="center")
        self.tree.column("total", width=100, anchor="e")
        self.tree.column("payment", width=100, anchor="center")
        self.tree.column("date", width=180)
        self.tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        self._load()

    def _load(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            for s in self.sale_model.get_all():
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        s["id"],
                        f'{s["total"]:.2f}',
                        s["payment_method"],
                        str(s["created_at"]),
                    ),
                )
            summary = self.sale_model.get_daily_summary(str(date.today()))
            if summary:
                self.summary_var.set(
                    f'Sales: {summary["total_sales"]} | '
                    f'Revenue: ${float(summary["revenue"]):.2f}'
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))
