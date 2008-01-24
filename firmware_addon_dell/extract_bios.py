

from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import extract_common as common

__VERSION__ = "1.0"
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"

moduleLog = getLog()

decorate(traceLog())
def config_hook(conduit, *args, **kargs):
    # try/except in case extract plugin not installed
    try:
        import extract_cmd
        extract_cmd.registerPlugin('dell_bios', testExtract, __VERSION__)
    except ImportError, e:
        moduleLog.info("failed to register extract module.")

decorate(traceLog())
def testExtract(statusObj, outputTopdir, logger, *args, **kargs):
    common.assertFileExt( statusObj.file, '.bin', '.exe')
    common.copyToTmp(statusObj)
    try:
        common.doOnce( statusObj, common.dupExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    except:
        pass
    try:
        common.doOnce( statusObj, common.zipExtract, statusObj.tmpfile, statusObj.tmpdir, logger )
    except:
        pass
    try:
        common.doOnce( statusObj, common.cabExtract, "data1.cab", statusObj.tmpdir, logger )
    except:
        pass


def copyHdr(hdrFile, outputDir, logger):
    ret = 0
    if not os.path.exists(hdrFile):
       return ret

    ver = biosHdr.getBiosHdrVersion(hdrFile)
    logger.info("hdr version: %s\n" % ver)
    logger.info("hdr system ids: %s\n" % biosHdr.getHdrSystemIds(hdrFile))
    # ids here are nums
    for id in biosHdr.getHdrSystemIds(hdrFile):
        if id in dell_system_id_blacklist:
            logger.info("Skipping because it is in blacklist: %s\n" % id)
            continue
        systemName = ("system_bios_ven_0x1028_dev_0x%04x" % id).lower()
        biosName = ("%s_version_%s" % (systemName, ver)).lower()
        dest = os.path.join(outputDir, biosName)
        common.safemkdir(dest)

        pycompat.copyFile( hdrFile, "%s/bios.hdr" % (dest))
        pycompat.copyFile( os.path.join(os.path.dirname(hdrFile), "package.xml"), "%s/package.xml" % (dest), ignoreException=1)

        deps = {}
        # these are (int, str) tuple
        for sysId, reqver in dell_repo_tools.extract_common.getBiosDependencies( os.path.join(dest,"package.xml")):
            deps[sysId] = reqver

        #setup deps
        minVer = deps.get(id)
        requires = ""
        if minVer:
            requires = "system_bios(ven_0x1028_dev_0x%04x) >= %s" % (id, minVer)

        packageIni = ConfigParser.ConfigParser()
        packageIni.read( os.path.join(dest, "package.ini"))
        if not packageIni.has_section("package"):
            packageIni.add_section("package")

        dell_repo_tools.extract_common.setIni( packageIni, "package",
            spec      = "bios",
            module    = "firmware_addon_dell.dellbios",
            type      = "BiosPackage",
            name      = "system_bios(ven_0x1028_dev_0x%04x)" % id,
            safe_name = systemName,
            vendor_id = "0x1028",
            device_id = "0x%04x" % id,
            requires  = requires,

            version        = ver,
            rpm_version    = ver,
            dell_version   = ver,
            vendor_version = ver,

            force_pkg_regen = 1,
            extract_ver = version,
            shortname = dell_repo_tools.extract_common.getShortname("0x1028", "0x%04x" % id))

        fd = None
        try:
            try:
                os.unlink(os.path.join(dest, "package.ini"))
            except: pass
            fd = open( os.path.join(dest, "package.ini"), "w+")
            packageIni.write( fd )
        finally:
            if fd is not None:
                fd.close()

    ret = 1
    return ret

