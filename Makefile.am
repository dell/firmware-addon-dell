# vim:noexpandtab:autoindent:tabstop=8:shiftwidth=8:filetype=make:nocindent:tw=0:

include Makefile-std

pkgdatadir = $(datadir)/firmware-tools/
nodist_pkgdata_DATA = doc/system_id2name.ini doc/bios.spec.in doc/dell-std-license.txt

pkgconfdir = $(sysconfdir)/firmware/firmware.d/
nodist_pkgconf_DATA = doc/firmware-addon-dell.conf

export top_srcdir top_builddir
EXTRA_DIST += doc test COPYING-GPL COPYING-OSL
TESTS = test/testAll.py

pkgpython_PYTHON = \
	firmware_addon_dell/generated/__init__.py	\
	firmware_addon_dell/biosHdr.py   	\
	firmware_addon_dell/dellbios.py  	\
	firmware_addon_dell/extract_bios.py    	\
	firmware_addon_dell/extract_bios_blacklist.py \
	firmware_addon_dell/extract_common.py  	\
	firmware_addon_dell/HelperXml.py

__VERSION__=$(VERSION)
PKGLIBEXECDIR=$(pkglibexecdir)
REPLACE_VARS+= __VERSION__ PKGLIBEXECDIR
EXTRA_DIST += firmware_addon_dell/__init__.py
DISTCLEANFILES +=   firmware_addon_dell/generated/__init__.py
firmware_addon_dell/generated/__init__.py: firmware_addon_dell/__init__.py configure Makefile config.status
	mkdir -p $$(dirname $@) ||:
	cp $< $@
	$(call replace_vars_in_file,$@)
