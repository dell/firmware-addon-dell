# This file is dual bash/make variable format so I have one place to bump the version.

RELEASE_NAME=firmware-addon-dell
RELEASE_MAJOR=1
RELEASE_MINOR=2
RELEASE_SUBLEVEL=13
RELEASE_EXTRALEVEL=
RPM_RELEASE=1
DEB_RELEASE=1
DEBARCH=i386
RPM_TYPE=$(shell uname -i)
PY_VER_UPDATES=bin/up2date_repo_autoconf yum-plugin/dellsysidplugin.py


