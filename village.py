from __future__ import annotations

from typing import TYPE_CHECKING, List

from game_map import GameMap
import tile_types
from entity import Entity
from render_order import RenderOrder

def generate_static_map(
    map_width: int,
    map_height: int,
    player: Entity,
    stairs: Entity,
    map_file: str,
) -> GameMap:
    """Generate a static map from a text file."""
    village = GameMap(map_width, map_height)
    village.editor_trigger_positions = set()  # positions of 'M' tiles
    
    # Fill with grass and mark as explored
    village.tiles[...] = tile_types.grass
    village.explored[...] = True

    try:
        path = f"artwork/maps/{map_file}"
        with open(path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print(f"Warning: {path} not found. Using empty grass map.")
        return village
        
    word_colors = {
        "farm": (255, 255, 102),
        "inn": (210, 180, 140),
        "cartographer": (255, 255, 192),
        "apothecary": (180, 100, 255),
        "home": (180, 120, 60),
    }

    for y, line in enumerate(lines):
        if y >= map_height:
            break
            
        char_colors = {}
        lower_line = line.lower()
        for word, color in word_colors.items():
            idx = lower_line.find(word)
            if idx != -1:
                for i in range(idx, idx + len(word)):
                    char_colors[i] = color
                    
        for x, char in enumerate(line):
            if x >= map_width:
                break
                
            if x in char_colors and char.isalpha():
                village.tiles[x, y] = tile_types.grass
                village.tiles["dark"][x, y]["ch"] = ord(char)
                village.tiles["light"][x, y]["ch"] = ord(char)
                village.tiles["dark"][x, y]["fg"] = char_colors[x]
                village.tiles["light"][x, y]["fg"] = char_colors[x]
            elif char == 'T':
                village.tiles[x, y] = tile_types.tree
            elif char == '^':
                village.tiles[x, y] = tile_types.corn
            elif char == ':':
                village.tiles[x, y] = tile_types.road
            elif char == 'w':
                village.tiles[x, y] = tile_types.water
            elif char == '#':
                village.tiles[x, y] = tile_types.wall
            elif char == '+':
                village.tiles[x, y] = tile_types.wood_floor # Door
            elif char == 'F':
                village.tiles[x, y] = tile_types.farm_floor
            elif char == 'I':
                village.tiles[x, y] = tile_types.inn_floor
            elif char == 'C':
                village.tiles[x, y] = tile_types.cartographer_floor
            elif char == 'M':
                village.tiles[x, y] = tile_types.cartographer_floor
                village.editor_trigger_positions.add((x, y))
            elif char == 'A':
                village.tiles[x, y] = tile_types.apothecary_floor
            elif char == 'P':
                village.tiles[x, y] = tile_types.player_floor
            elif char == '@':
                village.tiles[x, y] = tile_types.player_floor
                player.x, player.y = x, y
            elif char == 'V':
                village.tiles[x, y] = tile_types.grass
                stairs.x, stairs.y = x, y
            elif char == 'U':
                village.tiles[x, y] = tile_types.wood_floor
                stairs.char = "U"
                stairs.x, stairs.y = x, y
            elif char == '=':
                village.tiles[x, y] = tile_types.wall
            elif char == 'r':
                village.tiles[x, y] = tile_types.wood_floor
            elif char == '.':
                village.tiles[x, y] = tile_types.grass
            else:
                if char != ' ':
                    village.tiles[x, y] = tile_types.grass
                    village.tiles["dark"][x, y]["ch"] = ord(char)
                    village.tiles["light"][x, y]["ch"] = ord(char)
                    village.tiles["dark"][x, y]["fg"] = (200, 200, 200)
                    village.tiles["light"][x, y]["fg"] = (255, 255, 255)
                else:
                    village.tiles[x, y] = tile_types.grass

    # Spawn NPCs only if this is the hub map
    if map_file == "hub.txt":
        Entity(gamemap=village, x=10, y=9, char="f", color=(255, 255, 102), name="Farmer", blocks_movement=True, render_order=RenderOrder.ACTOR)
        Entity(gamemap=village, x=17, y=35, char="c", color=(255, 255, 192), name="Cartographer", blocks_movement=True, render_order=RenderOrder.ACTOR)
        # Shift innkeeper north of the ==== bar
        Entity(gamemap=village, x=60, y=6, char="i", color=(210, 180, 140), name="Innkeeper", blocks_movement=True, render_order=RenderOrder.ACTOR)
        Entity(gamemap=village, x=60, y=35, char="a", color=(180, 100, 255), name="Apothecary", blocks_movement=True, render_order=RenderOrder.ACTOR)
    elif map_file == "inn_cellar.txt":
        # Spawn rats at 'r' locations inside cellar
        from components.ai import HostileEnemy
        from components.fighter import Fighter
        for y, line in enumerate(lines):
            for x, char in enumerate(line):
                if char == 'r':
                    Entity(gamemap=village, x=x, y=y, char="r", color=(150, 150, 150), name="Rat", blocks_movement=True, render_order=RenderOrder.ACTOR, ai_cls=HostileEnemy, fighter=Fighter(hp=5, defense=0, power=2))
    
    return village
