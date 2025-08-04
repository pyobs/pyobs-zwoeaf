from .EAF_focuser import EAF  # type: ignore


def connect(eaf: EAF) -> None:
    # connect
    while True:
        inp = input("Enter device number [0]: ")
        device_number = 0 if len(inp) == 0 else int(inp)
        break

    print(f"Connecting to device {device_number}...")
    if not eaf.connect(device_number):
        raise ValueError(f"Could not connect to device {device_number}.")
    print(f"Connected to device {device_number}.")


def menu(eaf: EAF) -> bool:
    print()
    print(f"Temperature:      {eaf.getTemperature():.2f}°C")
    print(f"Step range:       {eaf.getStepRange()}")
    print(f"Is moving:        {eaf.isMoving()}")
    print(f"Position:         {eaf.getPosition()}")
    print(f"(1) Move")
    print(f"(2) Stop")
    print(f"(3) Set current position")
    print(f"(4) Maximal step: {eaf.getMaximalStep()}")
    print(f"(5) Sound:        {eaf.getSound()}")
    print(f"(6) Direction     {eaf.getDirection()}")
    print(f"(7) Backlash      {eaf.getBacklash()}")
    print(f"(0) Quit")

    while True:
        cmd = input("Enter command [0-7]: ")
        if cmd in ["1", "2", "3", "4", "5", "6", "7", "0", ""]:
            break

    if cmd == "1":
        move(eaf)
    elif cmd == "2":
        stop(eaf)
    elif cmd == "3":
        position(eaf)
    elif cmd == "4":
        max_step(eaf)
    elif cmd == "5":
        sound(eaf)
    elif cmd == "6":
        direction(eaf)
    elif cmd == "7":
        backlash(eaf)

    return cmd != "0"


def move(eaf: EAF) -> None:
    pos = input("Enter new position: ")
    if eaf.isMoving():
        eaf.stop()
    eaf.move(int(pos))


def stop(eaf: EAF) -> None:
    eaf.stop()


def sound(eaf: EAF) -> None:
    eaf.setSound(not eaf.getSound())


def position(eaf: EAF) -> None:
    pos = input("Enter current position: ")
    eaf.resetPosition(int(pos))


def max_step(eaf: EAF) -> None:
    pos = input("Enter maximum position: ")
    eaf.setMaximalStep(int(pos))


def direction(eaf: EAF) -> None:
    eaf.setDirection(not eaf.getDirection())


def backlash(eaf: EAF) -> None:
    pos = input("Enter new backlash: ")
    eaf.setBacklash(int(pos))


def main() -> None:
    # connect
    eaf = EAF()
    connect(eaf)

    # show menu until quit
    while menu(eaf):
        pass

    # disconnect
    eaf.disconnect()


if __name__ == "__main__":
    main()
