import tcod
import numpy as np
from typing import Iterable, Any

from tcod.context import Context
from tcod.console import Console

from entity import Entity
from game_map import GameMap
from input_handlers import EventHandler


class Engine:
    def __init__(self, entities: Iterable[Entity], event_handler: EventHandler, game_map: GameMap, player: Entity, stairs: Entity):
        self.entities = set(entities)
        self.event_handler = event_handler
        self.game_map = game_map
        self.player = player
        self.stairs = stairs

    def handle_events(self, events: Iterable[Any], context: Context) -> None:
        from input_handlers import Action, MovementAction, FullscreenAction, EscapeAction, MouseMovementAction

        for event in events:
            if isinstance(event, Action):
                action = event
            else:
                action = self.event_handler.dispatch(event)

            if action is None:
                continue

            if isinstance(action, MovementAction):
                action.perform(self, self.player)

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

            elif isinstance(action, FullscreenAction):
                context.sdl_window.fullscreen = not context.sdl_window.fullscreen

            elif isinstance(action, EscapeAction):
                action.perform(self, self.player)

    def new_level(self) -> None:
        from procgen import generate_dungeon

        self.game_map = generate_dungeon(
            max_rooms=30,
            room_min_size=6,
            room_max_size=10,
            map_width=self.game_map.width,
            map_height=self.game_map.height,
            player=self.player,
            stairs=self.stairs,
        )

    def render(self, console: Console, context: Context) -> None:
        self.game_map.visible[:] = tcod.map.compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

        self.game_map.render(console)

        for entity in self.entities:
             # Only print entities that are in the FOV
             if self.game_map.visible[entity.x, entity.y]:
                 console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)

        context.present(console)
        console.clear()
