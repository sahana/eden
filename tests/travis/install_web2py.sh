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

# Use web2py-2.18.5-stable
WEB2PY_COMMIT=59700b8

cd ../..
git clone --recursive git://github.com/web2py/web2py.git
cd web2py
if [ ! -z "$WEB2PY_COMMIT" ]; then
   git checkout $WEB2PY_COMMIT
   git submodule update
fi
cd gluon
wget http://eden.sahanafoundation.org/downloads/scheduler.diff
patch -p0 < scheduler.diff
sed -i "s|if getattr(func, 'validate', None) is Validator.validate:|if getattr(func, 'validate', None) is not Validator.validate:|" packages/dal/pydal/validators.py
sed -i "s|\['password'\]|['passwd']|" packages/dal/pydal/adapters/mysql.py
cd ..
mv handlers/wsgihandler.py .
cd ..

chown -R ${USER} web2py
