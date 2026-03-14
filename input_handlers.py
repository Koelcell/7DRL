from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod.event

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class Action:
    def perform(self, engine: Engine, entity: Entity) -> None:
        """Perform this action with the objects needed to determine its scope.

        `engine` is the scope this action is being performed in.

        `entity` is the object performing the action.
        """
        raise NotImplementedError()


class EscapeAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        raise SystemExit()


class FullscreenAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        pass  # Handled in the main loop or via context.sdl_window.fullscreen


class MovementAction(Action):
    def __init__(self, dx: int, dy: int):
        super().__init__()
        self.dx = dx
        self.dy = dy

    def perform(self, engine: Engine, entity: Entity) -> None:
        dest_x = entity.x + self.dx
        dest_y = entity.y + self.dy

        if not engine.game_map.in_bounds(dest_x, dest_y):
            return  # Destination is out of bounds.
        if not engine.game_map.tiles["walkable"][dest_x, dest_y]:
            return  # Destination is blocked by a tile.

        entity.move(self.dx, self.dy)

        if entity.x == engine.stairs.x and entity.y == engine.stairs.y:
            engine.new_level()


class MouseMovementAction(Action):
    def __init__(self, x: int, y: int):
        self.target_x = x
        self.target_y = y

    def perform(self, engine: Engine, entity: Entity) -> None:
        # This will be handled in the Engine to calculate path and move the player.
        # However, it's better to keep logic in the Action if possible.
        pass


class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self) -> None:
        super().__init__()
        self.mouse_down = False
        self.last_mouse_tile = (0, 0)

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[Action]:
        if event.button == tcod.event.MouseButton.LEFT:
            self.mouse_down = True
            self.last_mouse_tile = event.tile
            return MouseMovementAction(*event.tile)
        return None

    def ev_mousebuttonup(self, event: tcod.event.MouseButtonUp) -> Optional[Action]:
        if event.button == tcod.event.MouseButton.LEFT:
            self.mouse_down = False
        return None

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> Optional[Action]:
        if self.mouse_down:
            self.last_mouse_tile = event.tile
        return None

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        action: Optional[Action] = None

        key = event.sym

        if key == tcod.event.KeySym.UP or key == tcod.event.KeySym.K or key == tcod.event.KeySym.KP_8:
            action = MovementAction(dx=0, dy=-1)
        elif key == tcod.event.KeySym.DOWN or key == tcod.event.KeySym.J or key == tcod.event.KeySym.KP_2:
            action = MovementAction(dx=0, dy=1)
        elif key == tcod.event.KeySym.LEFT or key == tcod.event.KeySym.H or key == tcod.event.KeySym.KP_4:
            action = MovementAction(dx=-1, dy=0)
        elif key == tcod.event.KeySym.RIGHT or key == tcod.event.KeySym.L or key == tcod.event.KeySym.KP_6:
            action = MovementAction(dx=1, dy=0)
        elif key == tcod.event.KeySym.Y or key == tcod.event.KeySym.KP_7:
            action = MovementAction(dx=-1, dy=-1)
        elif key == tcod.event.KeySym.U or key == tcod.event.KeySym.KP_9:
            action = MovementAction(dx=1, dy=-1)
        elif key == tcod.event.KeySym.B or key == tcod.event.KeySym.KP_1:
            action = MovementAction(dx=-1, dy=1)
        elif key == tcod.event.KeySym.N or key == tcod.event.KeySym.KP_3:
            action = MovementAction(dx=1, dy=1)

        elif key == tcod.event.KeySym.RETURN and (event.mod & tcod.event.Modifier.ALT):
            action = FullscreenAction()

        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction()

        return action

