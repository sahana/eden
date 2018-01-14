AMAZON EC2
************************

Amazon's Cloud provides a flexible platform to deploy Eden scalably.

The costs aren't fixed & can be difficult to predict, despite their `calculator <http://calculator.s3.amazonaws.com/index.html>`_ , but are competitive, especially in Singapore, which is a good base for the Asia Pacific region. Users who are using the free tier: Remember - after 750 hours, your trial will end and the credit card on file will be charged based on the rates shown in EC2. You can prevent these charges by closing the AWS account from the `AWS account management page <https://signin.aws.amazon.com/signin?redirect_uri=https%3A%2F%2Fconsole.aws.amazon.com%2Fbilling%2Fhome%3Fstate%3DhashArgs%2523%252Faccount%26isauthcode%3Dtrue&client_id=arn%3Aaws%3Aiam%3A%3A934814114565%3Auser%2Fportal-aws-auth&forceMobileApp=0>`_ .

1. CREATE AWS ACCOUNT
===================

If you haven't already, create an Amazon AWS account through  their `site <https://aws.amazon.com/es/free/>`_ .

2. CREATE INSTANCE
===================

1: Log In To The Management Console
----------------

- https://console.aws.amazon.com

2: Select A Region
----------------

Amazon supports multiple Regions in order to provide a service closest to your users.

- Namespaces of Instances, Volumes & Snapshots are unique only within a Region.
- Within each Region, there are a couple of Availability Zones to allow spreading the risk across different facilities.
- Volumes are located within a specific Availability Zone
- Bandwidth transfers are free within an Availability Zone

3: Launch A New Instance
----------------

4: Choose An Amazon Machine Image (AMI)
----------------

- **Recommend** using the AWS Marketplace Debian 64-bit image (as this has a sufficiently large HDD to start with & is EBS-backed, so has persistent storage even whilst powered down)
- this is now accessed via Community AMIs, select Debian OS, use latest debian-stretch-amd64-hvm image, which supports the new T2.micro free tier instances
- In time we may provide pre-built "Sahana Eden" AMIs (some old unmaintained ones may be available in some regions)
- The normal production 'small' instance can only run 32-bit.
- Larger production instances can only run 64-bit, so can't have the exact same image used.

5: Choose An Instance Type
----------------

- https://aws.amazon.com/ec2/instance-types/
- The free starter 'T2.micro' instance is flexible as it can run both 32-bit & 64-bit Operating Systems....it is suitable for prototyping, development, QA and smaller scale production services. Note that for User Training it can be good to increase capacity as this typically has more users accessing the system concurrently than in normal operations.
- For production-level performance of larger deployments, we recommend a balance of processor & RAM, so the M4.large would be our current recommendation, usually purchased as a 1 year reservation

6: Configure Instance Details
----------------

Default settings are fine for "Configure Instance Details" and "Add Storage" configuration pages.

7: Create KeyPair
----------------

Ensure that you keep the generated private key safe...save as private.pem. You will need this file to log into your instance.

8: Associate Elastic IP
----------------

Each time you start an instance up, it will be assigned a new IP ('Public DNS') although this can be overcome using an Elastic IP:

1. NETWORK & SECURITY > Elastic IPs
2. Allocate New Address
3. Associate Address. Set the instance to your new instance

Remember to set up Reverse DNS for your Elastic IP to be able to send emails reliably:

- https://aws-portal.amazon.com/gp/aws/html-forms-controller/contactus/ec2-email-limit-rdns-request

NB If you have a free EC2 instance, be sure to release your Elastic IP if you shut down your instance. IPv4 addresses are a "scarce resource" so Amazon will charge you for wasting one if you keep it assigned to your instance while you are not using it.

9: Configure Security Group
----------------

NETWORK & SECURITY > Security Groups

You will need to set the following Inbound Rules:

- HTTP | TCP |80
- SSH | TCP | 22

Restricting the source will add further security, but obviously also restricts your ability to administer

10: Gain SSH Access
----------------

