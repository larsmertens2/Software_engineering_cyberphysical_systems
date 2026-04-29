"""
HAL COMPONENTS - Gedeelde hardware-abstracties

Bevat basis-klassen voor alle hardware-componenten:
- Motor control
- Sensoren (GPS, Compass, LIDAR)
- Communicatie (Receiver, Emitter)
"""

class Motor:
    """Abstractie voor een motor."""
    
    def __init__(self, motor_device):
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


class Receiver:
    """Abstractie voor Receiver communicatie device."""
    
    def __init__(self, receiver_device):
        self._device = receiver_device
    
    def enable(self, time_step):
        """Enable receiver."""
        self._device.enable(time_step)
    
    def getQueueLength(self):
        """Haal aantal berichten in queue op."""
        return self._device.getQueueLength()
    
    def getString(self):
        """Haal volgende bericht op als string."""
        return self._device.getString()
    
    def nextPacket(self):
        """Ga naar volgende packet."""
        self._device.nextPacket()
    
    def getChannel(self):
        """Haal communicatie channel op."""
        return self._device.getChannel()


class Emitter:
    """Abstractie voor Emitter communicatie device."""
    
    def __init__(self, emitter_device):
        self._device = emitter_device
    
    def send(self, message):
        """Verstuur bericht."""
        self._device.send(message)
    
    def setChannel(self, channel):
        """Stel communicatie channel in."""
        self._device.setChannel(channel)