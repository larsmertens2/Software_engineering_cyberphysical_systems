"""
HAL COMPONENTS - shared hardware abstractions

contains base classes for following hardware components:
- Motor control
- sensors (GPS, Compass, LIDAR)
- communication (Receiver, Emitter)
"""

class Motor:
    """abstraction for a motor."""
    
    def __init__(self, motor_device):
        self._device = motor_device
        
    def set_position_infinite(self):
        """set motor in velocity-modus (infinite position)."""
        self._device.setPosition(float('inf'))
    
    def setPosition(self, position):
        """set motor position (Webots API compatible)."""
        self._device.setPosition(position)
        
    def set_velocity(self, velocity):
        """set motor velocity"""
        self._device.setVelocity(velocity)
    
    def setVelocity(self, velocity):
        """set motor velocity (Webots API compatible)."""
        self._device.setVelocity(velocity)
        
    def get_velocity(self):
        """get current speed"""
        return self._device.getVelocity()


class GPSSensor:
    """Abstraction for GPS-sensor."""
    
    def __init__(self, gps_device, time_step):
        self._device = gps_device
        self._time_step = time_step
        self._device.enable(time_step)
    
    def enable(self, time_step):
        """Enable sensor (no-op if already enabled)."""
        self._device.enable(time_step)
        
    def get_position(self):
        """get current position"""
        return self._device.getValues()
    
    def getValues(self):
        """get values (Webots API compatible)."""
        return self._device.getValues()


class CompassSensor:
    """Abstraction for compass-sensor."""
    
    def __init__(self, compass_device, time_step):
        self._device = compass_device
        self._time_step = time_step
        self._device.enable(time_step)
    
    def enable(self, time_step):
        """Enable sensor (no-op if already enabled)."""
        self._device.enable(time_step)
        
    def get_direction(self):
        """get the direction"""
        return self._device.getValues()
    
    def getValues(self):
        """get sensor values (Webots API compatible)."""
        return self._device.getValues()


class LIDARSensor:
    """Abstraction for LIDAR-sensor."""
    
    def __init__(self, lidar_device, time_step):
        self._device = lidar_device
        self._time_step = time_step
        self._device.enable(time_step)
        self._device.enablePointCloud()
    
    def enable(self, time_step):
        """Enable sensor (no-op if already enabled)."""
        self._device.enable(time_step)
    
    def enablePointCloud(self):
        """Enable point cloud (no-op if already enabled)."""
        self._device.enablePointCloud()
        
    def get_range_image(self):
        """gets the range image"""
        return self._device.getRangeImage()
    
    def getRangeImage(self):
        """gets range image (Webots API compatible)."""
        return self._device.getRangeImage()
    
    def get_point_cloud(self):
        """get point cloud op."""
        return self._device.getPointCloud()


class Receiver:
    """Abstraction for Receiver communication device."""
    
    def __init__(self, receiver_device):
        self._device = receiver_device
    
    def enable(self, time_step):
        """Enable receiver."""
        self._device.enable(time_step)
    
    def getQueueLength(self):
        """Haal message from qeue"""
        return self._device.getQueueLength()
    
    def getString(self):
        """get message as a string"""
        return self._device.getString()
    
    def nextPacket(self):
        """go to the next packet"""
        self._device.nextPacket()
    
    def getChannel(self):
        """Hget next communication channel"""
        return self._device.getChannel()


class Emitter:
    """Abstraction for Emitter communication device."""
    
    def __init__(self, emitter_device):
        self._device = emitter_device
    
    def send(self, message):
        """send message"""
        self._device.send(message)
    
    def setChannel(self, channel):
        """set communictaion channel"""
        self._device.setChannel(channel)