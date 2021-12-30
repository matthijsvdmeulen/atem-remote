import threading
import logging
import sys
from mido import Message, open_input, open_output, get_input_names, get_output_names
from .atem import clean_shutdown

logging = logging.getLogger(__name__)

class MidiController:
    """
    Handles communication with the MIDI surface.
    X-Touch Mini must be in MC mode!

    LA/LB: Note 84/85
    Fader 1-8: CC16 - CC23, Note 32 - 39 on push
    Turn right: Values 1 - 10 (Increment)
    Turn left: Values 65 - 72 (Decrement)
    Buttons 1-8: Note 89, 90, 40, 41, 42, 43, 44, 45
    Buttons 9-16: Note 87, 88, 91, 92, 86, 93, 94, 95
    Master Fader: Pitch Wheel
    """
    MC_CHANNEL = 0

    MIDI_BUTTONS = [89, 90, 40, 41, 42, 43, 44, 45, 87, 88, 91, 92, 86, 93, 94, 95]
    MIDI_PUSH = [32, 33, 34, 35, 36, 37, 38, 39]
    MIDI_ENCODER = [16, 17, 18, 19, 20, 21, 22, 23]
    MIDI_RING = [48, 49, 50, 51, 52, 53, 54, 55]
    MIDI_LAYER = [84, 85]

    LED_OFF = 0
    LED_BLINK = 1
    LED_ON = 127

    inport = None
    outport = None

    def __init__(self, state):
        self.state = state
        state.midi_controller = self

        while self.inport is None or self.outport is None:
            for name in get_input_names():
                if "x-touch mini" in name.lower():
                    logging.info('Using MIDI input: ' + name)
                    try:
                        self.inport = open_input(name)
                    except IOError:
                        logging.error('Can not open MIDI input port ' + name)
                        sys.exit(1)
                    break

            for name in get_output_names():
                if "x-touch mini" in name.lower():
                    logging.info('Using MIDI output: ' + name)
                    try:
                        self.outport = open_output(name)
                    except IOError:
                        logging.error('Can not open MIDI input port ' + name)
                        sys.exit(1)
                    break

        if self.inport is None or self.outport is None:
            logging.error('X-Touch Mini not found. Make sure device is connected!')
            sys.exit(1)

        worker = threading.Thread(target = self.midi_listener)
        worker.daemon = True
        worker.start()

    def monitor_ports(self):
        if self.inport.name not in get_input_names():
            print("X-Touch disconnected - Exiting")
            clean_shutdown(self.state)
            sys.exit(1)

    def midi_listener(self):
        for msg in self.inport:
            # logging.debug(f'Received {msg}')
            if msg.type == 'note_on' and msg.velocity == 127:
                if msg.note in self.MIDI_BUTTONS:
                    self.button_pushed(self.MIDI_BUTTONS.index(msg.note))
                elif msg.note in self.MIDI_LAYER:
                    self.layer_pushed(self.MIDI_LAYER.index(msg.note))
            elif msg.type == 'pitchwheel':
                value = int((msg.pitch + 8192) / 16256 * 10000)
                self.state.set_transition_fader(value)

    def close_midi(self):
        for i in range(0, 16):
            self.outport.send(Message('note_on', channel = self.MC_CHANNEL, note = self.MIDI_BUTTONS[i], velocity = self.LED_OFF))
        for i in range(0, 2):
            self.outport.send(Message('note_on', channel = self.MC_CHANNEL, note = self.MIDI_LAYER[i], velocity = self.LED_OFF))
        self.inport.close()
        self.outport.close()


    def button_pushed(self, button):
        if button >= 0 and button <= 5:
            self.state.set_program_input(button+1)
        if button >= 8 and button <= 13:
            self.state.set_preview_input(button-8+1)

    def layer_pushed(self, button):
        if button == 0:
            self.state.exec_auto()
        else:
            self.state.exec_cut()

    def set_auto_button(self, on, blink=False):
        self.set_layer_button(0, on, blink)


    def set_cut_button(self, on):
        self.set_layer_button(1, on, False)

    def refresh_controls(self):
        self.set_preview_input(self.state.preview-1)
        self.set_program_input(self.state.program-1)
        if(self.state.preview != self.state.program):
            self.set_auto_button(True, self.state.autoBlink)
            self.set_cut_button(True)
        else:
            self.set_auto_button(False)
            self.set_cut_button(False)

    def set_program_input(self, input):
        self.set_button(input, 1)
        for i in range(0, 6):
            if i != input:
                self.set_button(i, 0)

    def set_preview_input(self, input):
        self.set_button(input + 8, 1)
        for i in range(0, 6):
            if i != input:
                self.set_button(i + 8, 0)

    def set_transition_position(self, value):
        self.set_ring(8, value)

    def set_button(self, button, on, blink = False, dict=MIDI_BUTTONS):
        try:
            if on == True:
                if blink == True:
                    self.outport.send(Message('note_on', channel = self.MC_CHANNEL, note = dict[button], velocity = self.LED_BLINK))
                else:
                    self.outport.send(Message('note_on', channel = self.MC_CHANNEL, note = dict[button], velocity = self.LED_ON))
            else:
                self.outport.send(Message('note_on', channel = self.MC_CHANNEL, note = dict[button], velocity = self.LED_OFF))
        except IndexError:
            return

    def set_layer_button(self, button, on, blink = False):
        self.set_button(button, on, blink, self.MIDI_LAYER)