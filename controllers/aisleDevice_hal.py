"""
HARDWARE ABSTRACTION LAYER - AisleDevice

Abstraheert hardware-interacties specifiek voor AisleDevice.
Bevat enkel communicatie-devices (Emitter, Receiver).
"""

from controller import Robot
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from controllers.hal_components import Receiver, Emitter


class AisleDeviceHAL:
    """Hardware Abstraction Layer voor AisleDevice (communicatie-only)."""
    
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
        """Haal device-naam op."""
        return self._robot.getName()
    
    def get_Name(self):
        """Haal device-naam op (camelCase variant)."""
        return self._robot.getName()
    
    def get_time_step(self):
        """Haal timestep op."""
        return self._time_step
    
    def getBasicTimeStep(self):
        """Haal timestep op (Webots API compatible)."""
        return self._time_step
    
    def step(self, time_step):
        """Voer een simulatiestap uit."""
        return self._robot.step(time_step)


def create_aisle_device_hal():
    """Factory-functie om AisleDevice HAL te creëren."""
    robot_instance = Robot()
    return AisleDeviceHAL(robot_instance)