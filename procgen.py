from __future__ import annotations

import random
from typing import Iterator, Tuple, List, TYPE_CHECKING

import tcod

from game_map import GameMap
import tile_types

if TYPE_CHECKING:
    from entity import Entity


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    @property
    def inner(self) -> Iterator[Tuple[int, int]]:
        """Return the coordinates of the inner area of this room."""
        for x in range(self.x1 + 1, self.x2):
            for y in range(self.y1 + 1, self.y2):
                yield x, y


class CircularRoom:
    def __init__(self, center_x: int, center_y: int, radius: int):
        self.x, self.y = center_x, center_y
        self.radius = radius

    @property
    def center(self) -> Tuple[int, int]:
        return self.x, self.y

    @property
    def inner(self) -> Iterator[Tuple[int, int]]:
        """Return the coordinates of the inner area of this circular room."""
        for x in range(self.x - self.radius, self.x + self.radius + 1):
            for y in range(self.y - self.radius, self.y + self.radius + 1):
                if ((x - self.x) ** 2 + (y - self.y) ** 2) <= self.radius ** 2:
                    yield x, y


class BlobRoom:
    def __init__(self, x: int, y: int, size: int):
        self.x, self.y = x, y
        self.size = size
        self._tiles: List[Tuple[int, int]] = []
        self._generate_blob()

    def _generate_blob(self) -> None:
        """Simple drunken walk to generate a blob shape."""
        cx, cy = self.x, self.y
        self._tiles.append((cx, cy))
        for _ in range(self.size * 3):
            cx += random.choice([-1, 0, 1])
            cy += random.choice([-1, 0, 1])
            self._tiles.append((cx, cy))

    @property
    def center(self) -> Tuple[int, int]:
        return self.x, self.y

    @property
    def inner(self) -> Iterator[Tuple[int, int]]:
        for x, y in self._tiles:
            yield x, y


def tunnel_between(
    start: Tuple[int, int], end: Tuple[int, int]
) -> Iterator[Tuple[int, int]]:
    """Return an L-shaped tunnel between these two points."""
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def generate_dungeon(
    max_rooms: int,
    room_min_size: int,
    room_max_size: int,
    map_width: int,
    map_height: int,
    player: Entity,
    stairs: Entity,
) -> GameMap:
    """Generate a new dungeon map."""
    dungeon = GameMap(map_width, map_height)

    rooms: List[Any] = []

    for r in range(max_rooms):
        room_type = random.random()
        
        if room_type < 0.6:  # 60% rectangles
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)
            x = random.randint(0, dungeon.width - room_width - 1)
            y = random.randint(0, dungeon.height - room_height - 1)
            new_room = RectangularRoom(x, y, room_width, room_height)
        elif room_type < 0.8:  # 20% circles
            radius = random.randint(room_min_size // 2, room_max_size // 2)
            x = random.randint(radius, dungeon.width - radius - 1)
            y = random.randint(radius, dungeon.height - radius - 1)
            new_room = CircularRoom(x, y, radius)
        else:  # 20% blobs
            size = random.randint(room_min_size, room_max_size)
            x = random.randint(5, dungeon.width - 6)
            y = random.randint(5, dungeon.height - 6)
            new_room = BlobRoom(x, y, size)

        # Dig out this rooms inner area.
        for x, y in new_room.inner:
            if dungeon.in_bounds(x, y):
                dungeon.tiles[x, y] = tile_types.floor

        if len(rooms) == 0:
            # The first room, where the player starts.
            player.x, player.y = new_room.center
        else:  # All rooms after the first.
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tiles[x, y] = tile_types.floor

        # Finally, append the new room to the list.
        rooms.append(new_room)

    # Place stairs in the last room
    stairs.x, stairs.y = rooms[-1].center

    return dungeon

