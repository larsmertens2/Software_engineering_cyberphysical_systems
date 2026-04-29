import math
import hardware_abstraction_layer as hal

def get_direction(compass_sensor):
    direction = compass_sensor.get_direction()  # ← HAL method
    return math.atan2(direction[0], direction[1])

def object_nearby(lidar_sensor, nearby_threshold):
    range_image = lidar_sensor.get_range_image()  # ← HAL method
    if not range_image:
        return False

    start_index = 180 - 60
    eind_index = 180 + 60

    for i in range(start_index, eind_index):
        distance = range_image[i % 360]
        if math.isinf(distance) or math.isnan(distance):
            continue
        if distance < nearby_threshold:
            return True

    return False


def is_path_clear(lidar_sensor, obstacle_threshold):
    range_image = lidar_sensor.get_range_image()  # ← HAL method
    if not range_image:
        return True

    start_index = 180 - 15
    eind_index = 180 + 15

    for i in range(start_index, eind_index):
        distance = range_image[i % 360]
        if math.isinf(distance) or math.isnan(distance):
            continue
        if distance < obstacle_threshold:
            return False

    return True


def detect_narrow_corridor(lidar_sensor):
    range_image = lidar_sensor.get_range_image()  # ← HAL method
    if not range_image:
        return False

    left_distance = range_image[90]
    right_distance = range_image[270]
    return left_distance < 0.4 and right_distance < 0.4


def get_side_distances(lidar_sensor):
    range_image = lidar_sensor.get_range_image()  # ← HAL method
    return range_image[90], range_image[270]
