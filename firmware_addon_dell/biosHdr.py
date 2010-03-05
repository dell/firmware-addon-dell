# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""module

some docs here eventually.
"""

from libsmbios_c import system_info as sysinfo
from libsmbios_c import rbu_update
from libsmbios_c import rbu_hdr

compareVersions = rbu_update.compareBiosVersions

class PermissionDenied (Exception): pass
class InternalError (Exception): pass
class InvalidHdr (Exception): pass

def getSystemId():
    return sysinfo.get_dell_system_id()

def getProductName():
    return sysinfo.get_system_name()

def getServiceTag():
    return sysinfo.get_service_tag()

def getSystemBiosVer():
    return sysinfo.get_bios_version()

# no good way to unit test this for now...
def isHdrFileNewer(file):
    try:
        ver = sysinfo.get_bios_version()
        hdrfile = rbu_hdr.HdrFile(file)
        return rbu_update.compareBiosVersions(hdrfile.biosVersion(), ver) > 0
    except rbu_hdr.InvalidRbuHdr, e:
        raise InvalidHdr(str(e))

def getBiosHdrVersion(file):
    try:
        f = rbu_hdr.HdrFile(file)
        return f.biosVersion()
    except rbu_hdr.InvalidRbuHdr, e:
        raise InvalidHdr(str(e))

def getHdrSystemIds(file):
    try:
        f = rbu_hdr.HdrFile(file)
        return ( id for id, hwrev in f.systemIds() )
    except rbu_hdr.InvalidRbuHdr, e:
        raise InvalidHdr(str(e))

