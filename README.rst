FAB! The Forgione-Avent-Barber Finger Pressure Stimulator
=========================================================

This repository contains the control software for the new
Forgione-Avent-Barber finger pressure stimulator. Details of the
original Forgione Barber device `are
here <static/ForgioneBarber1971.pdf>`__. The FAB updates this original
design to allow for indepenent computer control of pressure stimulation
of each hand, allowing for a much greater range of experimental designs
(e.g. deceptive or conditioned placebo designs).



Background
----------

Studies of pain and placebo analgesia have historically used a wide
variety of stimuli as laborotory analogues including electrical stimuli
[@wager2004placebo], cold water [i.e. a cold pressor;
@posner1985effects], heat [@petrovic2002placebo], iontophorensis
[@montgomery1997classical], lasers [@bingel2006mechanisms], and pressure
[@whalley2008consistency].

Pain stimuli for laborotory studies can be evaluated on a number of
dimensions: the *reliability* of the stimuli (in the sense the same stimuli
can be delivered consistently); *validity* of the stimuli, in the sense
that it corresponds to real world pain experiences; *repeatability*, in
the sense that multiple stimuli can be given in a single experiment;
whether *deception* is possible --- that is, whether participants can be
convincingly misinformed about the stimuli to be delivered (this would, for exaple, allow placebo-conditioning studies to take place, e.g. @montgomery1997classical); and
the *expense* and *practicality* of the techniques — for example whether
the equipment can be used by students without additional supervision.


|     Stimuli      | Reliablity | Validity | Repeatable | Deception | Blinding | Expense | Practical |
+------------------+------------+----------+------------+-----------+----------+---------+-----------+
| *Heat*           | Good       | Good     | Yes        | Yes       | Yes      | High    | Yes       |
| *Cold*           | Moderate   | Good     | No         | No        | No       | Low     | Yes       |
| *Iontophorensis* | Yes        | Poor     | Yes        | Yes       | Yes      | NA      | NA        |
| *Electrical*     | Good       | Poor     | Yes        | Yes       | Yes      | Med     | Yes       |
| *Laser*          | Good       | Poor     | Yes        | Yes       | Yes      | High    | No        |
| *Focal pressure* | Moderate   | Good     | Yes        | No        | No       | Low     | Yes       |



Focal pressure, applied to the skin over bone, is a method of evoking
experimental pain of an 'aching' nature. The experienced sensation is
relatively closely related to the pressure applied, and many studies of
pain and placebo analgesia use pressure stimuli because they are cheap,
practical, reliable and have reasonable ecological validity (see Table
for a comparison of the different types of pain stimulator available).
a 'Forgione-Barber' can be used to apply pressure to the fingers [@forgione1971strain], see Figure . However, three important
limitations of the original Forgione-Barber device are that i) it is
impossible to deceive pariticpants as to the true magnitude of the
stimulus to be delivered, ruling out conditioning studies; ii) it is
impossible to blind experimenters to the stimuli to be delivered (e.g.
via computer control), and that iii), the reliability of pain
measurements is limited by the resolution of pain self report scales.
The FAB is designed to resolve all three of these limitations.


.. figure:: static/hand.jpg?raw=true
   :alt: An original Forgione Barber device.




The FAB: Hardware
~~~~~~~~~~~~~~~~~~~

The FAB is based on cheap, readily available hardware (an Arduino
microcontroller and widely-available pressure-sensors) and the key
mechanical components are 3D printed and can be assembled by lab
technicians. Ready-assembled units will also be available to buy.

More details, including circuit diagrams, schematics, and CAD files
sufficient to enable 3d-printing and assembly of a device, will be
available soon under a permissive open source license.



FAB Software
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


On a Mac,
,,,,,,,,,,

1. Install XCode from the Mac App Store (you can skip this if you
   already have a working C compiler on your system).

2. Open the Terminal app (in the /Applications/Utilities folder).

3. If you don't already have
   ```pip`` <https://pypi.python.org/pypi/pip>`__ installed, type:

   ``sudo easy_install pip``

And then to install the software:

::

    `pip install fab-controller`

4. To run the machine, type the command:

   ``fab``

This should then show a few initialisation messages, and open a web
browser window with the interface to the device.

Note, log files will be saved into ``~/Documents/fab/logs/``

On Windows
,,,,,,,,,,,,,

1. Ensure you have GCC, Python and pip installed.

2. Repeat the steps above.

User guide
^^^^^^^^^^^^^^^^^^

On running the ``fab`` command, a browser window will open containing
the user interface for the FAB device, shown below.

.. figure:: static/manual.png?raw=true
   :alt: The FAB user interface

   The FAB user interface
The device has 3 primary modes of use:

-  Manual control
-  Programmed control
-  Calibration mode

Target weights and tracking
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

In both manual and programmed control, the interface distinguishes
between:

-  Target value for the weight applied to each hand
-  The actual force measurements recorded by the sensor [^actualforce]

 [1]_ Note that the exact presure applied to the finger will vary as a
function of the contact area, and can only be estimated based on the
width of the finger, but will be broadly similar between participants.

Targets can be set in 'grams' for each hand. Once a target has been set
the control software moves the blades up and down, attempting to
maintain the target weight, as measured by the sensor. Thus where
participants flex or move their fingers, the system will attempt to
compensate to keep the measured force constant.

Manual control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

Using the slider controls under the 'manual' tab, you can set a target
weight in grams for each hand.


Programmed control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

.. figure:: static/programmed.png?raw=true
   :alt: Program interface

   Program interface
Programs for blocks of stimuli can be entered in the text area. Programs
are simple lists of comma-separated integers. The first column specifies
the duration, the second the target in grams for the left hand, and the
third the target for the right hand. So, the following lines:

::

    `20,500,500`
    `10,1000,2000`

Denote a program which will deliver 500g to both hands for 20 seconds,
and then 1000g to the left and 2000g to the right hands for 10 seconds.

At the end of a program target weights are set to zero.



Get set, Stop and Reset buttons.
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

-  The get set button sets the target for both hands to 20g. This allows
   a participant to find a comfortable position, and for program to
   begin from a common reference point.
-  The stop button will always stop any program or manual setting, and
   reduce the target weights to zero. Additionally, the blades will be
   moved approx 1mm upwards to give the participant space to move their
   fingers.
-  The reset button moves both blades to their top resting points.




.. ##### Troubleshooting and known issues.

.. - The software must start in a position where neither blade is activating the top-microswitch. If the switch is depressed on startup the server may hand. The workaround is to remove power from the device and pull both pistons gently downwards.


.. Pressure = 980kpa
.. 2kg in newtons / 2mm*10mm area  / 1000 = kpa
.. ( 19.6/ (.002*.01)  )/1000

.. Could be between 816 and 1225 kpa depending on width of contact spot
