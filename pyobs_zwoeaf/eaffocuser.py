import asyncio
from abc import ABCMeta
from typing import Any, Optional
import logging

from pyobs.interfaces import IFocuser
from pyobs.modules import Module
from pyobs.utils.enums import MotionStatus
from pyobs.utils import exceptions as exc

from .pybind_wrapper import EAF

log = logging.getLogger(__name__)


class EAFFocuser(IFocuser, Module, metaclass=ABCMeta):
    """
    This is the pyobs software python class for the EAF := Electronic Automatic Focuser from ZWO for the 8 inch Monti telescope!
    """

    device_number = 0  # number of the device slot
    max_steps = 60000  # number of the maximal steps
    backlash = 0  # number of backlash steps
    direction = True  # direction false/true -> right/left-rotation
    sound = True  # sound false/true -> off/on sound when initating motion of the motor

    connected = False
    ready_changed = False
    step_to_mm_conversion = 0.00242105263
    time_limit = 60 * 5  # 5 minutes
    pose = 0
    set_pose = 0
    offset = 0
    eaf = None  # EAF c++ driver class object

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
        """
        Initiate EAF Focus device class!
        Give the following parameter:
            - device_number = 0       # number of the device USB slot, should be zero if not a second EAF is connected or similiar HID USB device ...
            - max_steps = 60000       # number of the maximal steps
            - backlash = 0            # number of backlash steps
            - direction = True        # direction false/true -> right/left-rotation
            - sound = True            # sound false/true -> off/on sound when initating motion of the motor
        """
        Module.__init__(self, **kwargs)
        self.device_number = device_number
        self.max_steps = max_steps
        self.backlash = backlash
        self.direction = direction
        self.sound = sound

    async def open(self) -> None:
        """
        Open Module
        """
        log.info("Opening EAF focusing device!")
        await Module.open(self)
        self.eaf = EAF(self.device_number, self.max_steps, self.backlash, self.direction, self.sound)
        success = self.eaf.Connect()
        if success is False:
            sys.exit(
                "EAF Focusing device failed to connect, exit program! Is the device connected vis USB? Permission for using the USB port? device_number available?"
            )
        self.connected = True
        temp = self.eaf.Temperature()
        log.info("The temperature of the EAF is {}".format(temp))
        self.pose = self.eaf.GetPose() * self.step_to_mm_conversion
        self.set_pose = self.pose
        log.info("The Motor position is at: {}".format(self.pose))
        task = asyncio.create_task(self.close())

    async def close(self):
        await Module.main(self)
        log.warning("The Focuser Module was called to close! Closing USB-Connection to the EAF!")
        self.Disconnect()

    async def init(self, **kwargs: Any):
        """
        Initializer for the EAF Motor.
        Needs to be called before accessing the other EAF focuser functions.
        Will initialize with the values given in the constructor!
        """
        if await self.is_ready() is False:
            self.eaf = EAF(self.device_number, self.max_steps, self.backlash, self.direction, self.sound)
            success = self.eaf.Connect()
            if success is False:
                sys.exit(
                    "EAF Focusing device failed to connect, exit program! Is the device connected vis USB? Permission for using the USB port? device_number available?"
                )
            temp = self.eaf.Temperature()
            log.info("The temperature of the EAF is {}".format(temp))
            self.pose = self.eaf.GetPose() * self.step_to_mm_conversion
            log.info("The Motor position is at: {}".format(self.pose))
        else:
            log.warning("No need no initialize, EAF is already Connected!")

    async def park(self, **kwargs: Any):
        log.info("Going park at position zero!")
        await self.stop_motion()
        await asyncio.sleep(0.1)
        await self.set_focus(0)
        self.Disconnect()

    async def is_ready(self, **kwargs: Any):
        if self.connected is True:
            if self.ready_changed is False:
                log.info("EAF is connected and ready")
                self.ready_changed = True
            return True
        else:
            if self.ready_changed is True:
                log.info("EAF is not connected and not ready!")
                self.ready_changed = False
            return False

    async def set_focus(
        self, focus: float, direction: bool = True, reset: bool = False, do_offset: bool = False, **kwargs: Any
    ) -> None:
        """
        - focus: Moves EAF motor to new value in the range [0, max_steps].
        - direction: Changes the direction the EAF motor moves, false/true -> right/left-rotation ...
        - reset: If reset is set True, the new focus value replaces the current value, without moving the EAF motor!

        Raises:
            MoveError: If focuser cannot be moved.
            InterruptedError: If movement was aborted.
        """
        if await self.is_ready() is True:
            if do_offset is False:
                self.set_pose = focus
            step = int(focus / self.step_to_mm_conversion)
            time_gone = 0
            moving = self.eaf.Moving()
            if moving is True:
                log.warning("The EAF is still moving from an old command please wait.")

            if reset is False and moving is False:
                success = self.eaf.MoveToPose(step)
                if success is False:
                    self.eaf.Disconnect()
                    raise exc.MoveError(
                        "Was not able to move the EAF motor. Tried to Disconnect the EAF device as a consequence!"
                    )
                else:
                    moving = True

                while moving is True:
                    if time_gone > self.time_limit:
                        self.eaf.Disconnect()
                        raise InterruptedError
                    moving = self.eaf.Moving()
                    self.pose = self.eaf.GetPose() * self.step_to_mm_conversion
                    log.info("EAF focusing motor is moving! Focus pose: {}mm!".format(self.pose))
                    await asyncio.sleep(0.5)
                    time_gone += 0.5

        elif reset is True and moving is False:
            self.eaf.SetPose(step)
            self.pose = step

    async def set_focus_offset(self, offset: float, **kwargs: Any) -> None:
        """Sets focus offset.

        Args:
            offset: New focus offset.

        Raises:
            ValueError: If given value is invalid.
            MoveError: If focuser cannot be moved.
        """
        if await self.is_ready() is True:
            self.offset = offset
            log.info("Setting offset: {}".format(self.offset))
            await self.set_focus(self.set_pose + offset, do_offset=True)

    async def get_focus(self, **kwargs: Any) -> float:
        """
        Return current focus.
        Returns:
            Current focus.
        """
        if await self.is_ready() is True:
            self.pose = self.eaf.GetPose() * self.step_to_mm_conversion
            self.set_pose = self.pose - self.offset
        return self.set_pose

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
        if await self.is_ready() is True:
            moving = self.eaf.Moving()
            if moving is True:
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
        success = self.eaf.MoveStop()
        if success is True:
            log.info("Stopped successfully")
        else:
            log.error("Did not stop, try to figure out why! Trying to disconnect device next. Maybe restart software")
            self.Disconnect()

    def Disconnect(self):
        log.warning("Try disconnecting EAF device!")
        success = self.eaf.Disconnect()
        if success is True:
            log.warning("Disconnected successfully!")
        else:
            log.error("Did not disconnect properly")


__all__ = ["EAFFocuser"]
