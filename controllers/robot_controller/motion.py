from sensors import object_nearby


def drive(left_motor, right_motor, left_speed, right_speed, lidar, nearby_threshold, slow_factor=3):
    if object_nearby(lidar, nearby_threshold):
        left_motor.setVelocity(left_speed / slow_factor)
        right_motor.setVelocity(right_speed / slow_factor)
    else:
        left_motor.setVelocity(left_speed)
        right_motor.setVelocity(right_speed)
