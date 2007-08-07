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
import commands
import os

class PermissionDenied (Exception): pass
class InternalError (Exception): pass
class InvalidHdr (Exception): pass

unit_test_mode = 0
def cmdFactory_getSystemId():
    if not unit_test_mode:
        status, output = commands.getstatusoutput("""getSystemId""")
        if status != 0:
            raise PermissionDenied("Failed to get System ID: %s" % output)
        return output
    else:
        return mockOutput_getSystemId


def getSystemId():
    output = cmdFactory_getSystemId()
    for line in output.split("\n"):
        if line.startswith("System ID:"):
            first, id = line.split(":", 1)
            return int(id.strip().lower(), 16)
    raise InternalError("Could not find System ID in getSystemId output.")

def getServiceTag():
    output = cmdFactory_getSystemId()
    for line in output.split("\n"):
        if line.startswith("Service Tag:"):
            first, id = line.split(":", 1)
            return id.strip()
    raise InternalError("Could not find System ID in getSystemId output.")
            
def getSystemBiosVer():
    output = cmdFactory_getSystemId()
    for line in output.split("\n"):
        if line.startswith("BIOS Version:"):
            first, id = line.split(":", 1)
            return id.strip().lower()
    raise InternalError("Could not find BIOS Version in getSystemId output.")
            

firstSpecialVer = 90
def compareVersions(latest, toTest):
    if latest == toTest:
        return 0

    #some broken bios were leaked with bad version
    # never let 'unknown' version override good version
    if toTest == "unknown" or toTest == "49.0.48":
        return 1

    if latest == "unknown" or latest == "49.0.48":
        return -1

    # old style bios versioning ("Ann", eg. "A01"...)
    if "." not in latest and "." not in toTest:
        # anything non "Ann" version is "special" and should never win a
        # ver comparison unless 'latest' is also "special" 
        if not toTest.lower().startswith("a") and latest.lower().startswith("a"):
            return 1
        elif toTest.lower().startswith("a") and not latest.lower().startswith("a"):
            return -1

        if toTest > latest:
            return -1
        else:
            return 1

    # only get here if one or other has new-style bios versioning

    # new style bios overrides old style...
    if "." not in latest:
        return -1
    if "." not in toTest:
        return 1

    # both new style, compare major/minor/build individually
    latestArr = latest.split(".")
    toTestArr = toTest.split(".")

    # versions 90-99 are "special" and should never win a ver comparison
    # unless 'latest' is also "special"
    try:
        if int(toTestArr[0]) >= firstSpecialVer and int(latestArr[0]) < firstSpecialVer:
            return 1
        if int(latestArr[0]) >= firstSpecialVer and int(toTestArr[0]) < firstSpecialVer:
            return -1
    except ValueError: # non-numeric version ?
        pass

    for i in xrange(0, len(latestArr)):
        # test array shorter than latest, 
        if i >= len(toTestArr):
            return 1
        try:
            if int(toTestArr[i]) > int(latestArr[i]):
                return -1
            if int(toTestArr[i]) < int(latestArr[i]):
                return 1
        except ValueError:  # non-numeric version?
            pass #punt...

    # if we get here, everything is equal (so far)
    if len(toTestArr) > len(latestArr):
        return -1

    return 1
            
        
def cmdFactory_dellBiosUpdate(filename):
    if not unit_test_mode:
        status, output = commands.getstatusoutput("""dellBiosUpdate -i -f %s""" % filename)
        if status != 0:
            raise InvalidHdr("(version) Not a BIOS HDR file (%s): %s" % (file,output))
        return output
    else:
        return mockOutput_dellBiosUpdate


# no good way to unit test this for now...
def isHdrFileNewer(file):
    status, output = commands.getstatusoutput("""dellBiosUpdate -t -f %s""" % file)
    return not status


def getBiosHdrVersion(file):
    output = cmdFactory_dellBiosUpdate(file)
    for line in output.split("\n"):
        if line.startswith("Version:"):
            first, ver = line.split(":", 1)
            ver = ver.strip().lower()
            if not ver: ver = "unknown"
            return ver
    raise InternalError("Could not find BIOS version in hdr file: %s" % file)

def getHdrSystemIds(file):
    output = cmdFactory_dellBiosUpdate(file)
    for line in output.split("\n"):
        if line.startswith("System ID List:"):
            first, idListStr = line.split(":", 1)
            idListStr = idListStr.strip().lower()
            outputList = [ int(s.lower(),16) for s in idListStr.split(" ") if s ]
            return outputList

    raise InternalError("Could not find System ID list in hdr file.")


#========================================
# mock stuff
#========================================

mockOutput_getSystemId = """Libsmbios:    0.11.1
System ID:    0x0183
Service Tag:  B0KGJ71
Product Name: PowerEdge 1800
BIOS Version: A05
Vendor:       Dell Computer Corporation
Is Dell:      1"""

mockResult_getSystemId = 0x0183
mockResult_getSystemBiosVer = "a05"


mockOutput_dellBiosUpdate = """HeaderId : $RBU
Header Length: 84
Header Major Ver: 1
Header Minor Ver: 1
Num Systems: 1
Version: A05
Quick Check: Copyright 2005 Dell Computer Corporation
System ID List: 0x0183

"""

mockResult_getBiosHdrVersion = "a05"
mockResult_getHdrSystemIds = [ 0x0183, ]