In order to get the public key (needed by SecureCRT for instance) then you need to login using CLI & retrieve it (username 'admin' for the AWS MarketPlace Debian, username 'root' for some other Images)::

 ssh -l admin -i private.pem <hostname>
 cat ~/.ssh/authorized_keys

On Windows, you can use Cygwin to get a CLI SSH client.

SecureCRT needs the private key storing as <filename> & the public as <filename.pub> (all on one line)

**Recovering From a Lost Keypair**

If you lose your keypair then you need to:

-Create a new keypair in the AWS console & download the generated private key
-Stop the instance
-Create an AMI from this instance
-Wait for the AMI to be ready
-Launch a new instance using this AMI
-Re-associate the Public IP
-Delete the old instance
-Deregister the AMI
-Delete the snapshot used to create the AMI

Thanks to:  http://itkbcentral.blogspot.co.uk/2011/07/replace-lost-key-pair-existing-aws-ec2.html

11: Add Swapfile
----------------

You should add swap from a swap file in order to improve performance (especially on a Micro instance)::

 sudo su -
 dd if=/dev/zero of=/swapfile1 bs=1024 count=524288
 mkswap /swapfile1
 chown root:root /swapfile1
 chmod 0600 /swapfile1
 swapon /swapfile1
 # Make persistent across reboots
 cat << EOF >> "/etc/fstab"
 /swapfile1 swap swap defaults 0 0
 EOF

3. INSTALL SAHANA
===================

- Copy the installation and configuration scripts into the launched instance (assuming  `Cherokee & PostgreSQL <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Linux/Server/CherokeePostgreSQL>`_ )::

 wget --no-check-certificate https://raw.githubusercontent.com/sahana/eden_deploy/master/install-eden-cherokee-postgis.sh
 chmod a+x install-eden-cherokee-postgis.sh
 wget --no-check-certificate https://raw.githubusercontent.com/sahana/eden_deploy/master/configure-eden-cherokee-postgis.sh
 chmod a+x configure-eden-cherokee-postgis.sh

- Run the install-eden-cherokee-postgis.sh script. [Note: This step takes about 10min - grab a coffee]::

 sudo su -
 ./install-eden-cherokee-postgis.sh

If you wish to update your site from an alternate github repo this can be done using:

- `ConfigurationGuidelines#SwitchtoanalternateGitHubrepo <http://eden.sahanafoundation.org/wiki/ConfigurationGuidelines#SwitchtoanalternateGitHubrepo>`_

4. CONFIGURE SAHANA
===================

Run configure-eden-cherokee-postgis.sh to configure the instance::

 sudo su -
 ./configure-eden-cherokee-postgis.sh

- Add your FQDN to /etc/hosts to ensure emails are accepted by all remote mailers::
 vim /etc/hosts
 127.0.0.1 host.domain host localhost

 /etc/init.d/exim4 restart

 NB On new Amazon instances you may also need to prevent Amazon from auto-updating this file by commenting this aspect:
 vim /etc/cloud/cloud.cfg
 # - update_etc_hosts

See `Admin Guide <http://eden.sahanafoundation.org/wiki/UserGuidelines/Admin/Configuration>`_ - especially read how to set the sender & approver emails

5. ADD A TEST SITE (OPTIONAL)
===================

This script requires at least 4Gb on the main disk::

 sudo su -
 wget https://raw.githubusercontent.com/sahana/eden_deploy/master/add_test_site.sh
 chmod a+x add_test_site.sh
 ./add_test_site.sh

NB This script has an issue & the file /etc/cherokee/cherokee.conf needs to be manually edited to fix the lines wrapping for Source 1 (fix welcomed!)

6. ADD A DEMO SITE (OPTIONAL)
===================

This script requires at least 6Gb on the main disk.

This script assumes that a Test site has already been installed::

   sudo su -
   wget https://raw.githubusercontent.com/sahana/eden_deploy/master/add_demo_site.sh
   chmod a+x add_demo_site.sh
   ./add_demo_site.sh

NB This script has an issue & the file /etc/cherokee/cherokee.conf needs to be manually edited to fix the lines wrapping for Source 1 (fix welcomed!)

OPTIONAL INSTANCE ADJUSTMENTS
===================

