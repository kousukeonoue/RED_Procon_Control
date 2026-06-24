import pigpio
import Radicon
import FloorLight
import socket
import os
import urllib.request
from datetime import datetime

CAMERA_SNAPSHOT_URL = "http://127.0.0.1:8080/?action=snapshot"
CAPTURE_DIR = "/home/red/captures"

os.makedirs(CAPTURE_DIR, exist_ok=True)

gpio = pigpio.pi()
radicon = Radicon.Radicon(gpio)
light = FloorLight.FloorLight(gpio)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", 5005))

print("UDP server start : port 5005")

while True:
    data, addr = sock.recvfrom(1024)
    cmd = data.decode().strip()

    print("recv:", cmd, "from", addr)

    light.on()

    if cmd == "forward":
        radicon.MoveForward()

    elif cmd == "back":
        radicon.MoveBackward()

    elif cmd == "left":
        radicon.TurnLeft()

    elif cmd == "right":
        radicon.TurnRight()

    elif cmd == "stop":
        radicon.Stop()

    elif cmd == "capture":
        filename = datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg")
        filepath = os.path.join(CAPTURE_DIR, filename)

        print("画像取得中:", filepath)

        try:
            urllib.request.urlretrieve(CAMERA_SNAPSHOT_URL, filepath)
            print("保存完了:", filepath)
        except Exception as e:
            print("画像取得失敗:", e)