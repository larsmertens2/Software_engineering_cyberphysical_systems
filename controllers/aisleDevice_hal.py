"""
HARDWARE ABSTRACTION LAYER - AisleDevice

abstracts hardware layer specifically for  AisleDevice.
contains only communication devices (Emitter, Receiver).
"""

from controller import Robot
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.hal_components import Receiver, Emitter


class AisleDeviceHAL:
    """Hardware Abstraction Layer for AisleDevice (communicatie-only)."""
    
    def __init__(self, robot_instance):
        """
        Args:
            robot_instance: Webots Robot object
        """
        self._robot = robot_instance
        self._time_step = int(self._robot.getBasicTimeStep())
        
        # Communicatie-devices
        self.receiver = Receiver(self._robot.getDevice('receiver'))
        self.emitter = Emitter(self._robot.getDevice('emitter'))
    
    def get_name(self):
        """get device name."""
        return self._robot.getName()
    
    def get_Name(self):
        """get device name in camelCase"""
        return self._robot.getName()
    
    def get_time_step(self):
        """get timestep"""
        return self._time_step
    
    def getBasicTimeStep(self):
        """get timestep (webots API compatible)"""
        return self._time_step
    
    def step(self, time_step):
        """do a simulation step"""
        return self._robot.step(time_step)


def create_aisle_device_hal():
    """Factory-function to create AisleDevice HAL"""
    robot_instance = Robot()
    return AisleDeviceHAL(robot_instance)