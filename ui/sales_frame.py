import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from models.sale import SaleModel
from ui.table import Table


class SalesFrame(ttk.Frame):
    """View sales history and daily summary."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.sale_model = SaleModel(db)

        self._build_ui()
        self._load()

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
        self.table = Table(self, columns=[
            {"key": "id", "label": "Id", "width": 60, "anchor": "center", "stretch": False},
            {"key": "total", "label": "Total", "width": 150, "anchor": "e", "stretch": False},
            {"key": "payment", "label": "Payment", "width": 150, "anchor": "center", "stretch": False},
            {"key": "date", "label": "Date", "width": 250, "anchor": "w", "stretch": True},
        ])
        self.table.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    def _load(self):
        try:
            sales = self.sale_model.get_all()
            data = [
                {
                    "id": s["id"],
                    "total": f'{s["total"]:.2f}',
                    "payment": s["payment_method"],
                    "date": str(s["created_at"]),
                }
                for s in sales
            ]
            self.table.set_data(data)

            summary = self.sale_model.get_daily_summary(str(date.today()))
            if summary:
                self.summary_var.set(
                    f'Sales: {summary["total_sales"]} | '
                    f'Revenue: ${float(summary["revenue"]):.2f}'
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))
