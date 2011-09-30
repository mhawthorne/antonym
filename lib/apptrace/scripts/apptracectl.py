# -*- coding: utf-8 -*-
#
# Copyright 2010 Tobias Rodäbel
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Control script for apptrace."""

import optparse
import os
import re
import shutil
import sys


USAGE = "usage: %prog [options] <command> <application root>"

DESCRIPTION = ("Control script to perform common tasks on configuring "
               "apptrace and retrieve data.")

COMMANDS = [('init', "install apptrace package into the application root")]


def copytree(src, dst, symlinks=False, exclude=[], ignore=False):
    """Local implementation of shutil's copytree function.

    Args:
        src: Source directory.
        dst: Destination directory.
        symlinks: Create symlinks instead of copying files.
        exclude: List of files patterns to be excluded.
        ignore: Ignore if a file already exists.

    Checks wheather destination directory exists or not
    before creating it.
    """
    if not os.path.isdir(src):
        src = os.path.dirname(src)
        dst = os.path.dirname(dst)
    names = os.listdir(src)
    if not os.path.exists(dst):
        os.mkdir(dst)
    for name in names:
        base, ext = os.path.splitext(name)
        if ext == ".egg-info":
            continue
        srcname = os.path.join(os.path.abspath(src), name)
        dstname = os.path.join(dst, name)
        exclude_src = False
        for regex in [re.compile(p) for p in exclude]:
            if re.match(regex, os.path.basename(srcname)):
                exclude_src = True
                break
        if exclude_src:
            continue
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, exclude, ignore)
            elif not os.path.isfile(dstname) and symlinks:
                os.symlink(srcname, dstname)
            elif not symlinks:
                shutil.copy2(srcname, dstname)
        except (IOError, os.error), why:
            if ignore: return
            raise RuntimeError("can't copy %s to %s: %s" % 
                               (srcname, dstname, str(why)))


def initApptracePackage(app_root, dependencies):
    """Initialize the apptrace package and copy all dependencies.

    Args:
        app_root: The application root directory.
        dependencies: List of required modules.
    """
    copytree(os.path.dirname(__file__)[:-16],
             app_root,
             symlinks=True,
             exclude=['scripts', 'tests'],
             ignore=True)
    for dep in dependencies:
        src = os.path.dirname(dep.__file__)
        copytree(src,
                 os.path.join(app_root, 'apptrace', os.path.basename(src)),
                 symlinks=True,
                 ignore=True)

def main():
    """The main function."""

    def format_commands(cmds):
        text = "\n\nCommands:"
        for cmd, descr in cmds:
            text += "\n  %s\t\t%s" % (cmd, descr)
        return text

    op = optparse.OptionParser(usage=USAGE+format_commands(COMMANDS))

    op.add_option("-s", "--server", dest="server", metavar="SERVER",
                  help="the server to connect to (default: %default)",
                  default='localhost:8080')

    (options, args) = op.parse_args()

    if len(args) != 2:
        op.print_usage()
        return 1

    command, app_root = args

    if command not in [cmd for cmd, descr in COMMANDS]:
        op.error("unknown command")

    if command == 'init':
        try:
            import guppy
        except ImportError, e:
            op.error(e)

        initApptracePackage(app_root, [guppy])

    return 0


if __name__ == "__main__":
    sys.exit(main())
