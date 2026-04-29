"""
HARDWARE ABSTRACTION LAYER (HAL) - Webots TurtleBot3

Abstraheert alle directe Webots hardware-interacties.
Dit maakt de code onafhankelijk van het specifieke robotplatform.

Interface:
- RobotHAL: Centrale HAL-klasse
- Motor: Motoraansturing
- Sensor classes: GPS, Compass, LIDAR
"""

from controller import Robot

class Motor:
    """Abstractie voor een motor."""
    
    def __init__(self, motor_device):
        """
        Args:
            motor_device: Webots motor object
        """
        self._device = motor_device
        
    def set_position_infinite(self):
        """Zet motor in velocity-modus (oneindige positie)."""
        self._device.setPosition(float('inf'))
    
    def setPosition(self, position):
        """Stel motorpositie in (Webots API compatible)."""
        self._device.setPosition(position)
        
    def set_velocity(self, velocity):
        """Stel motorsnelheid in."""
        self._device.setVelocity(velocity)
    
    def setVelocity(self, velocity):
        """Stel motorsnelheid in (Webots API compatible)."""
        self._device.setVelocity(velocity)
        
    def get_velocity(self):
        """Haal huidige snelheid op."""
        return self._device.getVelocity()


class GPSSensor:
    """Abstractie voor GPS-sensor."""
    
    def __init__(self, gps_device, time_step):
        """
        Args:
            gps_device: Webots GPS object
            time_step: Robot timestep in ms
        """
        self._device = gps_device
        self._time_step = time_step
        self._device.enable(time_step)
    
    def enable(self, time_step):
        """Enable sensor (no-op als al enabled)."""
        self._device.enable(time_step)
        
    def get_position(self):
        """Haal huidige positie op."""
        return self._device.getValues()
    
    def getValues(self):
        """Haal sensorwaarden op (Webots API compatible)."""
        return self._device.getValues()


class CompassSensor:
    """Abstractie voor kompas-sensor."""
    
    def __init__(self, compass_device, time_step):
        """
        Args:
            compass_device: Webots compass object
            time_step: Robot timestep in ms
        """
        self._device = compass_device
        self._time_step = time_step
        self._device.enable(time_step)
    
    def enable(self, time_step):
        """Enable sensor (no-op als al enabled)."""
        self._device.enable(time_step)
        
    def get_direction(self):
        """Haal richting op."""
        return self._device.getValues()
    
    def getValues(self):
        """Haal sensorwaarden op (Webots API compatible)."""
        return self._device.getValues()


class LIDARSensor:
    """Abstractie voor LIDAR-sensor."""
    
    def __init__(self, lidar_device, time_step):
        """
        Args:
            lidar_device: Webots LIDAR object
            time_step: Robot timestep in ms
        """
        self._device = lidar_device
        self._time_step = time_step
        self._device.enable(time_step)
        self._device.enablePointCloud()
    
    def enable(self, time_step):
        """Enable sensor (no-op als al enabled)."""
        self._device.enable(time_step)
    
    def enablePointCloud(self):
        """Enable point cloud (no-op als al enabled)."""
        self._device.enablePointCloud()
        
    def get_range_image(self):
        """Haal range-afbeelding op."""
        return self._device.getRangeImage()
    
    def getRangeImage(self):
        """Haal range-afbeelding op (Webots API compatible)."""
        return self._device.getRangeImage()
    
    def get_point_cloud(self):
        """Haal point cloud op."""
        return self._device.getPointCloud()


class RobotHAL:
    """Centrale Hardware Abstraction Layer voor TurtleBot3."""
    
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
    
    def get_time_step(self):
        """Haal timestep op."""
        return self._time_step
    
    def get_time(self):
        """Haal huidige simulatietijd op."""
        return self._robot.getTime()
    
    def step(self, time_step):
        """Voer een simulatiestap uit."""
        return self._robot.step(time_step)


def create_robot_hal():
    """Factory-functie om HAL te creëren."""
    robot_instance = Robot()
    return RobotHAL(robot_instance)
