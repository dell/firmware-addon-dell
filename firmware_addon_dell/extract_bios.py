
import atexit
import ConfigParser
import glob
import os
import shutil
import tempfile

# workaround bug: NameError: global name 'WindowsError' is not defined
class WindowsError(Exception): pass
shutil.WindowsError=WindowsError

import firmwaretools
import firmwaretools.plugins as plugins
from firmwaretools.trace_decorator import decorate, traceLog, getLog
try:
    import firmware_extract as fte
except ImportError:
    raise plugins.DisablePlugin

import firmware_addon_dell as fad
import extract_common as common
import biosHdr
from extract_bios_blacklist import dell_system_id_blacklist

__VERSION__ = firmwaretools.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"

moduleLog = getLog()
conf = None
wineprefix = None
dosprefix = None

class noHdrs(fte.DebugExc): pass

decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf(conduit.getConf(), conduit.getBase().opts)

    # try/except in case extract plugin not installed
    try:
        import extract_cmd
        extract_cmd.registerPlugin(alreadyHdr, __VERSION__)
        extract_cmd.registerPlugin(biosFromLinuxDup, __VERSION__)
        extract_cmd.registerPlugin(biosFromWindowsDup, __VERSION__)
        if os.path.exists("/usr/bin/wine"):
            setupWine()
            extract_cmd.registerPlugin(biosFromWindowsExe, __VERSION__)
        if os.path.exists("/usr/bin/unshield"):
            extract_cmd.registerPlugin(biosFromInstallShield, __VERSION__)
        if getattr(conf, "helper_dat", None) is not None and os.path.exists(conf.helper_dat):
            setupFreedos()
            extract_cmd.registerPlugin(biosFromDOSExe, __VERSION__)
            extract_cmd.registerPlugin(biosFromDcopyExe, __VERSION__)
    except ImportError, e:
        moduleLog.info("failed to register extract module.")
        return


decorate(traceLog())
def extract_addSubOptions_hook(conduit, *args, **kargs):
    conduit.getOptParser().add_option(
        "--id2name-config", help="Add system id to name mapping config file.",
        action="append", dest="system_id2name_map", default=[])
    conduit.getOptParser().add_option(
        "--helper-dat", help="Path to extract_hdr_helper.dat.",
        action="store", dest="helper_dat", default=None)

true_vals = ("1", "true", "yes", "on")

decorate(traceLog())
def checkConf(conf, opts):
    if getattr(conf, "system_id2name_map", None) is None:
        conf.system_id2name_map = os.path.join(firmwaretools.DATADIR, "firmware-tools", "system_id2name.ini")

    if opts.helper_dat is not None:
        conf.helper_dat = os.path.realpath(opts.helper_dat)

    conf.id2name = ConfigParser.ConfigParser()
    conf.id2name.read(conf.system_id2name_map)
    conf.id2name.read(opts.system_id2name_map)
    return conf

decorate(traceLog())
def setupWine():
    getLog(prefix="verbose.").info("Running pre-setup for wine.")
    global wineprefix
    wineprefix = tempfile.mkdtemp(prefix="wineprefix-")
    env={
        "DISPLAY":"",
        "TERM":"",
        "PATH":os.environ["PATH"],
        "HOME":os.environ["HOME"],
        "WINEPREFIX": wineprefix,
        }
    common.loggedCmd(["wineprefixcreate", "-w", "--prefix", wineprefix], cwd=wineprefix, env=env, logger=getLog())
    atexit.register(shutil.rmtree, wineprefix)
    getLog(prefix="verbose.").info("Wine pre-setup finished.")

decorate(traceLog())
def setupFreedos():
    getLog(prefix="verbose.").info("Running pre-setup for freedos.")
    global dosprefix
    dosprefix = tempfile.mkdtemp(prefix="dosprefix-")
    common.loggedCmd(["tar", "xvjf", conf.helper_dat], cwd=dosprefix, logger=getLog())
    import commands
    status, output = commands.getstatusoutput("uname -m")
    if output.startswith("x86_64"):
        os.rename(os.path.join(dosprefix, "both", "64"), os.path.join(dosprefix, "freedos"))
    else:
        os.rename(os.path.join(dosprefix, "both", "32"), os.path.join(dosprefix, "freedos"))
    if not os.path.isdir(os.path.join(os.environ["HOME"], ".dosemu")):
        os.mkdir(os.path.join(os.environ["HOME"], ".dosemu"))
        open(os.path.join(os.environ["HOME"], ".dosemu", "disclaimer"), "w+").close()

    atexit.register(shutil.rmtree, dosprefix)
    getLog(prefix="verbose.").info("Freedos pre-setup finished.")

decorate(traceLog())
def biosFromLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    return genericBiosDup(statusObj, outputTopdir, logger, *args, **kargs)

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
    return genericBiosDup(statusObj, outputTopdir, logger, *args, **kargs)

