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
import package

# sample XML:
# <?xml version="1.0" encoding="UTF-8"?>
# <SVMInventory lang="en">
#   <Device vendorID="1028" deviceID="0015" subDeviceID="1F03" subVendorID="1028" bus="2" device="14" function="0" display="Dell PERC 5/i Integrated Controller 1">
#       <Application componentType="FRMW" version="5.0.1-0030" display="Dell PERC 5/i Integrated Controller 1 Firmware"/>
#   </Device>
#</SVMInventory>
#
# loathe SVM team. What kind of idiots specify hex values in a dtd without leading 0x? Are bus/device/function also hex? Who knows?

def genPackagesFromSvmXml(xmlstr):
    import xml.dom.minidom
    import HelperXml as xmlHelp
    otherAttrs={}
    dom = xml.dom.minidom.parseString(xmlstr)
    for nodeElem in xmlHelp.iterNodeElement( dom, "SVMInventory", "Device" ):
        try:
        
            venId = int(xmlHelp.getNodeAttribute(nodeElem, "vendorID"), 16)
            devId = int(xmlHelp.getNodeAttribute(nodeElem, "deviceID"), 16)
            name = "pci_firmware(ven_0x%04x_dev_0x%04x)".lower() % (venId, devId)

            try:
                subdevId = int(xmlHelp.getNodeAttribute(nodeElem, "subDeviceID"), 16)
                subvenId = int(xmlHelp.getNodeAttribute(nodeElem, "subVendorID"), 16)
                name = "pci_firmware(ven_0x%04x_dev_0x%04x_subven_0x%04x_subdev_0x%04x)".lower() % (venId, devId, subvenId, subdevId)
            except TypeError:
                pass

            try:
                bus = int(xmlHelp.getNodeAttribute(nodeElem, "bus"), 16)
                device = int(xmlHelp.getNodeAttribute(nodeElem, "device"), 16)
                function = int(xmlHelp.getNodeAttribute(nodeElem, "function"), 16)
                otherAttrs["pciDbdf"] = (0, bus, device, function)
            except TypeError:
                pass

            friendlyName =  xmlHelp.getNodeAttribute(nodeElem, "display", ("Application", {"componentType":"FRMW"}))
            ver = xmlHelp.getNodeAttribute(nodeElem, "version", ("Application", {"componentType":"FRMW"}))
    
            p = package.InstalledPackage(
                name=name,
                version = ver.lower(),
                friendlyName=friendlyName,
                **otherAttrs
                )

            yield p
        except:
            raise
