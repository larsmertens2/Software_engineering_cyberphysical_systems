import json, requests
from controller import Robot

class AisleDeviceController:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000/api"

        self.robot = Robot()
        self.time_step = int(self.robot.getBasicTimeStep())
        self.aisle_id = self.robot.getName()

        self.receiver = self.robot.getDevice('receiver')
        self.receiver.enable(self.time_step)
        self.emitter = self.robot.getDevice('emitter')

        self.locker = None
        self.queue = []

    def send_message(self, robot_id, msg):
        payload = json.dumps({"to": robot_id, "type": msg, "aisle": self.aisle_id})
        self.emitter.send(payload.encode('utf-8'))

    def update_state(self):
        requests.post(f"{self.base_url}/aisle/state", json={
            "aisle_id": self.aisle_id,
            "locker": self.locker,
            "waiting": self.queue
        }, timeout=5)

    def run(self):
        while self.robot.step(self.time_step) != -1:
            while self.receiver.getQueueLength() > 0:
                msg = json.loads(self.receiver.getString())
                self.receiver.nextPacket()

                if msg.get("aisle") != self.aisle_id:
                    continue

                t = msg.get("type")
                robot_id = msg.get("robot_id")

                if t == "REQUEST_ENTRY":
                    if self.locker is None:
                        self.locker = robot_id
                        self.send_message(robot_id, "ENTRY_GRANTED")
                    elif self.locker == robot_id:
                        self.send_message(robot_id, "ENTRY_GRANTED")
                    else:
                        self.queue.append({"robot_id": robot_id, "node": msg.get("node")})
                        self.send_message(robot_id, "ENTRY_DENIED")
                    self.update_state()

                elif t == "EXITING":
                    self.locker = None
                    if self.queue:
                        nxt = self.queue.pop(0)
                        self.locker = nxt["robot_id"]
                        self.send_message(self.locker, "ENTRY_GRANTED")
                    self.update_state()

if __name__ == "__main__":
    device = AisleDeviceController()
    device.run()
