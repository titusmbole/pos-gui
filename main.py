import tkinter as tk
from tkinter import ttk, messagebox

from config.settings import APP
from database.connection import Database
from ui.pos_frame import POSFrame
from ui.product_frame import ProductFrame
from ui.sales_frame import SalesFrame


class POSApp:
    """Main application window."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(APP["title"])
        self.root.geometry(f'{APP["width"]}x{APP["height"]}')

        style = ttk.Style()
        style.theme_use(APP["theme"])

        # Database
        self.db = Database()
        if not self.db.connect():
            messagebox.showerror(
                "Database Error",
                "Cannot connect to MySQL.\n"
                "Check config/settings.py and make sure MySQL is running.",
            )
            self.root.destroy()
            return

        self.db.init_tables()

        # Tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=5, pady=5)

        notebook.add(POSFrame(notebook, self.db), text="  POS  ")
        notebook.add(ProductFrame(notebook, self.db), text="  Products  ")
        notebook.add(SalesFrame(notebook, self.db), text="  Sales  ")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        self.db.disconnect()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    app = POSApp()
    app.run()
