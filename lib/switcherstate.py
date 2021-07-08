import PyATEMMax

"""
This module holds the mixer state of the X-Air device
"""

class SwitcherState:
    """
    This stores the mixer state in the application. It also keeps
    track of the current selected fader bank on the midi controller to
    decide whether state changes from the X-Air device need to be
    sent to the midi controller.
    """

    program = 0
    preview = 0
    transitionPosition = 0
    transitionMidiPosition = 0
    transitionWasTop = False
    autoBlink = False

    midi_controller = None
    switcher = None

    def exec_auto(self):
        self.switcher.execAutoME(0)

    def exec_cut(self):
        self.switcher.execCutME(0)

    def set_preview_input(self, input):
        self.switcher.setPreviewInputVideoSource(0, input + 1)

    def set_program_input(self, input):
        self.switcher.setProgramInputVideoSource(0, input + 1)

    def set_transition_fader(self, value):
        if self.transitionMidiPosition == 10000:
            self.transitionWasTop = True
        elif self.transitionMidiPosition == 0:
            self.transitionWasTop = False

        if self.transitionWasTop == True:
            self.switcher.setTransitionPosition(0, (value * -1 + 10000))
        else:
            self.switcher.setTransitionPosition(0, value)
        self.transitionMidiPosition = value

    def received_atem(self, params):
        # print(params["cmdName"])
        if params["cmdName"] == "Transition Position":
            # print(f"{params['cmdName']}: {params['switcher'].transition[0].position:04}", end="\r")
            self.transitionPosition = params["switcher"].transition[0].position
            autoBlinkOld = self.autoBlink
            if self.transitionPosition != 0 and self.transitionPosition != 10000:
                self.autoBlink = True
            else:
                self.autoBlink = False
            if self.autoBlink != autoBlinkOld:
                self.midi_controller.refresh_controls()
            return
        elif params["cmdName"] == "Preview Input":
            # print(f"{params['cmdName']}: {params['switcher'].previewInput[0].videoSource.value} ({params['switcher'].previewInput[0].videoSource})", end="\r")
            self.preview = params["switcher"].previewInput[0].videoSource.value - 1
            self.midi_controller.refresh_controls()
        elif params["cmdName"] == "Program Input":
            # print(f"{params['cmdName']}: {params['switcher'].programInput[0].videoSource.value} ({params['switcher'].programInput[0].videoSource})", end="\r")
            self.program = params["switcher"].programInput[0].videoSource.value - 1
            self.midi_controller.refresh_controls()

    def read_initial_state(self):
        self.program = self.switcher.programInput[0].videoSource.value - 1
        self.preview = self.switcher.previewInput[0].videoSource.value - 1
        self.midi_controller.refresh_controls()