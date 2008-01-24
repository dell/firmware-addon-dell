

from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins
import extract_common as common

__VERSION__ = "1.0"
plugin_type = (plugins.TYPE_CORE,)
requires_api_version = "2.0"

moduleLog = getLog()
moduleLogVerbose = getLog(prefix="verbose.")

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
    assertFileExt( ['.bin',] )
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

