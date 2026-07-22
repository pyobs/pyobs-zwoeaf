import asyncio
import logging
import threading
import time
from collections.abc import Callable
from typing import Any

import pyobs.utils.exceptions as exc
from pyobs.interfaces import IFocuser, IReady, ITemperatures
from pyobs.interfaces.IFocuser import FocuserState
from pyobs.interfaces.IReady import ReadyState
from pyobs.interfaces.ITemperatures import SensorReading, TemperaturesState
from pyobs.mixins import MotionStatusMixin
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus

log = logging.getLogger(__name__)

_STEP_TO_MM = 0.00242105263

# the ZWO EAF SDK's calls are blocking and are made directly on the event loop thread (see
# _run_blocking). If the focuser has gone unresponsive, they can hang indefinitely, so they're
# bounded with a timeout rather than let a single dead connection freeze the whole module.
_SDK_CALL_TIMEOUT = 5.0

# set_focus()'s move-and-wait-until-done sequence legitimately takes longer than the other SDK
# calls above, so it gets its own, more generous timeout.
_MOVE_TIMEOUT = 60.0


class EAFFocuser(Module, MotionStatusMixin, IFocuser, ITemperatures):
    """A pyobs module for the ZWO EAF electronic auto focuser."""

    __module__ = "pyobs_zwoeaf"

    def __init__(
        self,
        device_number: int = 0,
        max_steps: int = 60000,
        backlash: int = 0,
        direction: bool = True,
        sound: bool = True,
        **kwargs: Any,
    ) -> None:
        Module.__init__(self, **kwargs)
        MotionStatusMixin.__init__(self)

        self._device_number = device_number
        self._max_steps = max_steps
        self._backlash = backlash
        self._direction = direction
        self._sound = sound
        self._eaf: Any | None = None
        self._focus_setpoint = 0.0
        self._focus_offset = 0.0

        self.add_background_task(self._poll_temperature)

    @staticmethod
    async def _run_blocking(
        func: Callable[[], None], timeout: float = _SDK_CALL_TIMEOUT
    ) -> bool:
        """Run a blocking EAF SDK call in a daemon thread, so a hung call can't freeze the module.

        A plain executor isn't used here, since its worker threads are non-daemon and Python joins
        them on interpreter shutdown -- a hung call would then just move the freeze to process exit.

        Returns:
            True if func completed within timeout, False if it's still running in the background.
        """
        loop = asyncio.get_running_loop()
        future: asyncio.Future[None] = loop.create_future()

        def _wrapper() -> None:
            try:
                func()
            finally:
                loop.call_soon_threadsafe(future.set_result, None)

        threading.Thread(target=_wrapper, daemon=True).start()
        try:
            await asyncio.wait_for(future, timeout=timeout)
            return True
        except TimeoutError:
            return False

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        from .EAF_focuser import EAF  # type: ignore[import-untyped]

        self._eaf = EAF()
        eaf = self._eaf

        result: list[tuple[bool, float, float]] = []

        def _connect() -> None:
            if not eaf.connect(self._device_number):
                result.append((False, 0.0, 0.0))
                return
            eaf.setMaximalStep(self._max_steps)
            eaf.setBacklash(self._backlash)
            eaf.setDirection(self._direction)
            eaf.setSound(self._sound)
            result.append((True, eaf.getTemperature(), eaf.getPosition()))

        if not await self._run_blocking(_connect):
            raise TimeoutError(
                f"Timed out connecting to EAF focuser after {_SDK_CALL_TIMEOUT}s."
            )
        connected, temperature, position = result[0]
        if not connected:
            raise ValueError(
                "EAF focuser failed to connect. Is the device connected via USB? Correct device_number?"
            )

        log.info("Connected to EAF focuser, temperature: %.2f°C", temperature)

        await MotionStatusMixin.open(self)
        await self._change_motion_status(MotionStatus.IDLE)

        self._focus_setpoint = position * _STEP_TO_MM
        await self.comm.set_state(
            IFocuser,
            FocuserState(focus=self._focus_setpoint, focus_offset=self._focus_offset),
        )
        await self.comm.set_state(IReady, ReadyState(ready=True))

    async def close(self) -> None:
        """Close module."""
        if self._eaf is not None:
            eaf = self._eaf
            self._eaf = None
            if not await self._run_blocking(eaf.disconnect):
                log.error(
                    "Timed out disconnecting EAF focuser after %.1fs.",
                    _SDK_CALL_TIMEOUT,
                )
        await Module.close(self)

    async def init(self, **kwargs: Any) -> None:
        pass

    async def park(self, **kwargs: Any) -> None:
        """Park focuser at position zero."""
        await self.stop_motion()
        await self.set_focus(0.0)

    async def stop_motion(self, device: str | None = None, **kwargs: Any) -> None:
        """Stop focuser motion."""
        if self._eaf is not None:
            if not await self._run_blocking(self._eaf.stop):
                log.error(
                    "Timed out stopping EAF focuser motion after %.1fs.",
                    _SDK_CALL_TIMEOUT,
                )
        await self._change_motion_status(MotionStatus.IDLE)

    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        """Move focuser to given position.

        Args:
            focus: New focus position in mm.

        Raises:
            MoveError: If focuser cannot be moved.
        """
        if self._eaf is None:
            raise ValueError("Not connected.")
        eaf = self._eaf

        total_mm = focus + self._focus_offset
        step = int(total_mm / _STEP_TO_MM)
        log.info(
            "Moving EAF to %.4f mm (offset %.4f mm, step %d)...",
            focus,
            self._focus_offset,
            step,
        )

        await self._change_motion_status(MotionStatus.SLEWING)

        result: list[bool] = []

        def _move() -> None:
            if not eaf.move(step):
                result.append(False)
                return
            # run the whole "move, then poll until done" sequence as a single blocking call, so
            # only one thread gets spawned per move rather than one per 0.5s poll (see _run_blocking)
            while eaf.isMoving():
                time.sleep(0.1)
            result.append(True)

        if not await self._run_blocking(_move, timeout=_MOVE_TIMEOUT):
            await self._change_motion_status(MotionStatus.ERROR)
            raise exc.MoveError(f"Timed out moving EAF motor after {_MOVE_TIMEOUT}s.")
        if not result[0]:
            await self._change_motion_status(MotionStatus.ERROR)
            raise exc.MoveError("Could not move EAF motor.")

        self._focus_setpoint = focus
        await self._change_motion_status(MotionStatus.POSITIONED)
        await self.comm.set_state(
            IFocuser,
            FocuserState(focus=self._focus_setpoint, focus_offset=self._focus_offset),
        )

    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        """Set focus offset and re-apply.

        Args:
            offset: New focus offset in mm.

        Raises:
            MoveError: If focuser cannot be moved.
        """
        log.info("Setting focus offset to %.4f mm.", offset)
        self._focus_offset = offset
        await self.set_focus(self._focus_setpoint)

    async def _poll_temperature(self) -> None:
        """Background task: periodically reads EAF temperature."""
        while True:
            try:
                if self._eaf is not None:
                    eaf = self._eaf
                    result: list[float] = []

                    def _get_temp() -> None:
                        result.append(eaf.getTemperature())

                    if await self._run_blocking(_get_temp):
                        await self.comm.set_state(
                            ITemperatures,
                            TemperaturesState(
                                readings=[SensorReading(name="EAF", value=result[0])]
                            ),
                        )
            except Exception:
                pass
            await asyncio.sleep(10)


__all__ = ["EAFFocuser"]
