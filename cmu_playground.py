# cmu_playground.py - Circuit Playground Event Framework (spec v0.2)
#
# Students write callbacks in code.py and call runApp(). The runtime owns
# the App, polls the sensors, dispatches events, and applies the view.
#
#   Controllers (onAppStart, onTouch, onStep, ...) change the model.
#   updateAll(app) reads the model and drives LEDs and sound.
#
# The SAMD21 cannot compile this file in its 32 KB of RAM, so the board
# runs a precompiled CIRCUITPY/cmu_playground.mpy. After editing, rebuild it
# with build.cmd, which uses the mpy-cross matching CircuitPython 10.3.1.
# Keep cmu_playground.py out of the board's root, or it shadows the .mpy.

import array
import math
import board
import digitalio
import touchio
import neopixel
import audioio
import audiocore
import supervisor

__all__ = ('runApp', 'setLed', 'setAllLeds', 'clearLeds',
           'playTone', 'stopTone', 'playSound', 'MVCError')

CALLBACK_NAMES = ('onAppStart', 'onTouch', 'onTouchRelease',
                  'onButtonPress', 'onButtonRelease', 'onStep', 'updateAll')

COLORS = {
    'red': (255, 0, 0), 'green': (0, 255, 0), 'blue': (0, 0, 255),
    'yellow': (255, 255, 0), 'orange': (255, 80, 0),
    'purple': (128, 0, 255), 'pink': (255, 40, 120),
    'white': (255, 255, 255), 'black': (0, 0, 0), 'gold': (255, 160, 0),
}

BLACK = (0, 0, 0)
BRIGHTNESS = 0.1
NUM_LEDS = 10
TONE_VOLUME = 0x3FFF

# Execution phases
INTERNAL = 0
CONTROLLER = 1
VIEW = 2

_runtime = None


class MVCError(Exception):
    pass


# supervisor.ticks_ms() wraps every 2**29 ms, so compare ticks with this.
def _ticksDiff(a, b):
    return ((a - b + 0x10000000) & 0x1FFFFFFF) - 0x10000000


# ---------------------------------------------------------------- Model

class App:
    def __init__(self):
        object.__setattr__(self, 'stepsPerSecond', 10)
        object.__setattr__(self, 'running', True)

    def __setattr__(self, name, value):
        if _runtime.phase == VIEW:
            raise MVCError('updateAll(app) may not change the model '
                           '(tried to set app.' + name + ')')
        if name == 'elapsedTime':
            raise AttributeError('app.elapsedTime is read only')
        if name == 'stepsPerSecond':
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                raise TypeError('app.stepsPerSecond must be a number')
            if value < 0:
                raise ValueError('app.stepsPerSecond cannot be negative')
            _runtime.stepsChanged = True
        object.__setattr__(self, name, value)

    def __getattr__(self, name):
        # Only called for attributes that were never set.
        if name == 'elapsedTime':
            return _runtime.elapsedSeconds()
        raise AttributeError('app has no attribute ' + repr(name) +
                             ' (set it in onAppStart first)')


# ----------------------------------------------------------- Discovery

def discoverCallbacks(namespace):
    handlers = {}
    for name in CALLBACK_NAMES:
        try:
            callback = getattr(namespace, name)
        except AttributeError:
            continue
        if not callable(callback):
            raise TypeError(name + ' must be a function')
        handlers[name] = callback
    return handlers


# ------------------------------------------------------------ Hardware

