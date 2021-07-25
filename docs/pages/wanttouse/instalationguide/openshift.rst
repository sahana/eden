OPENSHIFT
************************

INTRODUCTION
===================

`OpenShift <https://www.openshift.com/>`_ is an Open Hybrid Cloud Application Platform / PaaS by Red Hat.It has a free plan as well as enterprise pricing options.

Here is a good `post <http://stackoverflow.com/questions/17727788/deploying-ruby-on-rails-is-there-a-good-alternative-for-heroku>`_ comparing `Heroku <http://heroku.com/>`_ and `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_

DEPLOYMENT STEPS
===================

Install RHC
----------------

The first step is to create an account on `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_ - it's free and easy.

The next step is to intstall RHC.RHC is the `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_ client tool. The simplest way to install it is to do::

  sudo gem install rhc
  
If the above command doesn't work install `Ruby first <https://www.ruby-lang.org/en/downloads/>`_ and then `Ruby Gems <http://rubygems.org/pages/download>`_

Deploy The Template Web2py App
----------------

Now we create a blank web2py app and get it running on `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_ . For this we use the following `repo <https://github.com/prelegalwonder/openshift_web2py>`_ .

You can follow the instructions given in the readme except change the Python version to 2.7 instead of 2.6

The basic steps are-

Create a python-2.7 application::

  rhc app create -a YOUR_APP_NAME -t python-2.7
  
Add this upstream repo::

    cd YOUR_APP_NAME
    git remote add upstream -m master git://github.com/prelegalwonder/openshift_web2py.git
    git pull -s recursive -X theirs upstream master
    Note: If you want a specific release and not the latest snapshot, 
    replace "master" with the branch name in the above lines (ie. 2.3.2).
    
Then push the repo upstream::

    git push
    
That's it, you can now checkout your application at::

    https://YOUR_APP_NAME-$yournamespace.rhcloud.com 
    # you'll be prompted for your namespace while creating your account, you needn't worry about it.

Once your app is up you'll need administrative access to continue.For the admin app to work you need to put your password hash in parameters_8080.py in wsgi/web2py/.

If you are using Ubuntu, you can find in your laptop, in "/home/YOUR_APP_NAME/wsgi/web2py/" a file called Parameters_*.py. there is a possibility that you can find more than one, with different numbers at the end. remove all of this file. then::

  $web2py.py -p 8080 -a YOUR_PASSWORD
  
OR::

  $web2py -p 8080 -a YOUR_PASSWORD

it will create a file called 'Parameters_8080.py' in directory /home/YOUR_APP_NAME/wsgi/web2py/ then do these::

  $ln -s parameters_8080.py parameters_443.py
  $ln -s parameters_8080.py parameters_80.py
  $ln -s parameters_8080.py parameters_8000.py
  $git add .
  $git commit
  $git push
  
Your parameters_*.py files will be sent to openshift. And then you can open  https://YOUR_APP_NAME-$yournamespace.rhcloud.com via your web browser, and use your password you just created. if it is not working, try to enable your browser to accept cookies.

Package And Deploy Eden
----------------

Now locally create package your local Eden setup via the administrative interface. Then create a new application on your `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_ by uploading the package.

To be able to do this, first you need to install Sahana Eden in your laptop. If you are using Ubuntu, the easiest possibility is to install `the windows version <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Windows/User>`_ using virtual machine such as   `Oracle Virtual Box <https://www.virtualbox.org/>`_ .

There is a file called 'Web2py.py' somewhere in your windows system. Find this using the windows explorer search facility. Probably it is located in C:\Users\Public\SahanaEden?. Then double click to run this file. Wait until it shows a small window, choose server IP= Local (127.0.0.1), enter a Password and press the 'Start Server' button. Your Web browser will directly trying to connect to that ip address. Stop it, and Go to:  http://127.0.0.1:8000/admin

Your browser will show the web2py admin page. enter your password and press Login. Now, on the left side, you will see many button, one of them, under Eden dir is called "Pack all". Press this button, and wait until its done (will take some time). The result is a file called "web2py.app.eden.w2p", this is the package that needs to be uploaded into Openshift.

Use your browser, and go to:  https://YOUR_APP_NAME-$yournamespace.rhcloud.com, enter the administrative interface, enter your password, and press Login. Now, you are at the Openshift Web2py admin page. On the right side, you can see: "Upload and install packed application" section, fill in the Application name, and choose your "web2py.app.eden.w2p" file, and then press Install. It will take some time to finish the uploading process, if it is interrupted, just repeat the process.

When it is installed, you will see your Application name on the left side. Phew.

If using 'web2py.app.eden.w2p' is only producing frustrating error message, use the 'Or Get from URL' option, and copy this::

  https://github.com/flavour/eden.git
  
and then press Install.

The next step is to install postgresql. From Ubuntu, use the terminal, and type::

  $rhc cartridge add postgresql-8.4 -a YOUR_APP_NAME

Once Eden is installed you will need OpenShift to install a lot of the required packages and libraries for it to work.For that edit the setup.py file in the following way-

Edit the install_requires line to::
  
  install_requires=['newrelic','GitPython','xlrd','lxml','shapely','python-dateutil','xlwt','pyserial','tweepy','pil'],

Note that these are only some of the libraries - please add them as needed. You can find the setup.py file in your own laptop. if you use Ubuntu, you can find it in /home/YOUR_APP_NAME::

  $gedit setup.py  # find a line 'install_requires', and make the above changes. CTRL-S and close gedit window.
  $git add .
  $git commit   # make sure you see file 'setup.py' is included in the list.
  $git push
  
Now, Access your openshift web2py admin page through  https://YOUR_APP_NAME-$yournamespace.rhcloud.com Enter your password, find a folder named 'models' and find a file named '000_config.py. Edit and save the file. In order to edit this file, you will need basic information of your postgresql. In your terminal, type::

  $rhc ssh
  $env | grep OPENSHIFT

you will see lots of lines, containing your postgresql info. Use this to edit the 000_config.py

If you are lucky, you can access Sahan Eden from Openshifht now. If not, pray for help might help you.

Probably you will receive an error message saying something about "No such file or directory: 'applications/sahana/models/0000_update_check.py'". Before you start praying, try to access your application at openshift server, using::

  $rhc ssh
  
then go to your sahana eden directory, and find a directory named 'models'. Inside 'models' directory, type::

  $nano 0000_update_check.py
  
then write::

  CANARY_UPDATE_CHECK_ID = 4

followed by CTRL-O, ENTER, and CTRL-X So, you have created the file yourself. at least, this way works for me.

You can find your openshift Sahana eden web address from Web2py administrative page, folder 'your application name' (the one that you uploaded), move your mouse cursor above it, and you can see the web address. If it still doesn't work, you can start praying now.

Updates
----------------

To deploy updates simply package Eden locally and re-deploy it on `OpenShift <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/OpenShift>`_ via the admin interface ( check the overwrite installed app option)

TODO?
===================

- Have the admin interface directly fetch Eden from a Git repo.

