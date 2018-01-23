#!/bin/bash

# Install a web2py Developer environment inside Travis

echo "installing required packages"
echo "============================"

apt-get update -qq
apt-get -q install python-dev
apt-get -q install build-essential
apt-get -q install python
apt-get -q install python-psycopg2


echo "downloading and installing web2py"
echo "================================="

# Use web2py-2.16.1-stable
WEB2PY_COMMIT=7035398

cd ../..
git clone --recursive git://github.com/web2py/web2py.git
cd web2py
if [ ! -z "$WEB2PY_COMMIT" ]; then
   git checkout $WEB2PY_COMMIT
   git submodule update
fi
mv handlers/wsgihandler.py .
cd ..

chown -R ${USER} web2py
