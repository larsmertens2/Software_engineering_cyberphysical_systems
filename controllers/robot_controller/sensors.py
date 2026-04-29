import math


def get_direction(compass):
    direction = compass.getValues()
    return math.atan2(direction[0], direction[1])


def object_nearby(lidar, nearby_threshold):
    range_image = lidar.getRangeImage()
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


def is_path_clear(lidar, obstacle_threshold):
    range_image = lidar.getRangeImage()
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


def detect_narrow_corridor(lidar):
    range_image = lidar.getRangeImage()
    if not range_image:
        return False

    left_distance = range_image[90]
    right_distance = range_image[270]
    return left_distance < 0.4 and right_distance < 0.4


def get_side_distances(lidar):
    range_image = lidar.getRangeImage()
    return range_image[90], range_image[270]
