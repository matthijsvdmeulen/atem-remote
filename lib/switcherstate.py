import logging
from types import SimpleNamespace

logging = logging.getLogger(__name__)

class SwitcherState:

    program = 1
    preview = 2
    transitionPosition = 0
    transitionLastPosition = 0

    transitionMidiPosition = 0
    transitionWasTop = False
    autoBlink = False

    lastIP = "0.0.0.1"

    midi_controller = None
    switchers = []

    noswitcher = SimpleNamespace()
    setattr(noswitcher, "ip", "0.0.0.0")

    def exec_auto(self):
        for sw in self.switchers:
            sw.execAutoME(0)

    def exec_cut(self):
        for sw in self.switchers:
            sw.execCutME(0)

    def set_preview_input(self, i, switcher = noswitcher):
        if i == 3010:
            input = 5
        elif i == 0:
            input = 6
        else:
            input = i
        logging.debug(f"IP: {switcher.ip}, Recieved Preview {input}")
        self.preview = input
        for sw in self.switchers:
            if not(sw.ip == switcher.ip or switcher.ip == self.lastIP):
                if sw.atemModel == "ATEM Mini Pro ISO":
                    if input == 5:
                        input = 3010
                    if input == 6:
                        input = 0
                sw.setPreviewInputVideoSource(0, input)
                logging.debug(f"IP {sw.ip}, Sending Preview change {input}, from: {switcher.ip}, last: {self.lastIP}")
                self.lastIP = sw.ip
        if self.midi_controller != None:
            self.midi_controller.refresh_controls()

    def set_program_input(self, i, switcher = noswitcher):
        if i == 3010:
            input = 5
        elif i == 0:
            input = 6
        else:
            input = i
        logging.debug(f"IP: {switcher.ip}, Recieved Program {input}")
        self.program = input
        for sw in self.switchers:
            if not(sw.ip == switcher.ip or switcher.ip == self.lastIP):
                if sw.atemModel == "ATEM Mini Pro ISO":
                    if input == 5:
                        input = 3010
                    if input == 6:
                        input = 0
                sw.setProgramInputVideoSource(0, input)
                self.lastIP = sw.ip
                logging.debug(f"IP {sw.ip}, Sending Program change {input}")
        if self.midi_controller != None:
            self.midi_controller.refresh_controls()

    def set_transition_fader(self, value, switcher = noswitcher):
        logging.debug(f"IP: {switcher.ip}, Recieved Preview {value}")
        self.transitionPosition = value
        if self.transitionMidiPosition == 10000:
            self.transitionWasTop = True
        elif self.transitionMidiPosition == 0:
            self.transitionWasTop = False

        self.transitionMidiPosition = value

        for sw in self.switchers:
            if not(sw.ip == switcher.ip or switcher.ip == self.lastIP):
                if not(self.transitionLastPosition >= 9500 and value == 0):
                    if self.transitionWasTop == True and switcher.ip != "0.0.0.0":
                        sw.setTransitionPosition(0, (value * -1 + 10000))
                    else:
                        sw.setTransitionPosition(0, value)
                self.transitionLastPosition = value
                self.lastIP = sw.ip
                logging.debug(f"IP {sw.ip}, Setting transition to {value}")

        autoBlinkOld = self.autoBlink
        if self.transitionPosition != 0 and self.transitionPosition != 10000:
            self.autoBlink = True
        else:
            self.autoBlink = False
        if self.autoBlink != autoBlinkOld:
            if self.midi_controller != None:
                self.midi_controller.refresh_controls()

    def received_atem(self, params):
        if params["cmdName"] == "Transition Position":
            sw = params["switcher"]
            value = sw.transition[0].position
            self.set_transition_fader(value, sw)
        elif params["cmdName"] == "Preview Input":
            sw = params["switcher"]
            value = sw.previewInput[0].videoSource.value
            self.set_preview_input(value, sw)
        elif params["cmdName"] == "Program Input":
            sw = params["switcher"]
            value = sw.programInput[0].videoSource.value
            self.set_program_input(value, sw)

    def read_initial_state(self):
        self.set_preview_input(self.switchers[0].previewInput[0].videoSource.value)
        self.set_program_input(self.switchers[0].programInput[0].videoSource.value)