class Hardware:
    def __init__(self):
        self.pixels = neopixel.NeoPixel(board.NEOPIXEL, NUM_LEDS,
                                        brightness=BRIGHTNESS,
                                        auto_write=False)
        self.pixels.fill(BLACK)
        self.pixels.show()

        # TX is the pad labeled A7. A0 is the speaker output, not a pad.
        self.padNames = ('A1', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7')
        self.pads = [touchio.TouchIn(pin) for pin in
                     (board.A1, board.A2, board.A3, board.A4,
                      board.A5, board.A6, board.TX)]

        self.buttonNames = ('A', 'B')
        self.buttons = []
        for pin in (board.BUTTON_A, board.BUTTON_B):
            button = digitalio.DigitalInOut(pin)
            button.switch_to_input(pull=digitalio.Pull.DOWN)
            self.buttons.append(button)

        self.speakerEnable = digitalio.DigitalInOut(board.SPEAKER_ENABLE)
        self.speakerEnable.switch_to_output(value=False)
        self.audio = audioio.AudioOut(board.SPEAKER)
        self.toneFrequency = None   # tone currently sounding
        self.wave = None            # WaveFile currently playing
        self.waveFile = None

    def readPads(self, out):
        pads = self.pads
        for i in range(len(pads)):
            out[i] = pads[i].value

    def readButtons(self, out):
        buttons = self.buttons
        for i in range(len(buttons)):
            out[i] = buttons[i].value

    def showPixels(self, frame):
        pixels = self.pixels
        for i in range(NUM_LEDS):
            pixels[i] = frame[i]
        pixels.show()

    # Audio: one source at a time. A sound file preempts the tone; the
    # requested tone resumes once the sound file finishes.

    def startTone(self, frequency):
        self.stopAudio()
        # One sine cycle, played at length * frequency samples per second,
        # gives an exact pitch with a small buffer.
        length = max(8, min(32, 64000 // frequency))
        wave = array.array('H', [0] * length)
        for i in range(length):
            wave[i] = int((1 + math.sin(math.pi * 2 * i / length)) *
                          TONE_VOLUME)
        sample = audiocore.RawSample(wave, sample_rate=length * frequency)
        self.speakerEnable.value = True
        self.audio.play(sample, loop=True)
        self.toneFrequency = frequency

    def startSound(self, filename):
        self.stopAudio()
        try:
            f = open(filename, 'rb')
        except OSError:
            raise ValueError('sound file not found: ' + repr(filename))
        self.waveFile = f
        self.wave = audiocore.WaveFile(f)
        self.speakerEnable.value = True
        self.audio.play(self.wave)

    def soundPlaying(self):
        return self.wave is not None and self.audio.playing

    def stopAudio(self):
        if self.audio.playing:
            self.audio.stop()
        self.toneFrequency = None
        if self.waveFile is not None:
            self.waveFile.close()
            self.waveFile = None
            self.wave = None
        self.speakerEnable.value = False

    def shutdown(self):
        # Leave the speaker silent and the LEDs dark, then release the pins.
        try:
            self.stopAudio()
        finally:
            self.pixels.fill(BLACK)
            self.pixels.show()
            for device in self.pads + self.buttons + [
                    self.audio, self.speakerEnable, self.pixels]:
                device.deinit()


# -------------------------------------------------------------- Runtime

class Runtime:
    def __init__(self, namespace):
        self.phase = INTERNAL
        self.stepsChanged = True
        self.lastTick = supervisor.ticks_ms()
        self.elapsedMs = 0

        self.app = App()
        handlers = discoverCallbacks(namespace)
        self.onAppStart = handlers.get('onAppStart')
        self.onTouch = handlers.get('onTouch')
        self.onTouchRelease = handlers.get('onTouchRelease')
        self.onButtonPress = handlers.get('onButtonPress')
        self.onButtonRelease = handlers.get('onButtonRelease')
        self.onStep = handlers.get('onStep')
        self.updateAll = handlers.get('updateAll')

        self.hw = Hardware()

        # View state, rebuilt on every view update
        self.frame = [BLACK] * NUM_LEDS
        self.shownFrame = [BLACK] * NUM_LEDS
        self.toneRequest = None
        self.soundRequest = None
        self.lastSoundRequest = None

        # Input state, preallocated so polling does not allocate
        self.padState = [False] * len(self.hw.pads)
        self.padNow = [False] * len(self.hw.pads)
        self.buttonState = [False] * len(self.hw.buttons)
        self.buttonNow = [False] * len(self.hw.buttons)

    # -- timing

    def tick(self):
        now = supervisor.ticks_ms()
        self.elapsedMs += _ticksDiff(now, self.lastTick)
        self.lastTick = now
        return self.elapsedMs

    def elapsedSeconds(self):
        now = supervisor.ticks_ms()
        return (self.elapsedMs + _ticksDiff(now, self.lastTick)) / 1000

    # -- dispatch

    def callController(self, callback, *args):
        self.phase = CONTROLLER
        try:
            callback(self.app, *args)
        finally:
            self.phase = INTERNAL

    def view(self):
        frame = self.frame
        for i in range(NUM_LEDS):
            frame[i] = BLACK
        self.toneRequest = None
        self.soundRequest = None

        if self.updateAll is not None:
            self.phase = VIEW
            try:
                self.updateAll(self.app)
            finally:
                self.phase = INTERNAL

        if frame != self.shownFrame:
            self.hw.showPixels(frame)
            self.shownFrame[:] = frame

        # A sound plays when it is newly requested; requesting the same
        # sound on consecutive view updates does not restart it.
        sound = self.soundRequest
        if sound is not None and sound != self.lastSoundRequest:
            self.hw.startSound(sound)
        self.lastSoundRequest = sound
        self.serviceAudio()

    def serviceAudio(self):
        hw = self.hw
        if hw.soundPlaying():
            return
        tone = self.toneRequest
        if tone != hw.toneFrequency or hw.wave is not None:
            if tone is None:
                hw.stopAudio()
            else:
                hw.startTone(tone)

    def pollInputs(self):
        changed = False
        app = self.app

        now = self.padNow
        state = self.padState
        self.hw.readPads(now)
        for i in range(len(now)):
            if now[i] != state[i]:
                state[i] = now[i]
                callback = self.onTouch if now[i] else self.onTouchRelease
                if callback is not None:
                    self.callController(callback, self.hw.padNames[i])
                    changed = True
                    if not app.running:
                        return changed

        now = self.buttonNow
        state = self.buttonState
        self.hw.readButtons(now)
        for i in range(len(now)):
            if now[i] != state[i]:
                state[i] = now[i]
                callback = (self.onButtonPress if now[i]
                            else self.onButtonRelease)
                if callback is not None:
                    self.callController(callback, self.hw.buttonNames[i])
                    changed = True
                    if not app.running:
                        return changed
        return changed

    # -- main loop

    def run(self):
        app = self.app
        try:
            if self.onAppStart is not None:
                self.callController(self.onAppStart)

            # Whatever is held at startup is the baseline, not an event.
            self.hw.readPads(self.padState)
            self.hw.readButtons(self.buttonState)

            self.view()

            interval = 0
            nextStep = 0
            while app.running:
                elapsed = self.tick()
                changed = self.pollInputs()

                if self.stepsChanged:
                    self.stepsChanged = False
                    sps = app.stepsPerSecond
                    interval = int(1000 / sps) if sps > 0 else 0
                    nextStep = elapsed + interval

                if (interval > 0 and self.onStep is not None
                        and app.running and elapsed >= nextStep):
                    self.callController(self.onStep)
                    changed = True
                    nextStep += interval
                    if nextStep <= elapsed:
                        # Fell behind: skip missed steps, no backlog.
                        nextStep = elapsed + interval

                if changed:
                    self.view()
                else:
                    self.serviceAudio()
        finally:
            self.phase = INTERNAL
            self.hw.shutdown()


# ------------------------------------------------------------ Public API

def runApp():
    global _runtime
    if _runtime is not None:
        raise RuntimeError('runApp() is already running')
    import __main__
    _runtime = Runtime(__main__)
    try:
        _runtime.run()
    finally:
        _runtime = None


def _checkView(name):
    if _runtime is None or _runtime.phase != VIEW:
        raise MVCError(name + '() can only be called from updateAll(app)')


def _toRGB(color):
    if isinstance(color, str):
        try:
            return COLORS[color.lower()]
        except KeyError:
            raise ValueError('unknown color ' + repr(color))
    if isinstance(color, tuple) and len(color) == 3:
        for c in color:
            if (not isinstance(c, int) or isinstance(c, bool)
                    or not 0 <= c <= 255):
                raise ValueError('RGB values must be integers from 0 to '
                                 '255, got ' + repr(color))
        return color
    raise ValueError("color must be a name like 'red' or an (r, g, b) "
                     'tuple, got ' + repr(color))


def setLed(index, color):
    _checkView('setLed')
    if (not isinstance(index, int) or isinstance(index, bool)
            or not 0 <= index < NUM_LEDS):
        raise IndexError('LED index must be 0 to 9, got ' + repr(index))
    _runtime.frame[index] = _toRGB(color)


def setAllLeds(color):
    _checkView('setAllLeds')
    rgb = _toRGB(color)
    frame = _runtime.frame
    for i in range(NUM_LEDS):
        frame[i] = rgb


def clearLeds():
    _checkView('clearLeds')
    frame = _runtime.frame
    for i in range(NUM_LEDS):
        frame[i] = BLACK


def playTone(frequency):
    _checkView('playTone')
    if (not isinstance(frequency, (int, float)) or isinstance(frequency, bool)
            or not 20 <= frequency <= 4000):
        raise ValueError('tone frequency must be 20 to 4000 Hz, got ' +
                         repr(frequency))
    _runtime.toneRequest = int(frequency)


def stopTone():
    _checkView('stopTone')
    _runtime.toneRequest = None


def playSound(filename):
    _checkView('playSound')
    if not isinstance(filename, str):
        raise TypeError("playSound() needs a file name like 'beep.wav'")
    _runtime.soundRequest = filename
