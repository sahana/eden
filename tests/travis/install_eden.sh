#!/bin/bash
set -e
#
# Install a Sahana Eden Developer environment inside Travis

echo "updating routes"
echo "=========================="

cat << EOF > ../../web2py/routes.py
#!/usr/bin/python
default_application = 'eden'
default_controller = 'default'
default_function = 'index'
routes_onerror = [
        ('eden/400', '!'),
        ('eden/401', '!'),
        ('eden/*', '/eden/errors/index'),
        ('*/*', '/eden/errors/index'),
    ]
EOF

echo "installing eden dependencies"
echo "=========================="

# matplotlib, lxml take a lot of time to build. So, installing from binaries
# numpy installed by default
# apt-get install numpy
apt-get install python-matplotlib python-lxml python-shapely -q
apt-get install python3-matplotlib python3-lxml python3-shapely -q

python tests/travis/generate_requirements_file.py tests/travis requirements.txt tests/travis/requirements.txt
pip install -q -r tests/travis/generated_requirements.txt
echo "Packages installed:"
cat tests/travis/generated_requirements.txt

echo "configuring eden"
echo "=========================="

cp -r . ../../web2py/applications/eden
cd ../../web2py/applications/eden
chown -R ${USER} .

cp modules/templates/000_config.py models/000_config.py

sed -ie 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' models/000_config.py
sed -ie 's|\#settings.base.prepopulate += ("default", "default/users")|settings.base.prepopulate += ("default", "default/users")|' models/000_config.py
