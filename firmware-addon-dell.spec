###################################################################
#
# WARNING
#
# These are all automatically replaced by the release script.
# START = Do not edit manually
%define major 1
%define minor 2
%define sub 8
%define extralevel %{nil}
%define release_name firmware-addon-dell
%define release_version %{major}.%{minor}.%{sub}%{extralevel}
#
# END = Do not edit manually
#
###################################################################

%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}

# SUSE 10 has a crazy distutils.cfg that specifies prefix=/usr/local
# have to override that.
%define suse_prefix %{nil}
%if %(test -e /etc/SuSE-release && echo 1 || echo 0)
%define suse_prefix --prefix=/usr
%endif

# Compat for RHEL3 build
%if %(test "%{dist}" == ".el3" && echo 1 || echo 0)
# needed for RHEL3 build, python-devel doesnt seem to Require: python in RHEL3
BuildRequires:  python
# override sitelib because this messes up on x86_64
%define python_sitelib %{_exec_prefix}/lib/python2.2/site-packages/
%endif

Name:           %{release_name}
Version:        %{release_version} 
Release:        1%{?dist}
Summary:        A firmware-tools plugin to handle BIOS/Firmware for Dell systems

Group:          Applications/System
# License is actually GPL/OSL dual license (GPL Compatible), but rpmlint complains
License:        GPL style
URL:            http://linux.dell.com/libsmbios/download/ 
Source0:        http://linux.dell.com/libsmbios/download/%{name}/%{name}-%{version}/%{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# This package is noarch for everything except RHEL3. Have to build arch
# specific pkgs for RHEL3
%if %(test "%{dist}" != ".el3" && echo 1 || echo 0)
BuildArch:      noarch
%endif

# Dell only sells Intel-compat systems, so this package doesnt make much sense
# on, eg. PPC.  Also, we rely on libsmbios, which is only avail on Intel-compat
ExcludeArch: ppc ppc64 s390


BuildRequires:  python-devel

# I know rpmlint complains about this (An ERROR, in fact), but it is a
# false positive. Auto deps cannot find this one because I actually am running
# binaries, not linking agains libs, as indicated by the fact that I require 
# the -bin package
Requires: libsmbios-bin 

Requires: firmware-tools > 0:1.1

Provides: firmware_inventory(system_bios)  = 0:%{version}
Provides: firmware_inventory(bmc) = 0:%{version}

%description
The firmware-addon-dell package provides plugins to firmware-tools which enable
BIOS updates for Dell system, plus pulls in standard inventory modules
applicable to most Dell systems.


%prep
%setup -q


%build
%{__python} setup.py build


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_datadir}/firmware/dell/bios
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT %{suse_prefix}

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc COPYING-GPL COPYING-OSL readme.txt
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/firmware/firmware.d/*.conf
%config(noreplace) %{_sysconfdir}/yum/pluginconf.d/dellsysidplugin.conf
%{_datadir}/firmware/dell
%{_exec_prefix}/lib/yum-plugins/dellsysidplugin.*
%attr(0755,root,root) %{_bindir}/*


%changelog
* Fri Apr 6 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.8-1
- sysid plugin: Zero pad value for sysid up to 4 chars
- sysid plugin: Add 0x to signify that it is a hex value

* Fri Mar 30 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.7-1
- yum plugin didnt work on FC5 due to extra, unneeded import.
- dont need plugin api 2.5, 2.2 will do

* Wed Mar 28 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.6-1
- Add yum plugins for setting system ID variables. repos can use $sys_ven_id
  $sys_dev_id in their baseurl= or mirrorlist= arguments.

* Sat Mar 17 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.5-1
- Add ExcludeArch for s390
- Remove python-abi dep for RHEL3 (it was broken)
- fix sitelib path missing /lib/ dir

* Fri Mar 16 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.4-1
- Add ExcludeArch to fix problem where f-a-d was being added to ppc repo

* Thu Mar 15 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.2-1
- Trivial changes to add specific {_datadir}/firmware/dell 

* Thu Mar 15 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.1-1
- Trivial changes to make rpmlint happier

* Wed Mar 14 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.0-1
- Fedora-compliant packaging changes.
