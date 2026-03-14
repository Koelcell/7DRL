from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from components.base_component import BaseComponent

if TYPE_CHECKING:
    from entity import Actor, Item
    from input_handlers import Action
    from components.inventory import Inventory


class Consumable(BaseComponent):
    parent: Item

    def get_action(self, consumer: Actor) -> Optional[Action]:
        """Try to return the action for this item."""
        return None

    def activate(self, action: Action) -> None:
        """Invoke this items ability.

        `action` is the context for this activation.
        """
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        from components.inventory import Inventory
        entity = self.parent
        inventory = entity.parent
        if isinstance(inventory, Inventory):
            inventory.items.remove(entity)


class HealingConsumable(Consumable):
    def __init__(self, amount: int = 5):
        self.amount = amount

    def activate(self, action: Action) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            self.engine.message_log.add_message(
                f"You consume the {self.parent.name}, and recover {amount_recovered} HP!",
                (0, 255, 0),
            )
            self.consume()
        else:
            self.engine.message_log.add_message("Your health is already full.", (255, 255, 0))
            # We don't consume it if it fails
