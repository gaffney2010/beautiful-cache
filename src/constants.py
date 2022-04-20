"""Some constants that will be shared potentially across files."""

import os

# If downloading, you need to set this directory to equal the directory that
#  houses this file.
import computer_constants

DEBUG = False

LOGGING_DIR = os.path.join(computer_constants.TOP_LEVEL_DIR, "logging")

MYSQL_USER = computer_constants.MYSQL_USER
MYSQL_PASSWORD = computer_constants.MYSQL_PASSWORD
MYSQL_DB = "bc"
