#!/usr/bin/env python

import sys
import os
import re
import enum
import codecs
import argparse

class LauncherMenuType(enum.Enum):
    unknown = 0,
    mainTitle = 1,
    fileChoice = 2,
    separator = 3,
    title = 4,
    command = 5,
    menu = 6,
    empty = 7,

class LauncherMenuModelItem(object):
    """ TODO: Docs
    """

    def __init__(self, command, params):

        self._command = command
        self._params = params

    def toJson(self):
        pass

    @staticmethod
    def getType(command):
        if command == '@main-title':
            return LauncherMenuType.mainTitle
        elif command == '@FileChoice':
            return LauncherMenuType.fileChoice
        elif command == '@separator':
            return LauncherMenuType.separator
        elif command == '@title':
            return LauncherMenuType.title
        elif command == '>launcher':
            return LauncherMenuType.menu
        elif command[0] == '#':
            return LauncherMenuType.empty
        else:
            return LauncherMenuType.command

class LauncherMenuModelItemFileChoice(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemFileChoice,self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
        self._file = command[1] + '.json'

    def toJson(self):
        return '''"file-choice": [
        {"text": "%s", "file": "%s"}
    ],\n''' % (self._text, self._file)

class LauncherMenuModelItemTitle(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemTitle,self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]

    def toJson(self):
        return '{"type": "title", "text": "%s"}' % self._text

class LauncherMenuModelItemCommand(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemCommand,self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
            self._text = self._text.replace('"', r'\"')

        self._cmdText = ''.join('%s ' % item for item in self._command)
        self._cmdText = self._cmdText.rstrip()
        
        # Escape possible double quotes in the command string
        self._cmdText = self._cmdText.replace('"', r'\"')
        self._cmdText = self._cmdText.replace('\t', ' ')

    def toJson(self):
        return '{"type": "cmd", "text": "%s", "param": "%s"}' \
            % (self._text, self._cmdText)

class LauncherMenuModelItemMenu(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemMenu,self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
        self._file = command[1] + '.json'
        
    def toJson(self):
        return '{"type": "menu", "text": "%s", "file": "%s"}' \
            % (self._text, self._file)

class LauncherMenuModel(object):
    """ TODO: Docs
    """

    # Regular expression to split the tcl configuration
    # lines into individual parameters
    regexSplit = re.compile('{([^\}]+)}[ \t]*')
    regexType = re.compile('([^ ]+)[ \t]*')
    
    # Translation table for character replacement
    translateTable = dict((ord(char), u'') for char in u'\\\n')

    def __init__(self, dirPath, filePath, outputPath, overwrite):

        self._dirPath = dirPath
        self._filePath = filePath
        self._outPath = outputPath 
        self._path = os.path.join(self._dirPath, self._filePath)
        self._overwrite = overwrite

        self._title = None
        self._fileChoice = None

        self._menuItems = list()

        self._lineNumber = 0
        self._parse()

    def _parse(self):
        with codecs.open(self._path, encoding='ISO-8859-1') as tickleFile:
            parseLine = ''

            for line in tickleFile:
                line = line.lstrip()
                line = line.rstrip('\n')
            
                # Track the current line number for logging output
                self._lineNumber += 1

                # Skip over empty lines
                if not line:
                    continue

                # Tickle has the option of multi-line-split
                # configuration lines using \ character
                if '\\' in line:
                    # Remove '\' character and newlines
                    line = line.translate(LauncherMenuModel.translateTable)
                    parseLine += line
                else:
                    parseLine += line
                    # Skip over comment lines
                    if line[0] != '#':
                        self._parseLine(parseLine)
                    parseLine = ''

    def _parseLine(self, line):
        params = re.split(LauncherMenuModel.regexSplit, line)

        # Remove empty strings in the parameter list
        for element in params:
            if not element:
                params.remove(element)

        command = re.split(LauncherMenuModel.regexType, params[0], 2)

        # Remove empty strings in the parameter list
        for element in command:
            if not element:
                command.remove(element)

        # Get type of configuration line
        itemType = LauncherMenuModelItem.getType(command[0])

        element = None;

        # Remove first parameter since it is parsed
        # and stored in the command variable
        params.remove(params[0])
        
        if len(params) == 0:
            print "WARNING: No parameters passed in file %s, line %d" \
                % (self._filePath, self._lineNumber)

        # Process line parameters depending on type
        if itemType == LauncherMenuType.mainTitle:
            self._title = params[0]
        elif itemType == LauncherMenuType.fileChoice:
            self._fileChoice = LauncherMenuModelItemFileChoice(command, params)
        elif itemType == LauncherMenuType.title:
            element = LauncherMenuModelItemTitle(command, params)
        elif itemType == LauncherMenuType.command:
            element = LauncherMenuModelItemCommand(command, params)
        elif itemType == LauncherMenuType.menu:
            element = LauncherMenuModelItemMenu(command, params)
        else:
            print 'INFO: Skipping over line with command: %s' % command[0]

        if element:
            self._menuItems.append(element)
            
    def toJson(self):
        split = os.path.splitext(self._filePath)
        if not split[1]:
            print 'ERROR: Unable to parse extension from file name: %s' % self._filePath
            return

        outFilePath = os.path.join(self._outPath, split[0] + '.json') 
        print 'INFO: Writing file: %s' % outFilePath

        if os.path.isdir(outFilePath):
            print 'ERROR: Output file "%s" is a directory!' % outFilePath
            return

        if os.path.isfile(outFilePath):
            if not self._overwrite:
                print 'WARNING: Output file "%s" already exists!' % outFilePath
                
                userInput = ''
                while True:
                    userInput = raw_input('Overwrite? [y/N]:')
                    if userInput == 'y' or userInput == 'Y':
                        break
                    elif userInput == 'n' or userInput == 'N' or not userInput:
                        return

        with codecs.open(outFilePath, mode='w', encoding='utf-8') as outFile:

            outFile.write('{\n')
            if self._title:
                outFile.write('    "menu-title": "%s",\n' % self._title)

            if self._fileChoice:
                outFile.write('    ' + self._fileChoice.toJson())

            outFile.write('    "menu": [\n')

            for item in menuModel._menuItems:

                if menuModel._menuItems[-1] is not item:
                    outFile.write('        %s,\n' % item.toJson());
                else:
                    outFile.write('        %s\n' % item.toJson());

            outFile.write('    ]\n}')
            outFile.close()

if __name__ == '__main__':

    # Usage: launcher.py menu config
    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('inputfile',
                          help='Tickle configuration script to be converted.')
    argsPars.add_argument('outputfolder',
                          help='Folder where the converted json file will be stored.')
    argsPars.add_argument('-y', '--yes', action='store_true',
                          help='Overwrite the output file.')

    args = argsPars.parse_args()

    ticklePath = os.path.normpath(args.inputfile)
    outputPath = os.path.normpath(args.outputfolder)

    if not os.path.isfile(ticklePath):
        print 'Tickle path "' + ticklePath + '" is not a regular file!'
        sys.exit(-1)

    if not os.path.isdir(outputPath):
        print 'Output path "' + outputPath + '" is not a directory!'
        sys.exit(-1)

    # Split path into filename and directory path
    tickleSplitPath = os.path.split(ticklePath);
    ticklePathDir = tickleSplitPath[0]
    ticklePathFile = tickleSplitPath[1]

    # Parse requested files
    menuModel = LauncherMenuModel(ticklePathDir, ticklePathFile, outputPath, args.yes)
    menuModel.toJson()
