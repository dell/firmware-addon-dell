
from __future__ import generators

import ConfigParser
import fcntl
import gzip
import os
import select
import shutil
import stat
import sys
import tempfile
import time
import xml.dom.minidom
try:
    import subprocess
except ImportError:
    import compat_subprocess as subprocess

import firmware_extract as fte
from firmwaretools.trace_decorator import decorate, traceLog, getLog
import firmwaretools.pycompat as pycompat
import firmware_addon_dell.HelperXml as HelperXml

class CommandException(Exception): pass
class CommandTimeoutExpired(CommandException): pass
class CommandFailed(CommandException): pass
class UnsupportedFileExt(fte.DebugExc): pass
class skip(fte.DebugExc): pass
class MarkerNotFound(fte.DebugExc): pass

moduleLog = getLog()

decorate(traceLog())
def copyToTmp(statusObj):
    if getattr(statusObj, "tmpdir", None) is not None:
        return

    def rmTmp(statusObj, status):
        statusObj.logger.debug("\tremoving tmpdir")
        for (dirpath, dirnames, filenames) in os.walk(statusObj.tmpdir):
            for f in filenames + dirnames:
                path = os.path.join(dirpath, f)
                if os.path.islink(path):
                    continue
                if not os.path.isdir(path) and not (os.path.isfile(path)):
                    continue
                oldmode = stat.S_IMODE(os.stat(path)[stat.ST_MODE])
                os.chmod(path, oldmode | stat.S_IRWXU)
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
def pad(s, n):
    return s[:n] + ' ' * (n-len(s))

decorate(traceLog())
def logOutput(fds, logger, returnOutput=1, start=0, timeout=0):
    output=""
    done = 0

    for fd in fds:
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        if not fd.closed:
            fcntl.fcntl(fd, fcntl.F_SETFL, flags| os.O_NONBLOCK)


    while not done:
        if (time.time() - start)>timeout and timeout!=0:
            done = 1
            break

        i_rdy,o_rdy,e_rdy = select.select(fds,[],[],1)
        for s in i_rdy:
            # slurp as much input as is ready
            input = s.read()
            if input == "":
                done = 1
                break
            if logger is not None:
                for line in input.split("\n"):
                    if line == '': continue
                    logger.debug(chomp(line))
                for h in logger.handlers:
                    h.flush()
            if returnOutput:
                output += input
    return output

decorate(traceLog())
def childSetPgrp(chain=None):
    def setpgrp():
        os.setpgrp()
        if chain is not None:
            chain()
    return setpgrp

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
            preexec_fn=childSetPgrp(preexec),
        )

        output = logOutput([child.stdout, child.stderr],
                           logger, returnOutput, start, timeout)
    except:
        # kill children if they arent done
        if child is not None and child.returncode is None:
            os.killpg(child.pid, 9)
        try:
            if child is not None:
                os.waitpid(child.pid, 0)
        except:
            pass
        raise

    # wait until child is done, kill it if it passes timeout
    niceExit=1
    while child.poll() is None:
        if (time.time() - start)>timeout and timeout!=0:
            niceExit=0
            os.killpg(child.pid, 15)
        if (time.time() - start)>(timeout+1) and timeout!=0:
            niceExit=0
            os.killpg(child.pid, 9)

    if not niceExit:
        raise CommandTimeoutExpired, ("Timeout(%s) expired for command:\n # %s\n%s" % (timeout, cmd, output))

    if raiseExc and child.returncode:
        if returnOutput:
            raise CommandFailed("The command failed (%s):\n\t# %s\n%s" % (child.returncode, cmd, output))
        else:
            raise CommandFailed("The command failed (%s):\n\t# %s" % (child.returncode, cmd))

    return output

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
def linkLog(dest, logger):
    # link the logfile, so we always have a log of the last extract for this bios
    while True:
        try:
            safeunlink(os.path.join(dest, "extract.log"))
            os.link(logger.handlers[0].baseFilename, os.path.join(dest, "extract.log"))
            break
        except OSError:
            pass

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
    except (OSError, CommandException), e:
        raise skip, str(e)

decorate(traceLog())
def gzipAfterHeader(inFN, outFN, marker):
    inFD = open(inFN, "rb")
    while True:
        line = inFD.readline()
        if line=="": # eof
            raise MarkerNotFound, "didnt find marker(%s) in file." % marker

        if chomp(line) == marker:
            z = gzip.GzipFile( fileobj = inFD )
            outFD = open(outFN, "w+")
            readsize=4096
            while 1:
                try:
                    byte = z.read(readsize)
                except IOError:
                    # hit this if there is trailing garbage in gzip file. nonfatal
                    if readsize == 1: raise
                    readsize = readsize / 2
                    continue

                if byte == "": break
                outFD.write(byte)
            outFD.close()
            break

    inFD.close()


decorate(traceLog())
def zipExtract(sourceFile, cwd, logger=None):
    try:
        loggedCmd(
            ["unzip", "-o", sourceFile],
            cwd=cwd, logger=logger,
            )
    except (OSError, CommandException), e:
        raise skip, str(e)

decorate(traceLog())
def cabExtract(sourceFile, cwd, logger=None):
    try:
        loggedCmd(
         ["unshield", "x", sourceFile],
         cwd=cwd, logger=logger,
         )
    except (OSError, CommandException), e:
        raise skip, str(e)

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


class ShortName(object):
    def __init__(self, parser, **kargs):
        self.systemConfIni = None
        parser.add_option(
            "--id2name-config", help="Add system id to name mapping config file.",
            action="append", dest="system_id2name_map", default=[])

    decorate(traceLog())
    def check(self, conf, opts):
        self.systemConfIni = ConfigParser.ConfigParser()

        if getattr(conf, "system_id2name_map", None) is not None:
            self.systemConfIni.read(conf.system_id2name_map)
        else:
            self.systemConfIni.read(
                os.path.join(firmwaretools.DATADIR, "firmware-tools", "system_id2name.ini"))

        self.systemConfIni.read(opts.system_id2name_map)

    decorate(traceLog())
    def getShortname(self, vendid, sysid):
        if not self.systemConfIni:
            return ""

        if not self.systemConfIni.has_section("id_to_name"):
            return ""

        if self.systemConfIni.has_option("id_to_name", "shortname_ven_%s_dev_%s" % (vendid, sysid)):
            try:
                return eval(self.systemConfIni.get("id_to_name", "shortname_ven_%s_dev_%s" % (vendid, sysid)))
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



