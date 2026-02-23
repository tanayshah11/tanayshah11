"""Generate an animated SVG of Conway's Game of Life for GitHub profile README."""

from pathlib import Path

import numpy as np

# Grid configuration
COLS = 80           # cells wide
ROWS = 20           # cells tall
CELL_SIZE = 12      # pixels per cell
GENERATIONS = 40    # number of frames
FRAME_DUR = 0.15    # seconds per frame

# Colors
BG_COLOR = "#0d1117"
CELL_COLOR = "#39d353"  # GitHub green

WIDTH = COLS * CELL_SIZE
HEIGHT = ROWS * CELL_SIZE

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = SCRIPT_DIR.parent / "assets" / "game-of-life.svg"


def random_grid(rng):
    """Generate a random initial grid with ~30% density."""
    return rng.choice([0, 1], size=(ROWS, COLS), p=[0.7, 0.3])


def step(grid):
    """Compute the next generation using Conway's rules."""
    neighbors = sum(
        np.roll(np.roll(grid, i, axis=0), j, axis=1)
        for i in (-1, 0, 1) for j in (-1, 0, 1)
        if not (i == 0 and j == 0)
    )
    birth = (grid == 0) & (neighbors == 3)
    survive = (grid == 1) & ((neighbors == 2) | (neighbors == 3))
    return (birth | survive).astype(int)


def generate_frames(grid, n_generations):
    """Run simulation and return list of grids."""
    frames = [grid.copy()]
    for _ in range(n_generations - 1):
        grid = step(grid)
        frames.append(grid.copy())
    return frames


def frames_to_svg(frames):
    """Convert list of grid frames into an animated SVG string."""
    total_dur = len(frames) * FRAME_DUR
    lines = []
    lines.append(
        f'<svg width="100%" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" '
        f'xmlns="http://www.w3.org/2000/svg">'
    )
    lines.append(f'  <rect width="{WIDTH}" height="{HEIGHT}" fill="{BG_COLOR}"/>')
    lines.append("  <style>")

    # Build keyframes: each cell that is alive in ANY frame gets an animation
    # Track which cells are alive in which frames
    cell_alive_frames = {}
    for fi, frame in enumerate(frames):
        for r in range(ROWS):
            for c in range(COLS):
                if frame[r, c] == 1:
                    key = (r, c)
                    if key not in cell_alive_frames:
                        cell_alive_frames[key] = set()
                    cell_alive_frames[key].add(fi)

    # Group cells by identical animation patterns to reduce SVG size
    pattern_to_cells = {}
    for cell, alive_set in cell_alive_frames.items():
        pattern = frozenset(alive_set)
        if pattern not in pattern_to_cells:
            pattern_to_cells[pattern] = []
        pattern_to_cells[pattern].append(cell)

    # Generate CSS keyframes for each unique pattern
    n_frames = len(frames)
    for pi, (pattern, cells) in enumerate(pattern_to_cells.items()):
        kf_name = f"p{pi}"
        lines.append(f"    @keyframes {kf_name} {{")
        prev_opacity = None
        for fi in range(n_frames):
            opacity = "1" if fi in pattern else "0"
            if opacity != prev_opacity:
                pct = fi * 100 // n_frames
                lines.append(f"      {pct}% {{ opacity: {opacity}; }}")
            prev_opacity = opacity
        final_opacity = "1" if 0 in pattern else "0"
        if prev_opacity != final_opacity:
            lines.append(f"      100% {{ opacity: {final_opacity}; }}")
        lines.append("    }")
        lines.append(
            f"    .p{pi} {{ animation: {kf_name} {total_dur:.1f}s steps(1) infinite; "
            f"opacity: {'1' if 0 in pattern else '0'}; }}"
        )

    lines.append("  </style>")

    # Render cells
    for pi, (pattern, cells) in enumerate(pattern_to_cells.items()):
        for r, c in cells:
            x = c * CELL_SIZE
            y = r * CELL_SIZE
            lines.append(
                f'  <rect class="p{pi}" x="{x}" y="{y}" '
                f'width="{CELL_SIZE - 1}" height="{CELL_SIZE - 1}" '
                f'rx="2" fill="{CELL_COLOR}"/>'
            )

    lines.append("</svg>")
    return "\n".join(lines)


def main():
    rng = np.random.default_rng()
    grid = random_grid(rng)
    frames = generate_frames(grid, GENERATIONS)
    svg = frames_to_svg(frames)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write(svg)
    print(f"Generated {len(frames)} frames, {len(svg)} bytes")


if __name__ == "__main__":
    main()
