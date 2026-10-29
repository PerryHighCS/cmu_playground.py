# cmu_playground API

`cmu_playground` lets you program the Circuit Playground Express the way you
program in CMU CS Academy: you write event functions, and the framework calls
them when things happen.

Your program has three parts:

- **Model**: the `app` object, which holds your program's state.
- **Controllers**: event functions such as `onTouch` and `onStep`, which
  change the model.
- **View**: `updateAll(app)`, which reads the model and sets the LEDs and
  sound.

## A complete program

```python
from cmu_playground import *

def onAppStart(app):
    app.score = 0
    app.color = 'blue'

def onTouch(app, pad):
    app.score += 1
    app.color = 'green'

def onTouchRelease(app, pad):
    app.color = 'blue'

def updateAll(app):
    setAllLeds(app.color)

def main():
    runApp()

main()
```

Save it as `code.py` on the `CIRCUITPY` drive. The board restarts and runs it.

## Starting the app

### `runApp()`

Starts your program. Call it once, at the end of `code.py`. You don't pass
it anything: it finds your event functions by name.

`runApp()` keeps running until `app.running` is set to `False` or an error
stops the program.

## Event functions

Define only the ones you need. Every one receives `app` first.

| Function | When it runs |
|---|---|
| `onAppStart(app)` | Once, when the program starts |
| `onTouch(app, pad)` | A touch pad is touched |
| `onTouchRelease(app, pad)` | A touch pad is let go |
| `onButtonPress(app, button)` | Button A or B is pressed |
| `onButtonRelease(app, button)` | Button A or B is released |
| `onStep(app)` | `app.stepsPerSecond` times per second |
| `updateAll(app)` | After the events above, to update the LEDs and sound |

### `onAppStart(app)`

Set up your model here. Any attribute you want to read later should get a
starting value in `onAppStart`.

```python
def onAppStart(app):
    app.score = 0
    app.stepsPerSecond = 5
```

### `onTouch(app, pad)` and `onTouchRelease(app, pad)`

`pad` is a string naming the pad: `'A1'`, `'A2'`, `'A3'`, `'A4'`, `'A5'`,
`'A6'`, or `'A7'`. The pad labeled TX is `'A7'`.

Holding a pad does not repeat `onTouch`. You get one `onTouch` when the touch
starts and one `onTouchRelease` when it ends.

```python
def onTouch(app, pad):
    if pad == 'A1':
        app.score += 1
```

The pads calibrate themselves when the program starts, so don't touch them
while the board is restarting.

### Touch calibration

