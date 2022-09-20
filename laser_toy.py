#!/usr/bin/env python
import argparse
import random
import time

import RPi.GPIO as GPIO

DEFAULT_RUN_TIME = 90
DEFAULT_MIN_MOVEMENT = 10
DEFAULT_X_MIN_POSITION = 20
DEFAULT_X_MAX_POSITION = 100
DEFAULT_Y_MIN_POSITION = 55
DEFAULT_Y_MAX_POSITION = 130

# define which GPIO pins to use for the servos and laser
GPIO_X_SERVO = 4
GPIO_Y_SERVO = 17
GPIO_LASER = 27


class Laser:
    def __init__(self, min_movement: int = DEFAULT_MIN_MOVEMENT,
                 x_min: int = DEFAULT_X_MIN_POSITION,
                 x_max: int = DEFAULT_X_MAX_POSITION,
                 y_min: int = DEFAULT_Y_MIN_POSITION,
                 y_max: int = DEFAULT_Y_MAX_POSITION,
                 rapid_movement: bool = False):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(GPIO_X_SERVO, GPIO.OUT)
        GPIO.setup(GPIO_Y_SERVO, GPIO.OUT)
        GPIO.setup(GPIO_LASER, GPIO.OUT)

        self.x_servo = GPIO.PWM(GPIO_X_SERVO, 50)
        self.y_servo = GPIO.PWM(GPIO_Y_SERVO, 50)

        # set config variables, using the defaults if one wasn't provided
        self.min_movement = DEFAULT_MIN_MOVEMENT if min_movement is None else min_movement
        self.x_min = DEFAULT_X_MIN_POSITION if x_min is None else x_min
        self.x_max = DEFAULT_X_MAX_POSITION if x_max is None else x_max
        self.y_min = DEFAULT_Y_MIN_POSITION if y_min is None else y_min
        self.y_max = DEFAULT_Y_MAX_POSITION if y_max is None else y_max

        self.x_position = self.x_min + (self.x_max - self.x_min) / 2
        self.y_position = self.y_min + (self.y_max - self.y_min) / 2
        self.last_y = self.y_min

        self.movement_time = self.__get_movement_time()
        self.rapid_movement = rapid_movement

    @staticmethod
    def laser_on():
        # turn on the laser and configure the servos
        GPIO.output(GPIO_LASER, 1)

    @staticmethod
    def laser_off():
        # turn on the laser and configure the servos
        GPIO.output(GPIO_LASER, 0)

    def calibrate_laser(self):
        # start at the center of our square/ rectangle.
        self.x_position = self.x_min + (self.x_max - self.x_min) / 2
        self.y_position = self.y_min + (self.y_max - self.y_min) / 2

        # turn on the laser and configure the servos
        self.laser_on()

        # start the servo which initializes it, and positions them center on the cartesian plane
        self.x_servo.start(self.__get_position(self.x_position))
        self.y_servo.start(self.__get_position(self.y_position))

        # give the servo a chance to position itself
        time.sleep(1)

    def fire(self):
        self.movement_time = self.__get_movement_time()
        print("Movement time: {0}".format(self.movement_time))
        print("Current position: X: {0}, Y: {1}".format(self.x_position, self.y_position))
        if self.rapid_movement:
            self.x_position = self.generate_new_x()
            self.y_position = self.generate_new_y()
            self.__set_servo_position(self.x_servo, self.x_position)
            self.__set_servo_position(self.y_servo, self.y_position)
        else:
            # how many steps (how long) should we take to get from old to new position
            x_incrementer = self.__get_position_incrementer(self.x_position, self.generate_new_x())
            y_incrementer = self.__get_position_incrementer(self.y_position, self.generate_new_y())
            print('Tokyo Drift engaged...')
            for index in range(self.movement_time + 1):
                print("For, X Position: {0}, Y Position: {1}".format(self.x_position, self.y_position))
                self.x_position += x_incrementer
                self.y_position += y_incrementer

                self.__set_servo_position(self.x_servo, self.x_position)
                self.__set_servo_position(self.y_servo, self.y_position)

                time.sleep(0.1)

        # leave the laser still so the cat has a chance to catch up
        time.sleep(self.__get_movement_delay())

    def stop(self):
        # always cleanup after ourselves
        print("\nTidying up")
        if self.x_servo is not None:
            self.x_servo.stop()

        if self.y_servo is not None:
            self.y_servo.stop()

        self.laser_off()

    def __set_servo_position(self, servo, position):
        servo.ChangeDutyCycle(self.__get_position(position))

    @staticmethod
    def __get_position(angle):
        return (angle / 18.0) + 2.5

    def generate_new_x(self):
        return self.__generate_new_coordinate(self.x_position, self.x_min, self.x_max)

    def generate_new_y(self):
        if self.last_y:
            self.last_y = False
            ret = self.y_max  # random.randint(int(self.y_max/2), int(self.y_max))
        else:
            self.last_y = True
            ret = self.y_min  # +(self.y_max/10)#random.randint(int(self.y_min), )
        return ret

    def __generate_new_coordinate(self, old_position, min_val, max_val):
        # randomly pick new position, leaving a buffer +- the min values for adjustment later
        while True:
            new_position = random.randint(min_val, max_val)
            if abs(new_position - old_position) > self.min_movement:
                break
        return new_position

    def __get_position_incrementer(self, position, desired_position):
        # bump up the new position if we didn't move more than our minimum requirement
        if (desired_position > position) and (abs(desired_position - position) < self.min_movement):
            desired_position += self.min_movement
        elif (desired_position < position) and (abs(desired_position - position) < self.min_movement):
            desired_position -= self.min_movement

        # return the number of steps, or incrementer, we should take to get to the new position
        # this is a convenient way to slow the movement down, rather than seeing very rapid movements
        # from point A to point B
        return float((desired_position - position) / self.movement_time)

    @staticmethod
    def __get_movement_delay():
        return random.uniform(2, 5)

    @staticmethod
    def __get_movement_time():
        return random.randint(10, 14)

    def _test_range(self):
        print(self.x_min, self.y_min)
        self.__set_servo_position(self.x_servo, self.x_min)
        self.__set_servo_position(self.y_servo, self.y_min)
        time.sleep(10)
        print(self.x_min, self.y_max)
        self.__set_servo_position(self.x_servo, self.x_min)
        self.__set_servo_position(self.y_servo, self.y_max)
        time.sleep(10)
        print(self.x_max, self.y_max)
        self.__set_servo_position(self.x_servo, self.x_max)
        self.__set_servo_position(self.y_servo, self.y_max)
        time.sleep(10)
        print(self.x_max, self.y_min)
        self.__set_servo_position(self.x_servo, self.x_max)
        self.__set_servo_position(self.y_servo, self.y_min)
        time.sleep(10)

    def set_position(self, x, y):
        print(x, y)
        self.x_servo.start(self.__get_position(x))
        self.y_servo.start(self.__get_position(y))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-x', '--xaxis')
    parser.add_argument('-y', '--yaxis')
    args = parser.parse_args()
    laser = Laser(min_movement=10, rapid_movement=True)

    laser.calibrate_laser()
    try:

        if args.xaxis and args.yaxis:
            laser.set_position(int(args.xaxis), int(args.yaxis))
            time.sleep(20)
        else:
            for i in range(1, 500):
                laser.fire()

    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(e)
    laser.stop()
