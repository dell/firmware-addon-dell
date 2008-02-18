#!/usr/bin/python
# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
"""

from __future__ import generators

import sys
import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        import firmware_addon_dell.biosHdr as biosHdr
        biosHdr.unit_test_mode = 1
    
    def tearDown(self):
        import firmware_addon_dell.biosHdr as biosHdr
        biosHdr.unit_test_mode = 0
        
    def testGetSystemID(self):
        import firmware_addon_dell.biosHdr as biosHdr
        id = biosHdr.getSystemId()
        self.assertEqual( id, biosHdr.mockResult_getSystemId )
 
    def testGetSystemBiosVer(self):
        import firmware_addon_dell.biosHdr as biosHdr
        biosVer = biosHdr.getSystemBiosVer()
        self.assertEqual( biosVer, biosHdr.mockResult_getSystemBiosVer )
 
    def testGetBiosHdrVersion(self):
        import firmware_addon_dell.biosHdr as biosHdr
        biosVer = biosHdr.getBiosHdrVersion("")
        self.assertEqual( biosVer, biosHdr.mockResult_getBiosHdrVersion )
 
    def testGetHdrSystemIds(self):
        import firmware_addon_dell.biosHdr as biosHdr
        biosVer = biosHdr.getHdrSystemIds("")
        self.assertEqual( biosVer, biosHdr.mockResult_getHdrSystemIds )

    def testVerCmp_old(self):
        from firmware_addon_dell.biosHdr import compareVersions
        self.assertEqual( -1, compareVersions("A00", "A01"))
        self.assertEqual( -1, compareVersions("A90", "A91"))
        self.assertEqual( -1, compareVersions("X02", "A01"))
        self.assertEqual( -1, compareVersions("T02", "A01"))
        self.assertEqual( -1, compareVersions("P02", "A01"))
        self.assertEqual( -1, compareVersions("B01", "C01"))

        # reversed
        self.assertEqual(  1, compareVersions("A01", "A00"))
        self.assertEqual(  1, compareVersions("A91", "A90"))
        self.assertEqual(  1, compareVersions("A01", "X02"))
        self.assertEqual(  1, compareVersions("A01", "T02"))
        self.assertEqual(  1, compareVersions("A01", "P02"))
        self.assertEqual(  1, compareVersions("C01", "B01"))

    def testVerCmp_new(self):
        from firmware_addon_dell.biosHdr import compareVersions
        # "special" versions
        self.assertEqual( -1, compareVersions("49.0.48", "1.0.0"))
        # test range
        self.assertEqual( -1, compareVersions("90.0.0", "1.0.0"))
        self.assertEqual( -1, compareVersions("90.1.0", "1.0.0"))
        self.assertEqual( -1, compareVersions("90.90.90", "1.0.0"))

        self.assertEqual( -1, compareVersions("1.0.0", "1.0.1"))
        self.assertEqual( -1, compareVersions("1.0.0", "1.1.0"))
        self.assertEqual( -1, compareVersions("1.0.0", "2.0.0"))
        self.assertEqual( -1, compareVersions("1.0",   "1.0.0"))
        self.assertEqual( -1, compareVersions("2.0.0", "3.0.0"))
 
    def testVerCmp_new_rev(self):
        from firmware_addon_dell.biosHdr import compareVersions
        # "special" versions
        self.assertEqual(  1, compareVersions("1.0.0", "49.0.48"))
        # test range
        self.assertEqual(  1, compareVersions("1.0.0", "90.0.0"))
        self.assertEqual(  1, compareVersions("1.0.0", "90.1.0"))
        self.assertEqual(  1, compareVersions("1.0.0", "90.90.90"))

        self.assertEqual(  1, compareVersions("1.0.1", "1.0.0"))
        self.assertEqual(  1, compareVersions("1.1.0", "1.0.0"))
        self.assertEqual(  1, compareVersions("2.0.0", "1.0.0"))
        self.assertEqual(  1, compareVersions("1.0.0", "1.0"))
        self.assertEqual(  1, compareVersions("3.0.0", "2.0.0"))
 




if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
