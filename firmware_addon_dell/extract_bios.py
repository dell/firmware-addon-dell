
import os
import shutil
import tempfile

from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.plugins as plugins

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
def copyToTmp(statusObj):
    if getattr(statusObj, "tmpdir", None) is not None:
        return

    def rmTmp(statusObj, status):
        statusObj.logger.debug("\tremoving tmpdir")
        shutil.rmtree(statusObj.tmpdir)
    
    statusObj.logger.debug("\tcreating temp dir")
    statusObj.tmpdir = tempfile.mkdtemp(prefix="firmware-tools-extract-")
    statusObj.logger.debug("\t\t--> %s" % statusObj.tmpdir)
    statusObj.logger.debug("\tcopying to tempdir")
    shutil.copy(statusObj.file, statusObj.tmpdir)
    statusObj.tmpfile = os.path.join(statusObj.tmpdir, os.path.basename(statusObj.file))
    statusObj.finalFuncs.append(rmTmp)

decorate(traceLog())
def testExtract(statusObj, outputTopdir, logger, *args, **kargs):
    copyToTmp(statusObj)

