#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


import os
from pipes import quote
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .Shell import Shell
from .FileManagerUtils import FILE_TYPE_FILE, FILE_TYPE_DIR, FILE_TYPE_LINK
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_FSTRIM, FILE_OP_ERROR_NONE
from .DelayTimer import DelayTimer


SCRIPTDIR = "/usr/script/CacheCockpit"


def removeEmptyDirs(src_path, plugin):
    logger.info("src_path: %s", src_path)
    src_bookmark = MountCockpit.getInstance().getBookmark(plugin, src_path)
    cmds = []
    while src_path != src_bookmark and os.path.dirname(src_path) != src_bookmark:
        cmds.append("%s %s" % (os.path.join(
            SCRIPTDIR, "rm_empty_dir.sh"), quote(src_path)))
        src_path = os.path.dirname(src_path)
    logger.debug("cmds: %s", cmds)
    return cmds


class DiskOps(Shell):

    def __init__(self):
        Shell.__init__(self)

    def execDiskOpCallback(self, _file_op, _path, _target_dir, _error):  # pylint: disable=W0221
        logger.error("should be overridden in child class")

    def execDiskOp(self, file_op, file_type, path, target_dir):
        error = FILE_OP_ERROR_NONE
        # first execution script, second execution script, abort cleanup script
        cmds = [[], [], []]
        wait_for_completion = True
        logger.info("file_op: %s, path: %s, target_dir: %s",
                    file_op, path, target_dir)
        if file_op == FILE_OP_DELETE:
            cmds[0] = self.execFileDelete(file_type, path)
        elif file_op == FILE_OP_MOVE:
            if MountCockpit.getInstance().sameMountPoint("MVC", path, target_dir):
                cmds[0] = self.execFileMove(file_type, path, target_dir)
                wait_for_completion = False
            else:
                cmds[0] = self.execFileCopy(file_type, path, target_dir)
                cmds[1] = self.execFileDelete(file_type, path)
                cmds[2] = self.execFileDelete(file_type, os.path.join(
                    target_dir, os.path.basename(path)), force=True)
        elif file_op == FILE_OP_COPY:
            cmds[0] = self.execFileCopy(file_type, path, target_dir)
            cmds[2] = self.execFileDelete(file_type, os.path.join(
                target_dir, os.path.basename(path)), force=True)
        elif file_op == FILE_OP_FSTRIM:
            cmds[0] = self.execFSTrim()
        logger.info("wait_for_completion: %s, cmds: %s",
                    wait_for_completion, cmds)
        if not wait_for_completion:
            self.execDiskOpCallback(file_op, path, target_dir, error)
        DelayTimer(100, self.execShell, cmds, wait_for_completion,
                   file_op, path, target_dir, error)

    def execFileDelete(self, file_type, path, force=False):
        logger.info("path: %s, force: %s", path, force)
        cmds = []
        if force:
            cmds.append("rm -f %s.*" % quote(os.path.splitext(path)[0]))
        else:
            if file_type == FILE_TYPE_FILE:
                cmds.append("rm -f %s.*" % quote(os.path.splitext(path)[0]))
            elif file_type == FILE_TYPE_LINK:
                cmds.append("rm -f %s" % quote(path))
            elif file_type == FILE_TYPE_DIR:
                cmds.append("rm -f %s.*" % quote(path))
                cmds.append("rm -rf %s" % quote(path))
        cmds += removeEmptyDirs(os.path.dirname(path), self.plugin)
        logger.info("cmds: %s", cmds)
        return cmds

    def execFileMove(self, file_type, path, target_dir):
        logger.info("path: %s, target_dir: %s", path, target_dir)
        cmds = ["mkdir -p %s" % quote(target_dir)]
        if file_type == FILE_TYPE_FILE:
            if "trashcan" in target_dir:
                cmds.append("touch %s.*" % quote(os.path.splitext(path)[0]))
            cmds.append("mv %s.* %s" %
                        (quote(os.path.splitext(path)[0]), quote(target_dir)))
            cmds.append("touch %s" % quote(target_dir))
        elif file_type == FILE_TYPE_LINK:
            if "trashcan" in target_dir:
                cmds.append("touch %s" % quote(path))
            cmds.append("mv %s %s/." % (quote(path), quote(target_dir)))
        elif file_type == FILE_TYPE_DIR:
            if "trashcan" in target_dir:
                cmds.append("find %s -exec touch {} +" % quote(path))
            cmds.append("mv %s.* %s/." % (quote(path), quote(target_dir)))
            cmds.append("%s %s %s" % (os.path.join(SCRIPTDIR, "mv.sh"), quote(
                path), quote(os.path.join(target_dir, os.path.basename(path)))))
        cmds += removeEmptyDirs(path, self.plugin)
        logger.info("cmds: %s", cmds)
        return cmds

    def execFileCopy(self, file_type, path, target_dir):
        logger.info("path: %s, target_dir: %s", path, target_dir)
        cmds = ["mkdir -p %s" % quote(target_dir)]
        if file_type == FILE_TYPE_FILE:
            cmds.append("cp -dp %s.* %s" %
                        (quote(os.path.splitext(path)[0]), quote(target_dir)))
            cmds.append("touch %s" % quote(target_dir))
        elif file_type == FILE_TYPE_LINK:
            cmds.append("cp -dp  %s %s/." % (quote(path), quote(target_dir)))
        elif file_type == FILE_TYPE_DIR:
            cmds.append("cp -a %s %s" % (quote(path), quote(target_dir)))
            cmds.append("cp %s.* %s/." % (quote(path), quote(target_dir)))
        logger.info("cmds: %s", cmds)
        return cmds

    def execFSTrim(self):
        cmds = [os.path.join(SCRIPTDIR, "fstrim.sh")]
        return cmds
