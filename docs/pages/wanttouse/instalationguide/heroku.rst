HEROKU
************************

THERE ARE STILL ISSUES WITH DEPLOYING SAHANA EDEN TO HEROKU - Please help us to get this working & improve these docs!

INTRODUCTION
===================

Heroku ( http://www.heroku.com) is a Cloud Application which Sahana Eden can easily be deployed on. The basic deployment is free of cost and does not require a credit card. For making the deployment scalable, and to introduce more add-ons to the deployment, Heroku offers a number of different `Pricing <https://www.heroku.com/pricing>`_ options.

DEPLOYMENT
===================

The deployment process is very straightforward.:

- Create Heroku Account
- Install `Heroku Toolbelt <https://toolbelt.heroku.com/>`_
- Create Git Branch with Web2Py + Sahana Eden
- Create Heroku App

Create Git Branch With Web2Py + Sahana Eden
----------------

It's recommended to do this in a separate local directory to avoid interfering with your working Web2Py + Sahana Eden branches::

  # Choose the Admin Password
  read -p "Choose your admin password?" passwd

  # Get latest web2py
  git clone https://github.com/web2py/web2py.git web2py
  cd web2py/applications

  # Get Sahana Eden TRUNK.
  git clone https://github.com/flavour/eden.git eden

  # OR get your Sahana Eden branch.
  git clone https://github.com/YOUR_GIT_USERNAME/eden.git eden

  # Copy and edit the config file
  cp eden/modules/templates/000_config.py eden/models/000_config.py
  cat eden/models/000_config.py | sed "s/FINISHED_EDITING_CONFIG_FILE = False/FINISHED_EDITING_CONFIG_FILE = True/" > temp
  mv temp eden/models/000_config.py
  
Create Heroku App
----------------

Creating Heroku App::

  # Install virtualenv and postgres DB
  sudo pip install virtualenv
  sudo pip install psycopg2

  # Activate the virtual environment
  virtualenv venv --distribute
  source venv/bin/activate

  # Generate the requirements for Eden.
  cp applications/eden/requirements.txt .
  echo "" >> requirements.txt
  pip freeze >> requirements.txt

  # Write the Procfile used by heroku
  echo "web: python web2py.py -a '$passwd' -i 0.0.0.0 -p \$PORT" > Procfile

  # Create a remote for heroku
  heroku create

  # Choose the application name
  read -p "Choose your application name?" appname
  heroku apps:rename $appname    

  # Remove eden from version control and add it to web2py version control (there should be one version control)
  cd applications/eden/
  rm -rf .git
  git add -f .
  cd ../../
  git add .
  git add Procfile

  git commit -a -m "first commit"

  # Push Eden to heroku
  git push heroku master

  # Add add-ons : Postgres DB
  heroku addons:add heroku-postgresql:dev --app $appname
  heroku scale web=1 --app $appname

  # Open the application.
  heroku open --app $appname

UPDATES
===================

When changes merged and the pushed to Heroku the application is rebuilt with these changes.

Currently updates can only be made directly to the combined branch. We need instructions to set up the git branch so that the you can still update from the Sahana Eden branch, eg::

  # THIS DOES NOT CURRENTLY WORK
  # Pull changes from trunk
  git pull upstream git://github.com/flavour/eden.git master

  # OR Pull changes from your branch 
  git pull git://github.com/YOUR_GIT_USERNAME/eden.git master

  # Push Changes to Heroku App
  git push heroku master
  
TO DO
===================

- Preserve Sahana Eden git to be able to pull Sahana Eden updates
- Redirect to Sahana Eden - not ( Web2Py routes.py?)
- Access Error Tickets
- Commands / Scripts to clear the database
- Make a `Heroku Button <https://blog.heroku.com/archives/2014/8/7/heroku-button>`_


