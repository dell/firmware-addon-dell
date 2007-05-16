#!/usr/bin/python2
# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
"""

import getopt
import sys
import xml.dom.minidom
import unittest

import HelperXml

testXml = """<?xml version="1.0" ?>
<root>
    <node attr="1"/>
    <node attr="2"/>
    <node attr="3"/>
    <blap>
        <subnode>
            <name>FOO</name>
        </subnode>
        <subnode>
            <name>BAR</name>
        </subnode>
    </blap>
</root>
"""

class TestCase(unittest.TestCase):
    def setUp(self):
        self.dom = xml.dom.minidom.parseString(testXml)
    
    def tearDown(self):
        self.dom = None
        
    def testOldFashionedAttr(self):
        result = []
        expected = ["1", "2", "3"]

        root = HelperXml.getNodeElement( self.dom, "root")
        for rootChild in root.childNodes:
            if rootChild.nodeName == "node":
                result.append(HelperXml.getNodeAttribute( rootChild, "attr" ))

        self.assertEqual( result, expected )

    def testIterNodeAttrManual(self):
        result = []
        expected = ["1", "2", "3"]

        for nodeElem in HelperXml.iterNodeElement( self.dom, "root", "node" ):
            result.append(HelperXml.getNodeAttribute(nodeElem, "attr"))

        self.assertEqual( result, expected )

    def testIterNodeAttrAuto(self):
        result = []
        expected = ["1", "2", "3"]

        for attr in HelperXml.iterNodeAttribute( self.dom, "attr", "root", "node" ):
            result.append(attr)
            
        self.assertEqual( result, expected )

    def testOldFashionedNode(self):
        result = []
        expected = ["FOO", "BAR"]

        elem = HelperXml.getNodeElement( self.dom, "root", "blap")
        for blapChild in elem.childNodes:
            if blapChild.nodeName == "subnode":
                for subnodeChild in blapChild.childNodes:
                    if subnodeChild.nodeName == "name":
                        result.append(HelperXml.getNodeText( subnodeChild ))
        self.assertEqual( result, expected )

    def testIterNode(self):
        result = []
        expected = ["FOO", "BAR"]

        for nameElem in HelperXml.iterNodeElement( self.dom, "root", "blap", "subnode", "name" ):
            result.append(HelperXml.getNodeText(nameElem))

        self.assertEqual( result, expected )

if __name__ == "__main__":
    import test.TestLib
    sys.exit(not test.TestLib.runTests( [TestCase] ))
