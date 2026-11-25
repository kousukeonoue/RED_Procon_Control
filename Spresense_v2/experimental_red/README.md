# Spresense yaw-controlled RED experiment

This is an isolated experimental implementation. Existing `for_pc/` and `for_raspberrypi/` files are preserved unchanged.

## Scope

- RED UDP server: port 5005
- Spresense yaw bridge: TCP 5000 on localhost
- Yaw-hold continuous drive: `forward`, `back`, `left`, `right`
- Discrete turns: `left5`, `right5`, `left45`, `right45`, `left90`, `right90`
- `stop` and `keepalive`

**50 cm position-integrated movement is deliberately removed.** The test stopped at 22.5 cm (27.5 cm short) and reported vertical drift. It is not a validated feature.

## Files

- `radicon_udp_server.py`: RED-side yaw controller derived from today's test version, with all 50 cm / XY-position movement code removed
- `procon_send_kenshin.py`: Nintendo Switch Pro Controller sender
- `xbox_send_kenshin.py`: Xbox 360 Controller sender

## Start

On RED, ensure pigpio and the Spresense bridge (TCP 5000) are running, then:

```bash
cd ~/Red2.0-Control-Software/explore_algorithm
python3 -B radicon_udp_server.py
```

Expected: `UDP server ready: 5005`

On Windows:

```powershell
python -m pip install pygame
```

Change `RED_IP` in the sender, then run only one controller sender at a time:

```powershell
python .\procon_send_kenshin.py
# or
python .\xbox_send_kenshin.py
```

The sender sends keepalive packets while a discrete turn is active. On Ctrl+C or controller disconnect, it sends repeated stop packets. The RED server stops the motors if UDP packets stop for 0.4 seconds.

## Controller mapping

### Pro Controller
- B/A: forward/back
- Left stick: continuous forward/back/left/right
- X/Y: stop
- D-pad: up/down forward/back; left/right 5 degree turns
- L/R: 45 degree turns
- Trigger axes: 90 degree turns

### Xbox 360 Controller
Based on the pygame mapping observed in today's controller test:
- Y/A: forward/back
- Left stick: continuous drive
- Back: stop
- X/B: 5 degree turns
- LB/RB: 45 degree turns
- LT/RT: 90 degree turns
- D-pad: forward/back or 5 degree turns

## Safety checks

1. First test with wheels lifted.
2. Confirm the displayed controller name and button mapping.
3. Confirm stop by button, Ctrl+C, disconnect, and UDP timeout.
4. Verify turn direction and angle on the actual rover before floor testing.

The GitHub upload itself has not been physically tested. Treat observed logs as experiment results, not guaranteed performance.
