import tkinter as tk
from tkinter import ttk, messagebox

from models.product import ProductModel
from models.category import CategoryModel
from ui.add_product_dialog import AddProductDialog


class ProductFrame(ttk.Frame):
    """Product management screen – add, edit, delete products."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.category_model = CategoryModel(db)
        self._build_ui()

    def _build_ui(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Form ──────────────────────────────────────────────────
        form = ttk.LabelFrame(self, text="Product Details")
        form.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        labels = ["Name", "Barcode", "Price", "Stock", "Category"]
        self.entries = {}

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
        ttk.Button(
            btn_frame, text="+ New Product", command=self._open_add_dialog
        ).pack(side="left", padx=5)
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
        cols = ("id", "name", "barcode", "price", "stock", "category")
        self.tree = ttk.Treeview(self, columns=cols, show="headings", height=18)
        for c in cols:
            self.tree.heading(c, text=c.capitalize())
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("name", width=180)
        self.tree.column("barcode", width=120)
        self.tree.column("price", width=80, anchor="e")
        self.tree.column("stock", width=60, anchor="center")
        self.tree.column("category", width=120)
        self.tree.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._load_categories()
        self._load_products()

    def _load_categories(self):
        try:
            cats = self.category_model.get_all()
            self._categories = {c["name"]: c["id"] for c in cats}
            self.cat_combo["values"] = list(self._categories.keys())
        except Exception:
            self._categories = {}

    def _load_products(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        try:
            for p in self.product_model.get_all():
                self.tree.insert(
                    "",
                    "end",
                    values=(
                        p["id"],
                        p["name"],
                        p["barcode"] or "",
                        f'{p["price"]:.2f}',
                        p["stock"],
                        p.get("category_name") or "",
                    ),
                )
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _on_select(self, _event):
        selected = self.tree.focus()
        if not selected:
            return
        vals = self.tree.item(selected, "values")
        self.entries["name"].set(vals[1])
        self.entries["barcode"].set(vals[2])
        self.entries["price"].set(vals[3])
        self.entries["stock"].set(vals[4])
        self.cat_combo.set(vals[5])

    def _get_category_id(self):
        name = self.cat_combo.get()
        return self._categories.get(name)

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
        selected = self.tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Select a product first.")
            return
        product_id = int(self.tree.item(selected, "values")[0])
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
        selected = self.tree.focus()
        if not selected:
            return
        product_id = int(self.tree.item(selected, "values")[0])
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

    def _open_add_dialog(self):
        AddProductDialog(self.winfo_toplevel(), self.db, on_save=self._load_products)
