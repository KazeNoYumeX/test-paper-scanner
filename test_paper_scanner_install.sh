whoami=`whoami`

# Remove because ubuntu always root, but root is not good
#if [ $(id -u) -eq 0 ]; then
#  echo "Please not run as root"
#  exit
#fi

# apt
sudo apt update

# required PPA
sudo apt install software-properties-common -y
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.11 -y

sudo apt -y install python3-pip
sudo pip3 install --upgrade pip

sudo pip3 install virtualenv

# deb
version=$(cat version)
sed -i "s/__version__.*/__version__ = \"$version\"/" Test_Paper_Scanner/__init__.py

python3 setup.py bdist_wheel
rm dist/scanner/Test_Paper_Scanner/*.whl
mv dist/Test_Paper_Scanner*.whl dist/scanner/Test_Paper_Scanner/
sudo mv requirements.txt dist/scanner/Test_Paper_Scanner
sudo mv dist/scanner/ /opt/
sudo mv Test_Paper_Scanner.service /etc/systemd/system/

virtualenv --python=python3.11 /opt/scanner/Test_Paper_Scanner/venv
/opt/scanner/Test_Paper_Scanner/venv/bin/python -m pip install --upgrade pip
/opt/scanner/Test_Paper_Scanner/venv/bin/pip3 install --force-reinstall /opt/scanner/Test_Paper_Scanner/Test_Paper_Scanner*
/opt/scanner/Test_Paper_Scanner/venv/bin/pip3 install -r /opt/scanner/Test_Paper_Scanner/requirements.txt

vim /opt/scanner/Test_Paper_Scanner/Test_Paper_Scanner_config.ini
cd /opt/scanner/Test_Paper_Scanner
export FLASK_APP=Test_Paper_Scanner.app

# service
sudo sed -i "s/User=.*/User=$whoami/" /etc/systemd/system/Test_Paper_Scanner.service
sudo systemctl daemon-reload
sudo systemctl enable Test_Paper_Scanner.service
sudo systemctl restart Test_Paper_Scanner.service
echo 'Test Paper Scanner server installation finished'
