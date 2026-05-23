from __future__ import annotations

import os
import math
from typing import Iterable, Optional, Sequence

import matplotlib

# Choose backend depending on environment. For web deployments set WEB=1.
_WEB = os.environ.get("WEB") == "1"
if _WEB:
    matplotlib.use("Agg")
    tk = None
    ttk = None
    FigureCanvasTkAgg = None
else:
    try:
        import tkinter as tk
        from tkinter import ttk
        matplotlib.use("TkAgg")
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    except Exception:
        tk = None
        ttk = None
        FigureCanvasTkAgg = None
        matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
import networkx as nx

from graph_data import CITY_POSITIONS


APP_BG = "#0f172a"
PANEL_BG = "#111827"
CARD_BG = "#1f2937"
TEXT_COLOR = "#e5e7eb"
MUTED_TEXT = "#9ca3af"
ACCENT = "#38bdf8"
HIGHLIGHT = "#f97316"
ROUTE_COLOR = "#ef4444"
VISITED_COLOR = "#f59e0b"
NODE_COLOR = "#475569"
CURRENT_COLOR = "#22c55e"
EDGE_COLOR = "#64748b"


def _edge_key(source: str, target: str) -> frozenset[str]:
    return frozenset((source, target))


def draw_graph_figure(
    graph: nx.Graph,
    positions: dict[str, tuple[int, int]] | None = None,
    path: Optional[Sequence[str]] = None,
    visited: Optional[Iterable[str]] = None,
    current_node: Optional[str] = None,
    route_only: bool = False,
    zoom: float = 1.0,
    title: str = "Route Visualization",
    center: tuple[float, float] | None = None,
    xlim: tuple[float, float] | None = None,
    ylim: tuple[float, float] | None = None,
):
    positions = positions or CITY_POSITIONS
    visited_set = set(visited or [])
    path_nodes = set(path or [])
    path_edges = {_edge_key(source, target) for source, target in zip(path or [], (path or [])[1:])}

    if route_only and path:
        nodes_to_draw = list(dict.fromkeys(path))
        edges_to_draw = list(zip(path, path[1:]))
    else:
        nodes_to_draw = list(graph.nodes())
        edges_to_draw = list(graph.edges())

    figure, axis = plt.subplots(figsize=(8.5, 6.5), dpi=110)
    figure.patch.set_facecolor(APP_BG)
    axis.set_facecolor(APP_BG)
    axis.set_title(title, color=TEXT_COLOR, fontsize=14, fontweight="bold", pad=16)
    axis.axis("off")

    if route_only and path:
        highlighted_edges = [edge for edge in graph.edges() if _edge_key(*edge) in path_edges]
        nx.draw_networkx_edges(
            graph,
            positions,
            ax=axis,
            edgelist=highlighted_edges,
            width=3.5,
            edge_color=ROUTE_COLOR,
        )
    else:
        nx.draw_networkx_edges(
            graph,
            positions,
            ax=axis,
            edgelist=edges_to_draw,
            width=1.5,
            alpha=0.35,
            edge_color=EDGE_COLOR,
        )

        if path_edges:
            highlighted_edges = [edge for edge in graph.edges() if _edge_key(*edge) in path_edges]
            nx.draw_networkx_edges(
                graph,
                positions,
                ax=axis,
                edgelist=highlighted_edges,
                width=3.5,
                edge_color=ROUTE_COLOR,
            )

    node_colors = []
    for node in nodes_to_draw:
        if node == current_node:
            node_colors.append(CURRENT_COLOR)
        elif route_only and path:
            node_colors.append(ROUTE_COLOR)
        elif node in path_nodes:
            node_colors.append(ROUTE_COLOR)
        elif node in visited_set:
            node_colors.append(VISITED_COLOR)
        else:
            node_colors.append(NODE_COLOR)

    # scale node size inversely with zoom for better visibility
    base_node_size = 600
    node_size = max(80, int(base_node_size / max(0.5, zoom)))

    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=axis,
        nodelist=nodes_to_draw,
        node_color=node_colors,
        node_size=node_size,
        linewidths=1.0,
        edgecolors="#0b1120",
    )

    # Draw labels with collision avoidance when not route-only
    # Always label path nodes and current node
    labeled_positions = []
    label_threshold = 50  # pixels
    transform = axis.transData.transform

    def draw_label(x, y, text, fontsize=9, weight="bold"):
        txt = axis.text(x, y, text, fontsize=fontsize, fontweight=weight, color="white", ha="center", va="center")
        txt.set_path_effects([path_effects.Stroke(linewidth=1.6, foreground=PANEL_BG), path_effects.Normal()])

    # draw labels for path nodes first
    if path:
        for node in nodes_to_draw:
            if node in path_nodes or node == current_node:
                x, y = positions[node]
                draw_label(x, y, node, fontsize=10 if route_only else 9)
                xdisp, ydisp = transform((x, y))
                labeled_positions.append((xdisp, ydisp))

    # for the rest, draw only if they don't collide with existing labels
    if not route_only:
        for node in nodes_to_draw:
            if node in path_nodes or node == current_node:
                continue
            x, y = positions[node]
            xdisp, ydisp = transform((x, y))
            too_close = any(math.hypot(xdisp - lx, ydisp - ly) < label_threshold for lx, ly in labeled_positions)
            if not too_close:
                draw_label(x, y, node, fontsize=8, weight="normal")
                labeled_positions.append((xdisp, ydisp))

    if route_only and path:
        # show labels only for the highlighted route edges
        edge_labels = {edge: graph[edge[0]][edge[1]]["weight"] for edge in edges_to_draw if graph.has_edge(*edge)}
    else:
        # avoid clutter: only show all edge labels when there are few edges
        if len(edges_to_draw) <= 30:
            edge_labels = nx.get_edge_attributes(graph, "weight")
        else:
            edge_labels = {}
    nx.draw_networkx_edge_labels(
        graph,
        positions,
        edge_labels=edge_labels,
        ax=axis,
        font_size=9,
        font_color=TEXT_COLOR,
        label_pos=0.5,
        bbox=dict(facecolor=PANEL_BG, edgecolor="none", alpha=0.8, pad=0.25),
    )

    if nodes_to_draw:
        x_values = [positions[node][0] for node in nodes_to_draw]
        y_values = [positions[node][1] for node in nodes_to_draw]
        computed_x_center = (min(x_values) + max(x_values)) / 2
        computed_y_center = (min(y_values) + max(y_values)) / 2
        x_center = center[0] if center is not None else computed_x_center
        y_center = center[1] if center is not None else computed_y_center
        x_span = max(max(x_values) - min(x_values), 1.0) / zoom
        y_span = max(max(y_values) - min(y_values), 1.0) / zoom
        padding = 0.8
        computed_xlim = (x_center - (x_span / 2) - padding, x_center + (x_span / 2) + padding)
        computed_ylim = (y_center - (y_span / 2) - padding, y_center + (y_span / 2) + padding)
        if xlim is not None and ylim is not None:
            axis.set_xlim(*xlim)
            axis.set_ylim(*ylim)
        else:
            axis.set_xlim(*computed_xlim)
            axis.set_ylim(*computed_ylim)

    return figure


