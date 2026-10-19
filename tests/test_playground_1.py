import gc
gc.collect(); f0 = gc.mem_free()
from cmu_playground import *
import cmu_playground
gc.collect(); print('free after import', gc.mem_free(), 'cost', f0 - gc.mem_free())

log = []
def onAppStart(app):
    app.stepsPerSecond = 10
    app.steps = 0
    app.starts = getattr(app, 'starts', 0) + 1 if False else 1
    log.append(('start', id(app)))
    global T1app; T1app = app
def onStep(app):
    app.steps += 1
    if app.steps == 1:
        log.append(('step', id(app)))
    if app.elapsedTime >= 2:
        app.running = False
def updateAll(app):
    setAllLeds('blue'); setLed(0, (255, 100, 0))
    playTone(440)
    if app.steps == 5:
        gc.collect(); log.append(('free in loop', gc.mem_free()))
runApp()
print('T1 log:', log)
print('  same app:', log[0][1] == log[1][1], 'steps in 2s @10sps:', T1app.steps)

def expect(label, exc):
    try:
        runApp()
        print(label, 'FAIL: no error')
    except exc as e:
        print(label, 'ok:', type(e).__name__, e)
    except Exception as e:
        print(label, 'FAIL other:', type(e).__name__, e)

def updateAll(app): pass
def onStep(app): setLed(0, 'red')
expect('T2 setLed in controller', MVCError)
def onStep(app): app.running = False
def updateAll(app): app.score = 1
expect('T3 assign in view', MVCError)
def updateAll(app): pass
def onAppStart(app): app.elapsedTime = 3
expect('T4 elapsedTime write', AttributeError)
def onAppStart(app): app.stepsPerSecond = -1
expect('T5 negative sps', ValueError)
def onAppStart(app): pass
def onAppStart(app): app.score = 0
def onStep(app): app.score += missingVariable
expect('T6 NameError preserved', NameError)
def onAppStart(app): pass
def onStep(app): app.running = False
def updateAll(app): setAllLeds('chartreuse')
expect('T7 bad color', ValueError)
def updateAll(app): setLed(10, 'red')
expect('T8 bad index', IndexError)
def updateAll(app): setLed(0, (300, 0, 0))
expect('T9 bad rgb', ValueError)
onTouch = 5
expect('T10 non-callable handler', TypeError)
del onTouch
try:
    setLed(0, 'red'); print('T11 FAIL')
except MVCError as e: print('T11 setLed outside app ok:', e)

