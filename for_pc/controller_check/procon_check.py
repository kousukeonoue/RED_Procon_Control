import pygame
import time

pygame.init()
pygame.joystick.init()

joy = pygame.joystick.Joystick(0)
joy.init()

print("=================================")
print("接続:", joy.get_name())
print("ボタン数:", joy.get_numbuttons())
print("軸数:", joy.get_numaxes())
print("=================================")

while True:

    pygame.event.pump()

    print("\n----------------------------")

    print("左スティック左右  axis0 =", round(joy.get_axis(0), 2))
    print("左スティック上下  axis1 =", round(joy.get_axis(1), 2))

    print("右スティック左右  axis2 =", round(joy.get_axis(2), 2))
    print("右スティック上下  axis3 =", round(joy.get_axis(3), 2))

    print("axis4 =", round(joy.get_axis(4), 2))
    print("axis5 =", round(joy.get_axis(5), 2))

    print("")

    for i in range(joy.get_numbuttons()):
        if joy.get_button(i):
            print("押されているボタン:", i)

    time.sleep(1)