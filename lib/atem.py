import time
import PyATEMMax
from mido import Message

def find_switcher(subnet = "192.168.1"):
    switcher = PyATEMMax.ATEMMax()
    for i in range(1,255):
        ip = f"{subnet}.{i}"
        print(f"Checking {ip}", end="\r")

        switcher.ping(ip)
        if switcher.waitForConnection():
            switcher.disconnect()
            return ip

        switcher.disconnect()

def refresh_connection(state):
        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            state.switcher.disconnect()
            state.midi_controller.close_midi()
            # exit()