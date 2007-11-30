# This file is dual bash/make variable format so I have one place to bump the version.

RELEASE_NAME=firmware-addon-dell
RELEASE_MAJOR=1
RELEASE_MINOR=4
RELEASE_SUBLEVEL=10
RELEASE_EXTRALEVEL=
RPM_RELEASE=1
DEB_RELEASE=0ubuntu1
DEBARCH=all
RPM_TYPE=$(shell uname -i)
PY_VER_UPDATES=yum-plugin/dellsysidplugin.py
