from sensors import object_nearby


def drive(left_motor, right_motor, left_speed, right_speed, lidar, nearby_threshold):
    if object_nearby(lidar, nearby_threshold):
        left_motor.setVelocity(left_speed / 3)
        right_motor.setVelocity(right_speed / 3)
    else:
        left_motor.setVelocity(left_speed)
        right_motor.setVelocity(right_speed)
