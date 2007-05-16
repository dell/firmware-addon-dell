# vim:expandtab:autoindent:tabstop=4:shiftwidth=4:filetype=python:
"""
Yum plugin to set up repo for hardware-specific repositories.
"""

import os
import sys

from biosHdr import getSystemId

from yum.plugins import TYPE_CORE

requires_api_version = '2.1'
plugin_type = TYPE_CORE

def init_hook(conduit):
    """ 
    Plugin initialization hook. Sets up system id variables.

    Note: this should be compatible with any other vendor plugin that sets
    these variables because we only ever set them on Dell systems.
    """

    conf = conduit.getConf()

    sysid=0
    try:
        sysid = getSystemId()
    except:
        pass

    if sysid:
        conf.yumvar["sys_ven_id"] = "0x1028"  # hex
        conf.yumvar["sys_dev_id"] = "0x%04x" % sysid

        repos = conduit.getRepos()
        for repo in repos.findRepos('*'):
            repo.yumvar.update(conf.yumvar)

        # re-process mirrorlist (it isnt varReplaced like baseUrl is)
        for repo in repos.findRepos('*'):
            try:
                if repo.mirrorlist:
                    repo.mirrorlist = repo.mirrorlist.replace("$sys_ven_id", conf.yumvar["sys_ven_id"])
                    repo.mirrorlist = repo.mirrorlist.replace("$sys_dev_id", conf.yumvar["sys_dev_id"])
            except AttributeError:
                pass


