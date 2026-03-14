from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import tcod.event

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class StartGame(Exception):
    """Exception raised when the player wants to start the game from the intro screen."""
    pass


class RetryGame(Exception):
    """Exception raised when the player wants to restart the game."""
    pass


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


class RetryAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        raise RetryGame()


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
        
        target_entity = engine.get_blocking_entity_at_location(dest_x, dest_y)
        from entity import Actor
        if target_entity and isinstance(target_entity, Actor) and target_entity.fighter:
            # Only attack if the target is of a different 'faction'
            # Simple rule: Player attacks anything, monsters only attack player
            if entity is engine.player or target_entity is engine.player:
                damage = entity.fighter.power - target_entity.fighter.defense
                
                attack_desc = f"{entity.name.capitalize()} attacks {target_entity.name}"
                
                # Red for player taking damage, Green for monsters
                if target_entity is engine.player:
                    color = (255, 0, 0)
                else:
                    color = (0, 255, 0)

                if damage > 0:
                    engine.message_log.add_message(f"{attack_desc} for {damage} hit points.", color)
                    target_entity.fighter.hp -= damage
                else:
                    engine.message_log.add_message(f"{attack_desc} but does no damage.", color)
            return
        elif target_entity:
            # If there's a blocking entity but it's not a fighter (like a door or something later)
            return

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


class AutoExploreAction(Action):
    def perform(self, engine: Engine, entity: Entity) -> None:
        """This will be handled in the Engine to find the nearest unexplored tile."""
        pass


class BaseEventHandler(tcod.event.EventDispatch[Action]):
    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class IntroEventHandler(BaseEventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.KeySym.SPACE:
            raise StartGame()
        elif event.sym == tcod.event.KeySym.ESCAPE:
            raise SystemExit()
        return None


class GameOverEventHandler(BaseEventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.KeySym.ESCAPE:
            return EscapeAction()
        elif event.sym == tcod.event.KeySym.SPACE:
            return RetryAction()
        return None


class PickupAction(Action):
    def perform(self, engine: Engine, entity: Actor) -> None:
        from entity import Item
        inventory = entity.inventory
        for item in engine.game_map.entities:
            if item.x == entity.x and item.y == entity.y and isinstance(item, Item):
                if len(inventory.items) >= inventory.capacity:
                    engine.message_log.add_message("Your inventory is full.", (255, 0, 0))
                    return

                engine.game_map.entities.remove(item)
                item.parent = inventory
                inventory.items.append(item)

                engine.message_log.add_message(f"You picked up the {item.name}!", item.color)
                return

        engine.message_log.add_message("There is nothing here to pick up.")


class QuickUseAction(Action):
    def perform(self, engine: Engine, entity: Actor) -> None:
        from entity import Actor
        self.entity = entity
        inventory = entity.inventory
        if not inventory.items:
            engine.message_log.add_message("You have no items in your inventory.", (255, 255, 0))
            return

        # Use the last health potion available (lowest on HUD)
        item = inventory.items[-1]
        item.consumable.activate(self)


class TakeStairsAction(Action):
    def perform(self, engine: Engine, entity: Actor) -> None:
        """
        Take the stairs, if any are under the player's feet.
        """
        if (entity.x, entity.y) == (engine.stairs.x, engine.stairs.y):
            if engine.stairs.char == "V":
                # Currently in HUB, going to Cellar
                engine.load_static_map("inn_cellar.txt")
                engine.message_log.add_message("You descend into the cellar.", (255, 255, 255))
            elif engine.stairs.char == "U":
                # Currently in cellar, returning to Hub
                engine.load_static_map("hub.txt")
                engine.message_log.add_message("You ascend back to the Inn.", (255, 255, 255))
            else:
                engine.new_level()
                engine.message_log.add_message("You descend the staircase.", (255, 255, 255))
        else:
            engine.message_log.add_message("There are no stairs here.", (255, 255, 0))


class ItemAction(Action):
    def __init__(self, item: Item):
        super().__init__()
        self.item = item

    def perform(self, engine: Engine, entity: Actor) -> None:
        """Invoke the item's ability, this action handles the context of use."""
        from entity import Actor
        self.entity = entity
        self.item.consumable.activate(self)


class MainGameEventHandler(BaseEventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.mouse_down = False
        self.last_mouse_tile = (0, 0)

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
        elif key == tcod.event.KeySym.LEFT or key == tcod.event.KeySym.KP_4:
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

        elif key == tcod.event.KeySym.G:
            action = PickupAction()

        elif key == tcod.event.KeySym.V:
            action = TakeStairsAction()

        elif key == tcod.event.KeySym.H:
            action = QuickUseAction()

        elif key == tcod.event.KeySym.KP_5 or key == tcod.event.KeySym.PERIOD:
            action = AutoExploreAction()

        elif key == tcod.event.KeySym.RETURN and (event.mod & tcod.event.Modifier.ALT):
            action = FullscreenAction()

        elif key == tcod.event.KeySym.ESCAPE:
            action = EscapeAction()

        return action

