#!/usr/bin/python2
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
"""

from __future__ import generators

import sys
import unittest

class TestCase(unittest.TestCase):
    def setUp(self):
        import biosHdr
        biosHdr.unit_test_mode = 1
    
    def tearDown(self):
        import biosHdr
        biosHdr.unit_test_mode = 0
        
    def testGetSystemID(self):
        import biosHdr
        id = biosHdr.getSystemId()
        self.assertEqual( id, biosHdr.mockResult_getSystemId )
 
    def testGetSystemBiosVer(self):
        import biosHdr
        biosVer = biosHdr.getSystemBiosVer()
        self.assertEqual( biosVer, biosHdr.mockResult_getSystemBiosVer )
 
    def testGetBiosHdrVersion(self):
        import biosHdr
        biosVer = biosHdr.getBiosHdrVersion("")
        self.assertEqual( biosVer, biosHdr.mockResult_getBiosHdrVersion )
 
    def testGetHdrSystemIds(self):
        import biosHdr
        biosVer = biosHdr.getHdrSystemIds("")
        self.assertEqual( biosVer, biosHdr.mockResult_getHdrSystemIds )
 



if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
