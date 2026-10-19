from cmu_playground import *

def onAppStart(app):
    app.stepsPerSecond = 10
    app.score = 0
    app.color = 'blue'
    app.frequency = None

def onTouch(app, pad):
    app.score += 1
    app.color = 'green'
    app.frequency = 440

def onTouchRelease(app, pad):
    app.color = 'blue'
    app.frequency = None

def onStep(app):
    if app.score >= 10:
        app.color = 'gold'

def updateAll(app):
    setAllLeds(app.color)

    if app.frequency is None:
        stopTone()
    else:
        playTone(app.frequency)

def main():
    runApp()

main()
