LINUX (PRODUCTION)
************************


Whilst any Linux distribution should be suitable, we use & hence support Debian v7 'Wheezy'. This is best installed using the `netinst <https://www.debian.org/CD/netinst/>`_ CD image. Default settings can be accepted, although we would recommend a dedicated 
partition for /var/log to reduce the possibility of a Denial of Service attack. It is not recommended to install a graphical desktop,
so this should be de-selected.

The easiest way to install onto Debian is to use the scripts which we've developed. If you wish to do a manual install, then you may use
these parts of these scripts as guidance (they are suitably commented). The scripts can be uploaded to the server using `WinSCP <https://winscp.net/eng/docs/lang:es>`_ . All 
administration can be done using `PuTTY <https://the.earth.li/~sgtatham/putty/0.70/w32/putty.exe>`_ .

We support either:

- `Apache/MySQL <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Linux/Server/ApacheMySQL>`_ 
- `Cherokee/PostgreSQL <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Linux/Server/CherokeePostgreSQL>`_

We support either of these on Amazon's EC2

- `Amazon EC2 <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Amazon>`_ 

Other (unsupported) guidelines:

- `Apache/PostGIS/Debian(8) <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Amazon>`_ 

Other combinations are, of course, possible, but we don't provide installation scripts for these.

- `ConfigurationGuidelines <http://eden.sahanafoundation.org/wiki/ConfigurationGuidelines>`_ 
- `MaintenanceGuidelines <http://eden.sahanafoundation.org/wiki/MaintenanceGuidelines>`_ 
- `MaintenanceGuidelines/Monitoring <http://eden.sahanafoundation.org/wiki/MaintenanceGuidelines/Monitoring>`_ 
- `TroubleShooting <http://eden.sahanafoundation.org/wiki/TroubleShooting>`_ 
- `SysAdmin <http://eden.sahanafoundation.org/wiki/SysAdmin>`_ 
- `GIS Tools <http://eden.sahanafoundation.org/wiki/GIS#Tools>`_ 

NOTES
===================

Here are a few notes on other platforms which should work, but which aren't supported by us:

- `Apache with mod_python <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesApacheModPython>`_ 
- `Apache with mod_proxy <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesApacheModProxy>`_ 
- `Apache with CGI <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesApacheCGI>`_ 
- `Apache with FastCGI <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesApacheFastCGI>`_ 
- `Cluster <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Cluster>`_ 
- `Lighttpd <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesLighttpd>`_ 
- `nginx <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesNginx>`_ 
- `GoogleAppEngine <http://eden.sahanafoundation.org/wiki/InstallationGuidelinesGoogleAppEngine>`_ 
- `RedHat <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Linux/Server/RedHat>`_ 
- `VirtualEnv <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/VirtualEnv>`_ 

