"""Smoke tests: import the driver and instantiate it without hardware, asserting it
advertises the interfaces it claims.

The native pybind11 extension (EAF_focuser) and the CLI entry point (cli.py) are
deliberately not imported here -- cli.py imports the native module at top level, and
EAFFocuser itself imports it lazily inside open().
"""

from pyobs.interfaces import IFocuser, ITemperatures
from pyobs.modules import Module

from pyobs_zwoeaf import EAFFocuser


def test_instantiate_focuser() -> None:
    focuser = EAFFocuser()
    assert isinstance(focuser, Module)
    assert isinstance(focuser, IFocuser)
    assert isinstance(focuser, ITemperatures)
