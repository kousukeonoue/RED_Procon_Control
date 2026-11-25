# Kenshin RED — experimental controller package

This folder keeps today's RED control experiment separate from the legacy root folders `for_pc/` and `for_raspberrypi/`.

## Folder structure

```text
Spresense_v2/Kenshin/
├── CBox/                         # Windows controller-PC programs
│   ├── procon_send_kenshin.py    # Nintendo Switch Pro Controller
│   ├── xbox_send_kenshin.py      # Xbox 360 Controller
│   ├── controller_check.py       # Read-only button/axis check
│   └── requirements.txt          # pygame
└── Kenshin/                      # Raspberry Pi side on RED
    ├── radicon_udp_server.py     # Spresense P-angle hold + turns
    └── MotorControl.py           # BD6231 motor driver dependency
```

## What this version contains

- UDP control server on port **5005**
- Reads the Spresense bridge's `P:` angle from TCP **127.0.0.1:5000**
- Straight/reverse heading hold using the tested PID settings in today's source
- Manual left/right drive
- 5°, 45°, and 90° turn commands
- Stops on missing IMU data or UDP timeout (**0.4 s**)
- `stop` and `keepalive` commands

**The 50 cm / XY-position movement code has been removed.** The failed 50 cm trial is not included as an available feature.

## Important version boundary

`radicon_udp_server.py` is based on the supplied `radicon_udp_server_50cm.py` source, with the position-based 50 cm mode and its XY-pose logic removed. It has **not** been confirmed byte-for-byte against the file currently running on the physical RED. Do not overwrite the live Pi program until the two files and their dependencies have been compared.

The server imports `MotorControl.py` from this same folder. It does not import the old `Radicon.py` or `FloorLight.py`.

The Spresense bridge `pospredict_bridge.py` is research-lab software and is not copied here. It must already be running and providing the `P:` field on TCP 5000. Do not start a second bridge if one is already active.

## Windows setup

In PowerShell, from this `CBox` folder:

```powershell
python -m pip install -r requirements.txt
python .\controller_check.py
```

Run `controller_check.py` first. It is read-only and sends no commands. Confirm the actual button/axis indices before using either sender; SDL mappings can differ by controller and operating system.

Set the RED IP for this PowerShell session. `192.168.1.247` is only the last IP recorded in the experiment notes; verify the current value on RED with `hostname -I`:

```powershell
$env:RED_IP = "192.168.1.247"
```

Then run only one sender:

```powershell
python .\procon_send_kenshin.py
# or
python .\xbox_send_kenshin.py
```

The sender sends repeated `stop` packets when Ctrl+C is pressed or the controller disconnects.

### Pro Controller mapping (provisional until checked)

- B/A: forward/back
- Left stick: forward/back/left/right
- X/Y: stop
- D-pad left/right: 5° turns; up/down: forward/back
- L/R: 45° turns
- Trigger axes 4/5: 90° turns

### Xbox 360 mapping (provisional until checked)

- Y/A: forward/back
- Left stick: forward/back/left/right
- Back: stop
- X/B: 5° turns
- LB/RB: 45° turns
- LT/RT axes 4/5: 90° turns
- D-pad left/right: 5° turns; up/down: forward/back

If the diagnostic output differs, change the button/axis constants in the sender before driving.

## Raspberry Pi setup

Prerequisites:
- pigpio Python module and running `pigpiod`
- Spresense physically connected and the existing lab `pospredict_bridge.py` serving TCP 5000
- Correct motor wiring and GPIO pins matching `MotorControl.py`

Before starting, check whether UDP 5005 is already occupied. Do not run this server beside the existing RED server on the same port.

```bash
pgrep -af 'radicon_udp_server|pospredict_bridge'
ss -lunp | grep ':5005'
ss -ltnp | grep ':5000'
```

After intentionally stopping the previous UDP 5005 server, run this experimental copy:

```bash
cd ~/Red2.0-Control-Software/Spresense_v2/Kenshin/Kenshin
python3 -B radicon_udp_server.py
```

Expected startup message: `UDP server ready: 5005`.

Test with the wheels lifted first. Verify forward/reverse, left/right, each turn direction, stop, Ctrl+C, controller disconnect, and UDP timeout before putting the rover on the floor.

## UWB status

UWB is **not integrated into this control package**. The UWB software is maintained in the separate lab repository `chuo-univ-klab-hub/RED_UWB_control-software`. The repository listing supplied in this conversation shows the Murata Type 2BP / SR150 multi-session code under `MURATA_Type_2BP/Raspberrypi_Multisession/version04.06.00/`, but the private repository could not be opened through the current GitHub connection, so its current serial settings, anchor startup commands, IDs, and network configuration have not been verified here.

The experiment notes last identified FTDI FT230X as the UWB USB interface and CP2102N as the Spresense interface. Re-check `/dev/serial/by-id/` on the actual RED; do not assume ttyUSB numbers are fixed. UWB and Spresense use separate adapters in the recorded setup, but simultaneous operation still needs an on-device test.

## Safety and validation status

- 50 cm mode: removed
- Existing root `for_pc/` and `for_raspberrypi/`: unchanged
- GitHub source files: organized here
- Controller button mappings: provisional; run the diagnostic
- Physical RED test of this packaged copy: not yet performed
- UWB multi-anchor startup and simultaneous operation: not yet verified
