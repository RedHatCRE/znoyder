#!/usr/bin/env python3
#
# Copyright 2021 Red Hat, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#
# Borrowed from InfraRed project
#

import logging
import sys
import traceback

import colorlog


logger_formatter = colorlog.ColoredFormatter(
    '%(log_color)s%(levelname)-8s%(message)s',
    log_colors=dict(
        DEBUG='blue',
        INFO='green',
        WARNING='yellow',
        ERROR='red',
        CRITICAL='bold_red,bg_white',
    )
)

file_logger_formater = logging.Formatter(fmt="%(levelname)-8s%(message)s")

LOGGER_NAME = 'znoyderLogger'
DEFAULT_LOG_LEVEL = logging.INFO

LOG = logging.getLogger(LOGGER_NAME)
LOG.setLevel(DEFAULT_LOG_LEVEL)

# Create stream handler with debug level
sh = logging.StreamHandler(sys.stderr)
sh.setLevel(logging.DEBUG)

# Add the logger_formatter to sh
sh.setFormatter(logger_formatter)

# Create logger and add handler to it
LOG.addHandler(sh)
LOG.propagate = False


def set_logger_destination(args) -> None:
    """Ensure that the logger respects the user choice to write to
    file/stderr/both"""
    if args.log_mode == "file":
        # remove log handler that writes to stderr
        LOG.handlers.pop()
    if args.log_file and args.log_mode != "terminal":
        file_handler = logging.FileHandler(args.log_file, mode="w")
        file_handler.setLevel(DEFAULT_LOG_LEVEL)
        file_handler.setFormatter(file_logger_formater)
        LOG.addHandler(file_handler)


def znoyder_excepthook(exc_type, exc_value, exc_traceback):
    '''exception hook that sends ZnoyderCliException to log and other
    exceptions to stderr (default excepthook)
    '''
    from znoyder.lib.exceptions import ZnoyderCliException

    # sends full exception with trace to log
    if not isinstance(exc_value, ZnoyderCliException):
        return sys.__excepthook__(exc_type, exc_value, exc_traceback)

    if LOG.getEffectiveLevel() <= logging.DEBUG:
        formated_exception = ''.join(
            traceback.format_exception(exc_type, exc_value, exc_traceback))
        LOG.error(formated_exception + exc_value.message)
    else:
        LOG.error(exc_value.message)


sys.excepthook = znoyder_excepthook
