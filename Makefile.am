# vim:noexpandtab:autoindent:tabstop=8:shiftwidth=8:filetype=make:nocindent:tw=0:

include Makefile-std

yumplugindir = $(exec_prefix)/lib/yum-plugins
dist_yumplugin_PYTHON = yum-plugin/dellsysidplugin.py
yumconfdir = $(sysconfdir)/yum/pluginconf.d/
dist_yumconf_DATA = yum-plugin/dellsysidplugin.conf

pkgdatadir = $(datadir)/firmware-tools/
nodist_pkgdata_DATA = doc/system_id2name.ini doc/bios.spec.in doc/dell-std-license.txt

pkgconfdir = $(sysconfdir)/firmware/firmware.d/
nodist_pkgconf_DATA = doc/firmware-addon-dell.conf

EXTRA_DIST += doc test COPYING-GPL COPYING-OSL

TESTS = test/testAll.py
nodist_check_SCRIPTS = test/testAll.py

pkglibexecdir = $(libexecdir)/$(PACKAGE_NAME)
dist_pkglibexec_DATA = \
	libexec/dup_pkginfo.py  \
	libexec/make_dell_mirror  \
	libexec/mkbiosrepo.sh

pkglibexec_LTLIBRARIES =\
	libexec/fakeroot-32.la
libexec_fakeroot_32_la_LDFLAGS = -module  -shared -m32
libexec_fakeroot_32_la_CFLAGS =  -m32
libexec_fakeroot_32_la_SOURCES = libexec/fakeroot.c

pkgpython_PYTHON = \
	firmware_addon_dell/__init__.py	\
	firmware_addon_dell/biosHdr.py   	\
	firmware_addon_dell/compat_subprocess.py \
	firmware_addon_dell/dellbios.py  	\
	firmware_addon_dell/extract_bios.py    	\
	firmware_addon_dell/extract_bios_blacklist.py \
	firmware_addon_dell/extract_common.py  	\
	firmware_addon_dell/HelperXml.py  	\
	firmware_addon_dell/svm.py

REPLACE_VARS_ON_INSTALL= \
	$(yumplugindir)/dellsysidplugin.py	\
	$(pkgpythondir)/__init__.py

