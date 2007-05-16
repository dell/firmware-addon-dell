"""
Yum plugin to set up repo for hardware-specific repositories.
"""

import os
import sys

from biosHdr import getSystemId

from yum.plugins import TYPE_CORE
from yum.yumRepo import YumRepository

requires_api_version = '2.5'
plugin_type = TYPE_CORE

def init_hook(conduit):
    """ 
    Plugin initialization hook. Sets up system id variables.

    Note: this should be compatible with any other vendor plugin that sets
    these variables because we only ever set them on Dell systems.
    """

    conf = conduit.getConf()

    sysid = getSystemId()

    if sysid:
        conf.yumvar["sys_ven_id"] = "1028"  # hex
        conf.yumvar["sys_dev_id"] = "%x" % sysid

        repos = conduit.getRepos()
        for repo in repos.findRepos('*'):
            repo.yumvar.update(conf.yumvar)
