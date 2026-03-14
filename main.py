import time
import tcod

from engine import Engine
from entity import Entity
from input_handlers import EventHandler, MouseMovementAction
from procgen import generate_dungeon


def main() -> None:
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    tileset = tcod.tileset.load_tilesheet(
        "dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    event_handler = EventHandler()

    player = Entity(int(screen_width / 2), int(screen_height / 2), "@", (255, 255, 255))
    stairs = Entity(int(screen_width / 2 - 5), int(screen_height / 2), "@", (255, 255, 0))
    entities = {stairs, player}

    game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        player=player,
        stairs=stairs,
    )

    engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player, stairs=stairs)

    last_move_time = 0.0
    move_delay = 0.1  # Seconds between automated mouse moves

    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="7DRL Prototype",
        vsync=True,
        sdl_window_flags=tcod.context.SDL_WINDOW_FULLSCREEN,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order="F")
        while True:
            engine.render(console=root_console, context=context)

            # Continuous movement handling
            if event_handler.mouse_down:
                current_time = time.time()
                if current_time - last_move_time >= move_delay:
                    action = MouseMovementAction(*event_handler.last_mouse_tile)
                    engine.handle_events([action], context)
                    last_move_time = current_time

            for event in tcod.event.get():
                context.convert_event(event)
                engine.handle_events([event], context)

            time.sleep(0.01)


if __name__ == "__main__":
    main()

