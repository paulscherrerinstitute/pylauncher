#!/usr/bin/env python

import sys
import os
import json
import codecs
import argparse
import pyparsing


class LauncherMenuModel(object):

    """Representation - model of the launcher menu configuration.

    This class cotains all logic and data needed to parse and output a
    single launcher menu configuration file. The configuration is read
    from a tickle script parsed, transmuted and output to a JSON
    configuration file. During parsing a list of files is compiled of
    all the menu configuration files that this file depends on. This
    list is used for recursive parsing.
    """

    # Parser to split the TCL configuration
    # lines into an list of parameters
    expr_split = pyparsing.nestedExpr('{', '}')

    # Translation table for character replacement
    translate_table = dict((ord(char), u'') for char in u'\\\n')

    def __init__(self, dir_path, file_path, force):
        self.dir_path = dir_path
        self.file_path = file_path
        self.path = os.path.join(self.dir_path, self.file_path)

        self.force = force

        self.title = None
        self.file_choice = None

        self.menu_items = list()
        self.json_config = dict()
        self.file_list = list()

        self.line_number = 0
        self.parse()

    def parse(self):
        """Entry method to parse the tickle configuration file.

        Opens the tickle file and reads it line by line. Each line is
        parsed separately by the parse_line method.
        """
        with codecs.open(self.path, encoding='ISO-8859-1') as tickle_file:
            parse_line = ''

            for line in tickle_file:
                line = line.lstrip()
                line = line.rstrip('\n')

                # Track the current line number for logging output
                self.line_number += 1

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
                        self.parse_line(parse_line)
                    parse_line = ''

    def parse_line(self, line):
        """Parses each line and converts it into objects.

        The data is stored into a structure of lists and dictionaries
        that can be directly output to JSON and have the same structure.
        Each line is transformed based on the first parameter in the
        line - the command.
        """
        # In order for the parser to behave properly we need
        # to add the curly brackets at the front and back of
        # the line.
        line = '{' + line + '}'

        items = LauncherMenuModel.expr_split.parseString(line).asList()[0]

        # Split parsed list into 2 lists depending on
        # function of the parameters inside
        command = items[0]
        items.pop(0)

        # Join internal lists into a string
        params = list()
        for item in items:
            if isinstance(item, list):
                params.append(self.concatenate(item))

        element = dict()

        # Configure the title of the main menu
        if command[0] == '@main-title':
            self.json_config['menu-title'] = params[0]

            if len(params) > 0:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self.file_path, self.line_number)

        # Add the file choice element to the configuration list
        elif command[0] == '@FileChoice':
            file_choice = list()
            file_choice.append(dict([('text', params[0]),
                                    ('file', command[1]+'.json')]))
            self.json_config['file-choice'] = file_choice

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self.file_path, self.line_number)

        # The command dictates that a separator is added
        elif command[0] == '@separator':
            element['type'] = 'separator'

            if len(params) > 0:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self.file_path, self.line_number)

        # The commands translates into the title element
        elif command[0] == '@title':
            element['type'] = 'title'
            element['text'] = params[0]

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self.file_path, self.line_number)

        # The command loads a new menu from another file
        elif command[0] == '>launcher':
            filepath = os.path.join(self.dir_path, command[1] + '.config')

            # Don't add the menu if the file does not exist
            if not os.path.isfile(filepath):
                if self.force:
                    print 'Wrn: File "%s" does not exist. Skipping...' % \
                        filepath
                    return
                else:
                    print 'Err: File "%s" does not exist.' % filepath
                    sys.exit(-1)

            element['type'] = 'menu'
            element['text'] = params[0]
            element['file'] = command[1] + '.json'

            if len(params) > 1:
                print ('Inf: Skipping additional parameters in '
                       'file "%s", line line %d') \
                    % (self.file_path, self.line_number)

            # Track all additional files that need to be parsed
            self.file_list.append(command[1] + '.config')

        # Skip over lines where the command starts with a hash (comment)
        elif command[0].startswith('#'):
            print 'Inf: Skipping line %d in file "%s" - comment' \
                % (self.line_number, self.file_path)

        # If nothing else this is a command
        else:
            cmd_text = self.concatenate(command)
            # Replace tabulators with spaces
            cmd_text = cmd_text.replace('\t', ' ')

            element['type'] = 'cmd'
            element['text'] = params[0].replace('"', r'\"')
            element['param'] = cmd_text

        # Add the element dictionary to the list of menu items
        if len(element) > 0:
            # Check if one of the parameters is a help link
            html_help = self.get_html_help(params[1:])
            if html_help:
                element['help-link'] = html_help

            self.menu_items.append(element)

    def get_html_help(self, parameters):
        """Checks the parameter if it is a link to a web page.

        The function checks if one of the parameters is a link to a page
        or html file that will be used as the help link text. If none of
        the paramters match the criteria, None is returned.
        """
        for param in parameters:
            part = param.split()[0]
            if (part == 'obj:' or
                    part == 'fltr:' or
                    part == 'lvl:'):
                continue
            else:
                part = os.path.splitext(param)
                if (len(part) > 1 and
                        (part[1] == '.html' or
                         part[1] == '.php3' or
                         part[1] == '.php')):
                    return param

        return None

    def concatenate(self, item_list, level=0):
        """Concatenates a list of string and list items into a string.

        If the list contains sub-lists they are recursively merged until
        we are left with a single string. The item_list parameter should
        be a list that contains string or list elements only. Each
        embedded list is marked in the final string with curly braces.
        """
        new_item_list = list()
        for item in item_list:
            if isinstance(item, list):
                new_item_list.append(self.concatenate(item, level+1))
            else:
                new_item_list.append(item)

        if level > 0:
            return '{%s}' % ' '.join(new_item_list)
        else:
            return ' '.join(new_item_list)

    def to_json(self, out_path, overwrite=False):
        """Mehod to output internal data into the JSON file.

        This method outputs the parsed configuration data into the JSON
        file. If the file already exists the user is asked if it should
        be overwritten or not. The overwrite flag parameter specifies
        if the files should be overwritten without asking the user.
        """
        split = os.path.splitext(self.file_path)
        if not split[1]:
            print 'Err: Unable to parse extension from file name: %s' \
                % self.file_path
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
        self.json_config['menu'] = self.menu_items

        with codecs.open(out_file, mode='w', encoding='utf-8') \
                as output_file:

            json.dump(self.json_config, output_file, indent=4)
            output_file.close()

    def get_file_list(self):
        """Method to get the list of menu files that this menu
        depends on."""
        return self.file_list


