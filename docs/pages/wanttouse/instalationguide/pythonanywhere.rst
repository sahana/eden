PythonAnywhere
************************

1. Sign up for a account at  https://www.pythonanywhere.com/pricing/ Beginner account will also do :)
2. Go to web tab
3. Press on add a new app button (Remember that you can only run a single app with a free account)
4. Configure the settings. Select web2py (If you want to deploy eden). Select the directory where you want to put the files of your app (By default it is /home/your_username/web2py/). Enter the administrative password. You will be issued with a domain which can be used to access your web2py server. (In case of a free account, it will be your_username.pythonanywhere.com)
5. After completing configuration, go to Files tab
6. There you will find a folder as specified by you in the configuration settings (web2py if you chose default settings)
7. Go to Your_Folder/applications
8. Here you can upload your Eden folder.
9. You can directly pull code from github. Go to Consoles tab and open Bash editor. Go to applications directory of your web2py project(cd your_app_folder/applications/). $ Clone the repo you want to deploy : git clone  https://github.com/username/repo_name
10. You can also compress your project folder on your own PC, and upload it using the Files tab. Then, open a Bash console to run unzip to decompress the zipfile you've uploaded.
11. You now have the web2py application you want to test ready for deployment. You can now go on and start the web2py server.
12. Go to /home/your_username/web2py/ using the bash editor
13. Run the following command::
  $ python web2py.py -a "your_desired_password"
14. This will start the web2py server on your created domain for this app ( https://your_username.pythonanywhere.com/ in case of a free account)
15. You can now navigate to other tabs(or do other things) and the bash console will keep running as a separate thread. In order to kill the current console you can go to "Console" tab and kill the desired bash console from the list.

**Creating MySQL Database**

1. In your pythonanywhere account go to Databases Tab
2. Go to MySQL Tab
3. Set the password for you MySQL connection then proceed
4. In the Create Database portion enter the database name that you want, then click create.
5. The details of you database will be shown once you have successfully created it.

Database host address : username.mysql.pythonanywhere-services.com

Database name : username$databasename

**Connecting your Database to Eden**

1. Proceed to the File Tab and navigate to your 000_config.py file. if you didn't change the name in the setup it will be in /home/username/web2py/applications/eden/models
2. Uncomment and edit the following lines::
  settings.database.db_type = "mysql"
  
  settings.database.host = "username.mysql.pythonanywhere-services.com"
  
  settings.database.database = "username$databasename"
  
  settings.database.username = "your pythonanywhere username"
  
  settings.database.password = "MySQL password you created"
  
3. Save it.
4. Go back to your dashboard and proceed to Web Tab
5. Click Reload and then proceed to accessing your Eden Site
