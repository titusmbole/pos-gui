import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import os
import shutil
import uuid

from models.product import ProductModel
from models.category import CategoryModel

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")


class AddProductDialog(tk.Toplevel):
    """Popup dialog for adding a new product."""

    def __init__(self, parent, db, on_save=None):
        super().__init__(parent)
        self.db = db
        self.product_model = ProductModel(db)
        self.category_model = CategoryModel(db)
        self.on_save_callback = on_save

        self.title("Add New Product")
        self.geometry("800x700")
        self.resizable(True, True)
        self.minsize(480, 550)
        self.grab_set()
        self.transient(parent)

        self._categories = {}
        self._build_ui()
        self._load_categories()
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

        ttk.Label(main, text="New Product", font=("Arial", 16, "bold")).pack(
            pady=(0, 15)
        )

        # ── Top section: Image + Fields side by side ──────────────
        top = ttk.Frame(main)
        top.pack(fill="x")

        # ── Image Upload (clickable rectangle with preview) ──────
        self._image_path = None
        self._photo = None

        img_container = ttk.Frame(top)
        img_container.pack(side="left", padx=(0, 15))

        self._img_canvas = tk.Canvas(
            img_container, width=150, height=150,
            bg="#f0f0f0", highlightthickness=1, highlightbackground="#ccc", cursor="hand2"
        )
        self._img_canvas.pack()
        self._img_canvas.bind("<Button-1>", lambda e: self._browse_image())
        self._draw_placeholder()

        clear_btn = ttk.Button(img_container, text="Remove", command=self._clear_image)
        clear_btn.pack(pady=(5, 0))

        # ── Fields ────────────────────────────────────────────────
        fields_frame = ttk.Frame(top)
        fields_frame.pack(side="left", fill="x", expand=True)

        self.name_var = tk.StringVar()
        self.barcode_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.cost_var = tk.StringVar(value="0.00")
        self.stock_var = tk.StringVar(value="0")

        field_defs = [
            ("Product Name *", self.name_var),
            ("Barcode", self.barcode_var),
            ("Selling Price *", self.price_var),
            ("Cost Price", self.cost_var),
            ("Stock Quantity *", self.stock_var),
        ]

        for label_text, var in field_defs:
            row = ttk.Frame(fields_frame)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=label_text, width=18, anchor="w").pack(side="left")
            ttk.Entry(row, textvariable=var, width=25).pack(
                side="left", fill="x", expand=True
            )

        # Category dropdown
        cat_row = ttk.Frame(fields_frame)
        cat_row.pack(fill="x", pady=4)
        ttk.Label(cat_row, text="Category", width=18, anchor="w").pack(side="left")
        self.cat_combo = ttk.Combobox(cat_row, width=22, state="readonly")
        self.cat_combo.pack(side="left", fill="x", expand=True)

        # ── Description ──────────────────────────────────────────
        desc_frame = ttk.Frame(main)
        desc_frame.pack(fill="x", pady=(8, 0))
        ttk.Label(desc_frame, text="Description", anchor="w").pack(
            fill="x", pady=(0, 2)
        )
        self.desc_text = tk.Text(desc_frame, height=4, width=40, wrap="word")
        self.desc_text.pack(fill="x")

        # ── Buttons ───────────────────────────────────────────────
        btn_frame = ttk.Frame(main)
        btn_frame.pack(pady=20)

        ttk.Button(btn_frame, text="Save Product", command=self._save).pack(
            side="left", padx=10
        )
        ttk.Button(
            btn_frame, text="Save & Add Another", command=self._save_and_clear
        ).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(
            side="left", padx=10
        )

    def _load_categories(self):
        try:
            cats = self.category_model.get_all()
            self._categories = {c["name"]: c["id"] for c in cats}
            self.cat_combo["values"] = list(self._categories.keys())
        except Exception:
            self._categories = {}

    def _validate(self):
        if not self.name_var.get().strip():
            messagebox.showwarning("Validation", "Product name is required.", parent=self)
            return False
        price_str = self.price_var.get().strip()
        if not price_str:
            messagebox.showwarning("Validation", "Selling price is required.", parent=self)
            return False
        try:
            if float(price_str) < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Validation", "Price must be a valid positive number.", parent=self
            )
            return False
        try:
            if int(self.stock_var.get().strip()) < 0:
                raise ValueError
        except ValueError:
            messagebox.showwarning(
                "Validation", "Stock must be a valid non-negative integer.", parent=self
            )
            return False
        return True

    def _save(self):
        if not self._validate():
            return
        if self._insert_product():
            self.destroy()

    def _save_and_clear(self):
        if not self._validate():
            return
        if self._insert_product():
            self._clear_form()

    def _insert_product(self):
        try:
            cat_name = self.cat_combo.get()
            category_id = self._categories.get(cat_name)
            image_filename = self._save_image()
            self.product_model.add(
                self.name_var.get().strip(),
                self.barcode_var.get().strip() or None,
                float(self.price_var.get().strip()),
                int(self.stock_var.get().strip()),
                category_id,
                image_filename,
            )
            messagebox.showinfo("Success", "Product added successfully!", parent=self)
            if self.on_save_callback:
                self.on_save_callback()
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save product:\n{e}", parent=self)
            return False

    def _clear_form(self):
        self.name_var.set("")
        self.barcode_var.set("")
        self.price_var.set("")
        self.cost_var.set("0.00")
        self.stock_var.set("0")
        self.cat_combo.set("")
        self.desc_text.delete("1.0", "end")
        self._clear_image()

    def _draw_placeholder(self):
        self._img_canvas.delete("all")
        self._img_canvas.create_text(
            75, 65, text="Click to\nupload image",
            fill="#999", font=("Segoe UI", 10), justify="center"
        )
        self._img_canvas.create_text(
            75, 100, text="+", fill="#aaa", font=("Segoe UI", 24, "bold")
        )

    def _show_preview(self, path):
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
            self._show_preview(path)

    def _clear_image(self):
        self._image_path = None
        self._photo = None
        self._draw_placeholder()

    def _save_image(self):
        """Copy selected image to uploads dir, return filename or None."""
        if not self._image_path:
            return None
        os.makedirs(UPLOADS_DIR, exist_ok=True)
        ext = os.path.splitext(self._image_path)[1].lower()
        filename = f"{uuid.uuid4().hex}{ext}"
        dest = os.path.join(UPLOADS_DIR, filename)
        shutil.copy2(self._image_path, dest)
        return filename
