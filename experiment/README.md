# Eyetracking

## Code by Andreas Säuberli and Ismail Prada

## What is this?
This is an implementation of the experiment described in this document: https://docs.google.com/document/d/1hxHqlpFRThOBxhxIBnlt6Mnn2_q5CX6vd30buggcTJ8/

## How to?
For each participant practice.py is run first to let them know what to do during the experiment and answer possible questions.
The actual trial is run by executing:
```
$ python3 experiment.py {participant-id}
```
Where participant-id is a number.

In dummy mode, the fixation information is written to the results/ folder.
In an actual experiment, the synchronisation messages would be used together with the eyetracker-log to get our necessary information.

## What is a fixation in pygaze?
A fixation is when the gaze point is relatively stable at a position for 150 ms or longer.
The allowed deviation is defined during calibration.
See also: http://www.pygaze.org/documentation/eyetracker/#EyeTracker.wait_for_fixation_start
