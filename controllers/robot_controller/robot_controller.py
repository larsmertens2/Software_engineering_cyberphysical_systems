from controller import Robot

robot = Robot()
timestep = int(robot.getBasicTimeStep())

motors = []
motors_names = ['motor_fl', 'motor_bl', 'motor_fr', 'motor_br']

for name in motors_names:
    m = robot.getDevice(name)
    m.setPosition(float('inf'))
    m.setVelocity(0.0)
    motors.append(m)
    
while robot.step(timestep) != -1:
    for m in motors:
        m.setVelocity(2.0)