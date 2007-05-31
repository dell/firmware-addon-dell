#!/usr/bin/python2
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
        import svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015_subven_0x1028_subdev_0x1f03)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 1 Firmware",
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
        import svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 1 Firmware",
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
        import svm
        expectedResult = [{"name": "pci_firmware(ven_0x1028_dev_0x0015)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 1 Firmware",
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
        import svm
        expectedResult = [
                {"name": "pci_firmware(ven_0x1028_dev_0x0015_subven_0x1028_subdev_0x1f03)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 1 Firmware",
                "pciDbdf": (0, 2, 0x14, 0)},
                {"name": "pci_firmware(ven_0x1028_dev_0x0016)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 2 Firmware",
                "pciDbdf": (0, 2, 0x15, 0)},
                {"name": "pci_firmware(ven_0x1028_dev_0x0017)", 
                "friendlyName": "Dell PERC 5/i Integrated Controller 3 Firmware",
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
 


if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
