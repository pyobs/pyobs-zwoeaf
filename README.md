# ZWO EAF module for *pyobs*

This module provides a [pyobs](https://www.pyobs.org) driver for the
[ZWO Electronic Auto Focuser (EAF)](https://astronomy-imaging-camera.com/product/zwo-eaf).
It exposes the focuser as a pyobs module implementing `IFocuser` and `ITemperatures`,
allowing remote focus control and temperature monitoring via the pyobs communication layer.

## Requirements

### Python

- Python 3.11 or later
- pyobs-core 2.0 or later

### System

The C++ extension is built against the ZWO EAF SDK (bundled) and requires
`libudev` at both build and runtime. Install the development package before
building:

```bash
sudo apt install libudev-dev
```

The runtime library (`libudev.so.1`) ships with most Linux distributions and
is usually already present; the `-dev` package provides the linker symlink
needed during the build.

## Installation

```bash
pip install pyobs-zwoeaf
```

Or from source:

```bash
uv sync
```

## udev rule

To allow access to the EAF USB device without root privileges, add a udev rule.
Create `/etc/udev/rules.d/99-hidraw.rules` with the following content:

    SUBSYSTEM=="hidraw",MODE="0660",GROUP="plugdev"

Then add your user to the `plugdev` group and reload the rules:

```bash
sudo usermod -aG plugdev $USER
sudo udevadm control --reload-rules && sudo udevadm trigger
```

## Configuration

Add the module to your pyobs configuration:

```yaml
focuser:
  class: pyobs_zwoeaf.EAFFocuser
  device_number: 0      # USB device index (0 for the first EAF)
  max_steps: 60000      # maximum step count
  backlash: 0           # backlash compensation in steps
  direction: true       # motor direction (true = left rotation)
  sound: true           # beep when motion starts
```

## CLI tool

A simple interactive terminal tool for direct hardware access is included,
useful for commissioning and manual adjustments:

```bash
pyobs-zwoeaf
```
