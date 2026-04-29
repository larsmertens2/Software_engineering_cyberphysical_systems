"""
HARDWARE ABSTRACTION LAYER - Webots TurtleBot3 Robot

Abstraheert hardware-interacties specifiek voor TurtleBot3 robots.
Bevat motoren, sensoren en communicatie.
"""

from controller import Robot
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.hal_components import Motor, GPSSensor, CompassSensor, LIDARSensor, Receiver, Emitter


class RobotHAL:
    """Hardware Abstraction Layer voor TurtleBot3 robot."""
    
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
        """Initialiseer een motor."""
        motor = Motor(self._robot.getDevice(motor_name))
        motor.set_position_infinite()
        motor.set_velocity(0)
        return motor
    
    def get_name(self):
        """Haal robot-naam op."""
        return self._robot.getName()
    
    def get_Name(self):
        """Haal robot-naam op (camelCase variant)."""
        return self._robot.getName()
    
    def get_time_step(self):
        """Haal timestep op."""
        return self._time_step
    
    def getBasicTimeStep(self):
        """Haal timestep op (Webots API compatible)."""
        return self._time_step
    
    def get_time(self):
        """Haal huidige simulatietijd op."""
        return self._robot.getTime()
    
    def step(self, time_step):
        """Voer een simulatiestap uit."""
        return self._robot.step(time_step)
    
    def getDevice(self, device_name):
        """Haal een device op en wrap het in passende HAL klasse."""
        device = self._robot.getDevice(device_name)
        
        if device_name.lower() in ['receiver']:
            return Receiver(device)
        elif device_name.lower() in ['emitter']:
            return Emitter(device)
        else:
            # Generieke device (ongewrapped)
            return device


def create_robot_hal():
    """Factory-functie om robot HAL te creëren."""
    robot_instance = Robot()
    return RobotHAL(robot_instance)