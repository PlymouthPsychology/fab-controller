

The FAB Hardware
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


.. [#grams]  Where 1kg = 9.8 mN


.. figure:: _static/piston_300.jpg?raw=true
   :alt: The FAB piston and probe
   :width: 200 px

   The FAB piston and probe



.. figure:: _static/pistons_long_shot_300.jpg?raw=true
   :alt: The prototype cabinet and both pistons
   :width: 200 px

   The prototype cabinet and both pistons





