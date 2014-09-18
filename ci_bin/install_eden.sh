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

python ci_bin/generate_requirements_file.py ci_bin requirements.txt optional_requirements.txt
pip install -q -r ci_bin/generated_requirements.txt

echo "Packages installed:"
cat ci_bin/generated_requirements.txt

# matplotlib, lxml take a lot of time to build. So, installing from binaries
# numpy installed by default
apt-get install python-matplotlib python-lxml -q
# apt-get install numpy #already present

echo "configuring eden"
echo "=========================="

cp -r . ../../web2py/applications/eden
cd ../../web2py/applications/eden
chown -R ${USER} .

cp private/templates/000_config.py models/000_config.py

sed -ie 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' models/000_config.py
sed -ie 's|\#settings.base.prepopulate = ("default", "default/users")|settings.base.prepopulate = ("default", "default/users")|' models/000_config.py
