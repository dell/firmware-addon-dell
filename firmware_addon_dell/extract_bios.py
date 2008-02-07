
import atexit
import ConfigParser
import glob
import gzip
import os
import shutil
import stat
import tempfile

# workaround bug: NameError: global name 'WindowsError' is not defined
class WindowsError(Exception): pass
shutil.WindowsError=WindowsError

import firmwaretools
import firmwaretools.plugins as plugins
from firmwaretools.trace_decorator import decorate, traceLog, getLog
try:
    import firmware_extract as fte
    import firmware_extract.buildrpm as br
    import extract_cmd
except ImportError:
    # disable this plugin if firmware_extract not installed
    raise plugins.DisablePlugin

import firmware_addon_dell as fad
import extract_common as common
import biosHdr
from extract_bios_blacklist import dell_system_id_blacklist

# required by the Firmware-Tools plugin API
__VERSION__ = firmwaretools.__VERSION__
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"
# end: api reqs

moduleLog = getLog()
conf = None
wineprefix = None
dosprefix = None

class noHdrs(fte.DebugExc): pass

# this is called from doCheck in buildrpm_cmd and should register any spec files
# and hooks this module supports
decorate(traceLog())
def buildrpm_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf_buildrpm(conduit.getConf(), conduit.getBase().opts)
    br.specMapping["BiosPackage"] = {"spec": conf.biospackagespec, "ini_hook": buildrpm_ini_hook}

# this is called by the buildrpm_doCheck_hook and should ensure that all config
# options have reasonable default values and that config file values are
# properly overridden by cmdline options, where applicable.
decorate(traceLog())
def checkConf_buildrpm(conf, opts):
    if getattr(conf, "biospackagespec", None) is None:
        conf.biospackagespec = None
    return conf

# this hook is called during the RPM build process. It should munge the ini
# as appropriate. The INI is used as source for substitutions in the spec
# file.
decorate(traceLog())
def buildrpm_ini_hook(ini):
    ver = ini.get("package", "version")

    if ver == "unknown":
        ini.set("package", "epoch", "0")

    # set epoch based on version
    # old version scheme:
    #   <any letter>99  --> 10
    #   P99  --> 20
    #   T99  --> 30
    #   X99  --> 40
    #   A99  --> 50
    if len(ver) == 3 and ver[0].isalpha() and ver[1].isdigit() and ver[2].isdigit():
        if ver[0].lower() == "p":
            ini.set("package", "epoch", "20")
        elif ver[0].lower() == "t":
            ini.set("package", "epoch", "30")
        elif ver[0].lower() == "x":
            ini.set("package", "epoch", "40")
        elif ver[0].lower() == "a":
            ini.set("package", "epoch", "50")
        else:
            ini.set("package", "epoch", "10")
        return

    # new version scheme:
    #   49.y.z -> 10
    #   90.y.z -> 20
    #   x.y.z  -> 55  # this is the new spec, so these should supercede old-style if present
    det = ver.split(".")
    if len(det) == 3:
        if det[0] == "49":
            ini.set("package", "epoch", "10")
        elif int(det[0],10) >= "90":
            ini.set("package", "epoch", "20")
        else:
            ini.set("package", "epoch", "55")
        return

    # some other really odd format. Set epoch to '0' so any of the above will
    # override it gracefully
    ini.set("package", "epoch", "0")


# this hook is called by doCheck in extract_cmd.
# it should register any extract plugins that is supports
decorate(traceLog())
def extract_doCheck_hook(conduit, *args, **kargs):
    global conf
    conf = checkConf_extract(conduit.getConf(), conduit.getBase().opts)

    extract_cmd.registerPlugin(alreadyHdr, __VERSION__)
    extract_cmd.registerPlugin(biosFromLinuxDup, __VERSION__)
    if os.path.exists("/usr/lib/libfakeroot/libfakeroot.so"):
        extract_cmd.registerPlugin(biosFromLinuxDup2, __VERSION__)
        extract_cmd.registerPlugin(biosFromLinuxDup3, __VERSION__)
    else:
        moduleLog.info("Disabled biosFromLinuxDup2 plugin due to missing fakeroot.i386 package.")
        moduleLog.info("Disabled biosFromLinuxDup3 plugin due to missing fakeroot.i386 package.")
    extract_cmd.registerPlugin(biosFromWindowsDup, __VERSION__)
    # if wine/unshield/helper_dat not installed, dont register the
    # respective plugins so that if we run again later with them installed,
    # it will properly go and try them.
    if os.path.exists("/usr/bin/wine"):
        setupWine()
        extract_cmd.registerPlugin(biosFromWindowsExe, __VERSION__)
    else:
        moduleLog.info("Disabled biosFromWindowsExe plugin due to missing wine package.")
    if os.path.exists("/usr/bin/unshield"):
        extract_cmd.registerPlugin(biosFromInstallShield, __VERSION__)
    else:
        moduleLog.info("Disabled biosFromWindowsExe plugin due to missing unshield package.")
    if os.path.exists(conf.helper_dat):
        setupFreedos()
        extract_cmd.registerPlugin(biosFromDOSExe, __VERSION__)
        extract_cmd.registerPlugin(biosFromDcopyExe, __VERSION__)
    else:
        moduleLog.info("Disabled biosFromDOSExe plugin due to missing dell-repo-tools package.")
        moduleLog.info("Disabled biosFromDcopyExe plugin due to missing dell-repo-tools package.")

shortName = None

decorate(traceLog())
def extract_addSubOptions_hook(conduit, *args, **kargs):
    global shortName
    shortName =common.ShortName(conduit.getOptParser())
    conduit.getOptParser().add_option(
        "--helper-dat", help="Path to extract_hdr_helper.dat.",
        action="store", dest="helper_dat", default=None)

