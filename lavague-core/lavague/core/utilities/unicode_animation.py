import os
from time import sleep
import random

term_size = 0
icons = ["  ", "🌊", "🏄", "🏄", "🏄", "🏄", "🏄", "🐬", "🦈", "🦀", "🐙", "🐟"]


def _full():
    frames = []
    waves = []
    bg = [0] * term_size
    i = 10
    iend = term_size - 1
    while iend > 0:
        line = list(bg)
        if i % 10 == 0:
            waves.append(0)
        for iw in range(len(waves)):
            line[waves[iw]] = 1
            if waves[iw] >= iend:
                continue
            waves[iw] += 1
            if waves[iw] == iend:
                iend -= 1
        frames.append(line)
        i += 1
    return frames


def _surfing():
    frames = []
    bg = [1] * term_size
    rider = random.randint(2, len(icons) - 1)
    for i in reversed(range(term_size)):
        line = list(bg)
        line[i] = rider
        frames.append(line)
    frames.append(bg)
    return frames


def _display(frames, sleep_time):
    for line in frames:
        print("".join(map(lambda x: icons[x], line)), end="\r", flush=True)
        sleep(sleep_time)


def clear_animation():
    print("  " * term_size)


def lavague_unicode_animation():
    global term_size
    term_size = os.get_terminal_size().columns // 2
    _display(_full(), 0.1)
    while True:
        _display(_surfing(), 0.1)
        sleep(random.uniform(0.5, 5))
