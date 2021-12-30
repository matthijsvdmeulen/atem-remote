#!/usr/bin/env python3
import logging
import argparse
import ipaddress
import sys
import time
import PyATEMMax
import threading
from lib.midicontroller import MidiController
from lib.atem import find_switchers, find_subnet, atem_watchdog, clean_shutdown
from lib.switcherstate import SwitcherState

logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(name)s:%(message)s')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description = 'Control one or more Blackmagic Design ATEM switchers with either an X-Touch mini, or another ATEM switcher'
    )
    parser.add_argument(
        'atem_address',
        help = 'ip address of your ATEM switcher (optional)',
        nargs = '?'
    )
    parser.add_argument(
        '-m',
        '--midi',
        help='enable midi function',
        action="store_true"
    )
    parser.add_argument(
        '-s',
        '--subnet',
        help='ip network where the switchers reside, only needed with exotic subnets (default is 192.168.1.0/24) (optional)',
        type=ipaddress.IPv4Network,
        default=find_subnet()
    )
    parser.add_argument(
        '-a',
        '--amount',
        help='max amount of switchers to connect to, to reduce scanning time (optional)',
        type=int,
        default=-1
    )
    parser.add_argument(
        '-n',
        '--minimum',
        help='min amount of switchers to connect to (optional)',
        type=int,
        default=0
    )
    args = parser.parse_args()

    while True:
        switchers = find_switchers(subnet=args.subnet, max=args.amount)
        logging.debug(f"Switchers: {switchers}, len: {len(switchers)}")
        if len(switchers) >= args.minimum or args.minimum <= 0:
            break

    if switchers == []:
        logging.error('Error: Could not find any switchers in network. Please specify subnet manually.')
        sys.exit(1)

    state = SwitcherState()

    for ip in switchers:
        switcher = PyATEMMax.ATEMMax()
        switcher.registerEvent(switcher.atem.events.receive, state.received_atem)
        logging.info(f"Connecting to {ip}")
        switcher.connect(ip)
        if switcher.waitForConnection(timeout=10):
            state.switchers.append(switcher)
            logging.info(f"Connected to {switcher.atemModel} on {switcher.ip}")
        else:
            logging.error(f"Failed to connect to {ip} after 10 seconds")
            switcher.disconnect()

    if state.switchers == []:
        logging.error('Could not connect to any of the detected switchers, exiting')
        sys.exit(1)

    if args.midi:
        midi = MidiController(state)

    state.read_initial_state()

    try:
        while True:
            time.sleep(1)
            if args.midi:
                midi.monitor_ports()
            atem_watchdog(state)
    except KeyboardInterrupt:
        clean_shutdown(state)