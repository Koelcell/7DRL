from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tcod.console import Console


def render_bar(
    console: Console,
    current_value: int,
    maximum_value: int,
    total_size: int,
    x: int,
    y: int,
    vertical: bool = False,
    label: str = "HP",
    bg_color: Tuple[int, int, int] = (64, 0, 0),
    fg_color: Tuple[int, int, int] = (0, 128, 0),
) -> None:
    fill_size = int(float(current_value) / maximum_value * total_size)

    if not vertical:
        # Horizontal bar
        console.draw_rect(x=x, y=y, width=total_size, height=1, ch=ord(" "), bg=bg_color)
        if fill_size > 0:
            console.draw_rect(x=x, y=y, width=fill_size, height=1, ch=ord(" "), bg=fg_color)
        console.print(x=x + 1, y=y, string=f"{label}: {current_value}/{maximum_value}", fg=(255, 255, 255))
    else:
        # Vertical bar (growing down from top as requested)
        full_label = f"{label}:{current_value}/{maximum_value}"
        background_height = max(total_size, len(full_label))
        
        console.draw_rect(x=x, y=y, width=1, height=background_height, ch=ord(" "), bg=bg_color)
        if fill_size > 0:
            console.draw_rect(x=x, y=y, width=1, height=fill_size, ch=ord(" "), bg=fg_color)
        
        # Print label text vertically inside the bar
        for i, char in enumerate(full_label):
            console.print(x=x, y=y + i, string=char, fg=(255, 255, 255))
