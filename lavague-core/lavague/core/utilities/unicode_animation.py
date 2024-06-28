import os
from time import sleep
import random

icons = ["  ", "🌊", "🏄", "🏄", "🏄", "🏄", "🏄", "🐬", "🦈", "🦀", "🐙", "🐟"]

size = os.get_terminal_size().columns // 2


def _full():
    frames = []
    waves = []
    bg = [0] * size
    i = 10
    iend = size - 1
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
    bg = [1] * size
    rider = random.randint(2, len(icons) - 1)
    for i in reversed(range(size)):
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
    print("  " * size)


def lavague_unicode_animation():
    _display(_full(), 0.1)
    while True:
        _display(_surfing(), 0.1)
        sleep(random.uniform(0.5, 5))
