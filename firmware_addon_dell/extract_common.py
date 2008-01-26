
from __future__ import generators

import os
import select
import shutil
import subprocess
import sys
import tempfile
import time
import xml.dom.minidom

import firmware_extract as fte
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.pycompat as pycompat
import firmware_addon_dell.HelperXml as HelperXml

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
def doOnce(statusObj, func, *args, **kargs):
    if getattr(statusObj, "doOnceFuncs", None) is None:
        statusObj.doOnceFuncs = {}

    key = (func.__name__, args, tuple(kargs))
    if statusObj.doOnceFuncs.has_key(key):
        ret = statusObj.doOnceFuncs[  key ]
    else:
        ret = func(*args, **kargs)
        statusObj.doOnceFuncs[  key ] = ret
    return ret

# not traced...
def chomp(line):
    if line.endswith("\n"):
        return line[:-1]
    else:
        return line

decorate(traceLog())
def logOutput(fds, logger, returnOutput=1, start=0, timeout=0):
    output=""
    done = 0
    while not done:
        if (time.time() - start)>timeout and timeout!=0:
            done = 1
            break

        i_rdy,o_rdy,e_rdy = select.select(fds,[],[],1)
        for s in i_rdy:
            # this isnt perfect as a whole line of input may not be
            # ready, but should be "good enough" for now
            line = s.readline()
            if line == "":
                done = 1
                break
            if logger is not None:
                logger.debug(chomp(line))
            if returnOutput:
                output += line
    return output

class commandTimeoutExpired(Exception): pass

decorate(traceLog())
def loggedCmd(cmd, logger=None, returnOutput=False, raiseExc=True, shell=False, cwd=None, env=None, timeout=0, preexec=None):
    output=None
    child = None
    try:
        logger.debug("Running command: %s" % ' '.join(cmd))
        start = time.time()
        child = subprocess.Popen(
            cmd, shell=shell, cwd=cwd, env=env,
            bufsize=0, close_fds=True,
            stdin=open("/dev/null", "r"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=preexec
        )
        output = logOutput([child.stdout, child.stderr],
                           logger, returnOutput, start, timeout)
    except:
        # kill children if they arent done
        if child is not None and child.returncode is None:
            os.kill(-child.pid, 15)
            os.kill(-child.pid, 9)
        raise

    # wait until child is done, kill it if it passes timeout
    while child.poll() is None:
        if (time.time() - start)>timeout and timeout!=0:
            os.kill(-child.pid, 15)
            os.kill(-child.pid, 9)
            raise commandTimeoutExpired, ("Timeout(%s) expired for command:\n # %s\n%s" % (cmd, output))


    if raiseExc and child.returncode:
        if returnOutput:
            raise subprocess.CalledProcessError, (child.returncode, cmd)
        else:
            raise subprocess.CalledProcessError, (child.returncode, cmd)

    return output

class UnsupportedFileExt(fte.DebugExc): pass
class CommandFailed(fte.DebugExc): pass

decorate(traceLog())
def assertFileExt(file, *args):
    good = 0
    for ext in args:
        if file.lower().endswith(ext.lower()):
            good=1
            break
    if not good:
        raise UnsupportedFileExt, "File %s does not have a supported extension: %s" % (file, repr(args))

decorate(traceLog())
def dupExtract(sourceFile, cwd, logger=None):
    try:
        loggedCmd(
            ['perl', '-p', '-i', '-e', 's/.*\$_ROOT_UID.*/true ||/; s/grep -an/grep -m1 -an/; s/tail \+/tail -n \+/', sourceFile],
            cwd=cwd, logger=logger,
            env={"LANG":"C"}
            )

        loggedCmd(
            ['sh', sourceFile, "--extract", cwd],
            cwd=cwd, logger=logger,
            env={"DISPLAY":"", "TERM":"", "PATH":os.environ["PATH"]}
            )
    except (OSError, subprocess.CalledProcessError), e:
        raise CommandFailed, str(e)

decorate(traceLog())
def zipExtract(sourceFile, cwd, logger=None):
    try:
        loggedCmd(
            ["unzip", "-o", sourceFile],
            cwd=cwd, logger=logger,
            )
    except (OSError, subprocess.CalledProcessError), e:
        raise CommandFailed, str(e)

decorate(traceLog())
def cabExtract(sourceFile, cwd, logger=None):
    try:
        loggedCmd(
         ["unshield", "x", sourceFile],
         cwd=cwd, logger=logger,
         )
    except (OSError, subprocess.CalledProcessError), e:
        raise CommandFailed, str(e)

decorate(traceLog())
def safemkdir(dest):
    try:
        os.makedirs( dest )
    except OSError: #already exists
        pass

decorate(traceLog())
def safeunlink(dest):
    try:
        os.unlink( dest )
    except OSError: #already exists
        pass

decorate(traceLog())
def setIni(ini, section, **kargs):
    if not ini.has_section(section):
        ini.add_section(section)

    for (key, item) in kargs.items():
        ini.set(section, key, item)

decorate(traceLog())
def getShortname(systemConfIni, vendid, sysid):
    if not systemConfIni:
        return ""

    if not systemConfIni.has_section("id_to_name"):
        return ""

    if systemConfIni.has_option("id_to_name", "shortname_ven_%s_dev_%s" % (vendid, sysid)):
        try:
            return eval(systemConfIni.get("id_to_name", "shortname_ven_%s_dev_%s" % (vendid, sysid)))
        except Exception, e:
            moduleLog.debug("Ignoring error in config file: %s" % e)

    return ""

decorate(traceLog())
def getBiosDependencies(packageXml):
    ''' returns list of supported systems from package xml '''
    if os.path.exists( packageXml ):
        dom = xml.dom.minidom.parse(packageXml)
        for modelElem in HelperXml.iterNodeElement(dom, "SoftwareComponent", "SupportedSystems", "Brand", "Model"):
            systemId = int(HelperXml.getNodeAttribute(modelElem, "systemID"),16)
            for dep in HelperXml.iterNodeAttribute(modelElem, "version", "Dependency"):
                dep = dep.lower()
                yield (systemId, dep)



