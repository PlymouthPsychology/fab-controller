# The pain machine


## Overview


This is the control software for the new Forgione Barber finger pressure stimulator device. The device requires has two software components which communicate via a USB serial link:

- The open source [Firmata](http://firmata.org) firmware, which runs on the embedded controller inside the device. This will be pre-installed on your device.
- This control software, which runs on a host computer and provides a user interface via a web browser.


## Installation

The software should work on both Mac and PC - it only requires a recent version of Python.


### On a Mac, 

1. Install XCode from the Mac App Store (you can skip this if you already have a working C compiler on your system).

2. Open the Terminal app (in the utilities folder) and type the following commmand to install the software needed:

	bash "$(curl -fsSL https://raw.githubusercontent.com/puterleat/fab-controller/master/install_osx.sh)"

./install_osx.sh

3. To run the software, type:

    ./run.sh

This should then show a few initialisation messages, and open a web browser window with the interface to the device.



### On windows

1. Ensure you have GCC, Python and pip installed.

2. Repeat the steps from 2 above.
