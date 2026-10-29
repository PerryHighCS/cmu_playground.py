"""Host-side checks for optional callback registration."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


def load_framework():
    spec = importlib.util.spec_from_file_location(
        'callback_test_framework',
        Path(__file__).resolve().parents[1] / 'cmu_playground.py')
    module = importlib.util.module_from_spec(spec)
    names = ('board', 'digitalio', 'touchio', 'neopixel', 'audioio',
             'audiocore', 'supervisor')
    with patch.dict(sys.modules, {name: ModuleType(name) for name in names}):
        spec.loader.exec_module(module)
    return module


framework = load_framework()


class CallbackRegistrationTests(unittest.TestCase):
    def setUp(self):
        hardware = patch.object(
            framework, 'Hardware', return_value=SimpleNamespace(pads=[], buttons=[]))
        hardware.start()
        self.addCleanup(hardware.stop)
        ticks = patch.object(framework.supervisor, 'ticks_ms',
                             return_value=0, create=True)
        ticks.start()
        self.addCleanup(ticks.stop)

    def test_all_callbacks_keep_their_identity(self):
        handlers = {name: lambda app: None for name in framework.CALLBACK_NAMES}
        runtime = framework.Runtime(SimpleNamespace(**handlers))
        for name, callback in handlers.items():
            self.assertIs(getattr(runtime, name), callback)

    def test_missing_callbacks_are_none(self):
        callback = lambda app: None
        runtime = framework.Runtime(SimpleNamespace(onTouch=callback))
        self.assertIs(runtime.onTouch, callback)
        for name in framework.CALLBACK_NAMES:
            if name != 'onTouch':
                self.assertIsNone(getattr(runtime, name))

    def test_explicit_noncallable_callbacks_are_rejected(self):
        for name in framework.CALLBACK_NAMES:
            for value in (None, 0, 'callback'):
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(TypeError, name + ' must be a function'):
                        framework.Runtime(SimpleNamespace(**{name: value}))


if __name__ == '__main__':
    unittest.main()
