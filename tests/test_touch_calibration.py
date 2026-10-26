"""Host-side checks: python -m unittest discover -s tests -p test_touch_calibration.py"""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def load_framework():
    # CircuitPython hardware modules are unavailable on the host. These tests
    # use the real API and input dispatcher with simulated touch measurements.
    names = ('board', 'digitalio', 'touchio', 'neopixel', 'audioio',
             'audiocore', 'supervisor')
    spec = importlib.util.spec_from_file_location(
        'touch_test_framework', Path(__file__).resolve().parents[1] / 'cmu_playground.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {name: ModuleType(name) for name in names}):
        spec.loader.exec_module(module)
    return module


framework = load_framework()


class Pad:
    def __init__(self, raw):
        self.raw_value = raw
        self.threshold = raw + 100

    @property
    def value(self):
        return self.raw_value > self.threshold


class TouchCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.pads = [Pad(1000 + i * 100) for i in range(7)]
        self.hw = framework.Hardware.__new__(framework.Hardware)
        self.hw.padNames = tuple('A' + str(i) for i in range(1, 8))
        self.hw.pads = self.pads
        self.hw.buttons = []
        self.runtime = framework.Runtime.__new__(framework.Runtime)
        self.runtime.hw = self.hw
        self.runtime.phase = framework.CONTROLLER
        self.runtime.app = SimpleNamespace(running=True)
        self.runtime.padNow = [False] * 7
        self.runtime.padState = [False] * 7
        self.runtime.buttonNow = []
        self.runtime.buttonState = []
        self.events = []
        self.runtime.onTouch = lambda app, pad: self.events.append(('touch', pad))
        self.runtime.onTouchRelease = lambda app, pad: self.events.append(('release', pad))
        framework._runtime = self.runtime

    def tearDown(self):
        framework._runtime = None

    def test_exports(self):
        for name in ('getTouchRawValue', 'getTouchThreshold',
                     'setTouchThreshold', 'calibrateTouch'):
            self.assertIn(name, framework.__all__)

    def test_reads_live_values_in_controller_and_view(self):
        for phase in (framework.CONTROLLER, framework.VIEW):
            self.runtime.phase = phase
            self.pads[6].raw_value += 10
            self.assertEqual(framework.getTouchRawValue('A7'), self.pads[6].raw_value)
            self.assertEqual(framework.getTouchThreshold('A7'), 1700)

    def test_manual_threshold_and_strict_touch_boundary(self):
        framework.setTouchThreshold('A1', 1000)
        self.runtime.pollInputs()
        self.assertEqual(self.events, [])
        self.pads[0].raw_value = 1001
        self.runtime.pollInputs()
        self.runtime.pollInputs()
        self.assertEqual(self.events, [('touch', 'A1')])
        self.runtime.phase = framework.CONTROLLER
        framework.setTouchThreshold('A1', 1001)
        self.runtime.pollInputs()
        self.assertEqual(self.events[-1], ('release', 'A1'))

    def test_recalibrate_one_pad_with_default_offset(self):
        self.pads[6].raw_value = 2100
        framework.calibrateTouch('A7')
        self.assertEqual(framework.getTouchThreshold('A7'), 2200)
        self.assertEqual(framework.getTouchThreshold('A1'), 1100)

    def test_recalibrate_all_with_custom_offset(self):
        framework.calibrateTouch(offset=250)
        self.assertEqual([pad.threshold for pad in self.pads],
                         [pad.raw_value + 250 for pad in self.pads])

    def test_recalibration_preserves_release_event(self):
        self.pads[0].raw_value = 1300
        self.runtime.pollInputs()
        self.runtime.phase = framework.CONTROLLER
        self.pads[0].raw_value = 1000
        framework.calibrateTouch('A1')
        self.runtime.pollInputs()
        self.assertEqual(self.events, [('touch', 'A1'), ('release', 'A1')])

    def test_recalibrate_during_touch_callback(self):
        def on_touch(app, pad):
            self.events.append(('touch', pad))
            framework.calibrateTouch(pad)

        self.runtime.onTouch = on_touch
        self.pads[0].raw_value = 1300
        self.runtime.pollInputs()
        self.runtime.pollInputs()
        self.assertEqual(self.events, [('touch', 'A1'), ('release', 'A1')])

    def test_rejects_bad_pad_names(self):
        for pad in ('A0', 'TX', 'a1', 'A8', 1, None, []):
            for function in (framework.getTouchRawValue, framework.getTouchThreshold,
                             lambda p: framework.setTouchThreshold(p, 1500)):
                with self.subTest(pad=pad, function=function), self.assertRaises(ValueError):
                    function(pad)
            if pad is not None:
                with self.assertRaises(ValueError):
                    framework.calibrateTouch(pad)

    def test_rejects_bad_numbers_without_changes(self):
        original = [pad.threshold for pad in self.pads]
        for value, error in ((True, TypeError), (1.5, TypeError), ('100', TypeError),
                             (None, TypeError), (-1, ValueError), (65536, ValueError)):
            with self.subTest(value=value):
                with self.assertRaises(error):
                    framework.setTouchThreshold('A1', value)
                with self.assertRaises(error):
                    framework.calibrateTouch(offset=value)
                self.assertEqual([pad.threshold for pad in self.pads], original)

    def test_overflow_does_not_partly_calibrate(self):
        original = [pad.threshold for pad in self.pads]
        self.pads[-1].raw_value = 65500
        with self.assertRaises(ValueError):
            framework.calibrateTouch()
        self.assertEqual([pad.threshold for pad in self.pads], original)

    def test_numeric_boundaries(self):
        for threshold in (0, 65535):
            framework.setTouchThreshold('A1', threshold)
            self.assertEqual(framework.getTouchThreshold('A1'), threshold)
        self.pads[0].raw_value = 0
        framework.calibrateTouch('A1', offset=65535)
        self.assertEqual(self.pads[0].threshold, 65535)
        framework.calibrateTouch('A1', offset=0)
        self.assertEqual(self.pads[0].threshold, 0)

    def test_mutations_require_controller(self):
        for phase in (framework.VIEW, framework.INTERNAL):
            self.runtime.phase = phase
            with self.assertRaises(framework.MVCError):
                framework.setTouchThreshold('A1', 1500)
            with self.assertRaises(framework.MVCError):
                framework.calibrateTouch()

    def test_all_helpers_require_running_app(self):
        framework._runtime = None
        for function, args in ((framework.getTouchRawValue, ('A1',)),
                               (framework.getTouchThreshold, ('A1',)),
                               (framework.setTouchThreshold, ('A1', 1500)),
                               (framework.calibrateTouch, ())):
            with self.assertRaises(framework.MVCError):
                function(*args)


if __name__ == '__main__':
    unittest.main()
