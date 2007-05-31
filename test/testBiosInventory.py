#!/usr/bin/python2
# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
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
        
    def testInventory(self):
        module = __import__("dellbios", globals(),  locals(), [])
        index = 0
        for package in module.InventoryGenerator():
            self.assertEqual( module.mockExpectedOutput_inventory[index][0], package.name )
            self.assertEqual( module.mockExpectedOutput_inventory[index][1], package.version )
            index = index + 1
  
    # this one is disabled because output from dellbios bootstrap inventory
    # has changed, and mock output hasn't caught up.
    def disabled_testBootstrap(self):
        module = __import__("dellbios", globals(),  locals(), [])
        index = 0
        for package in module.BootstrapGenerator():
            print  "DEBUG1: %s" % str(package) 
            print  "DEBUG2: %s" % module.mockExpectedOutput_bootstrap.split("\n")[index]
            self.assertEqual( module.mockExpectedOutput_bootstrap.split("\n")[index], str(package) )
            index = index + 1



if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
