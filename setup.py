#!/usr/bin/python2
# VIM declarations
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:

  #############################################################################
  #
  # Copyright (c) 2003 Dell Computer Corporation
  #
  #############################################################################
"""
"""
import distutils.core 
import glob
import os

###################################################################
#
# WARNING
#
# These are all automatically replaced by the release script.
# START = Do not edit manually
RELEASE_MAJOR="1"
RELEASE_MINOR="2"
RELEASE_SUBLEVEL="6"
RELEASE_EXTRALEVEL=""
#
# END = Do not edit manually
#
###################################################################

# override from makefile environment vars, if necessary
for i in ("RELEASE_MAJOR", "RELEASE_MINOR", "RELEASE_SUBLEVEL", "RELEASE_EXTRALEVEL",):
    if os.environ.get(i):
        globals()[i] = os.environ.get(i)

doc_files = [ "COPYING-GPL", "COPYING-OSL", "README", "readme.txt" ]

MANIFEST = open( "MANIFEST.in", "w+" )
MANIFEST.write( "#BEGIN AUTOGEN\n" )
# include binaries
for i in doc_files:
    MANIFEST.write("include " + i + "\n" )

MANIFEST.write("include doc/firmware-addon-dell.conf\n" )
MANIFEST.write("include yum-plugin/dellsysidplugin.conf\n" )
MANIFEST.write("include yum-plugin/dellsysidplugin.py\n" )
MANIFEST.write("include version.mk\n" )
MANIFEST.write("include firmware-addon-dell.spec\n" )
MANIFEST.write( "#END AUTOGEN\n" )
MANIFEST.close()

dataFileList = []
dataFileList.extend((  
    ("/usr/lib/yum-plugins/", ["yum-plugin/dellsysidplugin.py",] ),
    ("/etc/yum/pluginconf.d/", ["yum-plugin/dellsysidplugin.conf",] ),
    ("/etc/firmware/firmware.d/", ["doc/firmware-addon-dell.conf",] ),
    ))

distutils.core.setup (
        name = 'firmware-addon-dell',
        version = '%s.%s.%s%s' % (RELEASE_MAJOR, RELEASE_MINOR, RELEASE_SUBLEVEL, RELEASE_EXTRALEVEL,),

        description = 'Scripts and tools to manage firmware and BIOS updates for Dell system.',
        author="Libsmbios team",
        author_email="libsmbios-devel@lists.us.dell.com",
        url="http://linux.dell.com/libsmbios/main/",

        package_dir={'': 'pymod'},
        packages=[''],

        ext_modules = [ ],
        data_files=dataFileList,
        scripts=[],
)


