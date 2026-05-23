import os
from io import BytesIO
from flask import Flask, send_file, jsonify, request, render_template, make_response

# Set WEB env so visualization uses Agg
os.environ["WEB"] = "1"

from graph_data import build_graph, get_city_names, CITY_POSITIONS
from algorithm import greedy_best_first_search
from visualization import draw_graph_figure

app = Flask(__name__, static_folder="static", template_folder="templates")


@app.after_request
def add_no_cache(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/cities")
def cities():
    return jsonify(get_city_names())


@app.route("/search", methods=["POST"])
def search():
    data = request.get_json() or {}
    source = data.get("source")
    destination = data.get("destination")
    if not source or not destination:
        return jsonify({"error": "source and destination required"}), 400
    try:
        graph = build_graph()
        heuristics = None
        # run search
        result = greedy_best_first_search(graph, source, destination, lambda c, g: heuristics_lookup(c, destination))
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    if result is None:
        return jsonify({"error": "no path found"}), 404

    return jsonify({
        "path": result.path,
        "total_cost": result.total_cost,
        "visited_nodes": result.visited_nodes,
        "heuristic_trace": result.heuristic_trace,
    })


def heuristics_lookup(city: str, goal: str) -> float:
    # lazy import to avoid circular issues
    from graph_data import get_heuristic_values

    values = get_heuristic_values(goal)
    return float(values[city])


@app.route("/graph.png")
def graph_png():
    source = request.args.get("source")
    destination = request.args.get("destination")
    zoom = float(request.args.get("zoom", "1.6"))
    step = request.args.get("step")

    graph = build_graph()

    path = None
    visited = None
    current_node = None
    route_only = False
    if source and destination:
        result = greedy_best_first_search(graph, source, destination, lambda c, g: heuristics_lookup(c, destination))
        if result:
            path = result.path
            route_only = True
            # if a step is provided, show visited nodes up to that step
            if step is not None:
                try:
                    s = int(step)
                except Exception:
                    s = None
                if s is None:
                    visited = result.visited_nodes
                    current_node = path[-1]
                else:
                    visited = result.visited_nodes[: s + 1]
                    current_node = visited[-1] if visited else None
            else:
                visited = result.visited_nodes
                current_node = path[-1]

    fig = draw_graph_figure(graph, path=path, visited=visited, current_node=current_node, route_only=route_only, zoom=zoom)
    buf = BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/graph_data")
def graph_data_json():
    """Return graph structure and positions as JSON for client-side rendering.

    Query params: source, destination
    """
    source = request.args.get("source")
    destination = request.args.get("destination")

    graph = build_graph()

    nodes = {name: list(pos) for name, pos in CITY_POSITIONS.items()}
    edges = []
    for u, v, data in graph.edges(data=True):
        edges.append({"u": u, "v": v, "weight": float(data.get("weight", 0.0))})

    path = None
    visited = None
    if source and destination:
        result = greedy_best_first_search(graph, source, destination, lambda c, g: heuristics_lookup(c, destination))
        if result:
            path = result.path
            visited = result.visited_nodes

    return jsonify({"nodes": nodes, "edges": edges, "path": path or [], "visited": visited or []})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
