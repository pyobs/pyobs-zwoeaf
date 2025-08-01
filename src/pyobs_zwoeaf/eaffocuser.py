import asyncio
from abc import ABCMeta
from typing import Any, Optional
import logging

from pyobs.interfaces import IFocuser
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus
from pyobs.utils import exceptions as exc

from .pybind_wrapper import EAF  # type: ignore

log = logging.getLogger(__name__)


class EAFFocuser(IFocuser, Module, metaclass=ABCMeta):
    """
    This is the pyobs software python class for the EAF := Electronic Automatic Focuser from ZWO for the 8 inch Monti telescope!
    """

    __module__ = "pyobs.modules.focuser"

    def __init__(
        self,
        device_number: int = 0,
        max_steps: int = 60000,
        backlash: int = 0,
        direction: bool = True,
        sound: bool = True,
        **kwargs: Any,
    ):
        """Initiate EAF Focus device class!

        Args:
            device_number:  number of the device USB slot, should be zero if not a second EAF is connected
                            or similar HID USB device ...
            max_steps:      number of the maximal steps
            backlash:       number of backlash steps
            direction:      direction false/true -> right/left-rotation
            sound:          sound false/true -> off/on sound when initating motion of the motor
        """
        Module.__init__(self, **kwargs)
        self.device_number = device_number
        self.max_steps = max_steps
        self.backlash = backlash
        self.direction = direction
        self.sound = sound

        self.connected = False
        self.ready_changed = False
        self.step_to_mm_conversion = 0.00242105263
        self.time_limit = 60 * 5  # 5 minutes
        self.position = 0
        self.set_position = 0
        self.offset = 0
        self.eaf = None  # EAF c++ driver class object

    async def open(self) -> None:
        """Open Module"""
        await Module.open(self)
        log.info("Opening EAF focusing device!")

        # connect
        self.eaf = EAF(self.device_number, self.max_steps, self.backlash, self.direction, self.sound)
        if not self.eaf.Connect():
            raise ValueError("EAF Focusing device failed to connect.")
        self.connected = True

        # get temperature and position
        temp = self.eaf.Temperature()
        log.info(f"The temperature of the EAF is {temp:.2f}°C")
        self.position = self.eaf.GetPosition() * self.step_to_mm_conversion
        self.set_position = self.position
        log.info(f"The Motor position is at: {self.position:.2f}")

    async def close(self):
        await Module.main(self)
        log.warning("The Focuser Module was called to close! Closing USB-Connection to the EAF!")
        self.disconnect()

    async def init(self, **kwargs: Any):
        pass

    async def park(self, **kwargs: Any):
        pass

    async def is_ready(self, **kwargs: Any):
        if self.connected:
            if not self.ready_changed:
                log.info("EAF is connected and ready")
                self.ready_changed = True
            return True
        else:
            if self.ready_changed:
                log.info("EAF is not connected and not ready!")
                self.ready_changed = False
            return False

    async def _move_focus(self, focus: float):
        if await self.is_ready():
            step = int(focus / self.step_to_mm_conversion)
            time_gone = 0
            moving = self.eaf.Moving()
            if moving:
                log.warning("The EAF is still moving from an old command please wait.")

            if not moving:
                if not self.eaf.MoveToPosition(step):
                    self.eaf.disconnect()
                    raise exc.MoveError(
                        "Was not able to move the EAF motor. Tried to Disconnect the EAF device as a consequence!"
                    )
                else:
                    moving = True

                while moving:
                    if time_gone > self.time_limit:
                        self.eaf.disconnect()
                        raise InterruptedError
                    moving = self.eaf.Moving()
                    self.position = self.eaf.GetPosition() * self.step_to_mm_conversion
                    log.info("EAF focusing motor is moving! Focus position: {}mm!".format(self.position))
                    await asyncio.sleep(0.5)
                    time_gone += 0.5

    async def set_focus(self, focus: float, **kwargs: Any) -> None:
        """Sets new focus.

        Args:
            focus: New focus value.

        Raises:
            MoveError: If telescope cannot be moved.
            InterruptedError: If movement was aborted.
        """
        self.set_position = focus
        self.offset = 0.0
        log.info(f"Setting focus to {focus:.2f}mm.")
        await self._move_focus(focus)

    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        """Sets focus offset.

        Args:
            offset: New focus offset.

        Raises:
            ValueError: If given value is invalid.
            MoveError: If focuser cannot be moved.
        """
        self.offset = offset
        log.info(f"Setting focus offset to {offset:.2f}mm.")
        await self._move_focus(self.set_position + offset)

    async def get_focus(self, **kwargs: Any) -> float:
        """
        Return current focus.
        Returns:
            Current focus.
        """
        if await self.is_ready():
            self.position = self.eaf.GetPosition() * self.step_to_mm_conversion
        return self.position - self.offset

    async def get_focus_offset(self, **kwargs: Any) -> float:
        """
        Return current focus offset.
        Returns:
            Current focus offset.
        """
        return self.offset

    async def get_motion_status(self, device: Optional[str] = None, **kwargs: Any) -> MotionStatus:
        """Returns current motion status.

        Args:
            device: Name of device to get status for, or None.

        Returns:
            A string from the Status enumerator.
        """
        if await self.is_ready():
            if self.eaf.Moving():
                # log.info("EAF Motor is still is motion")
                return MotionStatus.SLEWING
            else:
                # log.info("EAF Motor is not moving or not connected properly")
                return MotionStatus.IDLE
        else:
            return MotionStatus.INITIALIZING

    async def stop_motion(self, device: Optional[str] = None, **kwargs: Any) -> None:
        """Stop the motion.

        Args:
            device: Name of device to stop, or None for all.
        """
        log.info("Stop motion of the EAF Focuser!")
        if self.eaf.MoveStop():
            log.info("Stopped successfully")
        else:
            log.error("Did not stop, try to figure out why! Trying to disconnect device next. Maybe restart software")
            self.disconnect()

    def disconnect(self):
        log.warning("Try disconnecting EAF device!")
        success = self.eaf.disconnect()
        if success is True:
            log.warning("Disconnected successfully!")
        else:
            log.error("Did not disconnect properly")


__all__ = ["EAFFocuser"]
