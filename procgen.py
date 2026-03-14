from __future__ import annotations

import random
from typing import Iterator, Tuple, List, TYPE_CHECKING

import tcod

from game_map import GameMap
import tile_types

from entity import Entity, Actor, Item
from components.fighter import Fighter
from components.ai import HostileEnemy
from components.inventory import Inventory
from components.consumable import HealingConsumable


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


def place_entities(
    room: RectangularRoom | CircularRoom | BlobRoom, 
    entities: List[Entity], 
    max_monsters: int,
    max_items: int,
) -> None:
    number_of_monsters = random.randint(0, max_monsters)
    number_of_items = random.randint(0, max_items)

    for i in range(number_of_monsters):
        # Choose a random spot in the room (from its inner tiles)
        inner_tiles = list(room.inner)
        if not inner_tiles:
            continue
        x, y = random.choice(inner_tiles)

        if not any(entity.x == x and entity.y == y for entity in entities):
            if random.random() < 0.8:
                entities.append(
                    Actor(
                        x=x,
                        y=y,
                        char="o",
                        color=(63, 127, 63),
                        name="Orc",
                        ai_cls=HostileEnemy,
                        fighter=Fighter(hp=10, defense=0, power=3),
                        inventory=Inventory(capacity=0),
                    )
                )
            else:
                entities.append(
                    Actor(
                        x=x,
                        y=y,
                        char="T",
                        color=(0, 127, 0),
                        name="Troll",
                        ai_cls=HostileEnemy,
                        fighter=Fighter(hp=16, defense=1, power=4),
                        inventory=Inventory(capacity=0),
                    )
                )

    for i in range(number_of_items):
        x, y = random.choice(list(room.inner))

        if not any(entity.x == x and entity.y == y for entity in entities):
            entities.append(
                Item(
                    x=x,
                    y=y,
                    char="!",
                    color=(127, 0, 255),
                    name="Health Potion",
                    consumable=HealingConsumable(amount=5),
                )
            )


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
    entities = [player, stairs]

    rooms: List[Any] = []

    for r in range(max_rooms):
        room_type = random.random()
        
        if room_type < 0.6:  # 60% rectangles
            room_width = random.randint(room_min_size, room_max_size)
            room_height = random.randint(room_min_size, room_max_size)
            x = random.randint(1, dungeon.width - room_width - 1)
            y = random.randint(1, dungeon.height - room_height - 1)
            new_room = RectangularRoom(x, y, room_width, room_height)
        elif room_type < 0.8:  # 20% circles
            radius = random.randint(room_min_size // 2, room_max_size // 2)
            x = random.randint(radius + 1, dungeon.width - radius - 2)
            y = random.randint(radius + 1, dungeon.height - radius - 2)
            new_room = CircularRoom(x, y, radius)
        else:  # 20% blobs
            size = random.randint(room_min_size, room_max_size)
            x = random.randint(size + 1, dungeon.width - size - 2)
            y = random.randint(size + 1, dungeon.height - size - 2)
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

        if len(rooms) > 0: # Don't place monsters in the first room
            place_entities(new_room, entities, 2, 1)

        # Finally, append the new room to the list.
        rooms.append(new_room)

    # Place stairs in the last room
    stairs.x, stairs.y = rooms[-1].center

    # Enforce a mandatory wall perimeter (closing all openings to the screen border)
    for x in range(dungeon.width):
        dungeon.tiles[x, 0] = tile_types.wall
        dungeon.tiles[x, dungeon.height - 1] = tile_types.wall
    for y in range(dungeon.height):
        dungeon.tiles[0, y] = tile_types.wall
        dungeon.tiles[dungeon.width - 1, y] = tile_types.wall

    return dungeon, entities

