INSTALLATION GUIDELINES: WINDOWS - END-USER
************************

This is a very common use case for Emergency Management workers in the field with poor connectivity to central servers.

It can be run on a Laptop or even on a USB stick.

Install Sahana-Eden
===================

This installer is for End-Users:

- http://eden.sahanafoundation.org/downloads/sahana-eden-setup.exe (35Mb. Updated: 2012-10-27)

The installer contains both - a Portable version (for USB pendrives and external harddrives) and a Local version to be installed on
the built-in harddrive. Sahana Eden requires a minimum of ~ 80MB free space, although more is recommended. NOTE: PDF-Support (reportlab) 
is currently broken in the installer-version. If you need it you have to install Python and the dependencies and get the current 
Eden-version from the VCS, not recommended for unexperienced users.

Launch Sahana-Eden
===================

- For the Local version: Either double-click on the shortcuts on your Desktop or the Startmenu or navigate to your installation directory and double-click on startweb2py.bat
- For the Portable version: Either use the Autostart/USB menu if available on your Operating System (Windows XP or older) or run the start-eden.bat in the root directory of your portable drive.


Done!
===================

- If not done automatically open a webbrowser and navigate to  http://localhost/

Configure As Windows Service (Optional)
===================
Configure as Windows Service::

  Navigate to your Sahana Eden installation.
  Right click on the options_std.py and rename it to options.py
  Open the renamed file and set your settings in it. Save it afterwards.
  Now navigate to the head-directory  of your Eden Installation (if you installed it to C:\Users\Public\SahanaEden\ it would be C:\Users\Public\)
  Shift + Right click on the SahanaEden-Folder and click "Open Command-Prompt here"
  In the Command-Prompt type "web2py.exe -W install"
  Done! 
  
  
- http://web2py.com/AlterEgo/default/show/77
- http://groups.google.com/group/web2py/browse_thread/thread/733896d0aec07d3e
- How the current installer was built: InstallationGuidelines/Windows/Maintenance
- `BluePrint/Installer/Windows <http://eden.sahanafoundation.org/wiki/BluePrint/Installer/Windows>`_

Attachments
===================

- `Autorun.inf <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Windows/User/Autorun.inf>`_ `Download <http://eden.sahanafoundation.org/raw-attachment/wiki/InstallationGuidelines/Windows/User/Autorun.inf>`_ (43 bytes) - added by *flavour* `6 years ago <http://eden.sahanafoundation.org/timeline?from=2011-10-22T06%3A58%3A14%2B01%3A00&precision=second>`_ . "For the USB"
- `favicon.ico <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Windows/User/favicon.ico>`_ `Download <http://eden.sahanafoundation.org/raw-attachment/wiki/InstallationGuidelines/Windows/User/favicon.ico>`_ (4.2 KB) - added by *flavour* `6 years ago <http://eden.sahanafoundation.org/timeline?from=2011-10-22T06%3A58%3A23%2B01%3A00&precision=second>`_ .
- `sahana.cmd <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Windows/User/sahana.cmd>`_ `Download <http://eden.sahanafoundation.org/raw-attachment/wiki/InstallationGuidelines/Windows/User/sahana.cmd>`_ (123 bytes) - added by *flavour* `6 years ago <http://eden.sahanafoundation.org/timeline?from=2011-10-22T06%3A58%3A37%2B01%3A00&precision=second>`_ . "Start script for USB version"
