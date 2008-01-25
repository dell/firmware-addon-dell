
import ConfigParser
import glob
import os
import shutil
import subprocess

import firmwaretools
import firmware_tools_extract as fte
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import extract_common as common
import biosHdr

__VERSION__ = firmwaretools.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"

moduleLog = getLog()
conf = None

class noHdrs(fte.DebugExc): pass
class skip(fte.DebugExc): pass

decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    # try/except in case extract plugin not installed
    try:
        import extract_cmd
        extract_cmd.registerPlugin(alreadyHdr, __VERSION__)
        extract_cmd.registerPlugin(extractBiosFromLinuxDup, __VERSION__)
        extract_cmd.registerPlugin(extractBiosFromWindowsDupOrInstallShield, __VERSION__)
        extract_cmd.registerPlugin(extractBiosFromPrecisionWindowsExe, __VERSION__)
        extract_cmd.registerPlugin(extractBiosFromDcopyExe, __VERSION__)
    except ImportError, e:
        moduleLog.info("failed to register extract module.")
        return

    global conf
    conf = checkConf(conduit.getConf(), conduit.getBase().opts)

decorate(traceLog())
def extract_addSubOptions_hook(conduit, *args, **kargs):
    conduit.getOptParser().add_option(
        "--id2name-config", help="Add system id to name mapping config file.",
        action="append", dest="system_id2name_map", default=[])

true_vals = ("1", "true", "yes", "on")

decorate(traceLog())
def checkConf(conf, opts):
    if getattr(conf, "system_id2name_map", None) is None:
        conf.system_id2name_map = os.path.join(firmwaretools.DATADIR, "firmware-tools", "system_id2name.ini")

    conf.id2name = ConfigParser.ConfigParser()
    conf.id2name.read(conf.system_id2name_map)
    conf.id2name.read(opts.system_id2name_map)
    return conf

decorate(traceLog())
def extractBiosFromLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )

    deps = {}
    # these are (int, str) tuple
    for sysId, reqver in common.getBiosDependencies( os.path.join(statusObj.tmpdir,"package.xml")):
        deps[sysId] = reqver

    gotOne=False
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        gotOne=True
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        shutil.copy( os.path.join(statusObj.tmpdir, "package.xml"), dest)

        #setup deps
        minVer = deps.get(id)
        requires = ""
        if minVer:
            requires = "system_bios(ven_0x1028_dev_0x%04x) >= %s" % (id, minVer)

        common.setIni(packageIni, "package", requires=requires)
        writePackageIni(dest, packageIni)

    return True

decorate(traceLog())
def alreadyHdr(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.hdr')
    for hdr, id, ver in getHdrIdVer(statusObj.file):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % hdr[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "info.txt") )
    return True

decorate(traceLog())
def extractBiosFromWindowsDupOrInstallShield(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    common.doOnce( statusObj, common.cabExtract, "data1.cab", statusObj.tmpdir, logger )
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir, os.path.join(statusObj.tmpdir,"BiosHeader")):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True

decorate(traceLog())
def extractBiosFromPrecisionWindowsExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    try:
        common.loggedCmd(["wineserver", "-k"], cwd=statusObj.tmpdir, logger=logger)
        common.loggedCmd(["wineserver", "-p0"], cwd=statusObj.tmpdir, logger=logger)

        common.loggedCmd(
            ["wine", statusObj.tmpfile, "-writehdrfile", "-nopause",],
            timeout=75,
            cwd=statusObj.tmpdir, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"]})
    except OSError, e:
        raise skip, "wine not installed"

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True


decorate(traceLog())
def extractBiosFromDcopyExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    try:
        common.loggedCmd(
            ["extract_hdr_helper.sh", statusObj.tmpfile, "bios.hdr"],
            timeout=75,
            cwd=statusObj.tmpdir, logger=logger,
            env={"WORKINGDIR":statusObj.tmpfile, "DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"]})

    except OSError, e:
        raise skip, "extract_hdr_helper.sh not installed."

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
    return True

decorate(traceLog())
def getHdrIdVer(*paths):
    gotOne = False
    toTry=[]
    for path in paths:
        if os.path.isdir(path):
            toTry.extend(glob.glob(os.path.join(path, "*.[hH][dD][rR]")))
        else:
            toTry.append(path)

    for i in toTry:
        ver = biosHdr.getBiosHdrVersion(i)
        for id in biosHdr.getHdrSystemIds(i):
            gotOne = True
            yield i, id, ver

    if not gotOne:
        raise noHdrs, "No .HDR file found in %s" % dir


decorate(traceLog())
def copyHdr(hdr, id, ver, destTop, logger):
    systemName = ("system_bios_ven_0x1028_dev_0x%04x" % id).lower()
    biosName = ("%s_version_%s" % (systemName, ver)).lower()
    dest = os.path.join(destTop, biosName)
    common.safemkdir(dest)
    shutil.copyfile(hdr, os.path.join(dest, "bios.hdr"))

    packageIni = ConfigParser.ConfigParser()
    packageIni.read( os.path.join(dest, "package.ini"))
    if not packageIni.has_section("package"):
        packageIni.add_section("package")

    common.setIni( packageIni, "package",
        spec      = "bios",
        module    = "firmware_addon_dell.dellbios",
        type      = "BiosPackage",
        name      = "system_bios(ven_0x1028_dev_0x%04x)" % id,
        safe_name = systemName,
        vendor_id = "0x1028",
        device_id = "0x%04x" % id,

        version        = ver,
        vendor_version = ver,

        shortname = common.getShortname(conf.id2name, "0x1028", "0x%04x" % id),
    )

    writePackageIni(dest, packageIni)
    return dest, packageIni

decorate(traceLog())
def writePackageIni(dest, ini):
    fd = None
    try:
        try:
            os.unlink(os.path.join(dest, "package.ini"))
        except: pass
        fd = open( os.path.join(dest, "package.ini"), "w+")
        ini.write( fd )
    finally:
        if fd is not None:
            fd.close()



