#! /usr/bin/python3

"""
Use like this:
python3 practice.py

This script is used before experiment.py to make the participant known with how the experiment works.
It's a reduced version of the actual experiment script.
"""

import constants
import numpy as np
import pygaze
from datetime import datetime
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker
from psychopy import event
from psychopy.visual.textbox2 import TextBox2, allFonts


allFonts.addFontDirectory("fonts")

class Stimulus:
    def __init__(self, text):
        if "|" in text:
            text_before, text_of_interest, text_after = text.split("|")
            self.text = text.replace("|", "")
            self.chars_of_interest = (
                len(text_before),
                len(text_before) + len(text_of_interest),
            )
        else:
            self.text = text
            self.chars_of_interest = None

stimuli = [
    Stimulus("Geben Sie mir Ihren Zylinder!"),
    Stimulus("Hier ist ein Rezept für Tabletten."),
    Stimulus("Ich bin gut in Chemie."),
    Stimulus("Möchten Sie gerne etwas essen?")
]

### experiment setup ###

# start timing
libtime.expstart()

disp = libscreen.Display()
tracker = eyetracker.EyeTracker(disp)
keyboard = libinput.Keyboard(keylist=["space"], timeout=None)

# local log (mainly for debugging)
log = liblog.Logfile()
log.write(
    [
        "time",
        "trialnr",
        "stimulus",
        "fixation_start",
        "fixation_pos",
    ]
)

inscreen = libscreen.Screen()
inscreen.draw_text(
    text=(
        "On the next screen look at the center of the cross on the left."
        " Then read the sentence and after reading it, look at the dot"
        " in the bottom right corner and press [SPACE] on the keyboard."
        "\n\n(press [SPACE] to start)"
    ),
    fontsize=24,
)
fixscreen = libscreen.Screen()
# NOTE: in dummy mode, this fixation cross is drawn over by drift_correction()
fixscreen.draw_fixation(fixtype="cross", pos=constants.STIMULUS_START, pw=3)


### run experiment ###

# calibrate eye tracker (doesn't do anything in dummy mode)
tracker.calibrate()

# show instructions
disp.fill(inscreen)
disp.show()
keyboard.get_key()

# TODO: Practice runs

for trialnr, stimulus in enumerate(stimuli):
    # drift correction: wait for fixation
    # (and, in a real experiment, allow interrupting for recalibration)
    checked = False
    while not checked:
        disp.fill(fixscreen)
        disp.show()
        checked = tracker.drift_correction(
            pos=constants.STIMULUS_START, fix_triggered=True
        )

    # show stimulus
    stimulus_screen = libscreen.Screen()
    textbox = TextBox2(
        pygaze.expdisplay,
        text=stimulus.text,
        font="Roboto Mono",
        letterHeight=24,
        color="black",
        size=(None, None),
        pos=(
            -constants.DISPSIZE[0] / 2 + constants.STIMULUS_START[0],
            -constants.DISPSIZE[1] / 2 + constants.STIMULUS_START[1],
        ),
        anchor="left",
    )

    stimulus_screen.screen.append(textbox)
    # draw "irrelevant" fixation point
    stimulus_screen.draw_fixation(
        fixtype="dot",
        pos=(constants.DISPSIZE[0] - 100, constants.DISPSIZE[1] - 100),
        pw=3,
    )
    disp.fill(stimulus_screen)
    disp.show()
    event.clearEvents()

    # start eye tracking
    tracker.start_recording()
    tracker.status_msg(f"trial {trialnr}")
    logmsg = f"start_trial {trialnr} stimulus '{stimulus.text}'"
    tracker.log(logmsg)

    response = None
    while not response:
        fixation_start_time, startpos = tracker.wait_for_fixation_start()
        log.write(
            [
                datetime.now().isoformat(),
                trialnr,
                stimulus.text,
                fixation_start_time,
                startpos
            ]
        )

        # If a regular or irregular break would occur,
        # the code to pause and pick up the experiment again would go here
        # The most important part would be to be able to trigger a new 
        # calibration sequence.

        # keypress to start next trial
        if "space" in event.getKeys():
            space_pressed = True
            event.clearEvents()
            break

    tracker.stop_recording()
    tracker.log(f"end_trial {trialnr}")


# finish up
log.close()
tracker.close()
disp.close()
libtime.expend()
