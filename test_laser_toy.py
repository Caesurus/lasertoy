#!/usr/bin/env python3
import sys
import time
import unittest
from turtle import Turtle
from unittest.mock import Mock, patch

sys.modules['RPi'] = Mock()
sys.modules['RPi.GPIO'] = Mock()

import laser_toy
from laser_toy import Laser


class Servo:
    def __init__(self, number, turtle_instance):
        self.turtle = turtle_instance
        self.number = number
        self.position = None

    def start(self, *args, **kwargs):
        self.position = args[0]
        self.update_location()

    def stop(self, *args, **kwargs):
        pass

    def update_location(self):
        MULTIPLICATION_FACTOR = 50
        if laser_toy.GPIO_X_SERVO == self.number:
            x_loc = self.position  # - laser_toy.DEFAULT_X_MIN_POSITION
            self.turtle.setx(x_loc * MULTIPLICATION_FACTOR)
        elif laser_toy.GPIO_Y_SERVO == self.number:
            y_loc = self.position  # - laser_toy.DEFAULT_Y_MIN_POSITION
            self.turtle.sety(y_loc * MULTIPLICATION_FACTOR)
            self.turtle.dot(5)

    def ChangeDutyCycle(self, *args, **kwargs):
        self.position = args[0]
        self.update_location()


class GPIOTestMock:
    BCM = None
    OUT = True

    def __init__(self):
        self.servos = {}
        self.turtle = Turtle()
        self.turtle.hideturtle()
        self.turtle.up()
        # self.turtle.down()
        pass

    def setmode(self, *args, **kwargs):
        pass

    def setup(self, *args, **kwargs):
        pass

    def PWM(self, *args, **kwargs):
        """returns servo instance"""
        print('PWM called')
        servo_num = args[0]
        if servo_num not in self.servos:
            self.servos[servo_num] = Servo(servo_num, self.turtle)
        return self.servos[servo_num]

    def output(self, *args, **kwargs):
        if laser_toy.GPIO_LASER == args[0]:
            if args[1]:
                self.turtle.down()
            else:
                self.turtle.up()


laser_toy.GPIO = GPIOTestMock()


class LaserTestCase(unittest.TestCase):

    def test_instance(self):
        # screen.setup(width=1024, height=1024)
        laser = Laser(rapid_movement=False, min_movement=20)
        laser.calibrate_laser()
        with patch('time.sleep') as mock_sleep:
            for i in range(0, 200):
                laser.fire()
        time.sleep(10)
        self.assertEqual(True, isinstance(laser, Laser))


if __name__ == '__main__':
    unittest.main()