true_vals = ("1", "true", "yes", "on")
decorate(traceLog())
def checkConf_extract(conf, opts):
    shortName.check(conf, opts)

    if opts.helper_dat is not None:
        conf.helper_dat = os.path.realpath(opts.helper_dat)
    if getattr(conf, "helper_dat", None) is None:
        conf.helper_dat = ""

    return conf

# optimize wine a bit. Since we want to have completely separate wine instances
# we will set up a master copy (slow) that we can just filecopy (quick) into
# each individual extract dir. If you dont have separate wine instances, you get
# massive hangs because some exe's will kill wine, and cause all further calls
# to wine to hang.
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

# optimize freedos setup. Untar and set up master copy of the freedos/dosemu
# tree that we can do a quick filecopy of for each instance.
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

# simplest extract case: they did the unthinkable and posted a raw .HDR
# file. awesome! unfortunately no way to get relnotes at all... :(
decorate(traceLog())
def alreadyHdr(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.hdr')
    for hdr, id, ver in getHdrIdVer(statusObj.file):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )
    return True

# DUPS for precision are posted inside a small shell gzip self-extractor.
# they self-extract into a single binary.
# some of them are broken and will reboot machine if they dont recognize
# --WriteHDRFile, so we will manually gzip -d them and call the binary
decorate(traceLog())
def biosFromLinuxDup2(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)

    flashbin = os.path.join(statusObj.tmpdir, "flashbin")
    common.gzipAfterHeader(statusObj.tmpfile, flashbin, "__ARC__")
    oldmode = stat.S_IMODE(os.stat(flashbin)[stat.ST_MODE])
    os.chmod(flashbin, oldmode | stat.S_IRWXU)

    try:
        common.loggedCmd(
            [flashbin, "--WriteHDRFile"],
            cwd=statusObj.tmpdir, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "LD_PRELOAD": "/usr/lib/libfakeroot/libfakeroot.so"}
            )
    except (OSError, common.CommandException), e:
        raise common.skip, str(e)

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )

    return True

# Some DUPS for precision were posted without a shell self-extracting wrapper
# otherwise same as above. Ensure it is an ELF before we run it.
decorate(traceLog())
def biosFromLinuxDup3(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)

    fd = open(statusObj.tmpfile, "r")
    buf = fd.read(4)
    fd.close()
    if buf != '\177ELF':
        raise common.skip, "not an ELF file." 

    oldmode = stat.S_IMODE(os.stat(statusObj.tmpfile)[stat.ST_MODE])
    os.chmod(statusObj.tmpfile, oldmode | stat.S_IRWXU)

    try:
        common.loggedCmd(
            [statusObj.tmpfile, "--WriteHDRFile"],
            cwd=statusObj.tmpdir, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"], "LD_PRELOAD": "/usr/lib/libfakeroot/libfakeroot.so"}
            )
    except (OSError, common.CommandException), e:
        raise common.skip, str(e)

    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )

    return True

# most "Server" Linux DUPS are gzipped tarballs with a shell self-extractor
# we call --extract method on them and check for .HDR files.
decorate(traceLog())
def biosFromLinuxDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    return genericBiosDup(statusObj, outputTopdir, logger, *args, **kargs)

# most Server Windows DUPS are self-extracting zip files. We just manually unzip.
# the python zipfile lib chokes on them, so we have to shell out to 'unzip'
decorate(traceLog())
def biosFromWindowsDup(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    return genericBiosDup(statusObj, outputTopdir, logger, *args, **kargs)

# after extraction, contents of windows/linux dups are generally the same 
# at the content level.
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
        if os.path.exists(packageXml):
            shutil.copy( packageXml, dest)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )
        for txt in glob.glob( os.path.join(statusObj.tmpdir, os.path.basename(hdr))[:-len(".hdr")] + ".[Tt][Xx][Tt]"):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )

        #setup deps
        minVer = deps.get(id)
        requires = ""
        if minVer:
            requires = "system_bios(ven_0x1028_dev_0x%04x) >= %s" % (id, minVer)

        common.setIni(packageIni, "package", requires=requires)
        writePackageIni(dest, packageIni)

    return True

# installshield format is just a self-extracting zip with an installshield
# cab file for a payload. unzip first, then unshield and look for header in
# proper subdir.
decorate(traceLog())
def biosFromInstallShield(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.exe')
    common.copyToTmp(statusObj)
    common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    common.doOnce( statusObj, common.cabExtract, "data1.cab", statusObj.tmpdir, logger )
    for hdr, id, ver in getHdrIdVer(statusObj.tmpdir, os.path.join(statusObj.tmpdir,"BiosHeader")):
        dest, packageIni = copyHdr(hdr, id, ver, outputTopdir, logger)
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )

    return True

# this is one of the more popular formats. Cannot manually get the content out
# so we use wine to call it with -writehdrfile -nopause. The second argument is
# to keep it from trying to pop up a dialog box.
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
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )

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

# somewhat older format. Dos executable that you can use -writehdrfile to
# extract.
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
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )
    return True

# horribly convoluted dcopy format. Ugh.
# unzip to run an exe that writes to a floppy, then take the executable
# off of the floppy and run it with -writehdrfile. What in the heck were
# they thinking?
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
        for txt in glob.glob( "%s.[Tt][Xx][Tt]" % statusObj.file[:-len(".txt")] ):
            shutil.copyfile( txt, os.path.join(dest, "relnotes.txt") )
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
    shutil.copyfile(conf.license, os.path.join(dest, os.path.basename(conf.license)))

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

        shortname = shortName.getShortname("0x1028", "0x%04x" % id),
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



