import tkinter as tk
from tkinter import ttk, messagebox

from models.product import ProductModel
from models.sale import SaleModel
from ui.table import Table


class POSFrame(ttk.Frame):
    """Main point-of-sale checkout screen."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.sale_model = SaleModel(db)
        self.cart = []

        self._build_ui()
        self._load_products()

    def _build_ui(self):
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        # ── Search bar ────────────────────────────────────────────
        search_frame = ttk.LabelFrame(self, text="Search Product")
        search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=40)
        search_entry.pack(side="left", padx=5, pady=5)
        search_entry.bind("<Return>", lambda e: self._search_product())

        ttk.Button(search_frame, text="Search", command=self._search_product).pack(
            side="left", padx=5
        )

        # ── Product list (left) ───────────────────────────────────
        prod_frame = ttk.LabelFrame(self, text="Products")
        prod_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        prod_frame.columnconfigure(0, weight=1)
        prod_frame.rowconfigure(0, weight=1)

        self.product_table = Table(prod_frame, columns=[
            {"key": "id", "label": "Id", "width": 60, "anchor": "center", "stretch": False},
            {"key": "name", "label": "Name", "width": 250, "anchor": "w", "stretch": True},
            {"key": "price", "label": "Price", "width": 120, "anchor": "e", "stretch": False},
            {"key": "stock", "label": "Stock", "width": 80, "anchor": "center", "stretch": False},
        ])
        self.product_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        ttk.Button(prod_frame, text="Add to Cart", command=self._add_to_cart).grid(
            row=1, column=0, pady=5
        )

        # ── Cart (right) ──────────────────────────────────────────
        cart_frame = ttk.LabelFrame(self, text="Cart")
        cart_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        cart_frame.columnconfigure(0, weight=1)
        cart_frame.rowconfigure(0, weight=1)

        self.cart_table = Table(cart_frame, columns=[
            {"key": "name", "label": "Name", "width": 200, "anchor": "w", "stretch": True},
            {"key": "qty", "label": "Qty", "width": 60, "anchor": "center", "stretch": False},
            {"key": "price", "label": "Price", "width": 100, "anchor": "e", "stretch": False},
            {"key": "subtotal", "label": "Subtotal", "width": 100, "anchor": "e", "stretch": False},
        ])
        self.cart_table.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        btn_row = ttk.Frame(cart_frame)
        btn_row.grid(row=1, column=0, pady=5)
        ttk.Button(btn_row, text="Remove", command=self._remove_from_cart).pack(
            side="left", padx=5
        )
        ttk.Button(btn_row, text="Clear Cart", command=self._clear_cart).pack(
            side="left", padx=5
        )

        # ── Totals & checkout ─────────────────────────────────────
        checkout_frame = ttk.Frame(self)
        checkout_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.total_var = tk.StringVar(value="Total: $0.00")
        ttk.Label(
            checkout_frame, textvariable=self.total_var, font=("Arial", 16, "bold")
        ).pack(side="left", padx=20)

        self.payment_var = tk.StringVar(value="cash")
        ttk.Radiobutton(
            checkout_frame, text="Cash", variable=self.payment_var, value="cash"
        ).pack(side="left", padx=5)
        ttk.Radiobutton(
            checkout_frame, text="Card", variable=self.payment_var, value="card"
        ).pack(side="left", padx=5)

        ttk.Button(checkout_frame, text="Checkout", command=self._checkout).pack(
            side="right", padx=20
        )

    # ── Actions ───────────────────────────────────────────────────

    def _load_products(self):
        try:
            products = self.product_model.get_all()
            data = [
                {"id": p["id"], "name": p["name"], "price": f'{p["price"]:.2f}', "stock": p["stock"]}
                for p in products
            ]
            self.product_table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products:\n{e}")

    def _search_product(self):
        keyword = self.search_var.get().strip()
        try:
            products = (
                self.product_model.search(keyword)
                if keyword
                else self.product_model.get_all()
            )
            data = [
                {"id": p["id"], "name": p["name"], "price": f'{p["price"]:.2f}', "stock": p["stock"]}
                for p in products
            ]
            self.product_table.set_data(data)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed:\n{e}")

    def _add_to_cart(self):
        row = self.product_table.get_selected()
        if not row:
            messagebox.showwarning("Select", "Select a product first.")
            return
        product_id = int(row["id"])
        name = row["name"]
        price = float(row["price"])

        for item in self.cart:
            if item["product_id"] == product_id:
                item["quantity"] += 1
                item["subtotal"] = item["quantity"] * item["unit_price"]
                self._refresh_cart()
                return

        self.cart.append({
            "product_id": product_id,
            "name": name,
            "quantity": 1,
            "unit_price": price,
            "subtotal": price,
        })
        self._refresh_cart()

    def _remove_from_cart(self):
        idx = self.cart_table.get_selected_index()
        if idx is None:
            return
        self.cart.pop(idx)
        self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()

    def _refresh_cart(self):
        total = 0.0
        data = []
        for item in self.cart:
            data.append({
                "name": item["name"],
                "qty": item["quantity"],
                "price": f'{item["unit_price"]:.2f}',
                "subtotal": f'{item["subtotal"]:.2f}',
            })
            total += item["subtotal"]
        self.cart_table.set_data(data)
        self.total_var.set(f"Total: ${total:.2f}")

    def _checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add products to the cart first.")
            return
        total = sum(i["subtotal"] for i in self.cart)
        if not messagebox.askyesno(
            "Confirm", f"Complete sale for ${total:.2f} ({self.payment_var.get()})?"
        ):
            return
        try:
            self.sale_model.create_sale(total, self.payment_var.get(), self.cart)
            for item in self.cart:
                self.product_model.update_stock(item["product_id"], item["quantity"])
            messagebox.showinfo("Success", f"Sale ${total:.2f} completed!")
            self._clear_cart()
            self._load_products()
        except Exception as e:
            messagebox.showerror("Error", f"Checkout failed:\n{e}")
