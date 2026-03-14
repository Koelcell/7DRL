from __future__ import annotations

from typing import List, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(BaseComponent):
    parent: Actor

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """Compute and return a path to the target position.

        If there is no valid path then returns an empty list.
        """
        cost = np.array(self.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.gamemap.entities:
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more frequent wall-bumping, which is better
                # than walking into walls every time.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.parent.x, self.parent.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]

class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__()
        self.parent = entity
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        from input_handlers import MovementAction
        
        target = self.engine.player
        dx = target.x - self.parent.x
        dy = target.y - self.parent.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if self.gamemap.visible[self.parent.x, self.parent.y]:
            if distance <= 1:
                return MovementAction(dx, dy).perform(self.engine, self.parent)

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            dest_x, dest_y = self.path.pop(0)
            return MovementAction(
                dest_x - self.parent.x, dest_y - self.parent.y,
            ).perform(self.engine, self.parent)

        return MovementAction(0, 0).perform(self.engine, self.parent)
