import pygame
import socket
import time

# =====================================
# RED側のIPアドレス
# =====================================
RED_IP = "192.168.1.171"

# RED側で待ち受けしているポート
RED_PORT = 5005

# スティックの遊び
# 少しズレても反応しないようにする
DEADZONE = 0.55

# =====================================
# UDP通信の準備
# =====================================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# =====================================
# pygame初期化
# =====================================
pygame.init()
pygame.joystick.init()

# コントローラー確認
if pygame.joystick.get_count() == 0:
    print("コントローラーが見つかりません")
    exit()

# 1台目のコントローラーを取得
joy = pygame.joystick.Joystick(0)
joy.init()

print("接続:", joy.get_name())

# =====================================
# 状態管理
# =====================================

# 最後に送信したコマンド
last_cmd = ""

# AやBで設定される移動モード
# stop
# forward
# back
mode = "stop"

# L+Rキャプチャ用
last_capture = False

# =====================================
# REDへコマンド送信
# =====================================
def send(cmd, force=False):

    global last_cmd

    # 同じコマンドを連打しない
    if force or cmd != last_cmd:

        sock.sendto(
            cmd.encode(),
            (RED_IP, RED_PORT)
        )

        print("send:", cmd)

        last_cmd = cmd


# =====================================
# メインループ
# =====================================
while True:

    pygame.event.pump()

    # ---------------------------------
    # 左スティック
    # ---------------------------------
    lx = joy.get_axis(0)
    ly = joy.get_axis(1)

    # ---------------------------------
    # 右スティック
    # ---------------------------------
    rx = joy.get_axis(2)
    ry = joy.get_axis(3)

    # ---------------------------------
    # ボタン取得
    # ---------------------------------

    # A
    a = joy.get_button(0)

    # B
    b = joy.get_button(1)

    # X
    x = joy.get_button(2)

    # Y
    y = joy.get_button(3)

    # L
    l = joy.get_button(9)

    # R
    r = joy.get_button(10)

    # =================================
    # L + R 同時押し
    # 写真撮影
    # =================================
    capture_now = l and r

    if capture_now and not last_capture:

        send("capture", force=True)

    last_capture = capture_now

    # =================================
    # ボタンでモード切替
    # =================================

    # A押したら前進モード
    if a:
        mode = "forward"

    # B押したら後退モード
    elif b:
        mode = "back"

    # XかY押したら停止モード
    elif x or y:
        mode = "stop"

    # =================================
    # スティック優先操作
    # =================================

    # 前進
    if ly < -DEADZONE or ry < -DEADZONE:

        send("forward")

    # 後退
    elif ly > DEADZONE or ry > DEADZONE:

        send("back")

    # 左旋回
    elif lx < -DEADZONE or rx < -DEADZONE:

        send("left")

    # 右旋回
    elif lx > DEADZONE or rx > DEADZONE:

        send("right")

    # スティックを離したら
    # ボタンで設定されたモードに戻る
    else:

        send(mode)

    time.sleep(0.08)