decorate(traceLog())
def genericBiosDup(statusObj, outputTopdir, logger, *args, **kargs):
    deps = {}
    packageXml = os.path.join(statusObj.tmpdir, "package.xml")
    # these are (int, str) tuple
    for sysId, reqver in common.getBiosDependencies( packageXml):
        deps[sysId] = reqver

    gotOne=False
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        gotOne=True
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        if os.path.exists(os.path.join(dest, "package.xml")):
            os.unlink(os.path.join(dest, "package.xml"))
        shutil.copy( packageXml, dest)

        #setup deps
        minVer = deps.get(id)
        requires = ""
        if minVer:
            requires = "system_bios(ven_0x1028_dev_0x%04x) >= %s" % (id, minVer)

        common.setIni(packageIni, "package", requires=requires)
        writePackageIni(dest, packageIni)

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
def biosFromWindowsExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    thiswineprefix = os.path.join(statusObj.tmpdir, "wine")
    env={
        "DISPLAY":"",
        "TERM":"",
        "PATH":os.environ["PATH"],
        "HOME":os.environ["HOME"],
        "WINEPREFIX": thiswineprefix
        }
    shutil.copytree(wineprefix, thiswineprefix, symlinks=True)
    try:
        common.loggedCmd(
            ["wine", os.path.basename(statusObj.tmpfile), "-writehdrfile", "-nopause",],
            timeout=75, raiseExc=0,
            cwd=statusObj.tmpdir, logger=logger,
            env=env)
        common.loggedCmd(["wineserver", "-k"], cwd=statusObj.tmpdir, logger=logger, env=env)
    except (common.CommandException), e:
        raise common.skip, "couldnt extract with wine"
    except OSError, e:
        raise common.skip, "wine not installed"

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)

    return True

decorate(traceLog())
def setupFreedosForThisDir(subdir, file):
    thisdosprefix = os.path.join(subdir, "dos")
    shutil.copytree(dosprefix, thisdosprefix, symlinks=True)

    fdPath = os.path.join(subdir, "dos", "freedos")
    dosemu = os.path.join(fdPath, "dosemu.bin")
    globalconf = os.path.join(fdPath, "conf", "global.conf")
    dosemurc = os.path.join(fdPath, "conf", "dosemurc")
    cmd = [ dosemu, "-I", "video{none}", "-n", "-F", globalconf, "-f", dosemurc, "-C", "-E" ]

    inp = open( "%s.in" % dosemurc, "r" )
    out = open(dosemurc, "w+")
    for line in inp.readlines():
        line = line.replace("CURRENT_DIRECTORY", fdPath)
        if "$_vbootfloppy =" in line:
            line = """$_vbootfloppy = "%s/dos/floppy.img +hd" """ % subdir
        out.write(line)
    out.close()
    inp.close()

    shutil.copy(file, fdPath)
    return cmd

decorate(traceLog())
def biosFromDOSExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    cmd = common.doOnce(statusObj, setupFreedosForThisDir, statusObj.tmpdir, statusObj.tmpfile)

    try:
        common.loggedCmd(
            cmd + [ "%s -writehdrfile" % os.path.basename(statusObj.tmpfile) ],
            timeout=75,
            cwd=statusObj.tmpdir, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "HOME": os.environ["HOME"]})

    except common.CommandException, e:
        raise common.skip, "couldnt extract with extract_hdr_helper.sh"
    except OSError, e:
        raise common.skip, "extract_hdr_helper.sh not installed."

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir, os.path.join(statusObj.tmpdir,"dos","freedos")):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
    return True

decorate(traceLog())
def biosFromDcopyExe(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    dcopydir = os.path.join(statusObj.tmpdir, "dos", "freedos", "dcopy")
    os.mkdir(dcopydir)
    os.mkdir(dcopydir + "2")
    common.doOnce(statusObj, common.zipExtract, statusObj.tmpfile, dcopydir, logger)
    if not os.path.exists(os.path.join(dcopydir, "MAKEDISK.BAT")):
        raise common.skip, "not a dcopy image."

    cmd = common.doOnce(statusObj, setupFreedosForThisDir, statusObj.tmpdir, statusObj.tmpfile)

    try:
        for exe in glob.glob(os.path.join(dcopydir, "*.[Ee][Xx][Ee]")):
            common.loggedCmd(
                cmd + [ "dcopy\\%s /s a:" % os.path.basename(exe) ],
                timeout=75,
                cwd=statusObj.tmpdir, logger=logger,
                env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "HOME": os.environ["HOME"]})

        common.loggedCmd(
            cmd + [ "copy a:\\*.* c:\\dcopy2" ],
            timeout=75,
            cwd=statusObj.tmpdir, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "HOME": os.environ["HOME"]})

        for exe in glob.glob(os.path.join(dcopydir + "2", "*.[Ee][Xx][Ee]")):
            if "ync.exe" in exe.lower():
                continue
            common.loggedCmd(
                cmd + [ "dcopy2\\%s -writehdrfile" % os.path.basename(exe) ],
                timeout=10,
                cwd=statusObj.tmpdir, logger=logger,
                env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "HOME": os.environ["HOME"]})

    except common.CommandException, e:
        raise common.skip, "couldnt extract with extract_hdr_helper.sh"
    except OSError, e:
        raise

    for hdr, id, ver in getHdrIdVer(
            statusObj.tmpdir,
            os.path.join(statusObj.tmpdir,"dos","freedos"),
            os.path.join(statusObj.tmpdir,"dos","freedos", "dcopy"),
            os.path.join(statusObj.tmpdir,"dos","freedos", "dcopy2"),
            ):
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

    common.linkLog(dest, logger)

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



