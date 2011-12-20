#
# http://eden.sahanafoundation.org/wiki/SysAdmin
#
# Assumptions:
# - for PostgreSQL, running Debian Squeeze's version of PostGIS
# - for MySQL, /root/.my.cnf is configured to allow root access to MySQL without password
# - root on Prod can SSH to Test without password
#
# Usage:
# fab [test|demo|prod] deploy
#

from __future__ import with_statement
from fabric.api import *
from fabric.colors import red, green
import os
from datetime import date
import pexpect

# Database
# - default to MySQL currently
env.database = "mysql"

# For PostGIS
# Debian Squeeze
env.postgis_path = "/usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql"
env.postgis_spatial_ref_path = "/usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql"
# Ubuntu Lucid: copy these lines into the host definition
#env.postgis_path = "/usr/share/postgresql/8.4/contrib/postgis.sql"
#env.postgis_spatial_ref_path = "/usr/share/postgresql/8.4/contrib/spatial_ref_sys.sql"

# Definitions for 'Demo' infrastructure
# (updates from Trunk)
env.tested = False
def demo():
    env.user = "root"
    env.database = "postgresql"
    env.hosts = ["demo.eden.sahanafoundation.org"]

def camp():
    env.user = "root"
    env.database = "postgresql"
    env.hosts = ["eden.camp.sahanafoundation.org"]

def larc():
    env.user = "root"
    env.database = "postgresql"
    env.hosts = ["larc.sahanafoundation.org"]

def libya():
    env.user = "root"
    env.database = "postgresql"
    env.hosts = ["libya.sahanafoundation.org"]

def atlantico():
    env.user = "root"
    env.hosts = ["atlantico.colombia.sahanafoundation.org"]

def california():
    env.user = "root"
    env.hosts = ["california.sahanafoundation.org"]

def japan():
    env.user = "root"
    env.database = "postgresql"
    env.hosts = ["japan.sahanafoundation.org"]

def taiwan():
    env.user = "root"
    env.hosts = ["taiwan.sahanafoundation.org"]

def vietnam():
    env.user = "root"
    env.hosts = ["vietnam.sahanafoundation.org"]

# Definitions for 'Test' infrastructure
# (updates from Trunk after copying data from Prod)
# NB Not yet supported with PostgreSQL (db_sync not yet supported)
test_host = "test.eden.sahanafoundation.org"
def test():
    env.user = "root"
    env.hosts = [test_host]

# Definitions for 'Production' infrastructure
# (updates from version currently on Test)
# NB Script needs reworking to be able to support multiple concurrent instances
prod_host = "pakistan.sahanafoundation.org"
def pakistan():
    env.user = "root"
    env.tested = True
    env.hosts = [prod_host]

# Definitions for 'All' infrastructure
# used for OS updates
all_hosts = ["eden.sahanafoundation.org", "demo.eden.sahanafoundation.org", "ci.eden.sahanafoundation.org", "humanityroad.sahanafoundation.org", "geo.eden.sahanafoundation.org"]
def all():
    """ List of server(s) for All infrastructure """
    env.user = "root"
    env.hosts = all_hosts


# Key distribution and management
env.key_filename = ["/root/.ssh/sahana_release"]
def generate_keys():
    """ Generate an SSH key to be used for password-less control """
    local("ssh-keygen -N '' -q -t rsa -f ~/.ssh/sahana_release")

def distribute_keys():
    """ Distribute keys to servers - requires preceding with 'test' or 'prod' """
    local("ssh-copy-id -i ~/.ssh/sahana_release.pub %s@%s" % (env.user, env.host))

#
# Deployment, Maintenance and Migrations
#

def deploy():
    """
        Perform the full upgrade cycle
        - need to prefix with 'demo', 'test' or 'prod'
    """
    print(green("Deploying to %s" % env.host))
    maintenance_on()
    backup()
    pull()
    cleanup()
    migrate_on()
    if "test" in env.host:
        db_sync()
    else:
        db_upgrade()
        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()
        # Do the actual DB upgrade
        # (split into a separate function to allow it to easily be run manually if there is a problem with the previous step)
        db_upgrade_()
    migrate_off()
    optimise()
    maintenance_off()

