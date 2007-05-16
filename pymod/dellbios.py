#!/usr/bin/python
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:

  #############################################################################
  #
  # Copyright (c) 2005 Dell Computer Corporation
  # Dual Licenced under GNU GPL and OSL
  #
  #############################################################################
"""module

some docs here eventually.
"""

from __future__ import generators

# import arranged alphabetically
import commands
import os

# local modules
import biosHdr
import package

class BiosPackageWrapper(object):
    def __init__(self, package):
        package.installFunction = self.installFunction
        package.compareStrategy = biosHdr.compareVersions
        package.type = self

    def installFunction(self, package):
        ret = os.system("/sbin/modprobe dell_rbu")
        if ret:
            out = ("Could not load Dell RBU kernel driver (dell_rbu).\n"
                  " This kernel driver is included in Linux kernel 2.6.14 and later.\n"
                  " For earlier releases, you can download the dell_rbu dkms module.\n\n"
                  " Cannot continue, exiting...\n")
            return (0, out)
        status, output = commands.getstatusoutput("""dellBiosUpdate -u -f %s""" % os.path.join(package.path, "bios.hdr"))
        if status:
            raise package.InstallError(output)
        return 1


import traceback

# standard entry point -- Bootstrap
def BootstrapGenerator(): 
    sysId = biosHdr.getSystemId()

    for i in [ "system_bios(ven_0x1028_dev_0x%04x)", "bmc_firmware(ven_0x1028_dev_0x%04x)" ]:
        p = package.InstalledPackage(
            name = (i % sysId).lower()
            )
        yield p

    # output all normal PCI bootstrap packages with system-specific name
    module = __import__("bootstrap_pci", globals(),  locals(), [])
    for pkg in module.BootstrapGenerator():
        pkg.name = "%s/%s" % (pkg.name, "system(ven_0x1028_dev_0x%04x)" % sysId)
        yield pkg


# standard entry point -- Inventory
#  -- this is a generator function, but system can only have one system bios,
#     so, only one yield, no loop
def InventoryGenerator(): 
    sysId = biosHdr.getSystemId()
    biosVer = biosHdr.getSystemBiosVer()
    p = package.InstalledPackage(
        name = ("system_bios(ven_0x1028_dev_0x%04x)" % sysId).lower(),
        version = biosVer,
        compareStrategy = biosHdr.compareVersions,
        )
    yield p

#==============================================================
# mock classes for unit tests
#   plus expected data returns
#==============================================================

# re-use mock data from low-level getSystemId mock function
mockExpectedOutput_inventory = [("system_bios(ven_0x1028_dev_0x0183)", "a05"), ]

#==============================================================
# mock classes for unit tests
#   plus expected data returns
#==============================================================

# re-use mock data from low-level getSystemId mock function
mockExpectedOutput_bootstrap = """system_bios(ven_0x1028_dev_0x0183)
bmc_firmware(ven_0x1028_dev_0x0183)"""

