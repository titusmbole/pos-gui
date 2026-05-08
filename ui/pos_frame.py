import tkinter as tk
from tkinter import ttk, messagebox

from models.product import ProductModel
from models.sale import SaleModel


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

        cols = ("id", "name", "price", "stock")
        self.product_tree = ttk.Treeview(
            prod_frame, columns=cols, show="headings", height=15
        )
        for col, heading, width, anchor in [
            ("id", "Id", 50, "center"),
            ("name", "Name", 250, "w"),
            ("price", "Price", 100, "e"),
            ("stock", "Stock", 80, "center"),
        ]:
            self.product_tree.heading(col, text=heading)
            self.product_tree.column(col, width=width, minwidth=40, anchor=anchor)
        self.product_tree.pack(fill="both", expand=True, padx=5, pady=5)

        ttk.Button(prod_frame, text="Add to Cart", command=self._add_to_cart).pack(
            pady=5
        )

        # ── Cart (right) ──────────────────────────────────────────
        cart_frame = ttk.LabelFrame(self, text="Cart")
        cart_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

        cart_cols = ("name", "qty", "price", "subtotal")
        self.cart_tree = ttk.Treeview(
            cart_frame, columns=cart_cols, show="headings", height=15
        )
        for col, heading, width, anchor in [
            ("name", "Name", 200, "w"),
            ("qty", "Qty", 60, "center"),
            ("price", "Price", 100, "e"),
            ("subtotal", "Subtotal", 100, "e"),
        ]:
            self.cart_tree.heading(col, text=heading)
            self.cart_tree.column(col, width=width, minwidth=40, anchor=anchor)
        self.cart_tree.pack(fill="both", expand=True, padx=5, pady=5)

        btn_row = ttk.Frame(cart_frame)
        btn_row.pack(pady=5)
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
        self._clear_tree(self.product_tree)
        try:
            for p in self.product_model.get_all():
                self.product_tree.insert(
                    "", "end", values=(p["id"], p["name"], f'{p["price"]:.2f}', p["stock"])
                )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load products:\n{e}")

    def _search_product(self):
        keyword = self.search_var.get().strip()
        self._clear_tree(self.product_tree)
        try:
            products = (
                self.product_model.search(keyword)
                if keyword
                else self.product_model.get_all()
            )
            for p in products:
                self.product_tree.insert(
                    "", "end", values=(p["id"], p["name"], f'{p["price"]:.2f}', p["stock"])
                )
        except Exception as e:
            messagebox.showerror("Error", f"Search failed:\n{e}")

    def _add_to_cart(self):
        selected = self.product_tree.focus()
        if not selected:
            messagebox.showwarning("Select", "Select a product first.")
            return
        vals = self.product_tree.item(selected, "values")
        product_id = int(vals[0])
        name = vals[1]
        price = float(vals[2])

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
        selected = self.cart_tree.focus()
        if not selected:
            return
        idx = self.cart_tree.index(selected)
        self.cart.pop(idx)
        self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()

    def _refresh_cart(self):
        self._clear_tree(self.cart_tree)
        total = 0.0
        for item in self.cart:
            self.cart_tree.insert("", "end", values=(
                item["name"], item["quantity"],
                f'{item["unit_price"]:.2f}', f'{item["subtotal"]:.2f}',
            ))
            total += item["subtotal"]
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

    @staticmethod
    def _clear_tree(tree):
        for row in tree.get_children():
            tree.delete(row)
