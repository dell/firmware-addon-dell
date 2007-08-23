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

from __future__ import generators

# import arranged alphabetically
import commands
import os

# local modules
import biosHdr
import firmwaretools.package as package

rbu_load_error="""Could not load Dell RBU kernel driver (dell_rbu).
This kernel driver is included in Linux kernel 2.6.14 and later.
For earlier releases, you can download the dell_rbu dkms module.

Cannot continue, exiting...
"""

bios_update_error="""Could not update the system BIOS.

Many times, this is due to memory constraints. The BIOS update can require from
1 to 4 megabytes of physically contiguous free RAM in order to do the update.
Because memory can become fragmented, this is not always available. To correct
this, try rebooting and running the update immediately after reboot.

The output from the low-level bios update command was:

%s
"""

class BiosPackage(package.RepositoryPackage):
    def __init__(self, *args, **kargs):
        super(BiosPackage, self).__init__(*args, **kargs)
        self.compareStrategy = biosHdr.compareVersions
        self.capabilities['can_downgrade'] = True
        self.capabilities['can_reflash'] = True

    def install(self):
        self.status = "in_progress"
        override=""
        # only activate override in cases where it is needed.
        installDevice = self.getCurrentInstallDevice()
        #print "BiosPackage DEBUG: %s" % self.compareVersion(installDevice)
        if self.compareVersion(installDevice) <= 0:   # activate for downgrade and reflash
            override="--override_bios_version"
        instStr = """dellBiosUpdate %s -u -f %s""" % (override, os.path.join(self.path, "bios.hdr"))
        #print "BiosPackage: %s" % instStr

        ret = os.system("/sbin/modprobe dell_rbu")
        if ret:
            return (0, rbu_load_error)
        status, output = commands.getstatusoutput(instStr)
        if status:
            self.status = "failed"
            raise package.InstallError(bios_update_error % output)

        self.status = "success"
        return 1


import traceback

# standard entry point -- Bootstrap
def BootstrapGenerator(): 
    sysId = biosHdr.getSystemId()
    biosVer = biosHdr.getSystemBiosVer()

    yield package.Device(
            name = ("bmc_firmware(ven_0x1028_dev_0x%04x)" % sysId).lower(),
            displayname = "System BIOS for %s" % biosHdr.getProductName(),
            version = biosVer,
            )

    yield package.Device(
            name = ("system_bios(ven_0x1028_dev_0x%04x)" % sysId).lower(),
            displayname = "Baseboard Management Controller (BMC) for %s" % biosHdr.getProductName(),
            version = biosVer,
            )

    # output all normal PCI bootstrap packages with system-specific name
    pymod = "firmwaretools.bootstrap_pci"
    module = __import__(pymod, globals(),  locals(), [])
    for i in pymod.split(".")[1:]:
        module = getattr(module, i)
    for pkg in module.BootstrapGenerator():
        pkg.name = "%s/%s" % (pkg.name, "system(ven_0x1028_dev_0x%04x)" % sysId)
        yield pkg


# standard entry point -- Inventory
#  -- this is a generator function, but system can only have one system bios,
#     so, only one yield, no loop
def InventoryGenerator(): 
    sysId = biosHdr.getSystemId()
    biosVer = biosHdr.getSystemBiosVer()
    p = package.Device(
        name = ("system_bios(ven_0x1028_dev_0x%04x)" % sysId).lower(),
        displayname = "System BIOS for %s" % biosHdr.getProductName(),
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

