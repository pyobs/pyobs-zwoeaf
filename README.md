# ZWO EAF module for *pyobs*

## udev rule
Add file `/etc/udev/rules.d/99-hidraw.rules` with the following content: 

    SUBSYSTEM=="hidraw",MODE="0660",GROUP="plugdev"`