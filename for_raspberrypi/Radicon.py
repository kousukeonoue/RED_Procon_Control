import MotorControl
import pigpio

class Radicon:
    def __init__(self, gpio:pigpio.pi) :
        self.__gpio = gpio
        self.__left_motor = MotorControl.BD6231(self.__gpio, 27, 22)
        self.__right_motor = MotorControl.BD6231(self.__gpio, 19, 26)

    def TurnLeft(self):
        self.__right_motor.forward_rotation()
        self.__left_motor.forward_rotation()

    def TurnRight(self):
        self.__right_motor.backward_rotation()
        self.__left_motor.backward_rotation()

    def MoveForward(self):
        self.__left_motor.backward_rotation()
        self.__right_motor.forward_rotation()

    def MoveBackward(self):
        self.__left_motor.forward_rotation()
        self.__right_motor.backward_rotation()

    def Stop(self):
        self.__left_motor.break_rotation()
        self.__right_motor.break_rotation()
        self.__left_motor.stop_rotation()
        self.__right_motor.stop_rotation()

if __name__ == '__main__':
    gpio = pigpio.pi()
    radicon = Radicon(gpio)
    while True:
         key = input("Please input key.\nw : Move forward.\na : Turn left.\nd : Turn right.\ns : Move backward.\nx : Stop.\n")

         if key == "w":
            radicon.MoveForward()
         if key == "a":
            radicon.TurnLeft()
         if key == "d":
            radicon.TurnRight()
         if key == "s":
            radicon.MoveBackward()
         if key == "x":
            radicon.Stop()