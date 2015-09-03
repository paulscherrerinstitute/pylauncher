#!/usr/bin/env python

import sys
import os
import re
import enum
import codecs
import argparse


class LauncherMenuType(enum.Enum):
    unknown = 0,
    main_title = 1,
    file_choice = 2,
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

    def to_json(self):
        pass

    @staticmethod
    def get_type(command):
        if command == '@main-title':
            return LauncherMenuType.main_title
        elif command == '@FileChoice':
            return LauncherMenuType.file_choice
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
        super(LauncherMenuModelItemFileChoice, self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
        self._file = command[1] + '.json'

    def to_json(self):
        return '''"file-choice": [
        {"text": "%s", "file": "%s"}
    ],\n''' % (self._text, self._file)


class LauncherMenuModelItemTitle(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemTitle, self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]

    def to_json(self):
        return '{"type": "title", "text": "%s"}' % self._text


class LauncherMenuModelItemCommand(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemCommand, self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
            self._text = self._text.replace('"', r'\"')

        self._cmd_text = ''.join('%s ' % item for item in self._command)
        self._cmd_text = self._cmd_text.rstrip()

        # Escape possible double quotes in the command string
        self._cmd_text = self._cmd_text.replace('"', r'\"')
        self._cmd_text = self._cmd_text.replace('\t', ' ')

    def to_json(self):
        return '{"type": "cmd", "text": "%s", "param": "%s"}' \
            % (self._text, self._cmd_text)


class LauncherMenuModelItemMenu(LauncherMenuModelItem):

    def __init__(self, command, param):
        super(LauncherMenuModelItemMenu, self).__init__(command, param)

        if len(param) == 0:
            self._text = 'None'
        else:
            self._text = param[0]
        self._file = command[1] + '.json'

    def to_json(self):
        return '{"type": "menu", "text": "%s", "file": "%s"}' \
            % (self._text, self._file)


class LauncherMenuModel(object):
    """ TODO: Docs
    """

    # Regular expression to split the tcl configuration
    # lines into individual parameters
    regex_split = re.compile('{([^\}]+)}[ \t]*')
    regex_type = re.compile('([^ ]+)[ \t]*')

    # Translation table for character replacement
    translate_table = dict((ord(char), u'') for char in u'\\\n')

    def __init__(self, dir_path, file_path, output_path, overwrite):

        self._dir_path = dir_path
        self._file_path = file_path
        self._out_path = output_path
        self._path = os.path.join(self._dir_path, self._file_path)
        self._overwrite = overwrite

        self._title = None
        self._file_choice = None

        self._menu_items = list()

        self._line_number = 0
        self._parse()

    def _parse(self):
        with codecs.open(self._path, encoding='ISO-8859-1') as tickle_file:
            parse_line = ''

            for line in tickle_file:
                line = line.lstrip()
                line = line.rstrip('\n')

                # Track the current line number for logging output
                self._line_number += 1

                # Skip over empty lines
                if not line:
                    continue

                # Tickle has the option of multi-line-split
                # configuration lines using \ character
                if '\\' in line:
                    # Remove '\' character and newlines
                    line = line.translate(LauncherMenuModel.translate_table)
                    parse_line += line
                else:
                    parse_line += line
                    # Skip over comment lines
                    if line[0] != '#':
                        self._parse_line(parse_line)
                    parse_line = ''

    def _parse_line(self, line):
        params = re.split(LauncherMenuModel.regex_split, line)

        # Remove empty strings in the parameter list
        for element in params:
            if not element:
                params.remove(element)

        command = re.split(LauncherMenuModel.regex_type, params[0], 2)

        # Remove empty strings in the parameter list
        for element in command:
            if not element:
                command.remove(element)

        # Get type of configuration line
        item_type = LauncherMenuModelItem.get_type(command[0])

        element = None

        # Remove first parameter since it is parsed
        # and stored in the command variable
        params.remove(params[0])

        if len(params) == 0:
            print "WARNING: No parameters passed in file %s, line %d" \
                % (self._file_path, self._line_number)

        # Process line parameters depending on type
        if item_type == LauncherMenuType.main_title:
            self._title = params[0]
        elif item_type == LauncherMenuType.file_choice:
            self._file_Choice = LauncherMenuModelItemFileChoice(command,
                                                                params)
        elif item_type == LauncherMenuType.title:
            element = LauncherMenuModelItemTitle(command, params)
        elif item_type == LauncherMenuType.command:
            element = LauncherMenuModelItemCommand(command, params)
        elif item_type == LauncherMenuType.menu:
            element = LauncherMenuModelItemMenu(command, params)
        else:
            print 'INFO: Skipping over line with command: %s' % command[0]

        if element:
            self._menu_items.append(element)

    def to_json(self):
        split = os.path.splitext(self._file_path)
        if not split[1]:
            print 'ERROR: Unable to parse extension from file name: %s' \
                % self._file_path
            return

        out_file_path = os.path.join(self._out_path, split[0] + '.json')
        print 'INFO: Writing file: %s' % out_file_path

        if os.path.isdir(out_file_path):
            print 'ERROR: Output file "%s" is a directory!' % out_file_path
            return

        if os.path.isfile(out_file_path):
            if not self._overwrite:
                print 'WARNING: Output file "%s" already exists!' \
                    % out_file_path

                user_input = ''
                while True:
                    userInput = raw_input('Overwrite? [y/N]:')
                    if user_input == 'y' or user_input == 'Y':
                        break
                    elif (user_input == 'n' or
                          user_input == 'N' or
                          not user_input):
                        return

        with codecs.open(out_file_path, mode='w', encoding='utf-8') \
                as out_file:

            out_file.write('{\n')
            if self._title:
                out_file.write('    "menu-title": "%s",\n' % self._title)

            if self._file_choice:
                out_file.write('    ' + self._file_choice.to_json())

            out_file.write('    "menu": [\n')

            for item in self._menu_items:

                if menuModel._menu_items[-1] is not item:
                    out_file.write('        %s,\n' % item.to_json())
                else:
                    out_file.write('        %s\n' % item.to_json())

            out_file.write('    ]\n}')
            out_file.close()

if __name__ == '__main__':

    # Usage: launcher.py menu config
    args_pars = argparse.ArgumentParser()
    args_pars.add_argument('inputfile',
                           help='Tickle configuration script to be converted.')
    args_pars.add_argument('outputfolder',
                           help='Folder where the converted json file \
                           will be stored.')
    args_pars.add_argument('-y', '--yes', action='store_true',
                           help='Overwrite the output file.')

    args = args_pars.parse_args()

    tickle_path = os.path.normpath(args.inputfile)
    output_path = os.path.normpath(args.outputfolder)

    if not os.path.isfile(tickle_path):
        print 'Tickle path "' + tickle_path + '" is not a regular file!'
        sys.exit(-1)

    if not os.path.isdir(output_path):
        print 'Output path "' + output_path + '" is not a directory!'
        sys.exit(-1)

    # Split path into filename and directory path
    tickle_split_path = os.path.split(tickle_path)
    tickle_path_dir = tickle_split_path[0]
    tickle_path_file = tickle_split_path[1]

    # Parse requested files
    menuModel = LauncherMenuModel(tickle_path_dir, tickle_path_file,
                                  output_path, args.yes)
    menuModel.to_json()
