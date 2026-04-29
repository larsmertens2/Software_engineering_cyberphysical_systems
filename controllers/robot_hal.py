"""
HARDWARE ABSTRACTION LAYER - Webots TurtleBot3 Robot

Abstracts hardware interactions specific to TurtleBot3 robots.

Includes motors, sensors, and communication.
"""

from controller import Robot
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.hal_components import Motor, GPSSensor, CompassSensor, LIDARSensor, Receiver, Emitter


class RobotHAL:
    """Hardware Abstraction Layer for TurtleBot3 robot."""
    
    def __init__(self, robot_instance):
        """
        Args:
            robot_instance: Webots Robot object
        """
        self._robot = robot_instance
        self._time_step = int(self._robot.getBasicTimeStep())
        
        # Motor-initialisatie
        self.left_motor = self._init_motor("left wheel motor")
        self.right_motor = self._init_motor("right wheel motor")
        
        # Sensor-initialisatie
        self.gps = GPSSensor(
            self._robot.getDevice("GPS"),
            self._time_step
        )
        self.compass = CompassSensor(
            self._robot.getDevice("compass"),
            self._time_step
        )
        self.lidar = LIDARSensor(
            self._robot.getDevice("LDS-01"),
            self._time_step
        )
        
    def _init_motor(self, motor_name):
        """initialise a motor."""
        motor = Motor(self._robot.getDevice(motor_name))
        motor.set_position_infinite()
        motor.set_velocity(0)
        return motor
    
    def get_name(self):
        """get robot name op."""
        return self._robot.getName()
    
    def get_Name(self):
        """get robot name op (camelCase variant)."""
        return self._robot.getName()
    
    def get_time_step(self):
        """get timestep"""
        return self._time_step
    
    def getBasicTimeStep(self):
        """get timestep (Webots API compatible)."""
        return self._time_step
    
    def get_time(self):
        """get the current simulation time"""
        return self._robot.getTime()
    
    def step(self, time_step):
        """does a simulation step"""
        return self._robot.step(time_step)
    
    def getDevice(self, device_name):
        """get a device and wrap it in HAL class"""
        device = self._robot.getDevice(device_name)
        
        if device_name.lower() in ['receiver']:
            return Receiver(device)
        elif device_name.lower() in ['emitter']:
            return Emitter(device)
        else:
            return device


def create_robot_hal():
    """Factory-functie to create robot HAL"""
    robot_instance = Robot()
    return RobotHAL(robot_instance)