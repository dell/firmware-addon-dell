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
        
    def testInventory(self):
        import firmware_addon_dell.dellbios
        # need to figure out a way to write a test for this....
  
    def testBootstrap(self):
        import firmware_addon_dell.dellbios
        # need to figure out a way to write a test for this....



if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
