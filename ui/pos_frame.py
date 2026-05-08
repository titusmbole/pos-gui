import tkinter as tk
from tkinter import ttk, messagebox
import os

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from models.product import ProductModel
from models.sale import SaleModel
from ui.table import Table

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
COLS_PER_ROW = 4


class POSFrame(ttk.Frame):
    """Main point-of-sale checkout screen."""

    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.sale_model = SaleModel(db)
        self.cart = []
        self._product_list = []
        self._selected_product = None
        self._card_widgets = []
        self._image_cache = []

        self._build_ui()
        self._load_products()

    def _build_ui(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=2)
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
        ttk.Button(search_frame, text="Show All", command=self._load_products).pack(
            side="left", padx=5
        )

        # ── Product grid (left) ───────────────────────────────────
        prod_frame = ttk.LabelFrame(self, text="Products")
        prod_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        prod_frame.columnconfigure(0, weight=1)
        prod_frame.rowconfigure(0, weight=1)

        self._grid_canvas = tk.Canvas(prod_frame, bg="#f5f5f5", highlightthickness=0)
        self._grid_scrollbar = ttk.Scrollbar(
            prod_frame, orient="vertical", command=self._grid_canvas.yview
        )
        self._grid_canvas.configure(yscrollcommand=self._grid_scrollbar.set)

        self._grid_canvas.grid(row=0, column=0, sticky="nsew")
        self._grid_scrollbar.grid(row=0, column=1, sticky="ns")

        self._grid_inner = tk.Frame(self._grid_canvas, bg="#f5f5f5")
        self._grid_window = self._grid_canvas.create_window(
            (0, 0), window=self._grid_inner, anchor="nw"
        )

        self._grid_inner.bind("<Configure>", lambda e: self._grid_canvas.configure(
            scrollregion=self._grid_canvas.bbox("all")
        ))
        self._grid_canvas.bind("<Configure>", self._on_grid_canvas_resize)
        self._grid_canvas.bind_all("<Button-4>", self._on_grid_scroll)
        self._grid_canvas.bind_all("<Button-5>", self._on_grid_scroll)

        # ── Cart (right) ──────────────────────────────────────────
        cart_frame = ttk.LabelFrame(self, text="Cart")
        cart_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
        cart_frame.columnconfigure(0, weight=1)
        cart_frame.rowconfigure(0, weight=1)

        self.cart_table = Table(cart_frame, columns=[
            {"key": "name", "label": "Name", "width": 180, "anchor": "w", "stretch": True},
            {"key": "qty", "label": "Qty", "width": 50, "anchor": "center", "stretch": False},
            {"key": "price", "label": "Price", "width": 90, "anchor": "e", "stretch": False},
            {"key": "subtotal", "label": "Subtotal", "width": 90, "anchor": "e", "stretch": False},
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

    # ── Product Grid ──────────────────────────────────────────────

    def _on_grid_canvas_resize(self, event):
        self._grid_canvas.itemconfig(self._grid_window, width=event.width)

    def _on_grid_scroll(self, event):
        if event.num == 4:
            self._grid_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._grid_canvas.yview_scroll(1, "units")

    def _render_grid(self, products):
        """Render product cards in a grid layout."""
        for w in self._grid_inner.winfo_children():
            w.destroy()
        self._card_widgets = []
        self._image_cache = []
        self._selected_product = None

        for i in range(COLS_PER_ROW):
            self._grid_inner.columnconfigure(i, weight=1)

        for idx, p in enumerate(products):
            row = idx // COLS_PER_ROW
            col = idx % COLS_PER_ROW

            card = tk.Frame(
                self._grid_inner, bg="#ffffff", relief="solid", bd=1,
                padx=8, pady=8, cursor="hand2"
            )
            card.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

            # Image
            img_label = tk.Label(card, bg="#f0f0f0", width=80, height=80)
            img_label.pack(pady=(0, 5))
            photo = self._load_product_image(p.get("image"), 72)
            if photo:
                img_label.configure(image=photo, width=80, height=80)
                self._image_cache.append(photo)
            else:
                img_label.configure(text="No Image", fg="#aaa", font=("Segoe UI", 8))

            # Name
            tk.Label(
                card, text=p["name"], bg="#ffffff", fg="#212529",
                font=("Segoe UI", 10, "bold"), wraplength=130, justify="center"
            ).pack()

            # Price
            tk.Label(
                card, text=f'${p["price"]:.2f}', bg="#ffffff", fg="#2c3e50",
                font=("Segoe UI", 12, "bold")
            ).pack(pady=(2, 0))

            # Stock
            stock = p["stock"]
            stock_color = "#27ae60" if stock > 5 else ("#e67e22" if stock > 0 else "#e74c3c")
            tk.Label(
                card, text=f"Stock: {stock}", bg="#ffffff", fg=stock_color,
                font=("Segoe UI", 9)
            ).pack()

            # Bind click
            product_data = p
            for widget in [card] + card.winfo_children():
                widget.bind("<Button-1>", lambda e, pd=product_data, c=card: self._select_card(pd, c))

            self._card_widgets.append(card)

    def _select_card(self, product_data, card):
        """Select a product card and add to cart."""
        # Deselect previous
        for c in self._card_widgets:
            c.configure(bg="#ffffff", highlightbackground="#ffffff")
            for child in c.winfo_children():
                if isinstance(child, tk.Label) and child.cget("bg") != "#f0f0f0":
                    child.configure(bg="#ffffff")

        # Highlight selected
        card.configure(bg="#d4e6f1")
        for child in card.winfo_children():
            if isinstance(child, tk.Label) and child.cget("bg") != "#f0f0f0":
                child.configure(bg="#d4e6f1")

        self._selected_product = product_data

        # Auto-add to cart on click
        self._add_product_to_cart(product_data)

    def _load_product_image(self, filename, size):
        if not filename or not HAS_PIL:
            return None
        path = os.path.join(UPLOADS_DIR, filename)
        if not os.path.isfile(path):
            return None
        try:
            img = Image.open(path)
            img.thumbnail((size, size))
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    # ── Actions ───────────────────────────────────────────────────

    def _load_products(self):
        try:
            self._product_list = self.product_model.get_all()
            self._render_grid(self._product_list)
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
            self._product_list = products
            self._render_grid(products)
        except Exception as e:
            messagebox.showerror("Error", f"Search failed:\n{e}")

    def _add_product_to_cart(self, p):
        product_id = p["id"]
        name = p["name"]
        price = float(p["price"])

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
