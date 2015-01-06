# FAB! The Forgione-Avent-Barber Finger Pressure Stimulator



## Hardware

The FAB is based on cheap, readily available hardware (an Arduino microcontroller and widely-available pressure-sensors) and the key mechanical components are 3D printed and can be assembled by lab technicians. Ready-assembled units will also be available to buy.

More details, including circuit diagrams, schematics, and CAD files sufficient to enable 3d-printing and assembly of a device, will be available soon under a permissive open source license.



## Software

This repository contains the control software for the new Forgione-Avent-Barber finger pressure stimulator. Details of the original Forgione Barber device [are here](static/ForgioneBarber1971.pdf). The FAB device 

The system includes two software components which communicate via a USB serial link:

- This control software, which runs on a host computer and provides a user interface via a web browser.

- The open source Standard [Firmata](http://firmata.org) firmware, which runs on the embedded controller inside the device. This is pre-installed on ready-assembled devices.
 


### Installation

The software should work on both Mac and PC - the primary dependencies are a recent version of Python plus a C compiler (needed to install the python-gevent library).


#### On a Mac, 

1. Install XCode from the Mac App Store (you can skip this if you already have a working C compiler on your system). 


2. Open the Terminal app (in the /Applications/Utilities folder).

3. If you don't already have [`pip`](https://pypi.python.org/pypi/pip) installed, type:

	`sudo easy_install pip`

And then to install the software:

	`pip install fab-controller`
	

4. To run the machine, type the command:
	
    `fab`

This should then show a few initialisation messages, and open a web browser window with the interface to the device.



Note, log files will be saved into `~/Documents/fab/logs/`



#### On Windows

1. Ensure you have GCC, Python and pip installed.

2. Repeat the steps above.





<!-- 

Pressure = 980kpa
2kg in newtons / 2mm*10mm area  / 1000 = kpa
( 19.6/ (.002*.01)  )/1000

Could be between 816 and 1225 kpa depending on width of contact spot

 -->