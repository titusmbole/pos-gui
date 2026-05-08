import tkinter as tk
from tkinter import ttk, messagebox

from models.product import ProductModel
from models.category import CategoryModel
from ui.add_product_dialog import AddProductDialog
from ui.table import Table


class ProductFrame(ttk.Frame):
    """Product management screen."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.category_model = CategoryModel(db)
        self.entries = {}
        self._categories = {}

        self._build_ui()
        self._load_categories()
        self._load_products()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Form ──────────────────────────────────────────────────
        form = ttk.LabelFrame(self, text="Product Details")
        form.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        labels = ["Name", "Barcode", "Price", "Stock", "Category"]
        for i, lbl in enumerate(labels):
            ttk.Label(form, text=lbl + ":").grid(row=0, column=i * 2, padx=5, pady=5)
            if lbl == "Category":
                self.cat_combo = ttk.Combobox(form, width=14, state="readonly")
                self.cat_combo.grid(row=0, column=i * 2 + 1, padx=5, pady=5)
            else:
                var = tk.StringVar()
                entry = ttk.Entry(form, textvariable=var, width=16)
                entry.grid(row=0, column=i * 2 + 1, padx=5, pady=5)
                self.entries[lbl.lower()] = var

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=1, column=0, columnspan=10, pady=5)
        ttk.Button(btn_frame, text="+ New Product", command=self._open_add_dialog).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Add", command=self._add).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Update", command=self._update).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Delete", command=self._delete).pack(
            side="left", padx=5
        )
        ttk.Button(btn_frame, text="Clear", command=self._clear_form).pack(
            side="left", padx=5
        )

        # ── Table ─────────────────────────────────────────────────
        self.table = Table(self, columns=[
            {"key": "id", "label": "Id", "width": 60, "anchor": "center", "stretch": False},
            {"key": "name", "label": "Name", "width": 250, "anchor": "w", "stretch": True},
            {"key": "barcode", "label": "Barcode", "width": 150, "anchor": "w", "stretch": True},
            {"key": "price", "label": "Price", "width": 120, "anchor": "e", "stretch": False},
            {"key": "stock", "label": "Stock", "width": 80, "anchor": "center", "stretch": False},
            {"key": "category", "label": "Category", "width": 150, "anchor": "w", "stretch": True},
        ], on_select=self._on_select)
        self.table.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

    # ── Actions ───────────────────────────────────────────────

    def _open_add_dialog(self):
        AddProductDialog(self.winfo_toplevel(), self.db, on_save=self._load_products)

    def _add(self):
        try:
            self.product_model.add(
                self.entries["name"].get(),
                self.entries["barcode"].get() or None,
                float(self.entries["price"].get()),
                int(self.entries["stock"].get()),
                self._get_category_id(),
            )
            self._load_products()
            self._clear_form()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _update(self):
        row = self.table.get_selected()
        if not row:
            messagebox.showwarning("Select", "Select a product first.")
            return
        product_id = row["id"]
        try:
            self.product_model.update(
                product_id,
                self.entries["name"].get(),
                self.entries["barcode"].get() or None,
                float(self.entries["price"].get()),
                int(self.entries["stock"].get()),
                self._get_category_id(),
            )
            self._load_products()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _delete(self):
        row = self.table.get_selected()
        if not row:
            return
        product_id = row["id"]
        if messagebox.askyesno("Confirm", "Delete this product?"):
            try:
                self.product_model.delete(product_id)
                self._load_products()
                self._clear_form()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _clear_form(self):
        for var in self.entries.values():
            var.set("")
        self.cat_combo.set("")

    # ── Helpers ───────────────────────────────────────────────

    def _on_select(self, row):
        self.entries["name"].set(row.get("name", ""))
        self.entries["barcode"].set(row.get("barcode", ""))
        self.entries["price"].set(row.get("price", ""))
        self.entries["stock"].set(row.get("stock", ""))
        self.cat_combo.set(row.get("category", ""))

    def _get_category_id(self):
        name = self.cat_combo.get()
        return self._categories.get(name)

    def _load_categories(self):
        try:
            cats = self.category_model.get_all()
            self._categories = {c["name"]: c["id"] for c in cats}
            self.cat_combo["values"] = list(self._categories.keys())
        except Exception:
            self._categories = {}

    def _load_products(self):
        try:
            products = self.product_model.get_all()
            data = [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "barcode": p["barcode"] or "",
                    "price": f'{p["price"]:.2f}',
                    "stock": p["stock"],
                    "category": p.get("category_name") or "",
                }
                for p in products
            ]
            self.table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", str(e))
