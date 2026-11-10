"""Host-side checks for the slide switch and onSwitch."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def load_framework():
    spec = importlib.util.spec_from_file_location(
        'switch_test_framework',
        Path(__file__).resolve().parents[1] / 'cmu_playground.py')
    module = importlib.util.module_from_spec(spec)
    names = ('board', 'digitalio', 'touchio', 'neopixel', 'audioio',
             'audiocore', 'supervisor')
    with patch.dict(sys.modules, {name: ModuleType(name) for name in names}):
        spec.loader.exec_module(module)
    return module


framework = load_framework()


class SlideSwitchTests(unittest.TestCase):
    def setUp(self):
        self.hw = SimpleNamespace(
            pads=[], buttons=[], padNames=(), buttonNames=(),
            switch=SimpleNamespace(value=True),
            readPads=lambda out: None, readButtons=lambda out: None,
            showPixels=lambda frame: None, soundPlaying=lambda: False,
            toneFrequency=None, wave=None, shutdown=lambda: None)
        hardware = patch.object(framework, 'Hardware', return_value=self.hw)
        hardware.start()
        self.addCleanup(hardware.stop)
        ticks = patch.object(framework.supervisor, 'ticks_ms',
                             return_value=0, create=True)
        ticks.start()
        self.addCleanup(ticks.stop)
        self.addCleanup(setattr, framework, '_runtime', None)
        self.events = []

    def make(self, **handlers):
        runtime = framework.Runtime(SimpleNamespace(**handlers))
        framework._runtime = runtime
        return runtime

    def test_onSwitch_is_a_callback(self):
        self.assertIn('onSwitch', framework.CALLBACK_NAMES)

    def test_reports_starting_position_after_onAppStart(self):
        def onAppStart(app):
            self.events.append('start')

        def onSwitch(app, isOn):
            self.events.append(isOn)
            app.running = False

        self.make(onAppStart=onAppStart, onSwitch=onSwitch).run()
        self.assertEqual(self.events, ['start', True])

    def test_runs_only_when_switch_moves(self):
        runtime = self.make(onSwitch=lambda app, isOn: self.events.append(isOn))
        runtime.switchState = True
        self.assertFalse(runtime.pollInputs())
        self.hw.switch.value = False
        self.assertTrue(runtime.pollInputs())
        self.assertFalse(runtime.pollInputs())
        self.hw.switch.value = True
        self.assertTrue(runtime.pollInputs())
        self.assertEqual(self.events, [False, True])

    def test_onSwitch_may_change_app(self):
        def onSwitch(app, isOn):
            app.on = isOn

        runtime = self.make(onSwitch=onSwitch)
        runtime.switchState = True
        self.hw.switch.value = False
        runtime.pollInputs()
        self.assertIs(runtime.app.on, False)

    def test_missing_onSwitch_tracks_state_without_change(self):
        runtime = self.make()
        self.hw.switch.value = False
        self.assertFalse(runtime.pollInputs())
        self.assertIs(runtime.switchState, False)


if __name__ == '__main__':
    unittest.main()
