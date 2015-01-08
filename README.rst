FAB! The Forgione-Avent-Barber Finger Pressure Stimulator
=========================================================

This repository contains the control software for the new
Forgione-Avent-Barber (FAB) finger pressure stimulator. Details of the
original Forgione Barber (FB) device [Forgione1971]_ `are
here <static/ForgioneBarber1971.pdf>`__. The FAB updates the original
design to allow for indepenent computer control of pressure stimulation
of each hand, allowing for a much greater range of experimental designs
(e.g. deceptive or conditioned placebo designs).





Background and rationale for the new design
--------------------------------------------------

Studies of pain and placebo analgesia have historically used a wide
variety of stimuli as laborotory analogues including electrical stimuli
[Wager2004]_, cold water (i.e. a cold pressor;
[Posner1985]_), heat [Ptrovic2002]_, iontophorensis
[Montgomery1997]_, lasers [Bingel2006]_, and pressure
[Whalley2008]_.

Pain stimuli for laborotory studies can be evaluated on a number of
dimensions: the *reliability* of the stimuli (in the sense the same stimuli
can be delivered consistently); *validity* of the stimuli, in the sense
that it corresponds to real world pain experiences; *repeatability*, in
the sense that multiple stimuli can be given in a single experiment;
whether *deception* is possible --- that is, whether participants can be
convincingly misinformed about the stimuli to be delivered (this would, for exaple, allow placebo-conditioning studies to take place, e.g. @montgomery1997classical); and
the *expense* and *practicality* of the techniques — for example whether
the equipment can be used by students without additional supervision.

==================   ============   ==========    ============    ===========   ==========    =========   ===========
     Stimuli          Reliablity     Validity      Repeatable      Deception     Blinding      Expense     Practical 
------------------   ------------   ----------    ------------    -----------   ----------    ---------   -----------
 *Heat*               Good           Good          Yes             Yes           Yes           High        Yes       
 *Cold*               Moderate       Good          No              No            No            Low         Yes       
 *Iontophorensis*     Yes            Poor          Yes             Yes           Yes           NA          NA        
 *Electrical*         Good           Poor          Yes             Yes           Yes           Med         Yes       
 *Laser*              Good           Poor          Yes             Yes           Yes           High        No        
 *Focal pressure*     Moderate       Good          Yes             No            No            Low         Yes       
==================   ============   ==========    ============    ===========   ==========    =========   ===========


Focal pressure, applied to the skin over bone, is a method of evoking
experimental pain of an 'aching' nature. The experienced sensation is
relatively closely related to the pressure applied, and many studies of
pain and placebo analgesia use pressure stimuli because they are cheap,
practical, reliable and have reasonable ecological validity (see Table
for a comparison of the different types of pain stimulator available).
The FB device is used to apply pressure to the fingers via lever [Forgione1971]_, see figure.  However, three important limitations of the original FB device are that 

1. it is impossible to deceive pariticpants as to the true magnitude of the
stimulus to be delivered, ruling out conditioning studies
2. it is impossible to blind experimenters to the stimuli to be delivered (e.g. via computer control), and that 
3. the reliability of pain measurements is limited by the resolution of pain self report scales.

The FAB is designed to resolve all three of these limitations.


.. figure:: static/hand_300.jpg?raw=true
   :alt: An original Forgione Barber device.
   :width: 200 px

   An original Forgione Barber device.




The FAB: Hardware
~~~~~~~~~~~~~~~~~~~

The FAB is based on cheap, readily available hardware (an Arduino
microcontroller and widely-available pressure-sensors) and the key
mechanical components are 3D printed and can be assembled by lab
technicians. Ready-assembled units are also be available to buy.

More details, including circuit diagrams, schematics, and CAD files
sufficient to enable 3d-printing and assembly of a device, will be
available soon under a permissive open source license.


The piston
  The key mechanical component is a 3D-printed piston which contains 2kg of
  ballast and a linear motor to drive the probe which makes contact with the participants finger.
  As the linear motor drives the probe downwards and makes contact with the finger
  the piston is lifted from a rest position, but the maximum weight which can be applied to
  the probe remains 2kg [#grams]_. 

Arduino microcontroller and sensors
  An arduino microcontroller is used to drive the linear actuators and capture data from 
  two load cells mounted within the pistons (between the probe and the motor). These data are fed
  to a controlling PC via the `Firmata <http://firmata.org/wiki/Main_Page>`_ serial protocol.


.. [#grams]  Where 1 g = 9.8 mN


.. figure:: static/piston_300.jpg?raw=true
   :alt: The FAB piston and probe
   :width: 200 px

   The FAB piston and probe



.. figure:: static/pistons_long_shot_300.jpg?raw=true
   :alt: The prototype cabinet and both pistons
   :width: 200 px

   The prototype cabinet and both pistons







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







User guide
~~~~~~~~~~~~~~~~



Getting started
^^^^^^^^^^^^^^^^^^

1. Connect both the DC power input and the USB cables.
2. Run the ``fab`` command from the Terminal.


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

-  Target value for the weight[#grams]_  applied to each hand.
-  The actual measurements recorded by the sensor [#actualforce]_.


.. [#actualforce] Note that the exact pressure applied to the finger will vary as a function of the contact area, and can only be estimated based on the width of the finger, but will be broadly similar between participants.


Targets can be set in 'grams' for each hand[#grams]_. Once a target has been set
the control software moves the probes up and down, attempting to
maintain the target weight, as measured by the sensor. Thus where
participants flex or move their fingers, the system will attempt to
compensate to keep the measured force constant.



Manual control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

Using the slider controls under the 'manual' tab, you can set a target
weight in grams for each hand.


.. figure:: static/manual.png?raw=true
   :alt: Manual control interface



Programmed control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

.. figure:: static/programmed.png?raw=true
   :alt: Program interface


Programs for blocks of stimuli can be entered in the text area. Programs
are simple lists of comma-separated integers. The first column specifies
the duration, the second the target in grams for the left hand, and the
third the target for the right hand. So, the following lines:

::

    20,500,500
    10,1000,2000

Denote a program which will deliver 500g to both hands for 20 seconds,
and then 1000g to the left and 2000g to the right hands for 10 seconds.

At the end of a program target weights are set to zero.



Get set, Stop and Reset buttons.
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

-  The get set button sets the target for both hands to 20g. This allows
   a participant to find a comfortable position, and for program to
   begin from a common reference point.
-  The stop button will always stop any program or manual setting, and
   reduce the target weights to zero. Additionally, the probes will be
   moved approx 1mm upwards to give the participant space to move their
   fingers.
-  The reset button moves both probes to their top resting points.





Instructions for participants
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,


.. note:: In addition to standard reminders that participants are free to withdraw from experiments at any time, participants in studies using the FAB should be explictly reminded that **if they wish to stop the study at any time they should simply remove their hands from the device by pulling backwards**.


The probes in contact with the participants' fingers are attached using magnets to ensure it will always be possible with only very moderate horzontal force, and it is recommended to demonstrate this feature to participants at the very start of the session.





Logging and data capture
,,,,,,,,,,,,,,,,,,,,,,,,,,,,

By default, log files will be saved into ``~/Documents/fab/logs/``.

The current log file name change be changed (e.g. per-participant) in the 'Detailed Log' tab, next to the console.





Troubleshooting and known issues
---------------------------------------------------------



Software hangs on start-up
  The device must start in a position where neither piston is activating the top-stop micro-switch. If the switch is depressed on startup the server may hang. The workaround is to remove power from the device and pull both pistons gently downwards approx 3 mm.





.. Pressure = 980kpa
.. 2kg in newtons / 2mm*10mm area  / 1000 = kpa
.. ( 19.6/ (.002*.01)  )/1000

.. Could be between 816 and 1225 kpa depending on width of contact spot









.. [Bingel2006] Bingel, Ulrike, Jürgen Lorenz, Eszter Schoell, Cornelius Weiller, and Christian Büchel. 2006. “Mechanisms of Placebo Analgesia: RACC Recruitment of a Subcortical Antinociceptive Network.” Pain 120 (1): 8–15.

.. [Forgione1971] Forgione, Albert G, and Theodore X Barber. 1971. “A Strain Gauge Pain Stimulator.” Psychophysiology 8 (1): 102–106.

.. [Montgomery1997] Montgomery, Guy H, and Irving Kirsch. 1997. “Classical Conditioning and the Placebo Effect.” Pain 72 (1): 107–113.

.. [Ptrovic2002] Petrovic, Predrag, Eija Kalso, Karl Magnus Petersson, and Martin Ingvar. 2002. “Placebo and Opioid Analgesia–Imaging a Shared Neuronal Network.” Science 295 (5560): 1737–1740.

.. [Posner1985] Posner, John, Andras Telekes, Dominic Crowley, Richard Phillipson, and Anthony W Peck. 1985. “Effects of an Opiate on Cold-Induced Pain and the CNS in Healthy Volunteers.” Pain 23 (1): 73–82.

.. [Treutwein1995] Treutwein, Bernhard. 1995. “Adaptive Psychophysical Procedures.” Vision Research 35 (17): 2503–2522.

.. [Wager2004] Wager, Tor D, James K Rilling, Edward E Smith, Alex Sokolik, Kenneth L Casey, Richard J Davidson, Stephen M Kosslyn, Robert M Rose, and Jonathan D Cohen. 2004. “Placebo-Induced Changes in FMRI in the Anticipation and Experience of Pain.” Science 303 (5661): 1162–1167.

.. [Whalley2008] Whalley, Ben, Michael E Hyland, and Irving Kirsch. 2008. “Consistency of the Placebo Effect.” Journal of Psychosomatic Research 64 (5): 537–541.




