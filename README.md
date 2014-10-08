# The pain machine


This is the control software for the pain machine, intended to run on the raspberry pi.


To install:

    sudo pip install virtualenvwrapper
    mkvirtualenv pain

    git clone https://github.com/puterleat/painmachine.git
    cd painmachine
    pip install -r requirements.txt


To run:

    python -u painmachine.py


Then open [http://127.0.0.1:2008/](http://127.0.0.1:2008/) in a reasonable browser (not tested in IE, and certainly won't work in an old IE).



## TODO

- Allow calibration by marking with button when system at 2kg on scales


