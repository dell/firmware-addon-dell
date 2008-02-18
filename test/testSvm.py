#!/usr/bin/python
# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
"""

from __future__ import generators

import sys
import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testSvm_onePkg(self):
        import firmware_addon_dell.svm as svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015_subven_0x1028_subdev_0x1f03)",
                "displayname": "Dell PERC 5/i Integrated Controller 1 Firmware",
                "pciDbdf": (0, 2, 0x14, 0)
            },]
        actualResult = []

        testXml="""<?xml version="1.0" encoding="UTF-8"?>
<SVMInventory lang="en">
    <Device vendorID="1028" deviceID="0015" subDeviceID="1F03" subVendorID="1028" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
</Device>
</SVMInventory>
"""

        for p in svm.genPackagesFromSvmXml(testXml):
            actualResult.append(p)

        self.assertEqual(len(expectedResult), len(actualResult))

        for i in xrange(0,len(actualResult)):
            for attr,value in expectedResult[i].items():
                self.assertEqual(value, getattr(actualResult[i], attr))

    def testSvm_pcivendev_only(self):
        import firmware_addon_dell.svm as svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015)",
                "displayname": "Dell PERC 5/i Integrated Controller 1 Firmware",
                "pciDbdf": (0, 2, 0x14, 0)
            },]
        actualResult = []

        testXml="""<?xml version="1.0" encoding="UTF-8"?>
<SVMInventory lang="en">
    <Device vendorID="1028" deviceID="0015" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
</Device>
</SVMInventory>
"""

        for p in svm.genPackagesFromSvmXml(testXml):
            actualResult.append(p)

        self.assertEqual(len(expectedResult), len(actualResult))

        for i in xrange(0,len(actualResult)):
            for attr,value in expectedResult[i].items():
                self.assertEqual(value, getattr(actualResult[i], attr))


    def testSvm_no_bdf(self):
        import firmware_addon_dell.svm as svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015)",
                "displayname": "Dell PERC 5/i Integrated Controller 1 Firmware",
            },]
        actualResult = []

        testXml="""<?xml version="1.0" encoding="UTF-8"?>
<SVMInventory lang="en">
    <Device vendorID="1028" deviceID="0015" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
</Device>
</SVMInventory>
"""

        for p in svm.genPackagesFromSvmXml(testXml):
            actualResult.append(p)

        self.assertEqual(len(expectedResult), len(actualResult))

        for i in xrange(0,len(actualResult)):
            for attr,value in expectedResult[i].items():
                self.assertEqual(value, getattr(actualResult[i], attr))

    def testSvm_multiPkg(self):
        import firmware_addon_dell.svm as svm
        expectedResult = [
                {"name": "pci_firmware(ven_0x1028_dev_0x0015_subven_0x1028_subdev_0x1f03)",
                "displayname": "Dell PERC 5/i Integrated Controller 1 Firmware",
                "pciDbdf": (0, 2, 0x14, 0)},
                {"name": "pci_firmware(ven_0x1028_dev_0x0016)",
                "displayname": "Dell PERC 5/i Integrated Controller 2 Firmware",
                "pciDbdf": (0, 2, 0x15, 0)},
                {"name": "pci_firmware(ven_0x1028_dev_0x0017)",
                "displayname": "Dell PERC 5/i Integrated Controller 3 Firmware",
                "pciDbdf": (0, 2, 0x16, 0)},
            ]
        actualResult = []

        testXml="""<?xml version="1.0" encoding="UTF-8"?>
<SVMInventory lang="en">
    <Device vendorID="1028" deviceID="0015" subDeviceID="1F03" subVendorID="1028" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
        <Application componentType="DRVR" version="xx" display="Dell PERC 5/i Integrated Controller 1 Driver"/>
    </Device>
    <Device vendorID="1028" deviceID="0016" bus="2" device="15" function="0" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 2 Firmware"/>
        <Application componentType="DRVR" version="xx" display="Dell PERC 5/i Integrated Controller 1 Driver"/>
    </Device>
    <Device vendorID="1028" deviceID="0017" bus="2" device="16" function="0" display="Dell PERC 5/i Integrated Controller 1">
        <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 3 Firmware"/>
        <Application componentType="DRVR" version="xx" display="Dell PERC 5/i Integrated Controller 1 Driver"/>
    </Device>
</SVMInventory>
"""

        for p in svm.genPackagesFromSvmXml(testXml):
            actualResult.append(p)

        self.assertEqual(len(expectedResult), len(actualResult))

        for i in xrange(0,len(actualResult)):
            for attr,value in expectedResult[i].items():
                self.assertEqual(value, getattr(actualResult[i], attr))


    def testSvm_nonPci(self):
        import firmware_addon_dell.svm as svm
        expectedResult = [
                {"name": "pci_firmware(ven_0x1000_dev_0x0060_subven_0x1028_subdev_0x1f0c)",
                "displayname": u'PERC 6/i Integrated Controller 0 Firmware',
                "pciDbdf": (0, 5, 0, 0)},

                {"name": "dell_dup_componentid_13313",
                "displayname": u"ST973402SS Firmware",
                "version": "s206",
                },

                {"name": "dell_dup_componentid_00000",
                "displayname": u"ST936701SS Firmware",
                "version": "s103",
                },

                {"name": "dell_dup_componentid_11204",
                "displayname": u"SAS/SATA Backplane 0:0 Backplane Firmware",
                "version": "1.05",
                },
            ]
        actualResult = []

        testXml="""<?xml version="1.0" encoding="UTF-8"?>

<SVMInventory lang="en">
    <Device vendorID="1000" deviceID="0060" subDeviceID="1F0C" subVendorID="1028" bus="5" device="0" function="0" display="PERC 6/i Integrated Controller 0" impactsTPMmeasurements="TRUE">
        <Application componentType="FRMW" version="6.0.1-0080" display="PERC 6/i Integrated Controller 0 Firmware"/>
    </Device>
    <Device componentID="13313" enum="CtrlId 0 DeviceId 0" display="ST973402SS">
        <Application componentType="FRMW" version="S206" display="ST973402SS Firmware"/>
    </Device>
    <Device componentID="00000" enum="CtrlId 0 DeviceId 1" display="ST936701SS">
        <Application componentType="FRMW" version="S103" display="ST936701SS Firmware"/>
    </Device>
    <Device componentID="11204" enum="CtrlId 0 DeviceId 20 Backplane" display="SAS/SATA Backplane 0:0 Backplane">
        <Application componentType="FRMW" version="1.05" display="SAS/SATA Backplane 0:0 Backplane Firmware"/>
    </Device>
</SVMInventory>"""

        for p in svm.genPackagesFromSvmXml(testXml):
            actualResult.append(p)

        self.assertEqual(len(expectedResult), len(actualResult))

        for i in xrange(0,len(actualResult)):
            for attr,value in expectedResult[i].items():
                self.assertEqual(value, getattr(actualResult[i], attr))


if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
