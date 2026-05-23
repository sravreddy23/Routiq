# Greedy Best First Search Route Planner

A beginner-friendly Python desktop application that demonstrates **Greedy Best First Search (GBFS)** for route planning. The app lets you choose a source city and a destination city, then shows the route, total path cost, traversed nodes, heuristic values, and a highlighted graph visualization.

## Features

- Tkinter-based desktop GUI with a dark modern UI
- Greedy Best First Search implemented with a priority queue
- Weighted sample graph with 10 cities
- Dynamic heuristic values calculated from city positions
- Embedded NetworkX + Matplotlib graph visualization
- Animated traversal window
- Route history panel
- Reset button and invalid-input handling
- No-path-found handling

## Project Structure

```text
main.py
algorithm.py
graph_data.py
gui.py
visualization.py
requirements.txt
README.md
```

## Requirements

- Python 3.10 or newer is recommended
- `tkinter` is included with most standard Python installations
- `networkx`
- `matplotlib`

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the App

```bash
python main.py
```

## How It Works

The route planner uses Greedy Best First Search, which selects the next node using only the heuristic value:

$$f(n) = h(n)$$

The heuristic in this project is the straight-line distance from each node to the chosen destination city.

The app reports:

- Best route/path
- Total path cost
- Traversed nodes
- Heuristic values used during traversal

## Sample Graph Data

The graph now loads an India-wide city dataset from [data/india_cities.json](data/india_cities.json) and builds a connected weighted network automatically using nearest-neighbor links.

If you want to expand or replace the dataset, edit the JSON file and keep the `name`, `x`, and `y` fields for each city.

## Screenshots

Add screenshots to a folder such as `screenshots/` and reference them here when you capture the finished UI.

Suggested files:

- `screenshots/main-window.png`
- `screenshots/route-details.png`
- `screenshots/traversal-animation.png`

## Notes

- GBFS is heuristic-driven, so it prioritizes promising nodes instead of guaranteeing the lowest-cost route.
- The application still calculates and displays the actual route cost for the path it finds.
- The graph uses an embedded Matplotlib canvas so the result updates inside the app window.
