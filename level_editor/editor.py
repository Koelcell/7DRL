"""
ASCII Level Editor - launched when the player stands on an 'M' tile.
Saves maps to artwork/maps/custom/*.txt
"""
from __future__ import annotations

import os
import time
from typing import Optional, Tuple, TYPE_CHECKING

import tcod
import tcod.event

# Editor settings
EDITOR_WIDTH  = 80
EDITOR_HEIGHT = 50
SAVE_DIR      = "artwork/maps/custom"

# Palette: char -> displayed glyph cycling through available symbols
PALETTE = list(".#TFCIAPW+=^:wVUrf@><") 

PALETTE_COLORS = {
    '.': (40, 80, 40),
    '#': (150, 150, 150),
    'T': (0, 127, 0),
    'F': (255, 255, 102),
    'I': (210, 180, 140),
    'C': (255, 255, 192),
    'A': (180, 100, 255),
    'P': (180, 120, 60),
    'W': (100, 100, 255),
    '+': (139, 69, 19),
    '=': (100, 60, 20),
    '^': (255, 255, 102),
    ':': (128, 128, 128),
    'w': (0, 191, 255),
    'V': (255, 255, 0),
    'U': (255, 255, 0),
    'r': (150, 150, 150),
    'f': (255, 200, 50),
    '@': (255, 255, 255),
    '>': (200, 200, 200),
    '<': (200, 200, 200),
}


class LevelEditor:
    """Simple ASCII level editor."""

    def __init__(self, map_width: int = EDITOR_WIDTH, map_height: int = EDITOR_HEIGHT):
        self.map_width = map_width
        self.map_height = max(1, map_height - 2)  # Reserve 2 lines for HUD
        self.grid = [['.'] * self.map_width for _ in range(self.map_height)]
        self.cursor_x = 0
        self.cursor_y = 0
        self.palette_index = 0
        self.current_char = PALETTE[self.palette_index]
        self.filename: Optional[str] = None
        self.message = "Level Editor | [Arrows] Move  [Enter] Paint  [Tab] Cycle  [S] Save  [ESC] Quit"

    @property
    def current_palette_char(self) -> str:
        return PALETTE[self.palette_index]

    def paint(self) -> None:
        """Paint current char at cursor."""
        self.grid[self.cursor_y][self.cursor_x] = self.current_palette_char

    def cycle_palette(self, reverse: bool = False) -> None:
        if reverse:
            self.palette_index = (self.palette_index - 1) % len(PALETTE)
        else:
            self.palette_index = (self.palette_index + 1) % len(PALETTE)

    def save(self) -> str:
        """Save to a uniquely timestamped file and return the path."""
        os.makedirs(SAVE_DIR, exist_ok=True)
        filename = os.path.join(SAVE_DIR, f"map_{int(time.time())}.txt")
        with open(filename, "w", encoding="utf-8") as f:
            for row in self.grid:
                f.write("".join(row) + "\n")
        self.filename = filename
        self.message = f"Saved to {filename}"
        return filename

    def render(self, console: tcod.console.Console) -> None:
        console.clear()
        # Draw grid
        for y, row in enumerate(self.grid):
            for x, ch in enumerate(row):
                fg = PALETTE_COLORS.get(ch, (200, 200, 200))
                console.print(x=x, y=y, string=ch, fg=fg)
        # Draw cursor
        console.print(x=self.cursor_x, y=self.cursor_y, string=self.current_palette_char, fg=(255, 0, 0))
        # HUD bar
        hud_y = self.map_height
        palette_preview = "  ".join(f"[{c}]" if i == self.palette_index else f" {c} " for i, c in enumerate(PALETTE[:10]))
        console.print(x=0, y=hud_y, string=f"Brush: [{self.current_palette_char}]  {palette_preview}", fg=(255, 255, 0))
        console.print(x=0, y=hud_y + 1, string=self.message[:self.map_width], fg=(180, 180, 180))

    def handle_event(self, event: tcod.event.Event) -> bool:
        """Handle a tcod event. Returns True to keep running, False to exit."""
        if isinstance(event, tcod.event.KeyDown):
            key = event.sym
            if key == tcod.event.KeySym.ESCAPE:
                return False
            elif key == tcod.event.KeySym.UP:
                self.cursor_y = max(0, self.cursor_y - 1)
            elif key == tcod.event.KeySym.DOWN:
                self.cursor_y = min(self.map_height - 1, self.cursor_y + 1)
            elif key == tcod.event.KeySym.LEFT:
                self.cursor_x = max(0, self.cursor_x - 1)
            elif key == tcod.event.KeySym.RIGHT:
                self.cursor_x = min(self.map_width - 1, self.cursor_x + 1)
            elif key == tcod.event.KeySym.RETURN:
                self.paint()
            elif key == tcod.event.KeySym.TAB:
                self.cycle_palette(reverse=bool(event.mod & tcod.event.Modifier.SHIFT))
            elif key == tcod.event.KeySym.s:
                self.save()
            else:
                # Type a character directly to set brush
                char = chr(key) if 32 <= key < 127 else None
                if char and char in PALETTE:
                    self.palette_index = PALETTE.index(char)
                    self.message = f"Brush set to [{char}]"
        elif isinstance(event, tcod.event.MouseMotion):
            # Allow painting by dragging (if LMB held)
            pass
        elif isinstance(event, tcod.event.MouseButtonDown):
            tile_x = event.tile.x
            tile_y = event.tile.y
            if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
                self.cursor_x = tile_x
                self.cursor_y = tile_y
                self.paint()
        elif isinstance(event, tcod.event.MouseButtonUp):
            pass
        return True


def run_level_editor(context: tcod.context.Context, console: tcod.console.Console) -> None:
    """Run the level editor in a modal loop. Exits on ESC."""
    editor = LevelEditor(map_width=console.width, map_height=console.height)
    running = True
    while running:
        editor.render(console)
        context.present(console)
        for event in tcod.event.wait():
            if isinstance(event, tcod.event.Quit):
                raise SystemExit()
            context.convert_event(event)
            running = editor.handle_event(event)
            if not running:
                break
