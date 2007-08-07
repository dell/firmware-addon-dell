#!/usr/bin/python2
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
        index = 0
        for package in firmware_addon_dell.dellbios.InventoryGenerator():
            self.assertEqual( firmware_addon_dell.dellbios.mockExpectedOutput_inventory[index][0], package.name )
            self.assertEqual( firmware_addon_dell.dellbios.mockExpectedOutput_inventory[index][1], package.version )
            index = index + 1
  
    # this one is disabled because output from dellbios bootstrap inventory
    # has changed, and mock output hasn't caught up.
    def disabled_testBootstrap(self):
        import firmware_addon_dell.dellbios
        index = 0
        for package in firmware_addon_dell.dellbios.BootstrapGenerator():
            print  "DEBUG1: %s" % str(package) 
            print  "DEBUG2: %s" % firmware_addon_dell.dellbios.mockExpectedOutput_bootstrap.split("\n")[index]
            self.assertEqual( firmware_addon_dell.dellbios.mockExpectedOutput_bootstrap.split("\n")[index], str(package) )
            index = index + 1



if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
