# The rainbow and rising beeps from Adafruit's Circuit Playground
# Express test sketch. The LEDs fill with a rainbow one at a time, with a
# higher beep for each LED. Slide the switch right to hear the beeps.
from cmu_playground import *

# How often the next LED lights, in steps of 1/20 second.
STEPS_PER_LED = 5

# Each beep lasts this many steps (1 step = 50 ms).
BEEP_STEPS = 1


def colorWheel(position):
    # Adafruit's colorWheel: position 0 to 255 goes around the rainbow.
    position = 255 - position
    if position < 85:
        return (255 - position * 3, 0, position * 3)
    if position < 170:
        position -= 85
        return (0, position * 3, 255 - position * 3)
    position -= 170
    return (position * 3, 255 - position * 3, 0)


def onAppStart(app):
    app.stepsPerSecond = 20
    app.soundOn = False
    app.lit = 0          # how many LEDs are lit, 0 to 10
    app.counter = 0      # steps since the last LED lit
    app.frequency = 500
    app.beepLeft = 0     # steps left in the current beep


def onSwitch(app, isOn):
    # The original only beeps when the switch is slid right.
    app.soundOn = not isOn


def onStep(app):
    if app.beepLeft > 0:
        app.beepLeft -= 1

    app.counter += 1
    if app.counter < STEPS_PER_LED:
        return
    app.counter = 0

    # Light one more LED. After the 10th, clear them all and start over.
    app.lit += 1
    if app.lit > 10:
        app.lit = 0

    # The pitch climbs with each LED: 1000, 1500, ... 5500, then 500.
    app.frequency = 500 * (app.lit + 1)
    app.beepLeft = BEEP_STEPS


def updateAll(app):
    for i in range(app.lit):
        setLed(i, colorWheel(25 * (i + 1)))

    if app.soundOn and app.beepLeft > 0:
        playTone(app.frequency)
    else:
        stopTone()


def main():
    runApp()

main()
