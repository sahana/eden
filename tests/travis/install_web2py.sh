#!/bin/bash

# Install a web2py Developer environment inside Travis

echo "installing required packages"
echo "============================"

sudo apt-get update -qq
sudo apt-get -q install build-essential

echo "downloading and installing web2py"
echo "================================="

# Handle for the checkout-directory (different paths for different repos)
BRANCH_HOME=`pwd`

# Use web2py-2.21.1-stable
WEB2PY_COMMIT=6da8479

# Clone web2py under build home (usually /home/travis/build)
cd ../..
git clone --recursive git://github.com/web2py/web2py.git

# Reset to target version
cd web2py
if [ ! -z "$WEB2PY_COMMIT" ]; then
   git reset --hard $WEB2PY_COMMIT
   git submodule update --recursive
fi

# Patch web2py/PyDAL
PYDAL=gluon/packages/dal/pydal
case $WEB2PY_COMMIT in
    59700b8 )
        # 2.18.5 patches

        # Scheduler (not needed for CI since not running scheduler)
        #cd gluon
        #wget http://eden.sahanafoundation.org/downloads/scheduler.diff
        #patch -p0 < scheduler.diff
        #cd ..

        # Shell (see https://github.com/web2py/web2py/issues/2292)
        git apply $BRANCH_HOME/tests/travis/shell-2.18.5.diff

        # PyDAL
        sed -i "s|if getattr(func, 'validate', None) is Validator.validate:|if getattr(func, 'validate', None) is not Validator.validate:|" $PYDAL/validators.py
        sed -i "s|\['password'\]|['passwd']|" $PYDAL/adapters/mysql.py
        ;;
esac

# Return to build home and fix permissions
cd ..
chown -R ${USER} web2py
