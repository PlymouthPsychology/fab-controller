

Software
~~~~~~~~~~~~

The system includes two software components which communicate via a USB
serial link:

-  This control software, which runs on a host computer and provides a
   user interface via a web browser.

-  The open source Standard `Firmata <http://firmata.org>`__ firmware,
   which runs on the embedded controller inside the device. This is
   pre-installed on ready-assembled devices.




Installation
^^^^^^^^^^^^^^^^^^

The software should work on both Mac and PC - the primary dependencies
are a recent version of Python plus a C compiler (needed to install the
python-gevent library).



On OS X (or BSD/Linux)
,,,,,,,,,,,,,,,,,,,,,,,,,

1. Install XCode from the Mac App Store (you can skip this if you
   already have a working C compiler on your linux system).

2. Open the Terminal app (in the /Applications/Utilities folder).

3. If you don't already have pip_ installed, type ``sudo easy_install pip``


.. _pip: https://pypi.python.org/pypi/pip


And then to install the software: ``pip install fab-controller``


4. To start using the FAB device, type the command: ``fab``


.. note: If all is well this will open a web browser window with the interface to the device. 





On Windows
,,,,,,,,,,,,,

1. Ensure you have GCC, Python and pip installed.

2. Repeat the steps above.





