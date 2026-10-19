import gc
gc.collect(); f0 = gc.mem_free()
from cmu_playground import *
import cmu_playground
# T12: tone not restarted on unchanged requests; sps=0 disables steps
starts = [0]
orig = cmu_playground.Hardware.startTone
def counting(self, f):
    starts[0] += 1; orig(self, f)
cmu_playground.Hardware.startTone = counting
def onAppStart(app):
    app.stepsPerSecond = 20; app.n = 0; app.freq = 440
def onStep(app):
    app.n += 1
    if app.n == 10: app.freq = 660
    if app.n == 20: app.freq = None
    if app.n == 30: app.running = False
def updateAll(app):
    if app.freq is None: stopTone()
    else: playTone(app.freq)
runApp()
print('T12 tone starts (expect 2):', starts[0])
cmu_playground.Hardware.startTone = orig

def onAppStart(app):
    app.stepsPerSecond = 0; app.n = 0; app.t0 = app.elapsedTime
def onStep(app): app.n += 1
log = []
def updateAll(app): log.append(app.n)
import time
def onTouch(app, pad): pass
# run for 1s with sps=0 by stopping from outside is not possible; use a timer via onTouchRelease? Instead patch tick:
orig_tick = cmu_playground.Runtime.tick
def tick(self):
    e = orig_tick(self)
    if e > 1000: self.app.running = False
    return e
cmu_playground.Runtime.tick = tick
runApp()
print('T13 sps=0 steps (expect 0):', log)
cmu_playground.Runtime.tick = orig_tick
gc.collect(); print('free end', gc.mem_free())
