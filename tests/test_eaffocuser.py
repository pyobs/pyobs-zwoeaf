"""Unit tests for the non-hardware logic in EAFFocuser: constructor defaults, the
_run_blocking timeout wrapper, and the steps<->mm conversion in set_focus.

The native EAF SDK (self._eaf) is mocked out.
"""

import asyncio
import threading
from unittest.mock import AsyncMock, MagicMock

import pytest

from pyobs_zwoeaf import EAFFocuser
from pyobs_zwoeaf.eaffocuser import _STEP_TO_MM


def test_constructor_defaults() -> None:
    focuser = EAFFocuser()
    assert focuser._device_number == 0
    assert focuser._max_steps == 60000
    assert focuser._backlash == 0
    assert focuser._direction is True
    assert focuser._sound is True
    assert focuser._eaf is None
    assert focuser._focus_offset == 0.0
    assert focuser._focus_setpoint == 0.0


@pytest.mark.asyncio
async def test_run_blocking_runs_func_and_returns_true() -> None:
    ran: list[bool] = []

    def fast() -> None:
        ran.append(True)

    assert await EAFFocuser._run_blocking(fast) is True
    assert ran == [True]


@pytest.mark.asyncio
async def test_run_blocking_times_out() -> None:
    done = threading.Event()

    def slow() -> None:
        done.wait()

    assert await EAFFocuser._run_blocking(slow, timeout=0.01) is False
    done.set()
    await asyncio.sleep(0.05)


@pytest.mark.asyncio
async def test_set_focus_requires_connection() -> None:
    focuser = EAFFocuser()
    with pytest.raises(ValueError):
        await focuser.set_focus(0.5)


@pytest.mark.asyncio
async def test_set_focus_computes_steps() -> None:
    focuser = EAFFocuser()
    focuser._eaf = MagicMock()
    focuser._eaf.move = MagicMock(return_value=True)
    focuser._eaf.isMoving = MagicMock(return_value=False)

    async def fake_run_blocking(func, timeout: float = 5.0) -> bool:
        func()
        return True

    focuser._run_blocking = fake_run_blocking  # type: ignore[method-assign]

    await focuser.set_focus(0.5)

    focuser._eaf.move.assert_called_once_with(int(0.5 / _STEP_TO_MM))
    assert focuser._focus_setpoint == 0.5


@pytest.mark.asyncio
async def test_set_focus_offset() -> None:
    focuser = EAFFocuser()
    focuser._focus_setpoint = 1.0
    focuser.set_focus = AsyncMock()  # type: ignore[method-assign]

    await focuser.set_focus_offset(0.25)

    assert focuser._focus_offset == 0.25
    focuser.set_focus.assert_awaited_once_with(1.0)
