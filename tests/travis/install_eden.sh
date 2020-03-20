#!/bin/bash
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

echo "configuring eden"
echo "=========================="

BRANCH_HOME=`pwd`

ln -s $BRANCH_HOME ../../web2py/applications/eden
chown -R ${USER} .

CONFIG=models/000_config.py
cp modules/templates/000_config.py $CONFIG
sed -ie 's|EDITING_CONFIG_FILE = False|EDITING_CONFIG_FILE = True|' $CONFIG
sed -ie 's|settings.base.template = "default"|settings.base.template = ("default", "default.Demo")|' $CONFIG
sed -ie 's|\#settings.base.prepopulate += ("default", "default/users")|settings.base.prepopulate += ("default", "default/users")|' $CONFIG
