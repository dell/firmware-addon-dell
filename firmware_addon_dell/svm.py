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

# import arranged alphabetically
import firmwaretools.package as package
import xml.dom.minidom
import HelperXml as xmlHelp

# sample XML:
# <?xml version="1.0" encoding="UTF-8"?>
# <SVMInventory lang="en">
#   <Device vendorID="1028" deviceID="0015" subDeviceID="1F03" subVendorID="1028" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
#       <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
#   </Device>
#</SVMInventory>
#
# loathe SVM team. What kind of idiots specify hex values in a dtd without leading 0x? Are bus/device/function also hex? Who knows?

# more sample XML:

#<?xml version="1.0" encoding="UTF-8"?>
#<SVMInventory lang="en">
#  <Device vendorID="1000" deviceID="0060" subDeviceID="1F0C" subVendorID="1028" bus="5" device="0" function="0" display="PERC 6/i Integrated Controller 0" impactsTPMmeasurements="TRUE">
#    <Application componentType="FRMW" version="6.0.1-0080" display="PERC 6/i Integrated Controller 0 Firmware"/>
#  </Device>
#  <Device componentID="13313" enum="CtrlId 0 DeviceId 0" display="ST973402SS">
#    <Application componentType="FRMW" version="S206" display="ST973402SS Firmware"/>
#  </Device>
#  <Device componentID="00000" enum="CtrlId 0 DeviceId 1" display="ST936701SS">
#     <Application componentType="FRMW" version="S103" display="ST936701SS Firmware"/>
#  </Device>
#  <Device componentID="11204" enum="CtrlId 0 DeviceId 20 Backplane" display="SAS/SATA Backplane 0:0 Backplane">
#    <Application componentType="FRMW" version="1.05" display="SAS/SATA Backplane 0:0 Backplane Firmware"/>
#  </Device>
# </SVMInventory>

pciShortFirmStr = "pci_firmware(ven_0x%04x_dev_0x%04x)"
pciFullFirmStr = "pci_firmware(ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x)"

def genPackagesFromSvmXml(xmlstr):
    otherAttrs={}
    dom = xml.dom.minidom.parseString(xmlstr)
    for nodeElem in xmlHelp.iterNodeElement( dom, "SVMInventory", "Device" ):
        type = package.Device
        name = None
        componentId = xmlHelp.getNodeAttribute(nodeElem, "componentID")
        venId = xmlHelp.getNodeAttribute(nodeElem, "vendorID")
        devId = xmlHelp.getNodeAttribute(nodeElem, "deviceID")
        subdevId = xmlHelp.getNodeAttribute(nodeElem, "subDeviceID")
        subvenId = xmlHelp.getNodeAttribute(nodeElem, "subVendorID")
        displayname =  xmlHelp.getNodeAttribute(nodeElem, "display", ("Application", {"componentType":"FRMW"}))
        ver = xmlHelp.getNodeAttribute(nodeElem, "version", ("Application", {"componentType":"FRMW"}))
        bus = xmlHelp.getNodeAttribute(nodeElem, "bus")
        device = xmlHelp.getNodeAttribute(nodeElem, "device")
        function = xmlHelp.getNodeAttribute(nodeElem, "function")

        if venId and devId:
            venId = int(venId, 16)
            devId = int(devId, 16)
            name = pciShortFirmStr % (venId, devId)
            otherAttrs["xmlNode"] = nodeElem
            if subvenId and subdevId:
                subdevId = int(subdevId,16)
                subvenId = int(subvenId,16)
                name = pciFullFirmStr % (venId, devId, subvenId, subdevId)
        else:
            componentId = int(componentId,10)
            name = "dell_dup_componentid_%05d" % componentId

        if bus and device and function:
            bus = int(bus, 16)
            device = int(device, 16)
            function = int(function, 16)
            otherAttrs["pciDbdf"] = (0, bus, device, function)
            type = package.PciDevice

        if not name:
            continue

        yield type(
            name=name,
            version = ver.lower(),
            displayname=displayname,
            **otherAttrs
            )
