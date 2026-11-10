from cmu_playground import *
import math

# How many LEDs are in the spinning band (1 to 6).
BAND_SIZE = 4

# Seconds for one full pulse, dim -> bright -> dim.
PULSE_SECONDS = 1.5

# Sounds are lists of (frequency, steps) notes. A frequency of 0 is a rest.
# At 10 steps per second, 1 step is 0.1 seconds.
HAND_SOUND = [(784, 2), (1047, 4)]                # gentle chime
HELP_SOUND = [(1568, 1), (0, 1), (1568, 1), (0, 1), (1568, 1)]  # 3 beeps


def hueToRgb(hue):
    # hue goes from 0 to 1 around the rainbow (full saturation and value).
    sector = int(hue * 6) % 6
    fraction = hue * 6 - int(hue * 6)
    up = int(255 * fraction)
    down = 255 - up
    return [(255, up, 0), (down, 255, 0), (0, 255, up),
            (0, down, 255), (up, 0, 255), (255, 0, down)][sector]


def onAppStart(app):
    app.stepsPerSecond = 10
    app.switchOn = False

    # Each LED in the band gets its own color, spread across the rainbow.
    app.bandColors = [hueToRgb(i / BAND_SIZE) for i in range(BAND_SIZE)]
    app.position = 0

    app.mode = 'spin'     # 'spin', 'blue', or 'red'
    app.level = 0         # pulse brightness, 0 to 1

    app.sound = None      # the sound playing now, or None
    app.note = 0          # which note of the sound is playing
    app.noteLeft = 0      # steps left in that note


def startSound(app, sound):
    app.sound = sound
    app.note = 0
    # A button press comes partway through a step, so give the first note
    # one extra step to keep it from being cut short.
    app.noteLeft = sound[0][1] + 1


def onSwitch(app, isOn):
    app.switchOn = isOn


def onButtonPress(app, button):
    if button == 'A':
        pressed = 'blue'
    else:
        pressed = 'red'

    # Pressing the same button again goes back to spinning.
    if app.mode == pressed:
        app.mode = 'spin'
        app.sound = None
    else:
        app.mode = pressed
        if pressed == 'blue':
            startSound(app, HAND_SOUND)
        else:
            startSound(app, HELP_SOUND)


def onStep(app):
    # Move through the notes of the current sound.
    if app.sound is not None:
        app.noteLeft -= 1
        if app.noteLeft == 0:
            app.note += 1
            if app.note == len(app.sound):
                app.sound = None
            else:
                app.noteLeft = app.sound[app.note][1]

    if app.mode == 'spin':
        if app.switchOn:
            app.position = (app.position + 1) % 10
    else:
        angle = 2 * math.pi * app.elapsedTime / PULSE_SECONDS
        app.level = (1 - math.cos(angle)) / 2


def updateAll(app):
    if app.mode == 'blue':
        setAllLeds((0, 0, int(255 * app.level)))
    elif app.mode == 'red':
        setAllLeds((int(255 * app.level), 0, 0))
    elif app.switchOn:
        for i in range(BAND_SIZE):
            setLed((app.position + i) % 10, app.bandColors[i])

    if app.sound is not None:
        frequency = app.sound[app.note][0]
        if frequency > 0:
            playTone(frequency)


def main():
    runApp()

main()
