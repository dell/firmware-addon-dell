###################################################################
#
# WARNING
#
# These are all automatically replaced by the release script.
# START = Do not edit manually
%define major 1
%define minor 2
%define sub 1
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
# add in required ABI (hardcode because /usr/bin/python not available at this point)
Requires:       python-abi = 2.2
# needed for RHEL3 build, python-devel doesnt seem to Require: python in RHEL3
BuildRequires:  python
# override sitelib because this messes up on x86_64
%define python_sitelib /usr/lib/python2.2/site-packages/
%endif

Name:           %{release_name}
Version:        %{release_version} 
Release:        1%{?dist}
Summary:        A firmware-tools plugin to handle BIOS/Firmware for Dell systems

Group:          Applications/System
# License is actually GPL/OSL dual license (GPL Compatible), but rpmlint complains
License:        GPL style
URL:            http://linux.dell.com/libsmbios/download/ 
Source0:        %{name}-%{version}.tar.gz
BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

# This package is noarch for everything except RHEL3. Have to build arch
# specific pkgs for RHEL3
%if %(test "%{dist}" != ".el3" && echo 1 || echo 0)
BuildArch:      noarch
%endif

BuildRequires:  python-devel

# I know rpmlint complains about this (An ERROR, in fact), but it is a
# false positive. Auto deps cannot find this one because I actually am running
# binaries, not linking agains libs, as indicated by the fact that I require 
# the -bin package
Requires: libsmbios-bin 

Requires: firmware-tools > 0:1.1

Provides: firmware_inventory(system_bios) 
Provides: firmware_inventory(bmc)

Obsoletes: fwupdate-tools
Provides: fwupdate-tools

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
%{__python} setup.py install -O1 --skip-build --root $RPM_BUILD_ROOT %{suse_prefix}

 
%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc COPYING-GPL COPYING-OSL readme.txt
%{python_sitelib}/*
%config(noreplace) %{_sysconfdir}/firmware/firmware.d/*.conf


%changelog
* Thu Mar 15 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.1-1
- Trivial changes to make rpmlint happier
* Wed Mar 14 2007 Michael E Brown <michael_e_brown at dell.com> - 1.2.0-1
- Fedora-compliant packaging changes.