class LauncherMenuModelParser(object):

    """Class for recursive module configuration parsing

    Holds information about the files that have been already parsed and
    those who still need to be. After each new menu file is parsed the
    list of files is extended with the menu's dependencies.
    """

    def __init__(self, input_file, output_path, overwrite=False):

        # Split path into filename and directory path
        input_file_split = os.path.split(input_file)

        self.input_file_path = input_file_split[0]
        self.output_path = output_path
        self.overwrite = overwrite

        self.input_files = dict()

        # Add the first input file to the dictionary
        self.input_files[input_file_split[1]] = None

    # Parse requested files
    def parse(self, single=False, force=True):
        """Method for recursive file parsing and tracking files.

        This method starts by parsing the configuration file that the user
        provided and continues to parse its dependent files if recursive
        parsing is enabled (it is by default).
        """
        finished = False

        while not finished:

            input_name = None

            # Check if we parsed all files and get the next
            # in line to be parsed
            for key, value in self.input_files.iteritems():
                if not value:
                    input_name = key
                    break

            # If we parsed all of them, stop
            if not input_name:
                finished = True
                print 'Inf: Successfully finished parsing!'
                continue

            # Parse the current file
            menu_model = LauncherMenuModel(self.input_file_path,
                                           input_name,
                                           force)

            # Store the file parsed model
            self.input_files[input_name] = menu_model

            # If we do not want to parse any additional files, stop
            if(single):
                break

            # Get list of all depending files that have been
            # detected during parsing of the configuration
            file_list = menu_model.get_file_list()

            # Add any files not yet present in the dictionary to it
            for input_file in file_list:
                if input_file not in self.input_files.keys():
                    self.input_files[input_file] = None

    def to_json(self):
        """Mehod to output menu data into the JSON file.

        This method outputs the parsed file contents converted into JSON
        format for each file that was parsed.
        """
        for key in self.input_files.keys():
            # Output the configuration to the json output file
            self.input_files[key].to_json(self.output_path, self.overwrite)

def main():

    args_pars = argparse.ArgumentParser()
    args_pars.add_argument('inputfile',
                           help='Tickle configuration script to be converted.')
    args_pars.add_argument('outputfolder',
                           help='Folder where the converted json file \
                           will be stored.')
    args_pars.add_argument('-o', '--overwrite', action='store_true',
                           help='Overwrite output files that already exist.')
    args_pars.add_argument('-s', '--single', action='store_true',
                           help='Convert only a single file (nonrecursive).')
    args_pars.add_argument('-f', '--force', action='store_true',
                           help='Continue even if some files cannot be found.')

    args = args_pars.parse_args()

    tickle_path = os.path.normpath(args.inputfile)
    output_path = os.path.normpath(args.outputfolder)

    if not os.path.isfile(tickle_path):
        print 'Tickle path "%s" is not a regular file!' % tickle_path
        sys.exit(-1)

    if not os.path.isdir(output_path):
        print 'Output path "%s" is not a directory!' % output_path
        sys.exit(-1)

    parser = LauncherMenuModelParser(tickle_path, output_path, args.overwrite)
    parser.parse(args.single, args.force)
    parser.to_json()


if __name__ == '__main__':
    main()