Add Swap Partition
----------------

You can add a swap partition in order to improve performance further:

- Create Volume in AWS Console (e.g. 4Gb)
- Attach as /dev/sdf::
 sudo su -
 swapoff -a
 mkswap /dev/xvdf
 swapon -a
 # Make persistent across reboots
 cat << EOF >> "/etc/fstab"
 /dev/xvdf swap  swap    defaults 0 0
 EOF
 rm -f /swapfile1

Grow The Diskspace
----------------

The initial disk space on some images is just 1GB. If you have this, then this should be grown to 4Gb (don't just size the volume to 4Gb to start with as the image only uses 1Gb of it!)

- this is still within the 10Gb free tier.
- 4Gb is needed for Prod & Test instances. If you just need a test then 3Gb is sufficient.

Add Storage
----------------
If you need an additional disk for Storage then configure a volume in the AWS console (magnetic is cheapest), attach as /dev/sdb1, then in Linux::

 sudo su -
 fdisk /dev/xvdf
 n
 (accept defaults)
 w
 mkfs.ext4 /dev/xvdf
 tune2fs -m 0 /dev/xvdf # Remove 5% reservation for reserved blocks
 mkdir /data
 cat << EOF >> "/etc/fstab"
 /dev/xvdf /data ext4    defaults,barrier=0 1 1
 EOF
 mount /data
 
Disk Striping
----------------
For DB I/O performance increase can stripe multiple EBS

- monitoring data is available to see if this is the issue

INSTALL USING 'SAHANA SETUP'
===================

See: `InstallationGuidelines/Amazon/Setup <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Amazon/Setup>`_

CLI TOOLS
===================

You can do this using the AWS EC2 Console or else you can do it via the CLI To use any of the AWS CLI tools on your own machine to remotely manage instances, then you need to generate a unique X.509 Certificate per account. This can be done from the 'Security Credentials' page within your account.

CLI Management
----------------
There are extensive CLI tools available to manipulate your instances.

- Java CLI for Windows/Linux
http://aws.amazon.com/developertools/351

http://serktools.com/2009/05/19/setting-up-ec2-command-line-tools-on-windows/

http://docs.amazonwebservices.com/AWSEC2/latest/CommandLineReference/

- Python:  http://libcloud.apache.org

CLI Script
----------------
Edit the settings as-indicated as you proceed through the script::

 # Settings for Instance
 set EC2_URL=https://ec2.us-east-1.amazonaws.com
 set ZONE=us-east-1c
 set DEV=i-950895f1
 set OLD=vol-31f5a35d
 # Stop Host
 ec2stop %DEV%
 # Create a snapshot
 ec2-create-snapshot %OLD%
 # Record the snapshot ID
 set SNAPSHOT=snap-63f89d08
 # Create new volume from snapshot
 ec2-create-volume -z %ZONE% --size 4 --snapshot %SNAPSHOT%
 # Record the new Volume ID
 set NEW=vol-a9c2a3c4
 # Attach new volume as secondary
 ec2-attach-volume -i %DEV% %NEW% -d /dev/sdb1
 # Delete Snapshot (if no data in yet)
 ec2-delete-snapshot %SNAPSHOT%
 # Start Host
 ec2start %DEV%
 # Re-attach the Public IP
 # Login
 mkdir /mnt/data
 echo '/dev/xvdb1 /mnt/data ext3 defaults,noatime 0 0' >> /etc/fstab
 mount /mnt/data
 resize2fs /dev/xvdb1
 umount /mnt/data
 shutdown -h now
 # Unattach volumes
 ec2-detach-volume -i %DEV% %OLD%
 ec2-detach-volume -i %DEV% %NEW%
 # Attach volume as boot
 ec2-attach-volume -i %DEV% %NEW% -d /dev/sda1
 # Attach old volume for /var/log
 ec2-attach-volume -i %DEV% %OLD% -d /dev/sdb1
 # OR Delete old volume
 #ec2-delete-volume %OLD%
 # Start Host
 ec2start %DEV%
 # Re-attach the Public IP
 # Login
 df -h
 # Use the old partition for /var/log (to avoid DoS)
 vi /etc/fstab
 /dev/xvdb1 /var/log  ext3    noatime 0 0

 mv /var/log /var/log_old
 mkdir /var/log
 mount /var/log
 mv /var/log_old/* /var/log
 rm -rf /var/log/bin/
 rm -rf /var/log/boot/
 rm -rf /var/log/dev/
 rm -rf /var/log/etc/
 rm -rf /var/log/home/
 rm -rf /var/log/initrd.img
 rm -rf /var/log/lib/
 rm -rf /var/log/mnt/
 rm -rf /var/log/media/
 rm -rf /var/log/opt/
 rm -rf /var/log/proc/
 rm -rf /var/log/root/
 rm -rf /var/log/sbin/
 rm -rf /var/log/selinux/
 rm -rf /var/log/srv/
 rm -rf /var/log/tmp/
 rm -rf /var/log/usr/
 rm -rf /var/log/var/
 rm -rf /var/log/vmlinuz
 rm -rf /var/log_old

BUILDING AMIS FOR EASIER DEPLOYMENT
===================
See: `InstallationGuidelines/Amazon/AMI <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Amazon/AMI>`_

TROUBLESHOOTING
===================

To troubleshoot any errors in installation of EC2 visit its `documentation <https://aws.amazon.com/es/documentation/ec2/>`_ . If you encounter problems installing eden on the EC2 instance, you can contact us via `IRC <http://eden.sahanafoundation.org/wiki/InstallationGuidelines/Chat>`_ or the `mailing list <http://eden.sahanafoundation.org/wiki/MailingList>`_ .

Attachments
----------------

- `ami-built.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/ami-built.png>`_  `Download <http://eden.sahanafoundation.org/chrome/common/download.png>`_ (156.9 KB) - added by *cshah* 4 years ago.
- `ami-permissions.2.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/ami-permissions.2.png>`_  `Download <http://eden.sahanafoundation.org/raw-attachment/wiki/InstallationGuidelines/Amazon/ami-permissions.2.png>`_ (176.1 KB) - added by *cshah* 4 years ago.
- `orig-ami-built.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-ami-built.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-ami-built.png>`_ (172.9 KB) - added by *ptressel* 4 years ago. lifeeth's original ami-built.png from 2 years ago
- `orig-create-image.png  <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-create-image.png>`_ `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-create-image.png>`_ (271.0 KB) - added by *ptressel* 4 years ago. lifeeth's original create-image.png from 2 years ago
- `orig-ami-permissions.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-ami-permissions.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-ami-permissions.png>`_ (215.7 KB) - added by *ptressel* 4 years ago. lifeeth's original ami-permissions.png from 2 years ago
- `orig-create-image-config.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-create-image-config.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/orig-create-image-config.png>`_ (270.8 KB) - added by *ptressel* 4 years ago. lifeeth's original create-image-config.png from 2 years ago
- `create-image-config.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/create-image-config.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/create-image-config.png>`_ (184.8 KB) - added by *cshah* 4 years ago.
- `create-image.png  <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/create-image.png>`_ `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/create-image.png>`_ (211.0 KB) - added by *cshah* 4 years ago.
- `Dashboard.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/Dashboard.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/Dashboard.png>`_ (103.7 KB) - added by *gnarula* 4 years ago.
- `SelectAMI.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/SelectAMI.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/SelectAMI.png>`_ (94.4 KB) - added by *gnarula* 4 years ago.
- `SecurityGroup.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/SecurityGroup.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/SecurityGroup.png>`_ (70.1 KB) - added by *gnarula* 4 years ago.
- `UserData.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/UserData.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/UserData.png>`_ (59.3 KB) - added by *gnarula* 4 years ago.
- `select_debian.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/select_debian.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/select_debian.png>`_ (68.2 KB) - added by *waidyanatha* 14 months ago. selct debian OS
- `select_region.png <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/select_region.png>`_  `Download <http://eden.sahanafoundation.org/attachment/wiki/InstallationGuidelines/Amazon/select_region.png>`_ (12.8 KB) - added by *waidyanatha* 14 months ago. select region
