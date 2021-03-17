#! /usr/bin/python3

import constants
import numpy as np
import pygaze
from datetime import datetime
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker
from pygaze.plugins.aoi import AOI
from psychopy import event
from psychopy.visual.textbox2 import TextBox2, allFonts
from psychopy.visual.rect import Rect


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


### for testing ###
stimuli = [
    Stimulus("Meine |Sekretärin| hat versprochen, mich morgen anzurufen."),
    Stimulus("Auf der Arbeit hatte er heute eine Beförderung erhalten."),
    Stimulus("Das älteste Kind hatte zuvor eine Ausbildung zum |Informatiker| gemacht."),
    Stimulus("Schon wieder hatte die Schule ihn angerufen, weil sein Sohn Probleme gemacht hatte."),
    Stimulus("Er war verärgert, denn er hatte die Bestellung schon vor drei Tagen bei dem |Florist| in Auftrag gegeben."),
    Stimulus("Wenn ich noch mehr arbeite, habe ich bald ein Burnout."),
    Stimulus("Als |Maurerin| zu arbeiten, war schon immer ihr Traum gewesen."),
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
        "within_aoi",
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

    # calculate area of interest
    if stimulus.chars_of_interest is not None:
        coi_start = stimulus.chars_of_interest[0]
        coi_end = stimulus.chars_of_interest[1]
        aoi_top_left = textbox.verticesPix[coi_start * 4 + 1] + (-7, -15)
        aoi_bottom_right = textbox.verticesPix[coi_end * 4 - 1] + (7, 15)
        aoi_width = aoi_bottom_right[0] - aoi_top_left[0]
        aoi_height = aoi_bottom_right[1] - aoi_top_left[1]
        aoi_center = (aoi_top_left + aoi_bottom_right) / 2

        # visualize area of interest
        aoi_rect = Rect(
            pygaze.expdisplay,
            width=aoi_width,
            height=aoi_height,
            pos=aoi_center,
            fillColor="red",
        )
        stimulus_screen.screen.append(aoi_rect)

        disp_center = np.array(constants.DISPSIZE) / 2
        aoi = AOI(
            "rectangle", tuple(aoi_top_left + disp_center), (aoi_width, aoi_height)
        )
    else:
        aoi = None

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
    if aoi is not None:
        logmsg += f" aoi x={aoi.pos[0]},y={aoi.pos[1]},w={aoi.size[0]},h={aoi.size[1]}"
    tracker.log(logmsg)

    response = None
    while not response:
        fixation_start_time, startpos = tracker.wait_for_fixation_start()
        within_aoi = aoi is not None and aoi.contains(startpos)
        log.write(
            [
                datetime.now().isoformat(),
                trialnr,
                stimulus.text,
                fixation_start_time,
                startpos,
                within_aoi,
            ]
        )

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
