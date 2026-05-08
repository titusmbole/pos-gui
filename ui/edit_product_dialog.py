import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import uuid

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from models.product import ProductModel
from models.category import CategoryModel

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


class EditProductDialog(tk.Toplevel):
    """Modal dialog for editing an existing product."""

    def __init__(self, parent, db, product_row, on_save=None):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.category_model = CategoryModel(db)
        self.product_row = product_row
        self.on_save_callback = on_save

        self.title("Edit Product")
        self.geometry("700x600")
        self.resizable(True, True)
        self.minsize(480, 500)
        self.grab_set()
        self.transient(parent)

        self._categories = {}
        self._image_path = None
        self._new_image_selected = False
        self._photo = None
        self._build_ui()
        self._load_categories()
        self._populate()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (w // 2)
        y = (self.winfo_screenheight() // 2) - (h // 2)
        self.geometry(f"+{x}+{y}")

    def _build_ui(self):
        main = ttk.Frame(self, padding=20)
        main.pack(fill="both", expand=True)

        ttk.Label(main, text="Edit Product", font=("Arial", 16, "bold")).pack(
            pady=(0, 15)
        )

        top = ttk.Frame(main)
        top.pack(fill="x")

        # ── Image ────────────────────────────────────────────────
        img_container = ttk.Frame(top)
        img_container.pack(side="left", padx=(0, 15))

        self._img_canvas = tk.Canvas(
            img_container, width=150, height=150,
            bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc", cursor="hand2"
        )
        self._img_canvas.pack()
        self._img_canvas.bind("<Button-1>", lambda e: self._browse_image())
        self._draw_placeholder()

        ttk.Button(img_container, text="Remove", command=self._clear_image).pack(pady=(5, 0))

        # ── Fields ────────────────────────────────────────────────
        fields_frame = ttk.Frame(top)
        fields_frame.pack(side="left", fill="x", expand=True)

        self.name_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()

        field_defs = [
            ("Product Name *", self.name_var),
            ("Barcode", self.barcode_var),
            ("Selling Price *", self.price_var),
            ("Stock Quantity *", self.stock_var),
        ]

        for label_text, var in field_defs:
            row = ttk.Frame(fields_frame)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label_text, width=18, anchor="w").pack(side="left")
            ttk.Entry(row, textvariable=var, width=25).pack(side="left", fill="x", expand=True)

        cat_row = ttk.Frame(fields_frame)
        cat_row.pack(fill="x", pady=4)
        ttk.Label(cat_row, text="Category", width=18, anchor="w").pack(side="left")
        self.cat_combo = ttk.Combobox(cat_row, width=22, state="readonly")
        self.cat_combo.pack(side="left", fill="x", expand=True)

        # ── Buttons ───────────────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Save Changes", command=self._save).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=10)

    def _populate(self):
        """Fill form with existing product data."""
        self.name_var.set(self.product_row.get("name", ""))
        self.barcode_var.set(self.product_row.get("barcode", ""))
        self.price_var.set(self.product_row.get("price", ""))
        self.stock_var.set(self.product_row.get("stock", ""))

        # Show existing image
        img_file = self.product_row.get("image", "")
        if img_file and HAS_PIL:
            path = os.path.join(UPLOADS_DIR, img_file)
            if os.path.isfile(path):
                self._show_preview(path)

    def _load_categories(self):
        try:
            cats = self.category_model.get_all()
            self._categories = {c["name"]: c["id"] for c in cats}
            self.cat_combo["values"] = list(self._categories.keys())
            # Set current category
            current_cat = self.product_row.get("category", "")
            if current_cat:
                self.cat_combo.set(current_cat)
        except Exception:
            self._categories = {}

    def _save(self):
        name = self.name_var.get().strip()
        barcode = self.barcode_var.get().strip() or None
        price_str = self.price_var.get().strip()
        stock_str = self.stock_var.get().strip()

        if not name:
            messagebox.showwarning("Required", "Product name is required.", parent=self)
            return
        try:
            price = float(price_str)
            if price < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Price must be a valid positive number.", parent=self)
            return
        try:
            stock = int(stock_str)
            if stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning("Invalid", "Stock must be a valid non-negative integer.", parent=self)
            return

        cat_name = self.cat_combo.get()
        category_id = self._categories.get(cat_name)

        image_filename = None
        if self._new_image_selected:
            image_filename = self._save_image_file()

        try:
            self.product_model.update(
                self.product_row["id"], name, barcode, price, stock, category_id, image_filename
            )
            messagebox.showinfo("Success", "Product updated.", parent=self)
            if self.on_save_callback:
                self.on_save_callback()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=self)

    # ── Image methods ─────────────────────────────────────────

    def _draw_placeholder(self):
        self._img_canvas.delete("all")
        self._img_canvas.create_text(
            75, 65, text="Click to\nchange image",
            fill="#999", font=("Segoe UI", 10), justify="center"
        )
        self._img_canvas.create_text(
            75, 100, text="+", fill="#aaa", font=("Segoe UI", 24, "bold")
        )

    def _show_preview(self, path):
        if not HAS_PIL:
            return
        try:
            img = Image.open(path)
            img.thumbnail((148, 148))
            self._photo = ImageTk.PhotoImage(img)
            self._img_canvas.delete("all")
            self._img_canvas.create_image(75, 75, image=self._photo, anchor="center")
        except Exception:
            self._draw_placeholder()

    def _browse_image(self):
        path = filedialog.askopenfilename(
            parent=self,
            title="Select Product Image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._image_path = path
            self._new_image_selected = True
            self._show_preview(path)

    def _clear_image(self):
        self._image_path = None
        self._new_image_selected = False
        self._photo = None
        self._draw_placeholder()

    def _save_image_file(self):
        if not self._image_path:
            return None
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ext = os.path.splitext(self._image_path)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(UPLOADS_DIR, filename)
        shutil.copy2(self._image_path, dest)
        return filename
