from controller import Robot
import time

robot = Robot()
timestep = int(robot.getBasicTimeStep())

motors = []
motors_names = ['motor_fl', 'motor_bl', 'motor_fr', 'motor_br']

for name in motors_names:
    m = robot.getDevice(name)
    m.setPosition(float('inf'))
    m.setVelocity(0.0)
    motors.append(m)
    
start_time = robot.getTime()
while robot.step(timestep) != -1:
    if robot.getTime() > start_time + 2.0:
        break
    
while robot.step(timestep) != -1:
    #for m in motors:
    #    m.setVelocity(2.0)
    motors[0].setVelocity(2.0) 
    motors[1].setVelocity(-2.0) 
    motors[2].setVelocity(-2.0) 
    motors[3].setVelocity(2.0) 
    
    