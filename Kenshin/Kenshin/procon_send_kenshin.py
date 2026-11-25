#!/usr/bin/env python3
import socket, time, pygame

RED_IP = "192.168.1.216"  # Change to the RED's current IP.
RED_PORT = 5005
DEADZONE = 0.55
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

def send(cmd):
    sock.sendto(cmd.encode("ascii"), (RED_IP, RED_PORT))

def main():
    pygame.init()
    pygame.joystick.init()
    if not pygame.joystick.get_count():
        raise RuntimeError("Nintendo Switch Pro Controller not found")
    joy = pygame.joystick.Joystick(0)
    joy.init()
    print("Controller:", joy.get_name(), flush=True)
    print("B/A=forward/back, stick=continuous drive, X/Y=stop", flush=True)
    print("D-pad left/right=5deg, L/R=45deg, triggers=90deg", flush=True)
    prev_discrete = set()
    active_discrete = False
    last = None
    try:
        while True:
            pygame.event.pump()
            if not pygame.joystick.get_count():
                break
            lx, ly = joy.get_axis(0), joy.get_axis(1)
            # Right stick is intentionally unused; 50 cm movement was removed.
            hat = joy.get_hat(0) if joy.get_numhats() else (0, 0)
            a, b, x, y = [joy.get_button(i) for i in range(4)]
            l = joy.get_button(4) if joy.get_numbuttons() > 4 else 0
            r = joy.get_button(5) if joy.get_numbuttons() > 5 else 0
            lt = joy.get_axis(4) if joy.get_numaxes() > 4 else -1.0
            rt = joy.get_axis(5) if joy.get_numaxes() > 5 else -1.0
            discrete = set()
            if l: discrete.add("left45")
            if r: discrete.add("right45")
            if lt > 0.5: discrete.add("left90")
            if rt > 0.5: discrete.add("right90")
            if hat[0] < 0: discrete.add("left5")
            elif hat[0] > 0: discrete.add("right5")
            if x or y or len(discrete) > 1:
                cmd, active_discrete = "stop", False
            elif discrete:
                cmd = next(iter(discrete)) if not active_discrete or discrete != prev_discrete else "keepalive"
                active_discrete = True
            elif abs(ly) > DEADZONE:
                cmd, active_discrete = ("forward" if ly < 0 else "back"), False
            elif abs(lx) > DEADZONE:
                cmd, active_discrete = ("left" if lx < 0 else "right"), False
            elif b: cmd, active_discrete = "forward", False
            elif a: cmd, active_discrete = "back", False
            elif hat[1] > 0: cmd, active_discrete = "forward", False
            elif hat[1] < 0: cmd, active_discrete = "back", False
            elif active_discrete: cmd = "keepalive"
            else: cmd, active_discrete = "stop", False
            send(cmd)
            if cmd != last and cmd != "keepalive":
                print("send:", cmd, flush=True)
                last = cmd
            prev_discrete = discrete
            time.sleep(0.05)
    except KeyboardInterrupt:
        pass
    finally:
        for _ in range(5):
            send("stop"); time.sleep(0.02)
        sock.close(); pygame.quit()

if __name__ == "__main__":
    main()
