pyobs-zwoeaf
############

This is a `pyobs <https://www.pyobs.org>`_ (`documentation <https://docs.pyobs.org>`_) module for the
`ZWO Electronic Auto Focuser (EAF) <https://astronomy-imaging-camera.com/product/zwo-eaf>`_.


Example configuration
*********************

This is an example configuration::

    class: pyobs_zwoeaf.EAFFocuser
    device_number: 0
    max_steps: 60000
    backlash: 0
    direction: true
    sound: true

    # communication
    comm:
      jid: test@example.com
      password: ***


Available classes
*****************

There is one single class for the ZWO EAF.

EAFFocuser
==========
.. autoclass:: pyobs_zwoeaf.EAFFocuser
   :members:
   :show-inheritance:
