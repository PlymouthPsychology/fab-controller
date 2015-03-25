

**********
User guide
**********




Getting started
^^^^^^^^^^^^^^^^^^

1. Connect both the DC power input and the USB cables.
2. Run the ``fab`` command from the Terminal.


On running the ``fab`` command, a browser window will open containing
the user interface for the FAB device, shown below.

.. figure:: _static/manual.png?raw=true
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

-  Target value for the weight in grams to be applied to each hand.
-  The actual measurements recorded by the sensor [#actualforce]_.


.. [#actualforce] Note that the exact pressure applied to the finger will vary as a function of the probe size.


Targets can be set in 'grams' for each hand[#grams]_. Once a target has been set
the control software moves the probes up and down, attempting to
maintain the target weight, as measured by the sensor. Thus where
participants flex or move their fingers, the system will attempt to
compensate to keep the measured force constant.



Manual control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

Using the slider controls under the 'manual' tab, you can set a target
weight in grams for each hand.


.. figure:: _static/manual.png?raw=true
   :alt: Manual control interface



Programmed control
,,,,,,,,,,,,,,,,,,,,,,,,,,,,,

.. figure:: _static/programmed.png?raw=true
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




Logging and data capture
,,,,,,,,,,,,,,,,,,,,,,,,,,,,

By default, log files will be saved into ``~/Documents/fab/logs/``.

The current log file name can be changed (e.g. per-participant) in the 'Detailed Log' tab, next to the console.

