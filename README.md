# Bloxorz Solver AI

A Python implementation of the classic **Bloxorz** puzzle game with an interactive **3D interface** and multiple AI search algorithms for automatically solving game levels.

## Features

- Play Bloxorz manually.
- AI can automatically solve maps using:
  - Breadth-First Search (BFS)
  - Depth-First Search (DFS)
  - Uniform Cost Search (UCS)
  - A* Search
- Supports advanced game mechanics:
  - Split Block
  - Bridge Switches
  - Heavy Switches
  - Fragile Tiles
  - Dynamic Bridges
- Displays AI statistics:
  - Search time
  - Peak memory usage
  - Expanded nodes
  - Solution length
- Undo previous move.
- Can switch to next level at will.
- Smooth 3D animation using Ursina Engine.
- Sound effects for movement, switches, winning, and falling.

---

# Project Structure

```
BloxorzSolver/
│
├── game_3d.py                # Main game and graphical interface
├── bloxorz_go_version.py     # AI search algorithms
├── levels.json               # Game maps
├── background.png
├── background2.png
├── move.wav
├── switch.wav
├── win.wav
├── fall.wav
├── requirements.txt
├── README.md
```

---

# Requirements

- Python 3.12 or 3.13
- Ursina Engine

Install dependencies:

```bash
pip install -r requirements.txt
```

```bash
pip install ursina
```

---

# Running the Game

Start the game with

```bash
python game_3d.py
```

---

# Controls

## Manual Mode

| Key | Action |
|------|--------|
| W / ↑ | Move Up |
| S / ↓ | Move Down |
| A / ← | Move Left |
| D / → | Move Right |
| Space | Switch active block (Split mode) |
| Z | Undo |
| R | Restart level |
| N | Next level |

---

# AI Algorithms

The project implements four search algorithms.

## Breadth-First Search (BFS)

- Complete
- Guarantees shortest path
- High memory usage

---

## Depth-First Search (DFS)

- Low memory usage
- Does not guarantee optimal solution

---

## Uniform Cost Search (UCS)

- Expands nodes according to cumulative path cost
- Supports different movement costs

---

## A* Search

Uses Manhattan Distance heuristic.

```
h(n) = |x - goal_x| + |y - goal_y|
```

Provides significantly faster searching than BFS on large maps.

---

# Game Mechanics

The implementation supports several special tiles.

| Tile | Description |
|------|-------------|
| S | Start position |
| E | Goal |
| ~ | Fragile tile |
| X | Split switch |
| [ ] | Split landing pads |
| q,w,e | Soft switches |
| a,s,d | Heavy switches |
| 1,2,3 | Dynamic bridges |

---

# AI Performance Metrics

After solving a level, the game reports:

- Search Time (ms)
- Peak Memory (KB)
- Expanded Nodes
- Solution Length

These statistics are generated automatically during search.

---

# Technologies

- Python
- Ursina Engine
- Object-Oriented Programming
- Graph Search Algorithms
- Heap Queue
- Queue / Stack
- Tracemalloc
- JSON

---

# Authors

Developed as an Artificial Intelligence course project.

Main components include:

- 3D game implementation
- AI search algorithms
- Interactive user interface
- Performance evaluation

---

# Future Improvements

- Greedy Best-First Search
- Iterative Deepening DFS
- Bidirectional Search
- Better heuristic functions
- Level editor
- Random map generation
- Additional puzzle mechanics

---

# License

This project is intended for educational purposes.
