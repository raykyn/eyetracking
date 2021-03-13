#! /usr/bin/python3

import pygaze
from pygaze import libscreen
from pygaze import libtime
from pygaze import liblog
from pygaze import libinput
from pygaze import eyetracker
from psychopy.visual.textbox2 import TextBox2, allFonts
from psychopy.visual.rect import Rect


allFonts.addFontDirectory("fonts")


class Stimulus:
    def __init__(self, text):
        if '|' in text:
            text_before, text_of_interest, text_after = text.split('|')
            self.text = text.replace('|', '')
            self.chars_of_interest = (len(text_before), len(text_before) + len(text_of_interest))
        else:
            self.text = text
            self.chars_of_interest = None


### for testing ###
stimuli = [
    Stimulus("Meine |Sekretärin| hat versprochen, mich morgen anzurufen."),
    Stimulus("|Auf| der Arbeit hatte er heute eine Beförderung erhalten."),
    Stimulus("Das älteste Kind hatte zuvor eine Ausbildung zum |Informatiker| gemacht."),
    Stimulus("Schon wieder hatte die Schule ihn angerufen, weil sein Sohn Probleme gemacht |hatte|."),
    Stimulus("Er war verärgert, denn er hatte die Bestellung schon vor drei Tagen bei dem |Florist| in Auftrag gegeben."),
    Stimulus("Wenn ich noch mehr arbeite|,| habe ich bald ein Burnout."),
    Stimulus("Als |Maurerin| zu arbeiten, war schon immer ihr Traum gewesen."),
]

"""
import os
from pygaze import FONTDIR
import pygame
font = "mono"
fontname = os.path.join(FONTDIR, font) + ".ttf"
font = pygame.font.Font(fontname, 24)
print(font.size(" "))
# 5 letters: 32px height, 70px width
# 1 letter: 32px, 14px width
"""


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
    tracker.log("start_trial {} trialtype '{}'".format(trialnr, stimulus.text))

    # show stimulus
    stimulus_screen = libscreen.Screen()
    textbox = TextBox2(pygaze.expdisplay, text=stimulus.text, font="Roboto Mono", letterHeight=24, color="black", size=(None, None))
    if stimulus.chars_of_interest is not None:
        coi_start = stimulus.chars_of_interest[0]
        coi_end = stimulus.chars_of_interest[1]
        aoi_top_left = textbox.verticesPix[coi_start * 4 + 1].copy()
        aoi_bottom_right = textbox.verticesPix[coi_end * 4 - 1].copy()
        aoi_width = aoi_bottom_right[0] - aoi_top_left[0]
        aoi_height = aoi_bottom_right[1] - aoi_top_left[1]
        aoi_center = (aoi_top_left + aoi_bottom_right) / 2
        aoi = Rect(pygaze.expdisplay, width=aoi_width, height=aoi_height, pos=aoi_center, fillColor="red")
        stimulus_screen.screen.append(aoi)

    stimulus_screen.screen.append(textbox)
    # stimulus_screen.draw_text(text=stimulus, fontsize=24)
    stimulus_screen.draw_fixation(fixtype='cross', pos=(1840, 1000), pw=3) # bottom right, look at it to finish reading sentence
    disp.fill(stimulus_screen)
    disp.show()

    # Big TODO: In the while-loop, check for each fixation if it's inside a boundary box of a word.
    # How do we get boundary boxes? We're using monofont, so we should be able to calculate each word position.
    # How wide are our characters in monofont???
    # Okay, I got the answer to that by testing in pygame:
    # Using our font (Roboto Mono), a single letter or whitespace has a width of 14px (and a height of 70, but that's less relevant)
    # Using this number, we can calculate where a stimulus starts (on the screen), and then be able to calculate each word boundary box.
    # Technically, we only need to get the coordinates of the whitespaces to do this.
    # The vertical position is almost irrelevant, because all stimuli are one-liners

    response = None
    while not response:
        fixation_start_time, startpos = tracker.wait_for_fixation_start()
        fixation_end_time, endpos = tracker.wait_for_fixation_end()
        tracker.log("Fixation: {} ms / pos start {}, {} / pos end {}, {}".format(
            fixation_end_time - fixation_start_time,
            startpos[0], startpos[1],
            endpos[0], endpos[1]
        ))

        # the person only needs to look approximately into the corner, so it counts 100 pixels around as well
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