These functions use the same pad names, `'A1'` through `'A7'` (TX).
Readings and thresholds come directly from CircuitPython's
[`touchio.TouchIn`](https://docs.circuitpython.org/en/latest/shared-bindings/touchio/index.html).
A pad counts as touched when its raw reading is **greater than** its
threshold. A lower threshold makes it more sensitive; a higher threshold
makes it less sensitive.

| Function | What it does |
|---|---|
| `getTouchRawValue(pad)` | Reads the current raw measurement |
| `getTouchThreshold(pad)` | Reads the current threshold |
| `setTouchThreshold(pad, threshold)` | Sets an absolute threshold |
| `calibrateTouch(pad=None, offset=100)` | Sets the threshold to a fresh raw reading plus `offset`; omit `pad` to calibrate all seven pads |

Call these functions while the app is running. Readings are allowed in any
callback. Set thresholds and calibrate only in event functions, such as
`onAppStart` or `onButtonPress`, because they change how inputs behave.
Thresholds and offsets must be integers from `0` to `65535`; the calibrated
threshold must also fit that range. Invalid calibration values leave all
thresholds unchanged.

Keep your fingers off the pads and any attached conductive objects during
calibration. Attach wires or foil before calibrating. Each pad is sampled
once, using the same reading-plus-offset approach as startup calibration.
The default offset is `100`; a larger offset reduces sensitivity.

```python
def onAppStart(app):
    calibrateTouch(offset=200)  # all pads, after attaching wires or foil

def onButtonPress(app, button):
    if button == 'B':
        calibrateTouch()       # recalibrate with all pads untouched
    elif button == 'A':
        print(getTouchRawValue('A1'), getTouchThreshold('A1'))
```

For manual tuning, use `setTouchThreshold('A1', 1500)` with a value chosen
from your own untouched and touched readings. Changes take effect on the
next input poll and can cause a touch or release event. Calibration does
not reset the event history. Settings last until changed or the program
restarts.

### `onButtonPress(app, button)` and `onButtonRelease(app, button)`

`button` is `'A'` or `'B'`. Like touch, holding a button does not repeat the
event.

```python
def onButtonPress(app, button):
    if button == 'B':
        app.score = 0
```

A pad or button that is already held when the program starts does not cause
an event.

### `onStep(app)`

Runs over and over, `app.stepsPerSecond` times per second. Use it for
anything that changes over time: animations, timers, blinking.

```python
def onStep(app):
    app.counter += 1
```

If your code is too slow to keep up, missed steps are skipped, not saved up
for later.

### `updateAll(app)`

Draws the model onto the board. It runs once after `onAppStart`, and again
after any event function runs. If nothing happens, it doesn't run.

```python
def updateAll(app):
    setAllLeds(app.color)
```

Inside `updateAll`:

- You can read `app`, but you can't change it.
- All the LEDs start off. Turn on every LED you want lit, every time.

## The `app` object

You can add any attributes you like to `app`. These three are built in:

| Attribute | Default | Meaning |
|---|---|---|
| `app.stepsPerSecond` | `10` | How often `onStep` runs |
| `app.elapsedTime` | `0` | Seconds since the program started (read only) |
| `app.running` | `True` | Set to `False` to stop the program |

### `app.stepsPerSecond`

Any number zero or larger. `0` turns `onStep` off, but touch and button
events still work. When you change it, the next step comes one new interval
later.

### `app.elapsedTime`

Seconds since the program started, as a decimal number like `3.25`. It keeps
counting on its own; you can read it in any function but can't set it.

```python
def onTouch(app, pad):
    app.touchTime = app.elapsedTime
```

### `app.running`

Set it to `False` to stop the program. The LEDs turn off and the speaker goes
quiet.

```python
def onButtonPress(app, button):
    if button == 'A':
        app.running = False
```

## LEDs

The board has 10 LEDs, numbered `0` through `9`. You can only use these
functions inside `updateAll(app)`.

### `setLed(index, color)`

Sets one LED. `index` is a whole number from `0` to `9`.

```python
setLed(0, 'red')
```

### `setAllLeds(color)`

Sets all 10 LEDs to one color.

### `clearLeds()`

Turns all the LEDs off. Each `updateAll` already starts with the LEDs off,
so you only need this to turn them off partway through.

### Colors

A color is either a name or an RGB tuple.

**Names** (capital letters are fine):
`'red'`, `'green'`, `'blue'`, `'yellow'`, `'orange'`, `'purple'`, `'pink'`,
`'white'`, `'black'`, `'gold'`

`'black'` means off.

**RGB tuples** are three whole numbers from `0` to `255`, for red, green and
blue, in parentheses:

```python
setLed(3, (255, 100, 0))   # orange-ish
```

The LEDs run at low brightness, so `255` won't be blinding.

## Sound

The board plays one sound at a time. You can only use these functions inside
`updateAll(app)`.

### `playTone(frequency)`

Plays a steady tone. `frequency` is in hertz, from `20` to `4000`. For
example, `440` is the note A.

The tone keeps playing until a later `updateAll` asks for something else. If
`updateAll` asks for the same tone again, it keeps going smoothly instead of
restarting.

Every time `updateAll` runs, it decides what you hear. If an `updateAll`
doesn't call `playTone`, the tone stops. So store the tone in the model and
call `playTone` every time:

```python
def onAppStart(app):
    app.frequency = None

def onTouch(app, pad):
    app.frequency = 440

def onTouchRelease(app, pad):
    app.frequency = None

def updateAll(app):
    if app.frequency is None:
        stopTone()
    else:
        playTone(app.frequency)
```

### `stopTone()`

Asks for silence. Leaving out `playTone` does the same thing, but `stopTone`
makes your intent clear.

### `playSound(filename)`

Plays a `.wav` file saved on the `CIRCUITPY` drive, such as
`playSound('beep.wav')`. Use uncompressed WAV files. 16-bit mono at 22,050 Hz
or lower works well.

A sound plays **once** when `updateAll` starts asking for it. It does not
restart while later `updateAll` calls keep asking for it. To play it again,
have one `updateAll` stop asking, then ask again. A simple way is to request
it while a pad is touched:

```python
def onAppStart(app):
    app.ding = False

def onTouch(app, pad):
    app.ding = True

def onTouchRelease(app, pad):
    app.ding = False

def updateAll(app):
    if app.ding:
        playSound('ding.wav')
```

A sound file interrupts a tone. When the sound finishes, the tone comes back
if `updateAll` is still asking for it.

## Rules and errors

The framework stops your program with an error message when a rule is
broken. The message appears in the serial console.

| What you did | Error |
|---|---|
| Called an LED or sound function outside `updateAll` | `MVCError` |
| Changed `app` inside `updateAll` | `MVCError` |
| Called a touch helper before `runApp`, or changed calibration outside an event function | `MVCError` |
| Used a touch pad name other than `'A1'` through `'A7'` | `ValueError` |
| Used a non-integer touch threshold or offset | `TypeError` |
| Used a touch threshold, offset, or calibrated result outside 0 to 65535 | `ValueError` |
| Read an `app` attribute you never set | `AttributeError` |
| Set `app.elapsedTime` | `AttributeError` |
| Set `app.stepsPerSecond` to something that isn't a number | `TypeError` |
| Set `app.stepsPerSecond` below zero | `ValueError` |
| Used an LED index outside 0 to 9 | `IndexError` |
| Used an unknown color name or a bad RGB value | `ValueError` |
| Used a tone frequency outside 20 to 4000 | `ValueError` |
| Passed `playSound` something that isn't a string | `TypeError` |
| Asked `playSound` for a file that doesn't exist | `ValueError` |
| Named a variable `onTouch` (or another event name) that isn't a function | `TypeError` |

Errors in your own code, such as a misspelled variable, show up as normal
Python errors with the line number in your `code.py`.

When the program stops, for any reason, the LEDs turn off and the speaker
goes quiet.

### Lists and dictionaries in the model

Changing a list or dictionary inside `updateAll`, as in
`app.scores.append(5)`, is against the rules even though the framework can't
catch it. Do all changes in your event functions.

## Board setup

The `CIRCUITPY` drive needs:

```text
CIRCUITPY/
    code.py              your program
    cmu_playground.mpy   the framework
```

Don't put `cmu_playground.py` (the source file) on the drive. The board
would try to load it instead of the `.mpy`, and run out of memory.

The board has very little memory. Long programs can stop with a
`MemoryError`. If that happens, make your program shorter or simpler.

### Freeze the framework into firmware

An `.mpy` on `CIRCUITPY` still loads its bytecode into RAM. Freezing
`cmu_playground` into a custom CircuitPython firmware keeps that bytecode
in flash. Runtime objects, dictionaries, the app model, and audio buffers
still need RAM. The exact savings need to be measured on the board.

The repository includes a manual GitHub Actions build for Circuit Playground
Express and CircuitPython **10.3.1**, matching `build.cmd`:

1. Push these build files and the current `cmu_playground.py` to GitHub.
2. Open **Actions → Build frozen Circuit Playground firmware → Run workflow**.
3. After a successful build, download and unzip the
   **cmu-playground-cpx-10.3.1** artifact.
4. Back up the files on `CIRCUITPY`. Double-press the board's reset button
   to open `CPLAYBOOT`, then copy `cmu-playground-cpx-10.3.1.uf2` onto it.
5. Once `CIRCUITPY` returns, remove any `cmu_playground.py` and
   `cmu_playground.mpy` from its root and `lib` directory. Files on the
   filesystem can shadow the frozen module. Keep your student `code.py`.

Use the same import in `code.py`: `from cmu_playground import *`.
On frozen firmware, copy just your app to `code.py`; `deploy.cmd` installs
the standalone `.mpy` again, so use it only with stock firmware.
Changes to the frozen framework require rebuilding and flashing the UF2.

This custom firmware disables `countio` (hardware pulse counting) to make
room in internal flash for the framework. The framework does not use it;
touch, buttons, LEDs, tones, and WAV playback keep their required modules.
Programs that import `countio` will need a different firmware configuration.

To confirm freezing at the serial REPL, run `help('modules')` and look
for `cmu_playground` after removing the filesystem copies. To compare RAM,
run this after a fresh restart with each firmware:

```python
import gc
gc.collect()
before = gc.mem_free()
import cmu_playground
gc.collect()
print('free:', gc.mem_free(), 'import used:', before - gc.mem_free())
```

For a local Linux/WSL build, follow
[CircuitPython's build setup](https://docs.circuitpython.org/en/latest/BUILDING.html),
activate the environment with its `requirements-dev.txt` installed, put ARM
GCC 14 or newer on `PATH` (the workflow uses 15.2.Rel1, matching upstream CI),
and run:

```bash
git clone --branch 10.3.1 https://github.com/adafruit/circuitpython.git
bash tools/build_frozen.sh circuitpython
```

Use a dedicated CircuitPython checkout: the script adds a frozen-module
directory and a supplemental build configuration, preserving its
existing frozen libraries. Dependencies are fetched for the Express board
rather than the entire SAMD port. Upstream's board fetch still includes
some shared port dependencies. The output goes in `firmware/`. The compiler
must successfully link the firmware to confirm that it fits the board's
internal flash. This build setup has not yet been compiled or tested on
hardware.

See [Adafruit's frozen-module guide](https://learn.adafruit.com/building-circuitpython/adding-frozen-modules)
for how this saves RAM.
