#!/usr/bin/env python3
"""Read-only pygame controller diagnostic. It sends no UDP commands."""
import time
import pygame

def main():
    pygame.init()
    pygame.joystick.init()
    if pygame.joystick.get_count() == 0:
        raise RuntimeError("No controller detected")
    joy = pygame.joystick.Joystick(0)
    joy.init()
    print("Controller:", joy.get_name())
    print("Axes:", joy.get_numaxes(), "Buttons:", joy.get_numbuttons(),
          "Hats:", joy.get_numhats())
    print("Press each button/trigger and move each stick/D-pad.")
    print("This tool only displays inputs; it does not control the RED.")
    print("Ctrl+C to exit.")
    try:
        while True:
            pygame.event.pump()
            axes = [round(joy.get_axis(i), 2) for i in range(joy.get_numaxes())]
            buttons = [i for i in range(joy.get_numbuttons()) if joy.get_button(i)]
            hats = [joy.get_hat(i) for i in range(joy.get_numhats())]
            print(f"axes={axes} buttons={buttons} hats={hats}", flush=True)
            time.sleep(0.2)
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()

if __name__ == "__main__":
    main()
