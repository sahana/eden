#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Downloads fonts for full unicode support on reportlab.
author: Shiv Deepak <idlecool@gmail.com>
"""

import tarfile
import urllib
import os
import shutil
import gzip


# set fonts to be downloaded
downloadfonts = [
    "arabic",    # urdu language support
    "unifont",   # unifont
    "japanese",  # japanese language support
    ]


## set up
print "Setting Up Environment"
script_directory = os.path.dirname(os.path.abspath(__file__))
temp_downloads_dir = os.path.join(script_directory, "temp")
if not os.path.exists(temp_downloads_dir):
    os.makedirs(temp_downloads_dir)
    os.chdir(temp_downloads_dir)
    print "Temporary Directory %s Created" % temp_downloads_dir
else:
    print "'%s' directory already exists!!!" % temp_downloads_dir
    print "Please make sure to delete this directory before running the script!"
    exit()


SFMIRROR = "downloads"      # Automatic
#SFMIRROR = "jaist.dl"       # Ishikawa, Japan
#SFMIRROR = "nchc.dl"        # Tainan, Taiwan
#SFMIRROR = "switch.dl"      # Lausanne, Switzerland
#SFMIRROR = "heanet.dl"      # Dublin, Ireland
#SFMIRROR = "garr.dl"        # Bologna, Italy
#SFMIRROR = "surfnet.dl"     # Amsterdam, Netherlands
#SFMIRROR = "kent.dl"        # Kent, UK
#SFMIRROR = "easynews.dl"    # Phoenix, AZ
#SFMIRROR = "internap.dl"    # San Jose, CA
#SFMIRROR = "superb-east.dl" # McLean, Virginia
#SFMIRROR = "superb-west.dl" # Seattle, Washington
#SFMIRROR = "ufpr.dl"        # Curitiba, Brazil

SOURCEFORGE = "%s.sourceforge.net/sourceforge" % SFMIRROR


## arabic fonts
fontcategory = "arabic"
if fontcategory in downloadfonts:
    if not os.path.exists(os.path.join(script_directory, fontcategory)):
        os.makedirs(os.path.join(script_directory, fontcategory))
    print "Downloading Arabic Fonts"
    url = "http://%s/arabeyes/ae_fonts_2.0.tar.bz2" % SOURCEFORGE
    filename = "aefonts.tar.bz2"
    filetype = "application/x-bzip2"
    fontfiles = [
        "ae_fonts_2.0/Kasr/ae_AlMateen-Bold.ttf",
        "ae_fonts_2.0/Kasr/ae_AlMohanad.ttf"
        ]
    print "Downloading Fonts to %s" % filename
    try:
        response = urllib.urlretrieve(url, filename)
        if response[1].type == filetype:
            print "Download Successful!! Extracting %s" % filename
            try:
                fontpack = tarfile.open(os.path.join(temp_downloads_dir,
                                                     filename))
                fontpack.extractfile("ae_fonts_2.0")
                for font in fontfiles:
                    fontpack.extract(font, path=temp_downloads_dir)
                    try:
                        shutil.move(os.path.join(temp_downloads_dir, font),
                            os.path.join(script_directory, fontcategory))
                    except:
                        pass
                fontpack.close()
            except:
                print "Improperly downloaded file!"
                print "Download Failed, Proceeding forward!!"
        else:
                print "Download Failed, Proceeding forward!!"
    except(IOError):
        print "Download Failed, Network Error!! Proceeding forward!!"


## unifont fonts
fontcategory = "unifont"
if fontcategory in downloadfonts:
    if not os.path.exists(os.path.join(script_directory, fontcategory)):
        os.makedirs(os.path.join(script_directory, fontcategory))
    print "Downloading Unifont"
    url = "http://www.lgm.cl/contenido/unifont.ttf.gz"
    filename = "unifont.ttf.gz"
    fontname = "unifont.ttf"
    filetype = "application/x-gzip"
    print "Downloading Fonts to %s" % filename
    try:
        response = urllib.urlretrieve(url, filename)
        if response[1].type == filetype:
            print "Download Successful! Extracting %s" % filename
            try:
                fontpack = gzip.open(os.path.join(temp_downloads_dir,
                                                            filename))
                fontfile = open(os.path.join(script_directory,
                                             fontcategory,
                                             fontname),
                                "w")
                fontfile.write(fontpack.read())
                fontfile.close()
                fontpack.close()
            except:
                print "Improperly downloaded file!"
                print "Download Failed, Proceeding forward!!"
        else:
                print "Download Failed, Proceeding forward!!"
    except(IOError):
        print "Download Failed, Network Error!! Proceeding forward!!"


## japanese fonts
fontcategory = "japanese"
if fontcategory in downloadfonts:
    if not os.path.exists(os.path.join(script_directory, fontcategory)):
        os.makedirs(os.path.join(script_directory, fontcategory))
    print "Downloading Japanese Fonts"
    url = """http://sourceforge.jp/frs/redir.php?m=jaist&f=%2Fefont%2F10087%2Fsazanami-20040629.tar.bz2"""
    filename = "sazanami-20040629.tar.bz2"
    filetype = "application/x-bzip2"
    fontfiles = [
        "sazanami-20040629/sazanami-mincho.ttf",
        "sazanami-20040629/sazanami-gothic.ttf"
        ]
    print "Downloading Fonts to %s" % filename
    try:
        response = urllib.urlretrieve(url, filename)
        if response[1].type == filetype:
            print "Download Successful!! Extracting %s" % filename
            try:
                fontpack = tarfile.open(os.path.join(temp_downloads_dir,
                                                     filename))
                fontpack.extractfile("sazanami-20040629")
                for font in fontfiles:
                    fontpack.extract(font, path=temp_downloads_dir)
                    try:
                        shutil.move(os.path.join(temp_downloads_dir, font),
                            os.path.join(script_directory, fontcategory))
                    except:
                        pass
                fontpack.close()
            except:
                print "Improperly downloaded file!"
                print "Download Failed, Proceeding forward!!"
        else:
                print "Download Failed, Proceeding forward!!"
    except(IOError):
        print "Download Failed, Network Error!! Proceeding forward!!"


## script exit
os.chdir(script_directory)
shutil.rmtree(temp_downloads_dir)
print "Deleted the script environment."
