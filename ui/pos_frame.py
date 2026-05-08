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
        cart_frame.rowconfigure(1, weight=1)

        # Cart header
        cart_header = tk.Frame(cart_frame, bg="#f5f5f5")
        cart_header.grid(row=0, column=0, sticky="ew", padx=5, pady=(5, 0))
        tk.Label(
            cart_header, text="Item", bg="#f5f5f5", fg="#555",
            font=("Segoe UI", 10, "bold"), anchor="w",
        ).pack(side="left", expand=True, fill="x")
        tk.Label(
            cart_header, text="Qty", bg="#f5f5f5", fg="#555",
            font=("Segoe UI", 10, "bold"), width=10, anchor="center",
        ).pack(side="left")
        tk.Label(
            cart_header, text="Total", bg="#f5f5f5", fg="#555",
            font=("Segoe UI", 10, "bold"), width=10, anchor="e",
        ).pack(side="left")
        # spacer for delete button column
        tk.Label(cart_header, text="", bg="#f5f5f5", width=3).pack(side="left")

        # Scrollable cart body
        self._cart_canvas = tk.Canvas(cart_frame, bg="#ffffff", highlightthickness=0)
        cart_scrollbar = ttk.Scrollbar(
            cart_frame, orient="vertical", command=self._cart_canvas.yview
        )
        self._cart_canvas.configure(yscrollcommand=cart_scrollbar.set)
        self._cart_canvas.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        cart_scrollbar.grid(row=1, column=1, sticky="ns", pady=5)

        self._cart_inner = tk.Frame(self._cart_canvas, bg="#ffffff")
        self._cart_window = self._cart_canvas.create_window(
            (0, 0), window=self._cart_inner, anchor="nw"
        )
        self._cart_inner.bind("<Configure>", lambda e: self._cart_canvas.configure(
            scrollregion=self._cart_canvas.bbox("all")
        ))
        self._cart_canvas.bind("<Configure>", lambda e: self._cart_canvas.itemconfig(
            self._cart_window, width=e.width
        ))

        # Clear cart button
        ttk.Button(cart_frame, text="Clear Cart", command=self._clear_cart).grid(
            row=2, column=0, pady=5
        )

        # ── Totals & payment buttons ──────────────────────────────
        checkout_frame = tk.Frame(self, bg="#f5f5f5")
        checkout_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

        self.total_var = tk.StringVar(value="Total: KES 0")
        ttk.Label(
            checkout_frame, textvariable=self.total_var, font=("Arial", 16, "bold")
        ).pack(side="left", padx=20)

        # Payment buttons (right-aligned)
        btn_container = tk.Frame(checkout_frame, bg="#f5f5f5")
        btn_container.pack(side="right", padx=10)

        cash_btn = tk.Button(
            btn_container, text="💵  Cash", bg="#27ae60", fg="#ffffff",
            font=("Segoe UI", 12, "bold"), relief="flat", padx=20, pady=8,
            cursor="hand2", activebackground="#219a52", activeforeground="#fff",
            command=self._pay_cash,
        )
        cash_btn.pack(side="left", padx=5)

        mpesa_btn = tk.Button(
            btn_container, text="📱  Mpesa", bg="#4caf50", fg="#ffffff",
            font=("Segoe UI", 12, "bold"), relief="flat", padx=20, pady=8,
            cursor="hand2", activebackground="#3d8b40", activeforeground="#fff",
            command=self._pay_mpesa,
        )
        mpesa_btn.pack(side="left", padx=5)

        card_btn = tk.Button(
            btn_container, text="💳  Card", bg="#2196f3", fg="#ffffff",
            font=("Segoe UI", 12, "bold"), relief="flat", padx=20, pady=8,
            cursor="hand2", activebackground="#1976d2", activeforeground="#fff",
            command=self._pay_card,
        )
        card_btn.pack(side="left", padx=5)

    # ── Product Grid ──────────────────────────────────────────────

    def _on_grid_canvas_resize(self, event):
        self._grid_canvas.itemconfig(self._grid_window, width=event.width)

    def _on_grid_scroll(self, event):
        if event.num == 4:
            self._grid_canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._grid_canvas.yview_scroll(1, "units")

    def _render_grid(self, products):
        """Render product cards in a grid layout matching reference design."""
        for w in self._grid_inner.winfo_children():
            w.destroy()
        self._card_widgets = []
        self._image_cache = []
        self._selected_product = None

        for i in range(COLS_PER_ROW):
            self._grid_inner.columnconfigure(i, weight=1, uniform="card")

        for idx, p in enumerate(products):
            row = idx // COLS_PER_ROW
            col = idx % COLS_PER_ROW

            card = tk.Frame(
                self._grid_inner, bg="#ffffff", relief="flat", bd=0,
                cursor="hand2", highlightthickness=1, highlightbackground="#e0e0e0",
            )
            card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

            # ── Image area (light gray background, full card width) ──
            img_frame = tk.Frame(card, bg="#f8f8f8", height=120)
            img_frame.pack(fill="x", padx=1, pady=(1, 0))
            img_frame.pack_propagate(False)

            img_label = tk.Label(img_frame, bg="#f8f8f8")
            img_label.pack(expand=True)
            photo = self._load_product_image(p.get("image"), 110)
            if photo:
                img_label.configure(image=photo)
                self._image_cache.append(photo)
            else:
                img_label.configure(
                    text="No Image", fg="#bbb", font=("Segoe UI", 9),
                )

            # ── Info area ────────────────────────────────────────────
            info_frame = tk.Frame(card, bg="#ffffff", padx=10, pady=6)
            info_frame.pack(fill="x", anchor="w")

            # Name (truncated, left-aligned)
            name_text = p["name"]
            if len(name_text) > 22:
                name_text = name_text[:20] + "..."
            tk.Label(
                info_frame, text=name_text, bg="#ffffff", fg="#333333",
                font=("Segoe UI", 10, "bold"), anchor="w",
            ).pack(fill="x")

            # Price (teal/green, left-aligned)
            tk.Label(
                info_frame, text=f'KES {p["price"]:,.0f}',
                bg="#ffffff", fg="#1a9e78",
                font=("Segoe UI", 11, "bold"), anchor="w",
            ).pack(fill="x", pady=(2, 4))

            # Stock dot + text (left-aligned)
            stock = p["stock"]
            stock_color = "#27ae60" if stock > 5 else ("#e67e22" if stock > 0 else "#e74c3c")
            stock_row = tk.Frame(info_frame, bg="#ffffff")
            stock_row.pack(fill="x")
            tk.Label(
                stock_row, text="●", bg="#ffffff", fg=stock_color,
                font=("Segoe UI", 10),
            ).pack(side="left")
            tk.Label(
                stock_row, text=f"  {stock} in stock", bg="#ffffff", fg="#888888",
                font=("Segoe UI", 9),
            ).pack(side="left")

            # ── Bind click to all widgets in card ────────────────────
            product_data = p
            all_widgets = [card, img_frame, img_label, info_frame, stock_row]
            all_widgets += info_frame.winfo_children()
            all_widgets += stock_row.winfo_children()
            for widget in all_widgets:
                widget.bind("<Button-1>", lambda e, pd=product_data, c=card: self._select_card(pd, c))

            self._card_widgets.append(card)

    def _select_card(self, product_data, card):
        """Select a product card and add to cart."""
        # Reset all cards
        for c in self._card_widgets:
            c.configure(highlightbackground="#e0e0e0", highlightthickness=1)

        # Highlight selected card
        card.configure(highlightbackground="#1a9e78", highlightthickness=2)

        self._selected_product = product_data
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
        category = p.get("category_name") or ""

        for item in self.cart:
            if item["product_id"] == product_id:
                item["quantity"] += 1
                item["subtotal"] = item["quantity"] * item["unit_price"]
                self._refresh_cart()
                return

        self.cart.append({
            "product_id": product_id,
            "name": name,
            "category": category,
            "quantity": 1,
            "unit_price": price,
            "subtotal": price,
        })
        self._refresh_cart()

    def _change_qty(self, index, delta):
        """Adjust quantity for a cart item by delta (+1 or -1)."""
        if 0 <= index < len(self.cart):
            item = self.cart[index]
            new_qty = item["quantity"] + delta
            if new_qty <= 0:
                self.cart.pop(index)
            else:
                item["quantity"] = new_qty
                item["subtotal"] = new_qty * item["unit_price"]
            self._refresh_cart()

    def _remove_item(self, index):
        """Remove a specific item from the cart."""
        if 0 <= index < len(self.cart):
            self.cart.pop(index)
            self._refresh_cart()

    def _clear_cart(self):
        self.cart.clear()
        self._refresh_cart()

    def _refresh_cart(self):
        # Clear existing cart rows
        for w in self._cart_inner.winfo_children():
            w.destroy()

        total = 0.0
        for idx, item in enumerate(self.cart):
            total += item["subtotal"]

            row_frame = tk.Frame(self._cart_inner, bg="#ffffff")
            row_frame.pack(fill="x", padx=0, pady=0)

            # Bottom separator line
            sep = tk.Frame(row_frame, bg="#eeeeee", height=1)
            sep.pack(side="bottom", fill="x")

            content = tk.Frame(row_frame, bg="#ffffff", pady=8, padx=8)
            content.pack(fill="x")
            content.columnconfigure(0, weight=1)

            # ── Left: item name + category ──
            info_col = tk.Frame(content, bg="#ffffff")
            info_col.grid(row=0, column=0, sticky="w")

            tk.Label(
                info_col, text=item["name"], bg="#ffffff", fg="#222222",
                font=("Segoe UI", 10, "bold"), anchor="w",
            ).pack(anchor="w")
            if item["category"]:
                tk.Label(
                    info_col, text=item["category"], bg="#ffffff", fg="#aaaaaa",
                    font=("Segoe UI", 9), anchor="w",
                ).pack(anchor="w")

            # ── Middle: − qty + buttons ──
            qty_col = tk.Frame(content, bg="#ffffff")
            qty_col.grid(row=0, column=1, padx=(10, 10))

            minus_btn = tk.Label(
                qty_col, text="−", bg="#f0f0f0", fg="#333", width=3,
                font=("Segoe UI", 11), relief="solid", bd=1, cursor="hand2",
            )
            minus_btn.pack(side="left")
            minus_btn.bind("<Button-1>", lambda e, i=idx: self._change_qty(i, -1))

            qty_label = tk.Label(
                qty_col, text=str(item["quantity"]), bg="#ffffff", fg="#222",
                font=("Segoe UI", 11), width=3, anchor="center",
                relief="solid", bd=1,
            )
            qty_label.pack(side="left")

            plus_btn = tk.Label(
                qty_col, text="+", bg="#f0f0f0", fg="#333", width=3,
                font=("Segoe UI", 11), relief="solid", bd=1, cursor="hand2",
            )
            plus_btn.pack(side="left")
            plus_btn.bind("<Button-1>", lambda e, i=idx: self._change_qty(i, +1))

            # ── Right: subtotal ──
            tk.Label(
                content, text=f'{item["subtotal"]:,.0f}', bg="#ffffff", fg="#222",
                font=("Segoe UI", 11), anchor="e", width=9,
            ).grid(row=0, column=2, padx=(5, 0))

            # ── Delete button (trash icon) ──
            del_btn = tk.Label(
                content, text="🗑", bg="#ffffff", fg="#cc3333",
                font=("Segoe UI", 13), cursor="hand2",
            )
            del_btn.grid(row=0, column=3, padx=(5, 0))
            del_btn.bind("<Button-1>", lambda e, i=idx: self._remove_item(i))

        self.total_var.set(f"Total: KES {total:,.0f}")

    def _get_cart_total(self):
        return sum(i["subtotal"] for i in self.cart)

    def _complete_sale(self, payment_method, extra_info=""):
        """Finalise the sale after payment is confirmed."""
        total = self._get_cart_total()
        try:
            self.sale_model.create_sale(total, payment_method, self.cart)
            for item in self.cart:
                self.product_model.update_stock(item["product_id"], item["quantity"])
            msg = f"Sale KES {total:,.0f} completed!\nPayment: {payment_method.upper()}"
            if extra_info:
                msg += f"\n{extra_info}"
            messagebox.showinfo("Success", msg)
            self._clear_cart()
            self._load_products()
        except Exception as e:
            messagebox.showerror("Error", f"Checkout failed:\n{e}")

    # ── Cash Payment ──────────────────────────────────────────────

    def _pay_cash(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add products to the cart first.")
            return
        total = self._get_cart_total()

        dlg = tk.Toplevel(self)
        dlg.title("Cash Payment")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.configure(bg="#ffffff")

        # Centre on screen
        w, h = 380, 220
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - w) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            dlg, text="Confirm Cash Payment", bg="#ffffff", fg="#222",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(20, 10))

        tk.Label(
            dlg, text=f"Total Amount", bg="#ffffff", fg="#888",
            font=("Segoe UI", 10),
        ).pack()
        tk.Label(
            dlg, text=f"KES {total:,.0f}", bg="#ffffff", fg="#27ae60",
            font=("Segoe UI", 22, "bold"),
        ).pack(pady=(0, 20))

        btn_row = tk.Frame(dlg, bg="#ffffff")
        btn_row.pack(pady=10)

        tk.Button(
            btn_row, text="Cancel", bg="#e0e0e0", fg="#333",
            font=("Segoe UI", 11), relief="flat", padx=25, pady=6,
            command=dlg.destroy,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_row, text="Confirm Payment", bg="#27ae60", fg="#fff",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=6,
            command=lambda: (dlg.destroy(), self._complete_sale("cash")),
        ).pack(side="left", padx=10)

    # ── Mpesa Payment ─────────────────────────────────────────────

    def _pay_mpesa(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add products to the cart first.")
            return
        total = self._get_cart_total()

        dlg = tk.Toplevel(self)
        dlg.title("Mpesa Payment")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.configure(bg="#ffffff")

        w, h = 500, 300
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - w) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

   
        tk.Label(
            dlg, text=f"Amount: KES {total:,.0f}", bg="#ffffff", fg="#4caf50",
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(0, 15))

        tk.Label(
            dlg, text="Phone Number", bg="#ffffff", fg="#555",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=40)

        phone_var = tk.StringVar()
        phone_entry = tk.Entry(
            dlg, textvariable=phone_var, font=("Segoe UI", 13),
            relief="solid", bd=1, width=25,
        )
        phone_entry.pack(padx=40, pady=(2, 5), ipady=6)
        phone_entry.insert(0, "07")
        phone_entry.focus_set()

        error_label = tk.Label(dlg, text="", bg="#ffffff", fg="#e74c3c", font=("Segoe UI", 9))
        error_label.pack()

        def submit():
            phone = phone_var.get().strip()
            if len(phone) < 10 or not phone.isdigit():
                error_label.config(text="Enter a valid phone number (e.g. 0712345678)")
                return
            dlg.destroy()
            self._complete_sale("mpesa", f"Phone: {phone}")

        btn_row = tk.Frame(dlg, bg="#ffffff")
        btn_row.pack(pady=10)

        tk.Button(
            btn_row, text="Cancel", bg="#e0e0e0", fg="#333",
            font=("Segoe UI", 11), relief="flat", padx=25, pady=6,
            command=dlg.destroy,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_row, text="Send STK Push", bg="#4caf50", fg="#fff",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=6,
            command=submit,
        ).pack(side="left", padx=10)

        phone_entry.bind("<Return>", lambda e: submit())

    # ── Card Payment ──────────────────────────────────────────────

    def _pay_card(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add products to the cart first.")
            return
        total = self._get_cart_total()

        dlg = tk.Toplevel(self)
        dlg.title("Card Payment")
        dlg.transient(self.winfo_toplevel())
        dlg.grab_set()
        dlg.resizable(False, False)
        dlg.configure(bg="#ffffff")

        w, h = 400, 360
        x = self.winfo_toplevel().winfo_x() + (self.winfo_toplevel().winfo_width() - w) // 2
        y = self.winfo_toplevel().winfo_y() + (self.winfo_toplevel().winfo_height() - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        tk.Label(
            dlg, text="Card Payment", bg="#ffffff", fg="#222",
            font=("Segoe UI", 14, "bold"),
        ).pack(pady=(20, 5))

        tk.Label(
            dlg, text=f"Amount: KES {total:,.0f}", bg="#ffffff", fg="#2196f3",
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=(0, 15))

        tk.Label(
            dlg, text="Select Bank", bg="#ffffff", fg="#555",
            font=("Segoe UI", 10),
        ).pack(anchor="w", padx=40)

        banks = [
            "KCB Bank", "Equity Bank", "Co-operative Bank",
            "ABSA Bank", "Standard Chartered", "NCBA Bank",
            "I&M Bank", "DTB Bank", "Stanbic Bank", "Family Bank",
        ]

        bank_var = tk.StringVar()
        bank_list = tk.Frame(dlg, bg="#ffffff")
        bank_list.pack(padx=40, pady=(5, 5), fill="x")

        # Scrollable bank list
        bank_canvas = tk.Canvas(bank_list, bg="#ffffff", highlightthickness=0, height=150)
        bank_sb = ttk.Scrollbar(bank_list, orient="vertical", command=bank_canvas.yview)
        bank_canvas.configure(yscrollcommand=bank_sb.set)
        bank_canvas.pack(side="left", fill="both", expand=True)
        bank_sb.pack(side="right", fill="y")

        bank_inner = tk.Frame(bank_canvas, bg="#ffffff")
        bank_canvas.create_window((0, 0), window=bank_inner, anchor="nw")
        bank_inner.bind("<Configure>", lambda e: bank_canvas.configure(
            scrollregion=bank_canvas.bbox("all")
        ))

        radio_buttons = []
        for bank in banks:
            rb = tk.Radiobutton(
                bank_inner, text=bank, variable=bank_var, value=bank,
                bg="#ffffff", fg="#333", font=("Segoe UI", 11),
                anchor="w", activebackground="#e3f2fd", selectcolor="#ffffff",
                indicatoron=True, padx=10, pady=3,
            )
            rb.pack(fill="x")
            radio_buttons.append(rb)

        error_label = tk.Label(dlg, text="", bg="#ffffff", fg="#e74c3c", font=("Segoe UI", 9))
        error_label.pack()

        def submit():
            selected = bank_var.get()
            if not selected:
                error_label.config(text="Please select a bank")
                return
            dlg.destroy()
            self._complete_sale("card", f"Bank: {selected}")

        btn_row = tk.Frame(dlg, bg="#ffffff")
        btn_row.pack(pady=10)

        tk.Button(
            btn_row, text="Cancel", bg="#e0e0e0", fg="#333",
            font=("Segoe UI", 11), relief="flat", padx=25, pady=6,
            command=dlg.destroy,
        ).pack(side="left", padx=10)

        tk.Button(
            btn_row, text="Pay with Card", bg="#2196f3", fg="#fff",
            font=("Segoe UI", 11, "bold"), relief="flat", padx=25, pady=6,
            command=submit,
        ).pack(side="left", padx=10)
