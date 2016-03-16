# Copyright 2014 ARM Limited
#
# Licensed under the Apache License, Version 2.0
# See LICENSE file for details.

# standard library modules, , ,
import argparse
import logging
import os
import subprocess
import shlex
import itertools

# Ordered JSON, , read & write json, internal
from yotta.lib import ordered_json
# Pack, , common parts of Components/Targets, internal
from yotta.lib import pack
# fsutils, , misc filesystem utils, internal
from yotta.lib import fsutils
# --config option, , , internal
from yotta import options
# Component, , represents an installed component, internal
from yotta.lib import component

logger = logging.getLogger('components')

def addOptions(parser):
    options.config.addTo(parser)
    parser.add_argument('script', default=None,
        help='name of the script to run'
    )

def _tryTerminate(process):
    try:
        process.terminate()
    except OSError as e:
        # if the error is "no such process" then the process probably exited
        # while we were waiting for it, so don't raise an exception
        if e.errno != errno.ESRCH:
            raise

def execCommand(args, following_args):
    wd = os.getcwd()
    c = component.Component(wd)
    # skip testing for target if we already found a component
    if not c:
        logging.debug(str(c.getError()))
        logging.error('The current directory does not contain a valid module.')
        return 1

    script = c.getScript(args.script)
    if script is None:
        logging.error('The script does not exist in the scripts field.')
        return 1

    logger.info("running script %s", script)
    
    cmd = shlex.split(script)

    script_child = None
    try:
        logger.debug('running test: %s', cmd)
        try:
            script_child = subprocess.Popen(
                cmd, stdout = subprocess.PIPE
            )
            for line in iter(script_child.stdout.readline,''):
                logger.info(line.rstrip())
            logger.debug('waiting for test child')
        except OSError as e:
            if e.errno == errno.ENOENT:
                logger.error('Error: no such file or directory: "%s"', cmd[0])
                return 1
            raise
        script_child.wait()
        returncode = script_child.returncode
        script_child = None
        if returncode:
            logger.debug("test process exited with status %s (=fail)", returncode)
            return 1
    finally:
        if script_child is not None:
            _tryTerminate(script_child)
    logger.info("script %s finished with status %s", cmd, returncode)
    return 0
