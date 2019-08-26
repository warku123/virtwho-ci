import re
import os
import sys
import json
import uuid
import time
import shutil
import random
import string
import logging
import socket
import select
import threading
import paramiko

try:
   import queue
except ImportError:
   import Queue as queue

from six import StringIO
from six import BytesIO

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from virt_who.settings import DeploySettings
from virt_who.settings import ConfigSettings
# configuration for provisioning environment
deploy = DeploySettings()
deploy.configure("provision.ini")
# configuration for debugging testcases
config = ConfigSettings()
config.configure("config.ini")

# result data for polarion importer
runtest_info = os.path.join(os.path.realpath(os.path.join(
    os.path.dirname(__file__),
    os.pardir)),
    "runtest.txt"
    )

# debug log file
DEBUG_FILE = os.path.join(os.path.realpath(os.path.join(
    os.path.dirname(__file__),
    os.pardir)),
    "debug.log"
    )

# console output
LOGGER_FILE = os.path.join(os.path.realpath(os.path.join(
    os.path.dirname(__file__),
    os.pardir)),
    "console.log"
    )

# create a logger
logger = logging.getLogger("vw")
logger.setLevel(logging.DEBUG)

# create file handler
fh = logging.FileHandler("%s" % LOGGER_FILE)
fh.setLevel(logging.DEBUG)

# create console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# logging format
formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
        )
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# turn off paramiko log off
paramiko_logger = logging.getLogger("paramiko.transport")
paramiko_logger.disabled = True

class FailException(BaseException):
    def __init__(self, error_message):
        logger.error(error_message)
