
hash pip &> /dev/null
if [ $? -eq 1 ]; then
    echo "Installing package manager"
	sudo easy_install pip
	sudo pip install virtualenvwrapper
else
	echo "Pip already installed"
fi


echo "Installing controller software"
git clone https://github.com/puterleat/fab-controller.git
cd fab-controller

echo "Installing dependencies"
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv FAB
pip install -r requirements.txt

echo "Finished installing"