import sys
import os
import json
import requests

# Add project root to path so we can import controllers module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from controllers.aisleDevice_hal import create_aisle_device_hal

class AisleDeviceController:
    def __init__(self):
        self.base_url = "http://127.0.0.1:5000/api"

        self.hal = create_aisle_device_hal()
        self.time_step = int(self.hal.getBasicTimeStep())
        self.aisle_id = self.hal.get_Name()

        self.receiver = self.hal.receiver
        self.receiver.enable(self.time_step)
        self.emitter = self.hal.emitter
        
        self.robot = self.hal._robot
        
        self.locker = None
        self.queue = []
        self._step_count = 0
        print(f"[{self.aisle_id}] Device gestart, luistert op channel {self.receiver.getChannel()}")

    def send_message(self, robot_id, msg):
        payload = json.dumps({"to": robot_id, "type": msg, "aisle": self.aisle_id})
        self.emitter.send(payload.encode('utf-8'))
        print(f"[{self.aisle_id}] SEND -> {robot_id}: {msg}")

    def update_state(self):
        try:
            requests.post(f"{self.base_url}/aisle/state", json={
                "aisle_id": self.aisle_id,
                "locker": self.locker,
                "waiting": self.queue
            }, timeout=5)
        except Exception as e:
            print(f"[{self.aisle_id}] Backend update mislukt: {e}")

    def run(self):
        self.hal.step(self.time_step)
        self.update_state()
        print(f"[{self.aisle_id}] State gereset bij herstart")

        while self.hal.step(self.time_step) != -1:
            self._step_count += 1

            if self._step_count % 500 == 0:
                print(f"[{self.aisle_id}] alive | locker={self.locker} | queue={self.queue}")

            queue_len = self.receiver.getQueueLength()
            if queue_len > 0:
                print(f"[{self.aisle_id}] {queue_len} bericht(en) ontvangen")

            while self.receiver.getQueueLength() > 0:
                raw = self.receiver.getString()
                self.receiver.nextPacket()

                print(f"[{self.aisle_id}] RAW bericht: {raw}")

                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError as e:
                    print(f"[{self.aisle_id}] JSON parse fout: {e}")
                    continue

                if msg.get("aisle") != self.aisle_id:
                    print(f"[{self.aisle_id}] Genegeerd: aisle='{msg.get('aisle')}' != '{self.aisle_id}'")
                    continue

                t = msg.get("type")
                robot_id = msg.get("robot_id")
                print(f"[{self.aisle_id}] Verwerk: type={t} van {robot_id}")

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

                else:
                    print(f"[{self.aisle_id}] Onbekend berichttype: {t}")

if __name__ == "__main__":
    device = AisleDeviceController()
    device.run()
