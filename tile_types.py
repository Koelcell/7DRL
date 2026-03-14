from typing import Tuple

import numpy as np  # type: ignore

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype(
    [
        ("ch", np.int32),  # Unicode codepoint.
        ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
        ("bg", "3B"),
    ]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("walkable", bool),  # True if this tile can be walked over.
        ("transparent", bool),  # True if this tile doesn't block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when this tile is in FOV.
    ]
)


def new_tile(
    *,
    walkable: int,
    transparent: int,
    dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
    light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
) -> np.ndarray:
    """Helper function for defining individual tile types """
    return np.array((walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord("#"), (24, 24, 24), (0, 0, 0)), dtype=graphic_dt)

floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (75, 37, 0), (0, 0, 0)),
    light=(ord("."), (150, 75, 0), (0, 0, 0)),
)
wall = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("#"), (64, 64, 64), (0, 0, 0)),
    light=(ord("#"), (200, 200, 200), (0, 0, 0)),
)

grass = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (0, 64, 0), (0, 0, 0)),
    light=(ord("\""), (0, 191, 0), (0, 0, 0)),
)

tree = new_tile(
    walkable=False,
    transparent=False,
    dark=(ord("T"), (0, 48, 0), (0, 0, 0)), # dark green
    light=(ord("T"), (0, 127, 0), (0, 0, 0)), # light green
)

corn = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("^"), (128, 128, 0), (0, 0, 0)), # dark yellow
    light=(ord("^"), (255, 255, 102), (0, 0, 0)), # light yellow corn
)

road = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord(":"), (64, 64, 64), (0, 0, 0)), # dark gray
    light=(ord(":"), (128, 128, 128), (0, 0, 0)), # light gray / bold look
)

water = new_tile(
    walkable=False,
    transparent=True,
    dark=(ord("~"), (0, 0, 64), (0, 0, 127)),
    light=(ord("~"), (0, 191, 255), (0, 0, 255)),
)

wood_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (64, 32, 0), (0, 0, 0)),
    light=(ord("."), (139, 69, 19), (0, 0, 0)),
)

farm_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (128, 128, 0), (0, 0, 0)), # dark yellow
    light=(ord("."), (255, 255, 0), (0, 0, 0)), # light yellow
)

apothecary_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (64, 0, 64), (0, 0, 0)), # dark purple
    light=(ord("."), (128, 0, 128), (0, 0, 0)), # light purple
)

cartographer_floor = new_tile(
    walkable=True,
    transparent=True,
    dark=(ord("."), (128, 128, 96), (0, 0, 0)), # dark parchment
    light=(ord("."), (255, 255, 192), (0, 0, 0)), # light parchment
)

player_floor = wood_floor
inn_floor = wood_floor


