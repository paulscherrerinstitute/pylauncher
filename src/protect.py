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
import sys

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

def processFile(filePath, password, recursive):
    data = loadJson(filePath)
    dirname = os.path.dirname(filePath)
    protected = addPassword(data, hashPassword(password))
    saveFile(protected, filePath)
    if recursive:
        files = findAllFiles(data)
        for file in files:
            processFile(os.path.join(dirname, file), password, recursive)

def findAllFiles(root):
    fileList = []
    for key in root:
        if key == 'file':
            fileList.append(root[key])
        elif isinstance(root[key], list):
            for element in root[key]:
                if isinstance(element, dict):
                    fileList += findAllFiles(element)
        elif isinstance(root[key], dict):
            fileList += findAllFiles(root[key])
    return fileList

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

    import getpass

    # Parse input arguments
    argsParse = argparse.ArgumentParser(description='Example: pylauncher-protect -r menus/menu.json -p *****')
    argsParse.add_argument('configuration',
                          help="menu/configuration file")
    argsParse.add_argument('--password', '-p',
                          help="password to be added to json file, if not provided user is prompted to enter it")
    argsParse.add_argument('--recursive', '-r',
                          help="add recursively to all files referenced in json", action='store_true')
    args = argsParse.parse_args()

    # Add password to json structure
    if args.password is None:
        # Ask for password
        password = getpass.getpass("Enter password: ")
    else:
        password = args.password

    # Get current dir and create path to json file
    cwd = os.getcwd()
    jsonFilePath = os.path.join(cwd, args.configuration)

    # Add password to file and, if recursive, to all the files within
    processFile(jsonFilePath, password, args.recursive)


# Start program here
if __name__ == '__main__':
    main()