def backup():
    """ Backup the current state """
    print(green("%s: Backing up" % env.host))
    with cd("/home/web2py/applications/eden/"):
        # Backup VERSION for rollbacks
        run("cp -f VERSION /root", pty=True)
        # Backup customised files
        # - should just be 000_config, Views, 00_db & zzz_1st_run prod optimisations
        # - currently still a few controller settings not yet controlled by deployment_settings
        # Using >, >> causes an error to be reported even when there's no error
        env.warn_only = True
        run("bzr diff controllers > /root/custom.diff", pty=True)
        run("bzr diff models >> /root/custom.diff", pty=True)
        run("bzr diff views >> /root/custom.diff", pty=True)
        env.warn_only = False
        # Backup database
        if env.database == "mysql":
            run("mysqldump sahana > /root/backup.sql", pty=True)
        elif env.database == "postgresql":
            run("sudo -H -u postgres pg_dump --disable-triggers -T spatial_ref_sys sahana > /root/backup.sql", pty=True)
        # Backup databases folder (includes sqlite db if used)
        run("rm -rf /root/databases", pty=True)
        run("cp -ar /home/web2py/applications/eden/databases /root", pty=True)
        # Backup uploads folder
        run("rm -rf /root/uploads", pty=True)
        run("cp -ar /home/web2py/applications/eden/uploads /root", pty=True)
        # Tar it all up
        filename = "/root/%s-%s.tar" % (env.host, str(date.today()))
        run("tar cf %s /root/VERSION /root/backup.sql /root/custom.diff /root/databases/ /root/uploads/" % filename, pty=True)
        env.warn_only = True
        run("rm -f %s.gz" % filename, pty=True)
        env.warn_only = False
        run("gzip -9 %s" % filename, pty=True)
        # scp it offsite
        # tbc