class TraversalAnimator:
    def __init__(
        self,
        parent: tk.Misc,
        graph: nx.Graph,
        positions: dict[str, tuple[int, int]],
        traversal_order: Sequence[str],
        path: Sequence[str],
        total_cost: float,
        zoom: float = 1.35,
        delay_ms: int = 750,
    ) -> None:
        self.parent = parent
        self.graph = graph
        self.positions = positions
        self.traversal_order = list(traversal_order)
        self.path = list(path)
        self.total_cost = total_cost
        self.zoom = zoom
        self.delay_ms = delay_ms
        self.step_index = 0
        self._after_id: Optional[str] = None

        self.window = tk.Toplevel(parent)
        self.window.title("Traversal Animation")
        self.window.configure(bg=APP_BG)
        self.window.geometry("960x720")
        self.window.minsize(860, 620)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        header = tk.Frame(self.window, bg=APP_BG)
        header.pack(fill=tk.X, padx=16, pady=(14, 6))
        tk.Label(
            header,
            text="GBFS Traversal Animation",
            bg=APP_BG,
            fg=TEXT_COLOR,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        self.status_label = tk.Label(
            header,
            text="Preparing traversal...",
            bg=APP_BG,
            fg=MUTED_TEXT,
            font=("Segoe UI", 10),
        )
        self.status_label.pack(anchor="w", pady=(2, 0))

        self.figure = draw_graph_figure(self.graph, self.positions, path=self.path, visited=[], current_node=None, route_only=True, zoom=self.zoom, title="Traversal in Progress")
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.window)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self.canvas.draw()

        footer = tk.Frame(self.window, bg=APP_BG)
        footer.pack(fill=tk.X, padx=16, pady=(0, 14))
        tk.Label(
            footer,
            text=f"Final route cost: {self.total_cost}",
            bg=APP_BG,
            fg=TEXT_COLOR,
            font=("Segoe UI", 10, "bold"),
        ).pack(side=tk.LEFT)
        ttk.Button(footer, text="Close", command=self.close).pack(side=tk.RIGHT)

        self.window.after(300, self._advance)

    def _advance(self) -> None:
        if self.step_index >= len(self.traversal_order):
            self.status_label.configure(text="Traversal complete. Final route is highlighted.")
            self._draw(current_node=None, visited=self.traversal_order)
            return

        current_node = self.traversal_order[self.step_index]
        visited_so_far = self.traversal_order[: self.step_index + 1]
        self.status_label.configure(
            text=f"Step {self.step_index + 1} of {len(self.traversal_order)}: visiting {current_node}"
        )
        self._draw(current_node=current_node, visited=visited_so_far)
        self.step_index += 1
        self._after_id = self.window.after(self.delay_ms, self._advance)

    def _draw(self, current_node: Optional[str] = None, visited: Optional[Sequence[str]] = None) -> None:
        plt.close(self.figure)
        self.figure = draw_graph_figure(
            self.graph,
            self.positions,
            path=self.path,
            visited=visited,
            current_node=current_node,
            route_only=True,
            zoom=self.zoom,
            title="Traversal Animation",
        )
        self.canvas.figure = self.figure
        self.canvas.draw_idle()

    def close(self) -> None:
        if self._after_id is not None:
            try:
                self.window.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None
        if self.window.winfo_exists():
            self.window.destroy()
