
import ConfigParser
import glob
import os
import shutil

import firmwaretools
import firmware_extract as fte
import firmware_addon_dell as fad
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import extract_common as common
import biosHdr
from extract_bios_blacklist import dell_system_id_blacklist

__VERSION__ = firmwaretools.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"

moduleLog = getLog()
conf = None

class noHdrs(fte.DebugExc): pass

decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    # try/except in case extract plugin not installed
    try:
        import extract_cmd
        extract_cmd.registerPlugin(alreadyHdr, __VERSION__)
        extract_cmd.registerPlugin(biosFromLinuxDup, __VERSION__)
        extract_cmd.registerPlugin(biosFromWindowsDup, __VERSION__)
        if os.path.exists("/usr/bin/wine"):
            extract_cmd.registerPlugin(biosFromPrecisionWindowsExe, __VERSION__)
        if os.path.exists("/usr/bin/unshield"):
            extract_cmd.registerPlugin(biosFromInstallShield, __VERSION__)
        if os.path.exists( os.path.join(fad.PKGLIBEXECDIR, "extract_hdr_helper.sh" )):
            extract_cmd.registerPlugin(biosFromDcopyExe, __VERSION__)
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
def biosFromLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
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
def biosFromWindowsDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir, os.path.join(statusObj.tmpdir,"BiosHeader")):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True

decorate(traceLog())
def biosFromInstallShield(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    common.doOnce( statusObj, common.cabExtract, "data1.cab", statusObj.tmpdir, logger )
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir, os.path.join(statusObj.tmpdir,"BiosHeader")):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True

decorate(traceLog())
def biosFromPrecisionWindowsExe(statusObj, outputTopdir, logger, *args, **kargs):
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
    except common.CommandFailed, e:
        raise common.skip, "couldnt extract with wine"
    except OSError, e:
        raise common.skip, "wine not installed"

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True

decorate(traceLog())
def biosFromDcopyExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    try:
        common.loggedCmd(
            [os.path.join(fad.PKGLIBEXECDIR, "extract_hdr_helper.sh"), statusObj.tmpfile, "bios.hdr"],
            timeout=75,
            cwd=statusObj.tmpdir, logger=logger,
            env={"WORKINGDIR":statusObj.tmpdir, "DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "HOME": os.environ["HOME"]})

    except common.CommandFailed, e:
        raise common.skip, "couldnt extract with extract_hdr_helper.sh"
    except OSError, e:
        raise common.skip, "extract_hdr_helper.sh not installed."

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
        elif os.path.isfile(path):
            toTry.append(path)

    for i in toTry:
        try:
            ver = biosHdr.getBiosHdrVersion(i)
            for id in biosHdr.getHdrSystemIds(i):
                gotOne = True
                yield i, id, ver
        except biosHdr.InvalidHdr, e:
            pass

    if not gotOne:
        raise noHdrs, "No .HDR file found in %s" % str(paths)

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

    if id in dell_system_id_blacklist:
        common.setIni( packageIni, "package",
            blacklisted="1",
            blacklist_reason="Broken RBU implementation.",
            name = "BLACKLISTED_system_bios(ven_0x1028_dev_0x%04x)" % id,
            vendor_id = "BLACKLISTED_0x1028",
            device_id = "BLACKLISTED_0x%04x" % id,
            safe_name = "BLACKLISTED_%s" % systemName,
        )

    # link the logfile, so we always have a log of the last extract for this bios
    while True:
        try:
            common.safeunlink(os.path.join(dest, "extract.log"))
            os.link(logger.handlers[0].baseFilename, os.path.join(dest, "extract.log"))
            break
        except OSError:
            pass

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



