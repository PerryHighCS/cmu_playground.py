from cmu_playground import *
import math

# How many LEDs are in the spinning band (1 to 6).
BAND_SIZE = 4

# Seconds for one full pulse, dim -> bright -> dim.
PULSE_SECONDS = 1.5


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
    else:
        app.mode = pressed


def onStep(app):
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


def main():
    runApp()

main()
