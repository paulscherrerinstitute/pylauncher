#!/usr/bin/env python

import sys
import os
import re
import json
import enum
import codecs
import argparse


class LauncherMenuModel(object):
    """ TODO: Docs
    """

    # Regular expression to split the tcl configuration
    # lines into individual parameters
    regex_split = re.compile('{([^\}]+)}[ \t]*')
    regex_type = re.compile('([^ ]+)[ \t]*')

    # Translation table for character replacement
    translate_table = dict((ord(char), u'') for char in u'\\\n')

    def __init__(self, dir_path, file_path):

        self._dir_path = dir_path
        self._file_path = file_path
        self._path = os.path.join(self._dir_path, self._file_path)

        self._title = None
        self._file_choice = None

        self._menu_items = list()
        self._json_config = dict()
        self._file_list = list()

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

        element = dict()

        # Remove first parameter since it is parsed
        # and stored in the command variable
        params.remove(params[0])

#         if len(params) == 0:
#             print 'Wrn: No parameters passed in file "%s", line %d' \
#                 % (self._file_path, self._line_number)

        # Configure the title of the main menu
        if command[0] == '@main-title':
            self._json_config['menu-title'] = params[0]

            if len(params) > 0:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self._file_path, self._line_number)

        # Add the file choice element to the configuration list
        elif command[0] == '@FileChoice':
            file_choice = list()
            file_choice.append(dict([('text', params[0]),
                                    ('file', command[1]+'.json')]))
            self._json_config['file-choice'] = file_choice

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self._file_path, self._line_number)

        # The command dictates that a separator is added
        elif command[0] == '@separator':
            element['type'] = 'separator'

            if len(params) > 0:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self._file_path, self._line_number)

        # The commands translates into the title element
        elif command[0] == '@title':
            element['type'] = 'title'
            element['text'] = params[0]

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self._file_path, self._line_number)

        # The command loads a new menu from another file
        elif command[0] == '>launcher':
            element['type'] = 'menu'
            element['text'] = params[0]
            element['file'] = command[1] + '.json'

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self._file_path, self._line_number)

            # Track all additional files that need to be parsed
            self._file_list.append(command[1] + '.config')

        # Skip over lines where the command starts with a hash (comment)
        elif command[0] == '#':
            print 'Inf: Skipping line %d in file "%s" - comment' \
                % (self._line_number, self._file_path)

        # If nothing else this is a command
        else:
            cmd_text = ''.join('%s ' % item for item in command).rstrip()
            # Escape possible double quotes in the command string
            cmd_text = cmd_text.replace('"', r'\"').replace('\t', ' ')

            element['type'] = 'cmd'
            element['text'] = params[0].replace('"', r'\"')
            element['param'] = cmd_text

        # Add the element dictionary to the list of menu items
        if len(element) > 0:
            self._menu_items.append(element)

    def to_json(self, out_path, overwrite=False):
        split = os.path.splitext(self._file_path)
        if not split[1]:
            print 'Err: Unable to parse extension from file name: %s' \
                % self._file_path
            return

        out_file = os.path.join(out_path, split[0] + '.json')
        print 'Inf: Writing file: %s' % out_file

        if os.path.isdir(out_file):
            print 'Err: Output file "%s" is a directory!' % out_file
            return

        if os.path.isfile(out_file):
            if not overwrite:
                print 'Wrn: Output file "%s" already exists!' \
                    % out_file

                user_input = ''
                while True:
                    user_input = raw_input('Overwrite? [y/N]:')
                    if user_input == 'y' or user_input == 'Y':
                        break
                    elif (user_input == 'n' or
                          user_input == 'N' or
                          not user_input):
                        return

        # Set the item list to the menu key in the top dictionary
        self._json_config['menu'] = self._menu_items

        with codecs.open(out_file, mode='w', encoding='utf-8') \
                as output_file:

            json.dump(self._json_config, output_file, indent=4)
            output_file.close()

    def get_file_list(self):
        return self._file_list


class LauncherMenuModelParser(object):

    def __init__(self, input_file, output_path, overwrite=False):

        # Split path into filename and directory path
        input_file_split = os.path.split(input_file)

        self._input_file_path = input_file_split[0]
        self._input_file_name = input_file_split[1]
        self._output_path = output_path
        self._overwrite = overwrite

        self._input_files = dict()

        self._input_files[self._input_file_name] = 'No'

    # Parse requested files
    def parse(self, single=False):

        finished = False

        while not finished:

            input_name = None

            # Check if we parsed all files and get the next
            # in line to be parsed
            for key, value in self._input_files.iteritems():
                if value == 'No':
                    input_name = key
                    break

            # If we parsed all of them, stop
            if not input_name:
                finished = True
                continue

            # Parse the current file
            menu_model = LauncherMenuModel(self._input_file_path,
                                           input_name)

            # Output the configuration to the json output file
            menu_model.to_json(self._output_path, self._overwrite)

            # If we do not want to parse any additional files, stop
            if(single):
                break

            # Tag the current file as checked
            self._input_files[input_name] = 'Yes'

            # Get list of all depending files that have been
            # detected during parsing of the configuration
            file_list = menu_model.get_file_list()

            # Add any files not yet present in the dictionary to it
            for input_file in file_list:
                if input_file not in self._input_files.keys():
                    self._input_files[input_file] = 'No'


if __name__ == '__main__':

    args_pars = argparse.ArgumentParser()
    args_pars.add_argument('inputfile',
                           help='Tickle configuration script to be converted.')
    args_pars.add_argument('outputfolder',
                           help='Folder where the converted json file \
                           will be stored.')
    args_pars.add_argument('-y', '--yes', action='store_true',
                           help='Overwrite the output file.')
    args_pars.add_argument('-s', '--single', action='store_true',
                           help='Convert only a single file.')

    args = args_pars.parse_args()

    tickle_path = os.path.normpath(args.inputfile)
    output_path = os.path.normpath(args.outputfolder)

    if not os.path.isfile(tickle_path):
        print 'Tickle path "' + tickle_path + '" is not a regular file!'
        sys.exit(-1)

    if not os.path.isdir(output_path):
        print 'Output path "' + output_path + '" is not a directory!'
        sys.exit(-1)

    parser = LauncherMenuModelParser(tickle_path, output_path, args.yes)
    parser.parse(args.single)
