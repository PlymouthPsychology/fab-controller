# TODO

- Calibration by marking with button when system at 2kg on scales?


# The pain machine


This is the control software for the pain machine, intended to run on the raspberry pi.



To install:

    sudo pip install virtualenvwrapper
    mkvirtualenv pain

    git clone https://github.com/puterleat/painmachine.git
    cd painmachine
    pip install -r requirements.txt

    git clone https://github.com/WiringPi/WiringPi-Python.git
    cd WiringPi-Python
    git submodule update --init
    sudo cp WiringPi/wiringPi/*.h /usr/include/  # headers not copied otherwise???
    sudo python setup.py install

    cd ~/
    git clone git://git.drogon.net/wiringPi
    cd wiringPi
    git pull origin
    ./build

To run:

    python painserver.py


Then open [http://127.0.0.1:5000/](http://127.0.0.1:5000/) in a reasonable browser (not tested in IE, and certainly won't work in an old IE).




sudo apt-get install python-setuptools
sudo python get-pip.py
sudo pip install -r requirements.txt
