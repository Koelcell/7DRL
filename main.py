import colorsys
import time
import tcod

from engine import Engine
from entity import Entity, Actor
from input_handlers import IntroEventHandler, MainGameEventHandler, MouseMovementAction, RetryGame, StartGame
from village import generate_static_map
from procgen import generate_dungeon
from components.fighter import Fighter
from components.inventory import Inventory


def main() -> None:
    screen_width = 80
    screen_height = 50

    map_width = 80
    map_height = 45

    room_max_size = 10
    room_min_size = 6
    max_rooms = 30

    tileset = tcod.tileset.load_tilesheet(
        "artwork/main_tileset/dejavu10x10_gs_tc.png", 32, 8, tcod.tileset.CHARMAP_TCOD
    )

    with tcod.context.new(
        columns=screen_width,
        rows=screen_height,
        tileset=tileset,
        title="7DRL Prototype",
        vsync=True,
        sdl_window_flags=tcod.context.SDL_WINDOW_FULLSCREEN,
    ) as context:
        root_console = tcod.console.Console(screen_width, screen_height, order="F")
        
        # Intro Screen
        try:
            intro_handler = IntroEventHandler()
            with open("artwork/intro_screen/title.txt", "r", encoding="utf-8") as f:
                intro_art = f.read().splitlines()
            
            while True:
                root_console.clear()
                
                # Center ASCII art
                art_width = max(len(line) for line in intro_art)
                art_height = len(intro_art)
                art_x = (screen_width - art_width) // 2
                art_y = (screen_height - art_height) // 2 - 2
                
                for i, line in enumerate(intro_art):
                    root_console.print(x=art_x, y=art_y + i, string=line, fg=(255, 0, 0))
                
                # Dynamic RGB "press space to start"
                t = time.time()
                parts = [
                    (" press ", (255, 255, 255)),
                    ("space", None), # RGB target
                    (" to start ", (255, 255, 255))
                ]
                
                start_x = (screen_width - sum(len(p[0]) for p in parts)) // 2
                start_y = art_y + art_height + 3
                
                current_x = start_x
                for text, color in parts:
                    if color:
                        root_console.print(x=current_x, y=start_y, string=text, fg=color)
                        current_x += len(text)
                    else:
                        # Character-by-character RGB for "space"
                        for i, char in enumerate(text):
                            hue = (t * 0.5 + i * 0.1) % 1.0
                            rgb = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                            root_console.print(
                                x=current_x, 
                                y=start_y, 
                                string=char, 
                                fg=(int(rgb[0] * 255), int(rgb[1] * 255), int(rgb[2] * 255))
                            )
                            current_x += 1
                
                context.present(root_console)
                
                for event in tcod.event.get():
                    context.convert_event(event)
                    intro_handler.dispatch(event)
                
                time.sleep(0.01)
        except StartGame:
            pass  # Proceed to game setup
        except SystemExit:
            return  # Exit the program

        try:
            while True:
                # Setup game state
                event_handler = MainGameEventHandler()
                player = Actor(
                    char="@",
                    color=(255, 255, 255),
                    name="Player",
                    ai_cls=None,
                    fighter=Fighter(hp=16, defense=2, power=5),
                    inventory=Inventory(capacity=3),
                )
                stairs = Entity(char="V", color=(255, 255, 0), name="Stairs", blocks_movement=False)

                game_map = generate_static_map(
                    map_width=map_width,
                    map_height=map_height,
                    player=player,
                    stairs=stairs,
                    map_file="hub.txt",
                )

                entities = {player, stairs}
                engine = Engine(entities=entities, event_handler=event_handler, game_map=game_map, player=player, stairs=stairs)
                
                last_move_time = 0.0
                move_delay = 0.1

                # Inner game loop
                try:
                    while True:
                        engine.render(console=root_console, context=context)

                        # Continuous movement handling
                        if isinstance(engine.event_handler, MainGameEventHandler) and engine.event_handler.mouse_down:
                            current_time = time.time()
                            if current_time - last_move_time >= move_delay:
                                action = MouseMovementAction(*engine.event_handler.last_mouse_tile)
                                engine.handle_events([action], context)
                                last_move_time = current_time

                        for event in tcod.event.get():
                            context.convert_event(event)
                            engine.handle_events([event], context)

                        time.sleep(0.01)
                except RetryGame:
                    continue  # Restart the setup and loop
                except SystemExit:
                    raise  # Exit main()
        except SystemExit:
            pass  # Terminate smoothly


if __name__ == "__main__":
    main()
