#!/bin/bash

# Install a web2py Developer environment inside Travis

echo "installing required packages"
echo "=========================="

apt-get update -qq
apt-get -q install python-dev
apt-get -q install build-essential
apt-get -q install python


echo "downloading and installing web2py"
echo "==========================================="

cd ../..
rm web2py_src.zip*
wget -nv http://web2py.com/examples/static/web2py_src.zip
unzip -q web2py_src.zip
chown -R ${USER} web2py
rm web2py_src.zip*
mv web2py/handlers/wsgihandler.py web2py/wsgihandler.py
