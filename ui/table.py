import tkinter as tk
from tkinter import ttk


class Table(ttk.Frame):
    """Custom reusable table widget with proper column stretching.

    Usage:
        table = Table(parent, columns=[
            {"key": "id", "label": "#", "width": 60, "anchor": "center", "stretch": False},
            {"key": "name", "label": "Name", "width": 200, "anchor": "w", "stretch": True},
            {"key": "price", "label": "Price", "width": 100, "anchor": "e", "stretch": False},
        ])
        table.pack(fill="both", expand=True)
        table.set_data([
            {"id": 1, "name": "Apple", "price": "$1.00"},
            {"id": 2, "name": "Banana", "price": "$0.50"},
        ])
    """

    HEADER_BG = "#2c3e50"
    HEADER_FG = "#ffffff"
    ROW_BG = "#ffffff"
    ROW_ALT_BG = "#f8f9fa"
    ROW_SELECTED_BG = "#3498db"
    ROW_SELECTED_FG = "#ffffff"
    ROW_FG = "#212529"
    BORDER_COLOR = "#dee2e6"
    FONT = ("Segoe UI", 11)
    HEADER_FONT = ("Segoe UI", 11, "bold")

    def __init__(self, parent, columns, height=400, on_select=None):
        super().__init__(parent)
        self.columns = columns
        self._data = []
        self._rows = []
        self._selected_index = None
        self._on_select = on_select

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_header()
        self._build_body(height)

    def _build_header(self):
        self._header_frame = tk.Frame(self, bg=self.HEADER_BG)
        self._header_frame.grid(row=0, column=0, sticky="ew")

        self._header_labels = []
        total_fixed = sum(c.get("width", 100) for c in self.columns if not c.get("stretch", False))
        stretch_cols = [i for i, c in enumerate(self.columns) if c.get("stretch", False)]

        for i, col in enumerate(self.columns):
            if col.get("stretch", False):
                self._header_frame.columnconfigure(i, weight=1, minsize=col.get("width", 100))
            else:
                self._header_frame.columnconfigure(i, weight=0, minsize=col.get("width", 100))

            lbl = tk.Label(
                self._header_frame,
                text=col["label"],
                bg=self.HEADER_BG,
                fg=self.HEADER_FG,
                font=self.HEADER_FONT,
                anchor=col.get("anchor", "w"),
                padx=12,
                pady=8,
            )
            lbl.grid(row=0, column=i, sticky="ew")
            self._header_labels.append(lbl)

    def _build_body(self, height):
        # Canvas with scrollbar for the table body
        container = ttk.Frame(self)
        container.grid(row=1, column=0, sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)

        self._canvas = tk.Canvas(
            container, bg=self.ROW_BG, highlightthickness=0, height=height
        )
        self._scrollbar = ttk.Scrollbar(
            container, orient="vertical", command=self._canvas.yview
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._scrollbar.grid(row=0, column=1, sticky="ns")

        self._body_frame = tk.Frame(self._canvas, bg=self.ROW_BG)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._body_frame, anchor="nw"
        )

        self._body_frame.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _on_body_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._canvas_window, width=event.width)
        self._sync_columns()

    def _on_mousewheel(self, event):
        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")
        elif event.delta:
            self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _sync_columns(self):
        """Sync body column widths with header."""
        for i, col in enumerate(self.columns):
            if col.get("stretch", False):
                self._body_frame.columnconfigure(i, weight=1, minsize=col.get("width", 100))
            else:
                self._body_frame.columnconfigure(i, weight=0, minsize=col.get("width", 100))

    def set_data(self, data):
        """Set/replace all table data. data is a list of dicts."""
        self._data = data
        self._selected_index = None
        self._render()

    def append_row(self, row_data):
        """Append a single row dict."""
        self._data.append(row_data)
        self._render()

    def clear(self):
        """Remove all rows."""
        self._data = []
        self._selected_index = None
        self._render()

    def get_selected(self):
        """Return the selected row dict or None."""
        if self._selected_index is not None and self._selected_index < len(self._data):
            return self._data[self._selected_index]
        return None

    def get_selected_index(self):
        """Return the selected row index or None."""
        return self._selected_index

    def _render(self):
        """Redraw all rows."""
        for widget in self._body_frame.winfo_children():
            widget.destroy()
        self._rows = []

        self._sync_columns()

        for row_idx, row_data in enumerate(self._data):
            bg = self.ROW_ALT_BG if row_idx % 2 else self.ROW_BG
            row_widgets = []

            for col_idx, col in enumerate(self.columns):
                value = row_data.get(col["key"], "")
                cell = tk.Label(
                    self._body_frame,
                    text=str(value),
                    bg=bg,
                    fg=self.ROW_FG,
                    font=self.FONT,
                    anchor=col.get("anchor", "w"),
                    padx=12,
                    pady=6,
                )
                cell.grid(row=row_idx, column=col_idx, sticky="ew")
                cell.bind("<Button-1>", lambda e, idx=row_idx: self._select_row(idx))
                row_widgets.append(cell)

            self._rows.append(row_widgets)

    def _select_row(self, index):
        """Handle row selection."""
        # Deselect previous
        if self._selected_index is not None and self._selected_index < len(self._rows):
            prev_bg = self.ROW_ALT_BG if self._selected_index % 2 else self.ROW_BG
            for cell in self._rows[self._selected_index]:
                cell.configure(bg=prev_bg, fg=self.ROW_FG)

        # Select new
        self._selected_index = index
        for cell in self._rows[index]:
            cell.configure(bg=self.ROW_SELECTED_BG, fg=self.ROW_SELECTED_FG)

        if self._on_select:
            self._on_select(self._data[index])
