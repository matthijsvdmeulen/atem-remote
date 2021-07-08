#!/usr/bin/env python3
import argparse
import threading
import PyATEMMax
from lib.midicontroller import MidiController
from lib.atem import find_switcher, refresh_connection
from lib.switcherstate import SwitcherState

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = 'Remote control X-Air mixers with a midi controller')
    parser.add_argument('atem_address', help = 'ip address of your X-Air mixer (optional)', nargs = '?')
    parser.add_argument('-m', '--monitor', help='monitor X-Touch connection and exit when disconnected', action="store_true")
    args = parser.parse_args()

    if args.atem_address is None:
        address = find_switcher()
        if address is None:
            print('Error: Could not find any switchers in network. Please specify ip address manually.')
            exit()
        else:
            args.atem_address = address

    state = SwitcherState()
    midi = MidiController(state)
    state.midi_controller = midi
    switcher = PyATEMMax.ATEMMax()
    switcher.registerEvent(switcher.atem.events.receive, state.received_atem)
    switcher.connect(args.atem_address)
    switcher.waitForConnection()
    state.switcher = switcher
    print(f"Connected to {switcher.atemModel} on {switcher.ip}")

    if args.monitor:
        print('Monitoring X-Touch connection enabled')
        monitor = threading.Thread(target = midi.monitor_ports)
        monitor.daemon = True
        monitor.start()

    state.read_initial_state()

    refresh_connection(state)
