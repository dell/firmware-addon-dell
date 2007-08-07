# vim:tw=0:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
Yum plugin to set up repo for hardware-specific repositories.
"""

import os
import sys

from firmware_addon_dell.biosHdr import getSystemId, getServiceTag

from yum.plugins import TYPE_CORE

version="1.4.1"

requires_api_version = '2.1'
plugin_type = TYPE_CORE
runInitHook = 1

def postconfig_hook(conduit):
    conf = conduit.getConf()
    try:
        conf.yumvar["dellsysidpluginver"] = version
        conf.yumvar["sys_dev_id"] = "0x%04x" % getSystemId()
        conf.yumvar["sys_ven_id"] = "0x1028"  # hex
        conf.yumvar["service_tag"] = getServiceTag()
        conf.yumvar["repo_config"] = conduit.confString("main", "repo_config", default="latest")
    except:
        pass

    global runInitHook
    runInitHook = 0
   

def init_hook(conduit):
    """ 
    Plugin initialization hook. Sets up system id variables.

    Note: this should be compatible with any other vendor plugin that sets
    these variables because we only ever set them on Dell systems.
    """

    global runInitHook
    if not runInitHook:
        return

    conf = conduit.getConf()

    sysid=0
    try:
        sysid = getSystemId()
    except:
        pass

    conf.yumvar["dellsysidpluginver"] = version

    if sysid:
        conf.yumvar["sys_ven_id"] = "0x1028"  # hex
        conf.yumvar["sys_dev_id"] = "0x%04x" % sysid
        conf.yumvar["service_tag"] = getServiceTag()
        conf.yumvar["repo_config"] = conduit.confString("main", "repo_config", default="latest")

    repos = conduit.getRepos()
    for repo in repos.findRepos('*'):
        repo.yumvar.update(conf.yumvar)

    # re-process mirrorlist (it isnt varReplaced like baseUrl is)
    for repo in repos.findRepos('*'):
        try:
            # yum 3.0+
            if repo.mirrorlist:
                for (key, value) in conf.yumvar.items():
                    repo.mirrorlist = repo.mirrorlist.replace("$%s" % key, value)
        except AttributeError:
            pass
    
        try:
            # yum 2.4.3
            if repo.mirrorlistfn:
                for (key, value) in conf.yumvar.items():
                    repo.mirrorlistfn = repo.mirrorlistfn.replace("$%s" % key, value)
        except AttributeError:
            pass