def cleanup():
    """
        Cleanup after the bzr pull
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Cleaning up" % env.host))
    with cd("/home/web2py/applications/eden/"):
        # Remove compiled version of the app
        run("/bin/rm -rf compiled", pty=True)
        # Resolve conflicts
        # @ToDo deal with .moved files
        run("find . -name *.BASE -print | xargs /bin/rm -f", pty=True)
        run("find . -name *.THIS -print | xargs /bin/rm -f", pty=True)
        run("for i in `find . -name *.OTHER` ; do mv $i ${i/.OTHER/}; done", pty=True)
        run("bzr resolve", pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        # @ToDo: Only apply customisations to files which had conflicts
        env.warn_only = True
        run("patch -f -p0 < /root/custom.diff", pty=True)
        env.warn_only = False

def db_create():
    """
        Create a new, empty Database
    """
    with cd("/home/web2py/applications/eden/"):
        print(green("%s: Creating new Database" % env.host))
        if env.database == "mysql":
            run("mysqladmin create sahana", pty=True)
        elif env.database == "postgresql":
            run("sudo -H -u postgres createdb -O sahana -E UTF8 sahana -T template0", pty=True)
            run("sudo -H -u postgres createlang plpgsql -d sahana", pty=True)
            run("sudo -H -u postgres psql -q -d sahana -f %s" % env.postgis_path, pty=True)
            run("sudo -H -u postgres psql -q -d sahana -f %s" % env.postgis_spatial_ref_path, pty=True)

def db_drop():
    """
        Drop the old Database
    """
    with cd("/home/web2py/applications/eden/"):
        print(green("%s: Dropping old Database" % env.host))
        # If database doesn't exist, we don't want to stop
        env.warn_only = True
        if env.database == "mysql":
            run("mysqladmin -f drop sahana", pty=True)
        elif env.database == "postgresql":
            run("pkill -f 'postgres: sahana sahana'", pty=True)
            run("sudo -H -u postgres dropdb sahana", pty=True)
        env.warn_only = False
        print(green("%s: Cleaning databases folder" % env.host))
        run("rm -rf databases/*", pty=True)

def db_upgrade():
    """
        Upgrade the Database
        - For MySQL, this assumes that /root/.my.cnf is configured on both Test & Prod
        to allow root to have access to the MySQL DB without needing '-u root -p'
    """
    print(green("%s: Upgrading Database" % env.host))
    # See dbstruct_mysql.py
    # Step 0: Drop old database 'sahana'
    db_drop()
    # Step 1: Create a new, empty database 'sahana' as-normal
    db_create()
    with cd("/home/web2py/applications/eden/"):
        # Step 2: set deployment_settings.base.prepopulate to False in models/000_config.py
        print(green("%s: Disabling prepopulate" % env.host))
        run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = 0/' models/000_config.py", pty=True)

def db_upgrade_():
    """
        Upgrade the Database (called by db_upgrade())
        - For MySQL, this assumes that /root/.my.cnf is configured on both Test & Prod
          to allow root to have access to the DB without needing '-u root -p'
    """
    with cd("/root/"):

        # Step 5: Use the backup to populate a new table 'old'
        print(green("%s: Restoring backup to 'old'" % env.host))
        # If database doesn't exist, we don't want to stop
        env.warn_only = True
        if env.database == "mysql":
            run("mysqladmin -f drop old", pty=True)
        elif env.database == "postgresql":
            run("pkill -f 'postgres: postgres old'", pty=True)
            run("sudo -H -u postgres dropdb old", pty=True)
        env.warn_only = False
        if env.database == "mysql":
            run("mysqladmin create old", pty=True)
            run("mysql old < backup.sql", pty=True)
        elif env.database == "postgresql":
            run("sudo -H -u postgres createdb -E UTF8 old -T template0", pty=True)
            run("sudo -H -u postgres psql -q -d old -f backup.sql", pty=True)

    # Step 7: Run the script: python dbstruct_mysql.py
    # use pexpect to allow us to jump in to do manual fixes
    print(green("%s: Fixing Database Structure" % env.host))
    child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
    child.expect(":~#")
    child.sendline("cd /home/web2py/applications/eden/static/scripts/tools")
    child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
    if env.database == "mysql":
         child.sendline("python dbstruct_mysql.py")
    elif env.database == "postgresql":
        child.sendline("python dbstruct_postgresql.py")
    # @ToDo check if we need to interact otherwise automate
    child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
    child.sendline("exit")
    #print child.before

    # Step 8: Fixup manually anything which couldn't be done automatically
    #print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
    #child.interact()     # Give control of the child to the user.
    with cd("/root/"):

        # Step 9: Take a dump of the fixed data (no structure, full inserts)
        print(green("%s: Dumping fixed data" % env.host))
        if env.database == "mysql":
            run("mysqldump -tc old > old.sql", pty=True)
        elif env.database == "postgresql":
            run("sudo -H -u postgres pg_dump --disable-triggers -a --column-inserts old > old.sql", pty=True)

        # Step 10: Import it into the empty database
        print(green("%s: Importing fixed data" % env.host))
        if env.database == "mysql":
            run("mysql sahana < old.sql", pty=True)
        elif env.database == "postgresql":
            # Re-apply the PostGIS link
            run("sudo -H -u postgres sh ~web2py/applications/eden/static/scripts/tools/postgis.sh", pty=True)
            run("sudo -H -u postgres psql -q -d sahana -f old.sql", pty=True)

def db_sync():
    """
        Synchronise the Database
        - PostgreSQL support not yet available!
        - For MySQL, this assumes that /root/.my.cnf is configured on both Test & Prod
          to allow the root SSH user to have access to the MySQL DB without needing '-u root -p'
    """
    if not "test" in env.host:
        db_upgrade()
    else:
        print(green("%s: Synchronising Database" % env.host))
        # See dbstruct_mysql.py
        with cd("/home/web2py/applications/eden/"):

            # Step 0: Drop old database 'sahana'
            print(green("%s: Dropping old Database" % env.host))
            # If database doesn't exist, we don't want to stop
            env.warn_only = True
            run("mysqladmin -f drop sahana", pty=True)
            env.warn_only = False
            print(green("%s: Cleaning databases folder" % env.host))
            run("rm -rf databases/*", pty=True)

            # Step 1: Create a new, empty MySQL database 'sahana' as-normal
            print(green("%s: Creating new Database" % env.host))
            run("mysqladmin create sahana", pty=True)

            # Step 2: set deployment_settings.base.prepopulate to False in models/000_config.py
            print(green("%s: Disabling prepopulate" % env.host))
            run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = 0/' models/000_config.py", pty=True)

        # Step 3: Allow web2py to run the Eden model to configure the Database structure
        migrate()

        # Step 4: Export the Live database from the Live server (including structure)
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, prod_host))
        child.expect(":~#")
        print(green("%s: Dumping live" % env.host))
        child.sendline("mysqldump sahana > new.sql")
        live = "/root/live.sql"
        print(green("%s: Transferring live" % env.host))
        child.sendline("scp -i /root/.ssh/sahana_release new.sql %s@%s:%s" % (env.user, env.host, live))
        child.expect(":~#")
        child.sendline("exit")
        with cd("/root/"):

            # Step 5: Use this to populate a new table 'old'
            print(green("%s: Restoring live to 'old'" % env.host))
            # If database doesn't exist, we don't want to stop
            env.warn_only = True
            run("mysqladmin -f drop old", pty=True)
            env.warn_only = False
            run("mysqladmin create old", pty=True)
            run("mysql old < live.sql", pty=True)

        # Step 7: Run the script: python dbstruct_mysql.py
        # use pexpect to allow us to jump in to do manual fixes
        child = pexpect.spawn("ssh -i /root/.ssh/sahana_release %s@%s" % (env.user, env.host))
        child.expect(":~#")
        child.sendline("cd /home/web2py/applications/eden/static/scripts/tools")
        child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
        child.sendline("python dbstruct_mysql.py")
        # @ToDo check if we need to interact otherwise automate
        child.expect(":/home/web2py/applications/eden/static/scripts/tools#")
        child.sendline("exit")
        #print child.before

        # Step 8: Fixup manually anything which couldn't be done automatically
        #print (green("Need to exit the SSH session once you have fixed anything which needs fixing"))
        #child.interact()     # Give control of the child to the user.
        with cd("/root/"):

            # Step 9: Take a dump of the fixed data (no structure, full inserts)
            print(green("%s: Dumping fixed data" % env.host))
            run("mysqldump -tc old > old.sql", pty=True)

            # Step 10: Import it into the empty database
            print(green("%s: Importing fixed data" % env.host))
            run("mysql sahana < old.sql", pty=True)

def maintenance_on():
    """ Enable maintenance mode """
    print(green("%s: Enabling Maintenance Mode" % env.host))
    # Disable Cron
    run("sed -i 's|0-59/1 * * * * web2py|#0-59/1 * * * * web2py|' /etc/crontab", pty=True)
    # Apply temporary Apache config
    run("a2dissite %s" % env.host, pty=True)
    run("a2ensite maintenance", pty=True)
    reload()

def maintenance_off():
    """ Disable maintenance mode """
    print(green("%s: Disabling Maintenance Mode" % env.host))
    # Enable Cron
    run("sed -i 's|#0-59/1 * * * * web2py|0-59/1 * * * * web2py|' /etc/crontab", pty=True)
    # Restore main Apache config
    run("a2dissite maintenance", pty=True)
    run("a2ensite %s" % env.host, pty=True)
    reload()

def migrate_on():
    """ Enabling migrations """
    print(green("%s: Enabling Migrations" % env.host))
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = False/deployment_settings.base.migrate = True/' 000_config.py", pty=True)

def migrate():
    """ Perform a Migration """
    print(green("%s: Performing Migration" % env.host))
    with cd("/home/web2py"):
        run("sudo -H -u web2py python web2py.py -N -S eden -M -R applications/eden/static/scripts/tools/noop.py", pty=True)

def migrate_off():
    """ Disabling migrations """
    print(green("%s: Disabling Migrations" % env.host))
    with cd("/home/web2py/applications/eden/models/"):
        run("sed -i 's/deployment_settings.base.migrate = True/deployment_settings.base.migrate = False/' 000_config.py", pty=True)

def optimise():
    """ Apply Optimisation """
    with cd("/home/web2py/"):
        # Restore indexes via Python script run in Web2Py environment
        run("python web2py.py -S eden -M -R applications/eden/static/scripts/tools/indexes.py", pty=True)
        # Compile application via Python script run in Web2Py environment
        run("python web2py.py -S eden -M -R applications/eden/static/scripts/tools/compile.py", pty=True)

def pull():
    """ Upgrade the Eden code """
    print(green("%s: Upgrading code" % env.host))
    with cd("/home/web2py/applications/eden/"):
        try:
            print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
            run("bzr pull -r %i" % env.revno, pty=True)
        except:
            if not env.tested:
                # Upgrade to current Trunk
                print(green("%s: Upgrading to current Trunk" % env.host))
                run("bzr pull", pty=True)
            else:
                # work out the VERSION to pull
                print(green("%s: Getting the version to update to" % env.host))
                run("scp -i /root/.ssh/sahana_release %s@%s:/home/web2py/applications/eden/VERSION /root/VERSION_test" % (env.user, test_host), pty=True)
                version = run("cat /root/VERSION_test", pty=True)
                env.revno = int(version.split(" ")[0].replace("r", ""))
                print(green("%s: Upgrading to version %i" % (env.host, env.revno)))
                run("bzr pull -r %i" % env.revno, pty=True)

def clean():
    """
        Wipe the instance's database & restore a fresh one
    """
    # Put site into maintenance
    maintenance_on()

    # Drop Database
    db_drop()

    # Create Empty Database
    db_create()

    # Delete compiled folder
    with cd("/home/web2py/applications/eden/"):
        # Remove compiled version of the app
        run("/bin/rm -rf compiled", pty=True)

    # Delete sessions
    with cd("/home/web2py/applications/eden/"):
        # Remove compiled version of the app
        run("/bin/rm -rf sessions/*", pty=True)

    # Enable migration
    migrate_on()

    # Enable Prepopulate
    with cd("/home/web2py/applications/eden/"):
        print(green("%s: Enabling prepopulate" % env.host))
        run("sed -i 's/deployment_settings.base.prepopulate = False/deployment_settings.base.prepopulate = 1/' models/000_config.py", pty=True)

    # Migrate
    migrate()

    # Disable Prepopulate
    with cd("/home/web2py/applications/eden/"):
        print(green("%s: Disabling prepopulate" % env.host))
        run("sed -i 's/deployment_settings.base.prepopulate = True/deployment_settings.base.prepopulate = 0/' models/000_config.py", pty=True)

    # Disable migration
    migrate_off()

    # Optimise
    optimise()

    # Init script (if present)
    print(green("%s: Init Script" % env.host))
    with cd("/home/web2py"):
        try:
            run("sudo -H -u web2py python web2py.py -N -S eden -M -R init.py", pty=True)
        except:
            pass

    # Take site out of maintenance
    maintenance_off()

def rollback():
    """
        Rollback from a failed upgrade
        - assumes that backup() was run before the upgrade!
    """
    print(green("%s: Rolling back" % env.host))
    with cd("/home/web2py/applications/eden/"):
        version = run("cat /root/VERSION", pty=True)
        env.revno = int(version.split(" ")[0].replace("r", ""))
        print(green("%s: Rolling back to rev %i" % (env.host, env.revno)))
        run("bzr revert -r %i" % env.revno, pty=True)
        # Restore customisations
        print(green("%s: Restoring Customisations" % env.host))
        env.warn_only = True
        run("patch -p0 < /root/custom.diff", pty=True)
        env.warn_only = False
        # Restore database
        print(green("%s: Restoring Database" % env.host))
        if env.database == "mysql":
            env.warn_only = True
            run("mysqladmin -f drop sahana", pty=True)
            env.warn_only = False
            run("mysqladmin create sahana", pty=True)
            run("mysql sahana < backup.sql", pty=True)
        elif env.database == "postgresql":
            env.warn_only = True
            run("pkill -f 'postgres: postgres sahana'", pty=True)
            run("sudo -H -u postgres dropdb sahana", pty=True)
            env.warn_only = False
            run("sudo -H -u postgres createdb -O sahana -E UTF8 sahana -T template0", pty=True)
            run("sudo -H -u postgres psql -q -d sahana -f backup.sql", pty=True)
        # Restore databases folder
        run("rm -rf databases/*", pty=True)
        run("cp -ar /root/databases/* databases", pty=True)
        reload()

def reload():
    """ Reload Apache """
    print(green("%s: Restarting Apache" % env.host))
    run("apache2ctl restart", pty=True)

def os_upgrade():
    """ Update OS """
    print(green("%s: Updating OS" % env.host))
    run("apt-get update", pty=True)
    run("apt-get upgrade -y", pty=True)

