#! /usr/bin/python3

import constants
import random
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker


### for testing ###
stimuli = [
    "Meine Sekretärin hat versprochen, mich morgen anzurufen.",
    "Auf der Arbeit hatte er heute eine Beförderung erhalten.",
    "Das älteste Kind hatte zuvor eine Ausbildung zum Informatiker gemacht.",
    "Schon wieder hatte die Schule ihn angerufen, weil sein Sohn Probleme gemacht hatte.",
    "Er war verärgert, denn er hatte die Bestellung schon vor drei Tagen bei dem Florist in Auftrag gegeben.",
    "Wenn ich noch mehr arbeite, habe ich bald ein Burnout.",
    "Als Maurerin zu arbeiten, war schon immer ihr Traum gewesen."
]


### constants ###

# display size in pixels
DISPSIZE = (1920, 1080)


### experiment setup ###

# start timing
libtime.expstart()

# create display object
disp = libscreen.Display()

# create eyetracker object
tracker = eyetracker.EyeTracker(disp)

# create keyboard object
keyboard = libinput.Keyboard(keylist=['space'], timeout=None)

# create logfile object
log = liblog.Logfile()
# TODO: Fill log with relevant info
log.write(["trialnr", "trialtype", "endpos", "latency"])

inscreen = libscreen.Screen()
inscreen.draw_text(text="In the next screen fixate on the dot in the lower left corner. Then read the sentence and after reading it, press space.\n\n(press space to start)", fontsize=24)
fixscreen = libscreen.Screen()
fixscreen.draw_fixation(fixtype='cross', pos=(80, 1000), pw=3) # lower left


### run experiment ###

# calibrate eye tracker
tracker.calibrate()

# show instructions
disp.fill(inscreen)
disp.show()
keyboard.get_key()

# TODO: Practice runs

for trialnr, stimulus in enumerate(stimuli):
    # drift correction
    checked = False
    while not checked:
        disp.fill(fixscreen)
        disp.show()
        checked = tracker.drift_correction(pos=(80, 1000), fix_triggered=True)

    # start eye tracking
    tracker.start_recording()
    tracker.status_msg("trial {}".format(trialnr))
    tracker.log("start_trial {} trialtype '{}'".format(trialnr, stimulus))

    # show stimulus
    stimulus_screen = libscreen.Screen()
    stimulus_screen.draw_text(text=stimulus, fontsize=24)
    stimulus_screen.draw_fixation(fixtype='cross', pos=(1840, 1000), pw=3) # bottom right, look at it to finish reading sentence
    disp.fill(stimulus_screen)
    disp.show()

    response = None
    while not response:
        fixation_start_time, startpos = tracker.wait_for_fixation_start()
        fixation_end_time, endpos = tracker.wait_for_fixation_end()
        tracker.log("Fixation: {} ms / pos start {}, {} / pos end {}, {}".format(
            fixation_end_time - fixation_start_time,
            startpos[0], startpos[1],
            endpos[0], endpos[1]
        ))

        # the person only needs to look approximately into the corner, so take a bit of space
        if endpos[0] > 1740 and endpos[1] > 900:
            break
        # TODO: I can't figure out how to escape the loop by pressing the button, so I'll just go back to looking in a corner
        # the bottom right to finish. TODO: Fix the instruction text if we keep it like that
        # response, presstime = keyboard.get_key(timeout=1)

    tracker.stop_recording()

    # TODO: Fill log with relevant info


# finish up
log.close()
tracker.close()
disp.close()
libtime.expend()