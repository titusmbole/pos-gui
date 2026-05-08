import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from models.session import session
from models.product import ProductModel
from models.sale import SaleModel
from ui.table import Table


class DashboardFrame(ttk.Frame):
    """Dashboard with welcome greeting, summaries, and quick actions."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.sale_model = SaleModel(db)

        self._build_ui()
        self._load_summaries()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)

        # ── Welcome greeting ──────────────────────────────────────
        greeting_frame = ttk.Frame(self)
        greeting_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=15, pady=(15, 5))

        name = session.full_name or session.username or "User"
        role = session.role or ""
        ttk.Label(
            greeting_frame,
            text=f"Welcome back, {name}!",
            font=("Arial", 20, "bold"),
        ).pack(side="left")
        ttk.Label(
            greeting_frame,
            text=f"  [{role}]",
            font=("Arial", 12),
            foreground="gray",
        ).pack(side="left", padx=10)

        # ── Summary cards ─────────────────────────────────────────
        cards_frame = ttk.Frame(self)
        cards_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1)

        self.cards = {}
        card_defs = [
            ("today_sales", "Today's Sales", "0"),
            ("today_revenue", "Today's Revenue", "$0.00"),
            ("total_products", "Total Products", "0"),
            ("low_stock", "Low Stock Items", "0"),
        ]

        for i, (key, title, default) in enumerate(card_defs):
            card = ttk.LabelFrame(cards_frame, text=title, padding=15)
            card.grid(row=0, column=i, padx=8, pady=5, sticky="nsew")
            lbl = ttk.Label(card, text=default, font=("Arial", 22, "bold"), anchor="center")
            lbl.pack(fill="x", expand=True)
            self.cards[key] = lbl

        # ── Quick Actions ─────────────────────────────────────────
        actions_frame = ttk.LabelFrame(self, text="Quick Actions", padding=15)
        actions_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        actions = [
            ("New Sale", self._goto_pos),
            ("Add Product", self._open_add_product),
            ("View Sales History", self._goto_sales),
            ("Refresh Dashboard", self._load_summaries),
        ]

        for text, cmd in actions:
            btn = ttk.Button(actions_frame, text=text, command=cmd)
            btn.pack(fill="x", pady=5, ipady=5)

        # ── Recent Sales ──────────────────────────────────────────
        recent_frame = ttk.LabelFrame(self, text="Recent Sales (Today)", padding=10)
        recent_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)
        recent_frame.columnconfigure(0, weight=1)
        recent_frame.rowconfigure(0, weight=1)

        self.recent_table = Table(recent_frame, columns=[
            {"key": "id", "label": "#", "width": 60, "anchor": "center", "stretch": False},
            {"key": "total", "label": "Total", "width": 120, "anchor": "e", "stretch": False},
            {"key": "payment", "label": "Payment", "width": 120, "anchor": "center", "stretch": True},
            {"key": "time", "label": "Time", "width": 200, "anchor": "w", "stretch": True},
        ])
        self.recent_table.grid(row=0, column=0, sticky="nsew")

    def _load_summaries(self):
        try:
            today = str(date.today())
            summary = self.sale_model.get_daily_summary(today)
            if summary:
                self.cards["today_sales"].configure(text=str(summary["total_sales"]))
                self.cards["today_revenue"].configure(
                    text=f'${float(summary["revenue"]):.2f}'
                )

            products = self.product_model.get_all()
            self.cards["total_products"].configure(text=str(len(products)))
            low_stock = sum(1 for p in products if p["stock"] <= 5)
            self.cards["low_stock"].configure(text=str(low_stock))

            # Recent sales
            sales = self.sale_model.get_all()
            data = [
                {
                    "id": s["id"],
                    "total": f'${s["total"]:.2f}',
                    "payment": s["payment_method"],
                    "time": str(s["created_at"]),
                }
                for s in sales[:10]
            ]
            self.recent_table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load dashboard:\n{e}")

    def _goto_pos(self):
        notebook = self.master
        notebook.select(1)  # POS tab (index 1 after Dashboard)

    def _goto_sales(self):
        notebook = self.master
        notebook.select(3)  # Sales tab

    def _open_add_product(self):
        from ui.add_product_dialog import AddProductDialog
        AddProductDialog(self.winfo_toplevel(), self.db, on_save=self._load_summaries)
