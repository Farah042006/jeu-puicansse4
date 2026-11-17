🎮 Connect 4 (Puissance 4) — MinMax vs Alpha-Beta
A Connect 4 game in Python with a Pygame interface, where you can play against a computer driven by **MinMax** or **Alpha-Beta pruning**, and compare both algorithms side by side on the same game.


 ✨ Features

- 👥 **Human vs Human** on one board.
- 🤖 **Human vs Computer** with a choice of algorithm:
  - 🔴 **MinMax**
  - ⚡ **Alpha-Beta** (same result as MinMax, far fewer nodes)
  - 🏆 **Both**: two boards in the same window, MinMax on the left and Alpha-Beta on the right. Your move is played on both boards, then both algorithms compute **in parallel**. Live timers, node counts and a final comparison show that the moves are identical and Alpha-Beta is faster.
- 🎚️ Adjustable search depth (1 to 8) and choice of who starts.
- ↩️ **Undo** button, and an end-of-game panel (**Replay**, **Main menu**, **View the board**).
- 🧵 The computer thinks in a background thread, so the window never freezes.
- 📊 Console benchmark (`compare.py`) comparing MinMax and Alpha-Beta at depths 1 to 6.

 📦 Requirements

- Python 3.8 or newer
- [Pygame](https://www.pygame.org/)

Install Pygame:

```bash
pip install pygame
```

 🚀 Run

```bash
python main.py       # The game
python compare.py    # Console benchmark: MinMax vs Alpha-Beta (same position)
```

 🎯 Controls

| Where | Key / Click | Action |
|---|---|---|
| Menu | Click, `1`–`8`, `Enter` | Choose options, set depth, start the game |
| Game | Click a column or `1`–`7` | Drop a piece |
| Game | `R` | New game |
| Game | `U` | Undo (your last move and the computer's reply) |
| Game | `V` | Show / hide the end-of-game panel |
| Game | `Enter` | Replay (when the end-of-game panel is shown) |
| Game | `Esc` | Back to the menu |

💡 The window size can be changed with `UI_SCALE` at the top of `main.py`.

 📁 Project Structure

| File | Role |
|---|---|
| `board.py` | Game rules: 6x7 board, gravity, win detection, `play` / `undo` |
| `ai.py` | Heuristic evaluation, MinMax, Alpha-Beta, best-move selection |
| `main.py` | Pygame interface: menu, game screen, computer thread, end-of-game panel |

**Dependencies:** `main.py` → `ai.py` → `board.py`.

The AI knows nothing about the interface, so it can be tested on its own.

 🧠 How It Works

 🎲 Board (`board.py`)

- `grid[r][c]` with `r = 0` as the **bottom** row. Cells hold:
  - `0` (empty)
  - `1` (X, red, first player)
  - `2` (O, yellow)
- `heights[c]` stores the number of pieces in each column, so the landing row is found in O(1).
- `play(c)` drops a piece and checks for a win **only around the new piece** (4 directions).
- `undo()` removes the last move exactly, which lets the search play, explore and undo without copying the board.
- `would_win(c, p)` tells whether player `p` would win immediately by playing column `c`, without changing the board.

 🔴 MinMax Algorithm

- Depth-limited search.
- MAX is the computer and MIN is the opponent.
- Leaves are scored by the heuristic, and finished games get an exact value.

 ⚡ Alpha-Beta Pruning

- Returns the same value as MinMax but stops exploring a branch as soon as `beta <= alpha`.
- Columns are explored center first (`3, 2, 4, 1, 5, 0, 6`), which improves pruning.

 🏅 Terminal Values

A win is worth `1_000_000 + depth` and a loss `-1_000_000 - depth`, so the computer prefers winning fast and losing late.

 🎯 Immediate Check (Optional)

Before searching, play a winning move if one exists; otherwise, block the opponent's winning move.

 📊 Heuristic Evaluation

The board contains **69 windows of 4 aligned cells**:

- 24 horizontal
- 21vertical
- 24 diagonal

For a position evaluated from the computer's point of view:

Window with 3 of my pieces + 1 empty (no opponent piece)    +5

Window with 2 of my pieces + 2 empty                        +2

Same patterns for the opponent                              -5 / -2

Piece in the center column                                  +3 (mine) / -3 (opponent's)

Window containing both colors                               0 (dead)

⏱️ Complexity

With a branching factor b (at most 7) and depth d:

MinMax: explores about O(b^d) nodes.

Alpha-Beta: explores between O(b^(d/2)) (best case with good move ordering) and O(b^d) (worst case).

So at the same depth, Alpha-Beta can play the same move with far fewer nodes, and for the same time it can search deeper.

🏆 Comparing the Algorithms

Two ways to see the comparison:

1. In-Game Comparison

Choose Human vs Computer → Both.

Play a few moves and read the timers and the comparison line under the boards.

2. Console Benchmark

Run:

python compare.py

It prints the chosen column, node count and time for MinMax and Alpha-Beta at depths 1 to 6, and checks that both choose the same column.

Note: In "Both" mode, the immediate win/block shortcut is disabled so the node counts reflect the real searches.

Times are wall-clock times; because of Python's GIL, the two threads share the CPU, which slightly penalizes Alpha-Beta, so the real performance gap is at least as large as shown.

🚀 Possible Improvements

Transposition table and iterative deepening.

Bitboard representation.

Heuristic that takes row parity and double threats into account.

Computer vs Computer mode.

👩‍💻 Author

 KEFFOUS Farah

Computer Science Student | Artificial Intelligence
