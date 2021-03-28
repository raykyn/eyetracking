import argparse
import csv
import math
import sys
from typing import List, TextIO, Iterator, Tuple

import matplotlib.pyplot as plt


DataPoint = Tuple[int, float, float]
Fixation = Tuple[int, int, float, float]


def dispersion(points: List[DataPoint]) -> float:
    xs = [x for _, x, y in points]
    ys = [y for _, x, y in points]
    return (abs(max(xs) - min(xs)) + abs(max(ys) - min(ys))) / 2


def centroid(points: List[DataPoint]) -> Tuple[float, float]:
    xs = [x for _, x, y in points]
    ys = [y for _, x, y in points]
    return (sum(xs) / len(xs), sum(ys) / len(ys))


def dispersion_based_fixations(
    points: List[DataPoint], dispersion_threshold: float, duration_threshold: int
) -> Iterator[Fixation]:
    points = iter(points)
    window = []
    while True:
        try:
            while len(window) < duration_threshold:
                window.append(next(points))
            if dispersion(window) <= dispersion_threshold:
                while dispersion(window) <= dispersion_threshold:
                    window.append(next(points))
                yield (window[0][0], window[-1][0], *centroid(window))
            else:
                del window[0]
        except StopIteration:
            break


def velocity_based_fixations(
    points: List[DataPoint], max_velocity: float, time_diff: float
) -> Iterator[Fixation]:
    last_point = [None, None, None]
    current_fixation = ()

    for point in iter(points):
        if not last_point[0]:
            last_point = point
            continue
        
        distance = math.sqrt((point[1] - last_point[1])**2 + (point[2] - last_point[2])**2)
        # time_diff = point[0] - last_point[0]  # could also give sampling freq as constant instead
        # NOTE: Time diff depends on the dataset and is given as a constant now instead
        velocity = distance / time_diff

        if velocity < max_velocity:
            if current_fixation:
                # NOTE: What should the position of the fixation be? Currently set to last point.
                current_fixation = (current_fixation[0], point[0], point[1], point[2])
            else:
                # NOTE: What should the position of the fixation be? Currently set to the end point.
                current_fixation = (last_point[0], point[0], point[1], point[2])
        else:
            if current_fixation:
                yield current_fixation
                current_fixation = ()
            # NOTE: Do nothing if it's a saccade?

        last_point = point


def read_trials(file: TextIO) -> Iterator[List[DataPoint]]:
    reader = csv.reader(file)
    # Skip header
    next(reader)
    trial = []
    current_trial_id = None
    for trial_id, _, time, x_left, y_left, _, x_right, y_right, _ in reader:
        # Skip missing data points
        if not x_left or not y_left:
            continue
        if trial_id != current_trial_id:
            if current_trial_id is not None:
                yield trial
            trial = []
            current_trial_id = trial_id
        trial.append((int(time), float(x_left), float(y_left)))


def read_parameters():
    parser = argparse.ArgumentParser(description='Apply dispersion or velocity-based algorithms to a eyegaze dataset and visualize results.')
    parser.add_argument("--mode", default="dispersion", choices=["dispersion", "velocity"], help="Algorithm used for detection.")
    parser.add_argument("--freq", type=int, help="Sampling frequency of given dataset. Required for velocity-based algorithm.")
    parser.add_argument("--threshold", type=float, help="Maximum velocity threshold to differenciate saccades from fixations. Required for velocity-based algorithm.")

    return vars(parser.parse_args())

if __name__ == "__main__":
    args = read_parameters()

    trials = read_trials(sys.stdin)
    for i, trial in enumerate(trials):
        fig, ax = plt.subplots()
        ax.invert_yaxis()

        xs = [x for time, x, y in trial]
        ys = [y for time, x, y in trial]
        ax.plot(xs, ys, color="red")

        if args["mode"] == "dispersion":
            fixations = list(dispersion_based_fixations(trial, 20.0, 10))
        elif args["mode"] == "velocity":
            # NOTE: The maximum velocity parameter is highly dependent on the sampling frequency (as mentioned in the paper)
            try:
                fixations = list(velocity_based_fixations(trial, args["threshold"], 1000 / args["freq"]))
            except TypeError:
                print("Velocity-based mode needs optional arguments 'threshold' and 'freq'! See --help for more.")
                exit()
        else:
            mode = args["mode"]
            print(f"Detection mode {mode} not recognized.")

        xs = [x for start_time, end_time, x, y in fixations]
        ys = [y for start_time, end_time, x, y in fixations]
        ax.plot(xs, ys, color="blue")
        for start_time, end_time, x, y in fixations:
            c = plt.Circle((x, y), radius=(end_time - start_time) / 100, color="blue")
            ax.add_patch(c)
        plt.savefig(f"trial{i}.png")
