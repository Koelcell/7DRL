from __future__ import annotations

import time
import tcod
import numpy as np
from typing import Iterable, Any, Optional, TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console

from entity import Entity
from game_map import GameMap
from input_handlers import BaseEventHandler
from message_log import MessageLog
from render_functions import render_bar

if TYPE_CHECKING:
    from entity import Actor


class Engine:
    def __init__(self, entities: Iterable[Entity], event_handler: BaseEventHandler, game_map: GameMap, player: Actor, stairs: Entity):
        self.event_handler = event_handler
        self.game_map = game_map
        self.game_map.engine = self
        self.player = player
        self.stairs = stairs
        self.message_log = MessageLog()
        self.message_log.add_message("Welcome to the dungeon, adventurer!")
        for entity in entities:
            entity.gamemap = self.game_map
            self.game_map.entities.add(entity)

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def handle_events(self, events: Iterable[Any], context: Context) -> None:
        from input_handlers import (
            Action, 
            MovementAction, 
            FullscreenAction, 
            EscapeAction, 
            MouseMovementAction, 
            AutoExploreAction,
            PickupAction,
            ItemAction,
            QuickUseAction,
            RetryAction,
            RetryGame,
            TakeStairsAction,
        )

        for event in events:
            if isinstance(event, Action):
                action = event
            else:
                action = self.event_handler.dispatch(event)

            if action is None:
                continue

            if isinstance(action, MovementAction):
                action.perform(self, self.player)
                self.handle_enemy_turns()
                # Check if player stepped on an M (editor trigger) tile
                editor_pos = getattr(self.game_map, 'editor_trigger_positions', set())
                if (self.player.x, self.player.y) in editor_pos:
                    from level_editor import run_level_editor
                    run_level_editor(context, console)
                    # After returning, re-render the hub
                    self.render(console, context)
            
            elif isinstance(action, (PickupAction, ItemAction, QuickUseAction, RetryAction, TakeStairsAction)):
                action.perform(self, self.player)
                self.handle_enemy_turns()
            
            elif isinstance(action, AutoExploreAction):
                self.perform_auto_explore()
                self.handle_enemy_turns()

            elif isinstance(action, MouseMovementAction):
                # Calculate path and move one step
                cost = np.array(self.game_map.tiles["walkable"], dtype=np.int8)
                graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((self.player.x, self.player.y))
                
                # Check if target is walkable
                if self.game_map.tiles["walkable"][int(action.target_x), int(action.target_y)]:
                    path = pathfinder.path_to((int(action.target_x), int(action.target_y))).tolist()
                    if len(path) > 1:
                        # Move to the first step in the path
                        next_x, next_y = path[1]
                        dx = next_x - self.player.x
                        dy = next_y - self.player.y
                        MovementAction(dx, dy).perform(self, self.player)
                        self.handle_enemy_turns()

            elif isinstance(action, FullscreenAction):
                context.sdl_window.fullscreen = not context.sdl_window.fullscreen

            elif isinstance(action, EscapeAction):
                action.perform(self, self.player)

    def perform_auto_explore(self) -> None:
        from input_handlers import MovementAction
        
        # 1. Get the cost map (walkable = 1, non-walkable = 0 for tcod.path)
        # However dijkstra2d often uses 0 for wall if it's a bool map, but cost usually is 1 for floor, 0 for wall
        cost = np.array(self.game_map.tiles["walkable"], dtype=np.int8)
        
        # 2. Compute distances from player to all tiles
        # dijkstra2d requires an output array initialized with high values and roots set to 0
        distances = np.full((self.game_map.width, self.game_map.height), fill_value=999, dtype=np.int32)
        distances[self.player.x, self.player.y] = 0
        tcod.path.dijkstra2d(distances, cost, 2, 3)
        
        # 3. Find candidates: walkable AND unexplored
        unexplored = ~self.game_map.explored
        candidates = self.game_map.tiles["walkable"] & unexplored
        
        if not np.any(candidates):
            print("No more unexplored walkable tiles.")
            return

        # 4. Filter distances to only include candidates
        # Use a large value for non-candidates
        masked_distances = np.where(candidates, distances, np.inf)
        
        # 5. Find the closest one
        min_dist = np.min(masked_distances)
        if min_dist == np.inf:
            print("No reachable unexplored tiles.")
            return
            
        # Get coordinates of all closest candidates
        min_indices = np.argwhere(masked_distances == min_dist)
        # Pick the first one (or random)
        target_x, target_y = min_indices[0]
        
        # 6. Pathfind to that target and take one step
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((self.player.x, self.player.y))
        path = pathfinder.path_to((target_x, target_y)).tolist()
        
        if len(path) > 1:
            next_x, next_y = path[1]
            dx = next_x - self.player.x
            dy = next_y - self.player.y
            MovementAction(dx, dy).perform(self, self.player)

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.game_map.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def handle_enemy_turns(self) -> None:
        from entity import Actor
        for entity in self.game_map.entities:
            if isinstance(entity, Actor) and entity.is_alive and entity != self.player:
                entity.ai.perform()

    def load_static_map(self, map_file: str) -> None:
        from village import generate_static_map
        
        # Clear existing entities except player and stairs
        # Note: In a full game, we'd preserve inventories/states, but here we just regenerate the map
        self.game_map, entities = generate_static_map(
            map_width=self.game_map.width,
            map_height=self.game_map.height,
            player=self.player,
            stairs=self.stairs,
            map_file=map_file,
        ), [] # Note: static map sets its own entities internally via Entity() calls
        
        self.game_map.engine = self
        self.game_map.entities.add(self.player)
        self.game_map.entities.add(self.stairs)
        
        for entity in self.game_map.entities:
            entity.gamemap = self.game_map
            
        self.update_fov()

    def new_level(self) -> None:
        from procgen import generate_dungeon

        self.game_map, entities = generate_dungeon(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=self.game_map.width,
            map_height=self.game_map.height,
            player=self.player,
            stairs=self.stairs,
        )
        self.game_map.engine = self
        for entity in entities:
            entity.gamemap = self.game_map
            self.game_map.entities.add(entity)

    def render(self, console: Console, context: Context) -> None:
        self.game_map.visible[:] = tcod.map.compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

        self.game_map.render(console)

        entities_sorted_for_rendering = sorted(
            self.game_map.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
             # Only print entities that are in the FOV
             if self.game_map.visible[entity.x, entity.y]:
                 console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

        if self.player.fighter.hp > 0:
            # Render game elements for living player
            self.message_log.render(console=console, x=1, y=45, width=78, height=4)
            
            # ... (render_bar call stays the same)
            render_bar(
                console=console,
                current_value=self.player.fighter.hp,
                maximum_value=self.player.fighter.max_hp,
                total_size=int(self.player.fighter.max_hp / 2),
                x=0,
                y=0,
                vertical=True,
                bg_color=(128, 0, 0),
                fg_color=(255, 0, 0),
            )

            # Render Monster HP for all visible monsters
            from entity import Actor
            visible_monsters = [
                entity for entity in self.game_map.entities
                if isinstance(entity, Actor) 
                and entity is not self.player 
                and self.game_map.visible[entity.x, entity.y]
                and entity.is_alive
            ]
            
            for i, monster in enumerate(visible_monsters):
                render_bar(
                    console=console,
                    current_value=monster.fighter.hp,
                    maximum_value=monster.fighter.max_hp,
                    total_size=int(monster.fighter.max_hp / 2),
                    x=79 - i, # Stack them from the right edge moving left
                    y=0,
                    vertical=True,
                    label=monster.name[:5],
                    bg_color=(31, 63, 31),
                    fg_color=(63, 127, 63),
                )

            # Render Inventory Items below the HP Bar
            # The HP bar occupies vertical space: y=0 to y=total_size-1
            hp_bar_height = int(self.player.fighter.max_hp / 2)
            inv_cap = self.player.inventory.capacity
            
            # Draw thin border outlines for all capacity slots
            for i in range(inv_cap):
                console.print(x=0, y=hp_bar_height + 1 + i, string="[ ]", fg=(128, 128, 128))
                
            # Draw the actual items inside the active slots
            for i, item in enumerate(self.player.inventory.items[:inv_cap]):
                console.print(
                    x=1,
                    y=hp_bar_height + 1 + i,
                    string=item.char,
                    fg=item.color,
                )
        else:
            # Darken the entire screen
            console.rgb["fg"] //= 4
            console.rgb["bg"] //= 4

            # Style 6: small Poison (Exact copy from styles.txt)
            game_over_lines = [
                " @@@@@@@   @@@@@@  @@@@@@@@@@  @@@@@@@@     @@@@@@  @@@  @@@ @@@@@@@@ @@@@@@@     ",
                "!@@       @@!  @@@ @@! @@! @@! @@!         @@!  @@@ @@!  @@@ @@!      @@!  @@@    ",
                "!@! @!@!@ @!@!@!@! @!! !!@ @!@ @!!!:!      @!@  !@! @!@  !@! @!!!:!   @!@!!@!     ",
                ":!!   !!: !!:  !!! !!:     !!: !!:         !!:  !!!  !: .:!  !!:      !!: :!!     ",
                " :: :: :   :   : :  :      :   : :: ::      : :. :     ::    : :: ::   :   : :    ",
            ]
            
            msg_width = max(len(line) for line in game_over_lines)
            msg_height = len(game_over_lines)
            render_x = (console.width - msg_width) // 2
            render_y = (console.height - msg_height) // 2

            # Draw a black box behind the text
            console.draw_rect(
                x=render_x - 1,
                y=render_y - 1,
                width=msg_width + 2,
                height=msg_height + 2,
                ch=ord(" "),
                bg=(0, 0, 0),
            )
            
            # Print the message lines (Character by character for random colors and dots)
            import random
            import time
            random.seed(int(time.time() * 4)) 
            
            for i, line in enumerate(game_over_lines):
                for j, char in enumerate(line):
                    if char == " ":
                        # Fill spaces with dark red dots
                        console.print(
                            x=render_x + j,
                            y=render_y + i,
                            string=".",
                            fg=(64, 0, 0),
                            bg=(0, 0, 0),
                        )
                        continue
                    
                    color = (255, 0, 0) # Red
                    if random.random() < 0.15: # 15% chance to be white
                        color = (255, 255, 255)
                        
                    console.print(
                        x=render_x + j,
                        y=render_y + i,
                        string=char,
                        fg=color,
                        bg=(0, 0, 0),
                    )

            # Center the retry message below the ASCII art
            retry_text = " press spacebar to retry "
            console.print(
                x=(console.width - len(retry_text)) // 2,
                y=render_y + msg_height + 4,
                string=retry_text,
                fg=(255, 255, 255),
                bg=(0, 0, 0),
            )

        context.present(console)
        console.clear()
