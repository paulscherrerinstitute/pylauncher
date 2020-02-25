#!/usr/bin/env python
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import os
import re
import json
import logging
import hashlib
import argparse
import collections

from .launcher_model import *

def loadJson(filePath):
    try:
        with open(filePath) as json_file:
            data = json.load(json_file, object_pairs_hook=collections.OrderedDict)
            return data
    except json.decoder.JSONDecodeError as error:
        error_msg = "File \"" + filePath + "\" is empty. " \
        "Json cannot be loaded."
        logging.error(error_msg)
    except IOError as error:
        error_msg = "Json cannot be loaded from file \"" + filePath + "\". " \
                "Wrong path."
        logging.error(error_msg)

    sys.exit(-1)

def addPassword(root, password):

    # Append password to json at the beginning
    root["password"]=password
    root.move_to_end('password', last=False)
    return root

def hashPassword(password):
    m = hashlib.md5()
    m.update(password.encode())
    return m.hexdigest()

def saveFile(jsonWithPwd, filename):
    with open(filename, 'w') as outfile:
        json.dump(jsonWithPwd, outfile, indent=4)

def main():
    """ Main logic """

    # Parse input arguments
    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('configuration',
                          help="menu/configuration file")
    args = argsPars.parse_args()

    # Ask for password
    password = input("Enter password: ")

    # Load json from file into json object
    cfg_model = loadJson(args.configuration)

    # Add password to json structure
    jsonWithPwd = addPassword(cfg_model, hashPassword(password))

    # Save json back to the original file
    saveFile(jsonWithPwd, args.configuration)

# Start program here
if __name__ == '__main__':
    main()