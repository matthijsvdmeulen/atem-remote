import logging
import socket
import ipaddress
import time
import PyATEMMax
import sys

logging = logging.getLogger(__name__)

def find_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def find_subnet():
    return ipaddress.IPv4Network(find_ip() + "/24", strict=False)

def find_switchers(subnet = find_subnet(), max = -1):
    switcher = PyATEMMax.ATEMMax()
    switchers = []
    for ip in subnet.hosts():
        logging.debug(f"Checking {str(ip)}")
        switcher.ping(str(ip))
        if switcher.waitForConnection(infinite=False, waitForFullHandshake=False):
            logging.info(f"Found: {str(ip)}")
            switchers.append(str(ip))
        switcher.disconnect()
        if len(switchers) == max:
            return switchers
    return switchers

def clean_shutdown(state):
    for switcher in state.switchers:
        logging.info(f"Disconnected from {switcher.atemModel} on {switcher.ip}")
        switcher.disconnect()
    if state.midi_controller != None:
        state.midi_controller.close_midi()

def atem_watchdog(state):
    for switcher in state.switchers:
        if not switcher.connected:
            logging.info(f"Detected disconnection from {switcher.atemModel} on {switcher.ip}, shutting down")
            clean_shutdown(state)
            sys.exit(1)
