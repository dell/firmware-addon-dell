
import os
import shutil
import tempfile

from firmwaretools.trace_decorator import decorate, traceLog, getLog

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
def dupExtract(statusObj):
    if getattr(statusObj, "dupExtract", None) is not None:
        return

    pycompat.executeCommand("""LANG=C perl -p -i -e 's/.*\$_ROOT_UID.*/true ||/; s/grep -an/grep -m1 -an/; s/tail \+/tail -n \+/' %s""" % sourceFile)
    pycompat.executeCommand("""LANG=C perl -p -i -e 's/.*\$_ROOT_UID.*/true ||/; s/grep -an/grep -m1 -an/; s/tail \+/tail -n \+/' %s""" % sourceFile)

decorate(traceLog())
def zipExtract(statusObj):
    if getattr(statusObj, "dupExtract", None) is not None:
        return

    pycompat.executeCommand("unzip -o %s > /dev/null 2>&1" % (sourceFile))

decorate(traceLog())
def cabExtract(statusObj):
    if getattr(statusObj, "dupExtract", None) is not None:
        return

    pycompat.executeCommand("unshield x data1.cab > /dev/null 2>&1")
