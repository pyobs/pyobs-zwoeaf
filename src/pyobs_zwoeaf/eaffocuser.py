import asyncio
import logging
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

    async def open(self) -> None:
        """Open module."""
        await Module.open(self)

        from .EAF_focuser import EAF  # type: ignore[import-untyped]

        self._eaf = EAF()
        if not self._eaf.connect(self._device_number):
            raise ValueError("EAF focuser failed to connect. Is the device connected via USB? Correct device_number?")

        self._eaf.setMaximalStep(self._max_steps)
        self._eaf.setBacklash(self._backlash)
        self._eaf.setDirection(self._direction)
        self._eaf.setSound(self._sound)

        log.info("Connected to EAF focuser, temperature: %.2f°C", self._eaf.getTemperature())

        await MotionStatusMixin.open(self)
        await self._change_motion_status(MotionStatus.IDLE)

        self._focus_setpoint = self._eaf.getPosition() * _STEP_TO_MM
        await self.comm.set_state(IFocuser, FocuserState(focus=self._focus_setpoint, focus_offset=self._focus_offset))
        await self.comm.set_state(IReady, ReadyState(ready=True))

    async def close(self) -> None:
        """Close module."""
        if self._eaf is not None:
            self._eaf.disconnect()
            self._eaf = None
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
            self._eaf.stop()
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

        total_mm = focus + self._focus_offset
        step = int(total_mm / _STEP_TO_MM)
        log.info("Moving EAF to %.4f mm (offset %.4f mm, step %d)...", focus, self._focus_offset, step)

        await self._change_motion_status(MotionStatus.SLEWING)
        if not self._eaf.move(step):
            await self._change_motion_status(MotionStatus.ERROR)
            raise exc.MoveError("Could not move EAF motor.")

        while self._eaf.isMoving():
            await asyncio.sleep(0.5)

        self._focus_setpoint = focus
        await self._change_motion_status(MotionStatus.POSITIONED)
        await self.comm.set_state(IFocuser, FocuserState(focus=self._focus_setpoint, focus_offset=self._focus_offset))

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
                    temp = self._eaf.getTemperature()
                    await self.comm.set_state(
                        ITemperatures,
                        TemperaturesState(readings=[SensorReading(name="EAF", value=temp)]),
                    )
            except Exception:
                pass
            await asyncio.sleep(10)


__all__ = ["EAFFocuser"]
