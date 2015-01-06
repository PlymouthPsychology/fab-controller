
hash pip &> /dev/null
if [ $? -eq 1 ]; then
    echo "Installing package manager"
	sudo easy_install pip
	sudo pip install virtualenvwrapper
else
	echo "Pip already installed"
fi


cd ~/Applications/

echo "Installing controller software"
git clone https://github.com/puterleat/fab-controller.git



echo "Installing dependencies"
source /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv FAB
pip install -r ~/Applications/fab-controller/requirements.txt

echo "Creating logfile folder..."
mkdir -pv ~/Documents/fab/logs/
touch ~/Documents/fab/logs/log.txt


echo "Finished installing"


