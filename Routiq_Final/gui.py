from __future__ import annotations

import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from typing import Optional

import networkx as nx
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from algorithm import RouteResult, greedy_best_first_search
from graph_data import CITY_POSITIONS, build_graph, get_city_names, get_heuristic_values
from visualization import APP_BG, CARD_BG, HIGHLIGHT, PANEL_BG, TEXT_COLOR, TraversalAnimator, draw_graph_figure


class RoutePlannerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Greedy Best First Search Route Planner")
        self.geometry("1440x860")
        self.minsize(1280, 760)
        self.configure(bg=APP_BG)

        self.graph = build_graph()
        self.cities = get_city_names()
        self.current_result: Optional[RouteResult] = None
        self.history: list[dict[str, str]] = []
        self.graph_canvas: Optional[FigureCanvasTkAgg] = None
        self.animation_window: Optional[TraversalAnimator] = None
        self.zoom_var = tk.DoubleVar(value=1.8)
        self._suspend_zoom_trace = False

        self._configure_style()
        self._build_layout()
        self._draw_initial_graph()

    def _configure_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Root.TFrame", background=APP_BG)
        style.configure("Panel.TFrame", background=PANEL_BG)
        style.configure("Card.TFrame", background=CARD_BG)
        style.configure("TLabel", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=APP_BG, foreground=TEXT_COLOR, font=("Segoe UI", 20, "bold"))
        style.configure("SubTitle.TLabel", background=APP_BG, foreground="#94a3b8", font=("Segoe UI", 10))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=(12, 8))
        style.map("TButton", background=[("active", HIGHLIGHT), ("!active", "#334155")], foreground=[("!disabled", "white")])
        style.configure("TCombobox", fieldbackground="#0f172a", background="#0f172a", foreground=TEXT_COLOR, arrowcolor="white")
        style.map("TCombobox", fieldbackground=[("readonly", "#0f172a")], foreground=[("readonly", TEXT_COLOR)])
        style.configure(
            "Treeview",
            background="#0b1220",
            fieldbackground="#0b1220",
            foreground=TEXT_COLOR,
            rowheight=28,
            bordercolor="#1e293b",
            lightcolor="#1e293b",
            darkcolor="#1e293b",
        )
        style.configure("Treeview.Heading", background="#1f2937", foreground="white", font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", "#1d4ed8")])

    def _build_layout(self) -> None:
        root = ttk.Frame(self, style="Root.TFrame", padding=16)
        root.pack(fill=tk.BOTH, expand=True)

        header = ttk.Frame(root, style="Root.TFrame")
        header.pack(fill=tk.X, pady=(0, 12))
        ttk.Label(header, text="Greedy Best First Search Route Planner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            header,
            text="Plan routes with heuristic-driven search, cost reporting, route history, and animated traversal.",
            style="SubTitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        content = ttk.Frame(root, style="Root.TFrame")
        content.pack(fill=tk.BOTH, expand=True)
        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=2)
        content.columnconfigure(2, weight=1)
        content.rowconfigure(0, weight=1)

        left_panel = ttk.Frame(content, style="Panel.TFrame", padding=16)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        center_panel = ttk.Frame(content, style="Panel.TFrame", padding=16)
        center_panel.grid(row=0, column=1, sticky="nsew", padx=(0, 12))
        right_panel = ttk.Frame(content, style="Panel.TFrame", padding=16)
        right_panel.grid(row=0, column=2, sticky="nsew")

        self._build_controls(left_panel)
        self._build_output_panel(left_panel)
        self._build_graph_panel(center_panel)
        self._build_history_panel(right_panel)

    def _build_controls(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill=tk.X)

        ttk.Label(card, text="Route Controls", background=CARD_BG, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text="Choose source and destination cities.", background=CARD_BG, foreground="#cbd5e1").pack(anchor="w", pady=(2, 12))

        ttk.Label(card, text="Source", background=CARD_BG).pack(anchor="w")
        self.source_var = tk.StringVar(value=self.cities[0])
        self.source_combo = ttk.Combobox(card, textvariable=self.source_var, values=self.cities, state="readonly")
        self.source_combo.pack(fill=tk.X, pady=(4, 10))

        ttk.Label(card, text="Destination", background=CARD_BG).pack(anchor="w")
        self.destination_var = tk.StringVar(value=self.cities[-1])
        self.destination_combo = ttk.Combobox(card, textvariable=self.destination_var, values=self.cities, state="readonly")
        self.destination_combo.pack(fill=tk.X, pady=(4, 10))

        ttk.Label(card, text="Zoom", background=CARD_BG).pack(anchor="w")

        zoom_button_row = ttk.Frame(card, style="Card.TFrame")
        zoom_button_row.pack(fill=tk.X, pady=(4, 12))

        btn_frame = ttk.Frame(zoom_button_row, style="Card.TFrame")
        btn_frame.pack(anchor="w")
        self.zoom_out_btn = ttk.Button(btn_frame, text="−", width=3, command=self.zoom_out)
        self.zoom_out_btn.pack(side=tk.LEFT, padx=(0, 6))
        self.zoom_in_btn = ttk.Button(btn_frame, text="+", width=3, command=self.zoom_in)
        self.zoom_in_btn.pack(side=tk.LEFT)

        zoom_value_row = ttk.Frame(card, style="Card.TFrame")
        zoom_value_row.pack(fill=tk.X, pady=(6, 10))
        self.zoom_value_label = ttk.Label(zoom_value_row, text=f"Zoom level: {self.zoom_var.get():.1f}x", background=CARD_BG)
        self.zoom_value_label.pack(anchor="w")
        self.zoom_var.trace_add("write", self._on_zoom_change)

        self.animate_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, text="Animate traversal", variable=self.animate_var).pack(anchor="w", pady=(2, 12))

        button_bar = ttk.Frame(card, style="Card.TFrame")
        button_bar.pack(fill=tk.X, pady=(4, 0))
        ttk.Button(button_bar, text="Find Route", command=self.find_route).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 6))
        ttk.Button(button_bar, text="Reset", command=self.reset).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(6, 0))

    def _build_output_panel(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill=tk.BOTH, expand=True, pady=(14, 0))

        ttk.Label(card, text="Route Details", background=CARD_BG, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text="Search results, path cost, and heuristic trace.", background=CARD_BG, foreground="#cbd5e1").pack(anchor="w", pady=(2, 10))

        self.output_text = tk.Text(
            card,
            height=18,
            wrap=tk.WORD,
            bg="#0b1220",
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief=tk.FLAT,
            borderwidth=0,
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self._write_output("Run a search to see the route summary here.")

    def _build_graph_panel(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill=tk.BOTH, expand=True)
        ttk.Label(card, text="Graph Visualization", background=CARD_BG, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text="Highlighted path and traversal state are drawn on the map.", background=CARD_BG, foreground="#cbd5e1").pack(anchor="w", pady=(2, 10))

        self.graph_frame = tk.Frame(card, bg=CARD_BG)
        self.graph_frame.pack(fill=tk.BOTH, expand=True)

    def _build_history_panel(self, parent: ttk.Frame) -> None:
        card = ttk.Frame(parent, style="Card.TFrame", padding=14)
        card.pack(fill=tk.BOTH, expand=True)
        ttk.Label(card, text="Route History", background=CARD_BG, font=("Segoe UI", 13, "bold")).pack(anchor="w")
        ttk.Label(card, text="Recent searches remain available in the list below.", background=CARD_BG, foreground="#cbd5e1").pack(anchor="w", pady=(2, 10))

        history_columns = ("time", "source", "destination", "cost", "path")
        self.history_tree = ttk.Treeview(card, columns=history_columns, show="headings", height=18)
        headings = {
            "time": "Time",
            "source": "Source",
            "destination": "Destination",
            "cost": "Cost",
            "path": "Path",
        }
        widths = {"time": 85, "source": 95, "destination": 95, "cost": 65, "path": 170}
        for column in history_columns:
            self.history_tree.heading(column, text=headings[column])
            self.history_tree.column(column, width=widths[column], anchor="center" if column != "path" else "w")

        history_scroll = ttk.Scrollbar(card, orient=tk.VERTICAL, command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        self.history_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        history_scroll.pack(side=tk.RIGHT, fill=tk.Y)

    def _draw_initial_graph(self) -> None:
        self._refresh_graph(path=None, visited=None, current_node=None)

    def _refresh_graph(self, path=None, visited=None, current_node=None) -> None:
        previous_figure = None
        if self.graph_canvas is not None:
            previous_figure = getattr(self.graph_canvas, "figure", None)
            self.graph_canvas.get_tk_widget().destroy()
            self.graph_canvas = None

        # center is optionally stored on the instance for cursor-centered zoom
        center = getattr(self, "_last_center", None)
        xlim = getattr(self, "_last_xlim", None)
        ylim = getattr(self, "_last_ylim", None)
        figure = draw_graph_figure(
            self.graph,
            path=path,
            visited=visited,
            current_node=current_node,
            route_only=path is not None,
            zoom=float(self.zoom_var.get()),
            title="City Network",
            center=center,
            xlim=xlim,
            ylim=ylim,
        )
        self.graph_canvas = FigureCanvasTkAgg(figure, master=self.graph_frame)
        widget = self.graph_canvas.get_tk_widget()
        widget.pack(fill=tk.BOTH, expand=True)
        self.graph_canvas.draw()
        try:
            # connect mouse wheel zoom on the matplotlib canvas
            self._canvas_scroll_cid = self.graph_canvas.mpl_connect("scroll_event", self._on_canvas_scroll)
        except Exception:
            self._canvas_scroll_cid = None
        if previous_figure is not None:
            try:
                import matplotlib.pyplot as plt

                plt.close(previous_figure)
            except Exception:
                pass

    def _on_zoom_change(self, *_args) -> None:
        # If a scroll handler set this flag to avoid double redraw, clear and skip refresh
        if getattr(self, "_suspend_zoom_trace", False):
            self._suspend_zoom_trace = False
            self.zoom_value_label.configure(text=f"Zoom level: {self.zoom_var.get():.1f}x")
            return

        self.zoom_value_label.configure(text=f"Zoom level: {self.zoom_var.get():.1f}x")
        if self.current_result is not None:
            self._refresh_graph(path=self.current_result.path, visited=self.current_result.visited_nodes, current_node=self.current_result.path[-1])
        elif self.graph_canvas is not None:
            self._refresh_graph(path=None, visited=None, current_node=None)

    def zoom_in(self) -> None:
        # clear explicit limits so draw computes a centered zoom
        if hasattr(self, "_last_xlim"):
            delattr(self, "_last_xlim")
        if hasattr(self, "_last_ylim"):
            delattr(self, "_last_ylim")
        new_zoom = min(4.0, float(self.zoom_var.get()) * 1.15)
        self.zoom_var.set(new_zoom)
        self._refresh_graph(path=(self.current_result.path if self.current_result else None), visited=(self.current_result.visited_nodes if self.current_result else None), current_node=(self.current_result.path[-1] if self.current_result else None))

    def zoom_out(self) -> None:
        # clear explicit limits so draw computes a centered zoom
        if hasattr(self, "_last_xlim"):
            delattr(self, "_last_xlim")
        if hasattr(self, "_last_ylim"):
            delattr(self, "_last_ylim")
        new_zoom = max(0.5, float(self.zoom_var.get()) / 1.15)
        self.zoom_var.set(new_zoom)
        self._refresh_graph(path=(self.current_result.path if self.current_result else None), visited=(self.current_result.visited_nodes if self.current_result else None), current_node=(self.current_result.path[-1] if self.current_result else None))

    def _on_canvas_scroll(self, event) -> None:
        # Matplotlib scroll_event: use event.step (positive for up/zoom-in)
        step = getattr(event, "step", None)
        if step is None:
            # fallback: some backends use button attribute
            if hasattr(event, "button") and event.button in ("up", "wheel_up"):
                step = 1
            else:
                step = -1 if hasattr(event, "button") and event.button in ("down", "wheel_down") else 0

        if step == 0:
            return

        # multiplicative zoom factor per step
        factor = 1.15 ** (1 if step > 0 else -1)
        current = float(self.zoom_var.get())
        new_zoom = min(4.0, max(0.2, current * factor))

        # compute new xlim/ylim anchored at the pointer data coords (pointer-anchored zoom)
        xdata = getattr(event, "xdata", None)
        ydata = getattr(event, "ydata", None)
        new_xlim = None
        new_ylim = None
        try:
            fig = self.graph_canvas.figure
            ax = fig.axes[0] if fig and fig.axes else None
            if ax is not None and xdata is not None and ydata is not None:
                old_xlim = ax.get_xlim()
                old_ylim = ax.get_ylim()
                new_xmin = xdata - (xdata - old_xlim[0]) / factor
                new_xmax = xdata + (old_xlim[1] - xdata) / factor
                new_ymin = ydata - (ydata - old_ylim[0]) / factor
                new_ymax = ydata + (old_ylim[1] - ydata) / factor
                new_xlim = (new_xmin, new_xmax)
                new_ylim = (new_ymin, new_ymax)
        except Exception:
            new_xlim = None
            new_ylim = None

        # save explicit limits so draw uses them
        if new_xlim is not None and new_ylim is not None:
            self._last_xlim = new_xlim
            self._last_ylim = new_ylim
        else:
            if hasattr(self, "_last_xlim"):
                delattr(self, "_last_xlim")
            if hasattr(self, "_last_ylim"):
                delattr(self, "_last_ylim")

        # avoid double redraw from trace handler
        self._suspend_zoom_trace = True
        self.zoom_var.set(new_zoom)

        # refresh with new limits (pointer-anchored if available)
        if self.current_result is not None:
            self._refresh_graph(path=self.current_result.path, visited=self.current_result.visited_nodes, current_node=self.current_result.path[-1])
        else:
            self._refresh_graph(path=None, visited=None, current_node=None)

    def find_route(self) -> None:
        source = self.source_var.get().strip()
        destination = self.destination_var.get().strip()

        if not source or not destination:
            messagebox.showerror("Missing Input", "Please select both a source and a destination.")
            return
        if source == destination:
            messagebox.showwarning("Invalid Route", "Source and destination must be different.")
            return

        try:
            heuristics = get_heuristic_values(destination)
            result = greedy_best_first_search(self.graph, source, destination, lambda city, goal: heuristics[city])
        except ValueError as error:
            messagebox.showerror("Invalid Node", str(error))
            return

        if result is None:
            self.current_result = None
            self._write_output(f"No path found between {source} and {destination}.")
            messagebox.showinfo("No Path Found", "The graph does not contain a route for this pair of nodes.")
            self._refresh_graph(path=None, visited=None, current_node=None)
            return

        self.current_result = result
        self._display_result(source, destination, result)
        self._append_history(source, destination, result)
        self._refresh_graph(path=result.path, visited=result.visited_nodes, current_node=result.path[-1])

        if self.animate_var.get():
            if self.animation_window is not None:
                self.animation_window.close()
            self.animation_window = TraversalAnimator(
                self,
                self.graph,
                CITY_POSITIONS,
                result.visited_nodes,
                result.path,
                result.total_cost,
                zoom=float(self.zoom_var.get()),
            )

    def _display_result(self, source: str, destination: str, result: RouteResult) -> None:
        heuristic_values = get_heuristic_values(destination)
        lines = [
            f"Source: {source}",
            f"Destination: {destination}",
            "",
            f"Best Route: {' -> '.join(result.path)}",
            f"Total Path Cost: {result.total_cost}",
            f"Traversed Nodes: {', '.join(result.visited_nodes)}",
            "",
            "Heuristic Values Used:",
        ]
        for node, heuristic_value in result.heuristic_trace:
            lines.append(f"  {node}: {heuristic_value}  (h to {destination}: {heuristic_values[node]})")
        self._write_output("\n".join(lines))

    def _append_history(self, source: str, destination: str, result: RouteResult) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        path_text = " -> ".join(result.path)
        self.history.append(
            {
                "time": timestamp,
                "source": source,
                "destination": destination,
                "cost": str(result.total_cost),
                "path": path_text,
            }
        )
        self.history_tree.insert("", tk.END, values=(timestamp, source, destination, result.total_cost, path_text))

    def _write_output(self, text: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, text)
        self.output_text.configure(state=tk.DISABLED)

    def reset(self) -> None:
        self.source_var.set(self.cities[0])
        self.destination_var.set(self.cities[-1])
        self.zoom_var.set(1.8)
        self.animate_var.set(True)
        self.current_result = None
        self._write_output("Run a search to see the route summary here.")
        self._refresh_graph(path=None, visited=None, current_node=None)
        if self.animation_window is not None:
            self.animation_window.close()
            self.animation_window = None
