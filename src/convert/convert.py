#!/usr/bin/env python

from __future__ import print_function
from __future__ import unicode_literals
import collections
import sys
import os
import json
import codecs
import argparse
import pyparsing
import traceback

class LauncherBaseModel(object):
    """Base class to parse launcher config and level files.

    It provides methods to parse each line into tokens list.
    """
    # Parser to split the TCL configuration
    # lines into an list of parameters
    expr_split = pyparsing.nestedExpr('{', '}')

    def __init__(self, path):
        """
        :param str path: file absolute path
        """
        self.path = path
        self.parse()

    @classmethod
    def readline(cls, file):
        """
        Read lines from file, taking line continuation '\\' into account.
        And parse it into a nested list of tokens, using { } as opener/closer.

        :param object file: file object to read from
        :return: (line_number, tokens_list)

        This returns a generator same as the file object.

        :note: The empty lines, comment lines and also lines like
               "{#This is really just comments}" are skipped.
        """
        line_number = 0
        for line in file:
            line = line.strip()
            line_number += 1
            while line.endswith('\\'):
                line_number += 1
                line = line[:-1] + next(file).strip()
            # skip empty and comment lines
            if not line or line.startswith('#'):
                continue
            
            # In order for the parser to behave properly we need
            # to add the curly brackets at the front and back of
            # the line.
            line = '{' + line + '}'
            items = LauncherBaseModel.expr_split.parseString(line).asList()[0]

            # skip empty or comment lines
            if not items or not items[0] or items[0][0].startswith('#'):
                continue

            yield line_number, items

    def parse(self):
        """Entry method to parse the tickle configuration file.

        Opens the tickle file and reads it line by line. Each line is
        parsed separately by the parse_line method.
        """
        with codecs.open(self.path, encoding='ISO-8859-1') as tickle_file:
            for line_number, items in self.readline(tickle_file):
                try:
                    self.parse_line(line_number, items)
                except SystemExit:
                    sys.exit(-1)
                except:
                    print('Err: Following line can not be parsed:')
                    print('    File: "%s", line %d' % (self.path, line_number))
                    print('        ', self.concatenate(items))
                    traceback.print_exc()
                    sys.exit(-1)

    @staticmethod
    def tkcolor_to_css(tkcolor):
        """
        Parse tk colors string to css color string.

        :param str tkcolor: tk color
        :return: css color

        tk colors take 3 forms:
        * rgb: ffff/ffff/ffff
        * #ffffff
        * <name>
        """
        if tkcolor.startswith('rgb:'):
            rgb = tkcolor[4:].split('/')
            return '#' + ''.join(rgb)
        elif tkcolor.strip('"').startswith('#'): # hexdecimal
            return tkcolor.strip('"')
        else:
            # tk color names could be of form "<basename><number>".
            # since css only accepts the "<basename>", so strip off the ending numbers.
            return tkcolor.strip('"').rstrip('0123456789')

    @staticmethod
    def tkfont_to_css(tkfont):
        """
        Parse tk font string to css font string.
        
        :param str tkfont: tk font
        :return: css font

        tk fonts take the form of "<family> <size> <weight>", while css fonts
        take the form "<style> <weight> <size> <family>".

        .. note: tk font size has no unit suffix, and in css "px" unit is added.
        """
        css = {}
        parts = tkfont.strip('"').split()
        for part in parts:
            if part == 'bold':
                css['weight'] = part
            elif part == 'italic':
                css['style'] = part
            elif part.isdigit():
                css['size'] = part + 'px'
            elif part.startswith('-') and part[1:].isdigit():
                css['size'] = part[1:] + 'px'
            else:
                css['family'] = part
       
        return ' '.join(css[p] for p in ['style', 'weight', 'size', 'family'] if p in css)

    @staticmethod
    def tkopt_to_css(tkopt):
        """
        Parse tk config string to css.
        
        :param str tkopt: tk config
        :return: css
        :rtype: dict

        .. note: css config is returned in a dict. 
                 This makes it convenient to update a single components.
        """
        css = {}
        for k, v in zip(tkopt[::2], tkopt[1::2]):
            if k == '-background':
                css['background-color'] = LauncherBaseModel.tkcolor_to_css(v)
            elif k == '-foreground':
                css['color'] = LauncherBaseModel.tkcolor_to_css(v)
            elif k == '-font':
                css['font'] = LauncherBaseModel.tkfont_to_css(v)
        return css

    @staticmethod
    def concatenate(item_list, level=0):
        """Concatenates a list of string and list items into a string.

        If the list contains sub-lists they are recursively merged until
        we are left with a single string. The item_list parameter should
        be a list that contains string or list elements only. Each
        embedded list is marked in the final string with curly braces.
        """
        new_item_list = list()
        for item in item_list:
            if isinstance(item, list):
                new_item_list.append(LauncherBaseModel.concatenate(item, level+1))
            else:
                new_item_list.append(item)

        if level > 0:
            return '{%s}' % ' '.join(new_item_list)
        else:
            return ' '.join(new_item_list)


class LauncherLevelModel(LauncherBaseModel):
    """Model of lancher level
    """
    def __init__(self, path):
        self.levels = {}
        super(LauncherLevelModel, self).__init__(path)

    def parse_line(self, line_number, items):
        command = items.pop(0)
        if command[0] != '@level' or len(command) != 2:
            return

        level_name = command[1]
        level_definition = {}
        for item in items:
            # skip empty list
            if not item:
                return
            level_definition.update(self.tkopt_to_css(item[1:]))
        self.levels[level_name] = level_definition


class LauncherMenuModel(LauncherBaseModel):

    """Representation - model of the launcher menu configuration.

    This class contains all logic and data needed to parse and output a
    single launcher menu configuration file. The configuration is read
    from a tickle script parsed, transmuted and output to a JSON
    configuration file. During parsing a list of files is compiled of
    all the menu configuration files that this file depends on. This
    list is used for recursive parsing.
    """
    def __init__(self, dir_path, file_name, levels, force):
        self.dir_path = dir_path
        self.file_name = file_name
        self.levels = levels
        self.force = force

        self.title = None
        self.file_choice = None

        self.menu_items = list()
        self.json_config = collections.OrderedDict()
        self.file_list = list()

        super(LauncherMenuModel, self).__init__(os.path.join(self.dir_path, self.file_name))

    def parse_line(self, line_number, items):
        """Parses each line and converts it into objects.

        The data is stored into a structure of lists and dictionaries
        that can be directly output to JSON and have the same structure.
        Each line is transformed based on the first parameter in the
        line - the command.
        """
        # the first two items are command and text
        command = items.pop(0)
        if items:
            text = self.concatenate(items.pop(0))

        if not isinstance(command, list):
            print('Err: Incorrect formatted line in file "%s", line %d'
                    % (self.file_name, line_number))
            sys.exit(-1) 

        element = collections.OrderedDict()
        extras = self.get_extra_param(items)

        # Configure the title of the main menu
        if command[0] == '@main-title':
            self.json_config['menu-title'] = collections.OrderedDict()
            self.json_config['menu-title']['text'] = text
            if 'opt' in extras:
                self.json_config['menu-title']['style'] = extras.pop('opt')
        # Add the file choice element to the configuration list
        elif command[0] == '@FileChoice':
            file_choice = list()
            file_choice.append(collections.OrderedDict(
                [('text', text), ('file', command[1]+'.json')]))
            self.json_config['file-choice'] = file_choice
        # The command dictates that a separator is added
        elif command[0] == '@separator':
            element['type'] = 'separator'
        # The commands translates into the title element
        elif command[0] == '@title':
            element['type'] = 'title'
            element['text'] = text
            if 'opt' in extras:
                element['style'] =  extras.pop('opt')
        elif command[0].startswith('@'):
            print('Wrn: Unknown command "%s" in file "%s", line %d.' % 
                    (command[0], self.file_name, line_number))
            return
        # The command loads a new menu from another file
        elif command[0] == '>launcher':
            filepath = os.path.join(self.dir_path, command[1] + '.config')

            # Don't add the menu if the file does not exist
            if not os.path.isfile(filepath):
                if self.force:
                    print('Wrn: File "%s" (referenced in file "%s", line %d) does not exist. Skipping...' 
                            % (filepath, self.file_name, line_number))
                    return
                else:
                    print('Err: File "%s" (referenced in file "%s", line %d) does not exist.' 
                            % (filepath, self.file_name, line_number))
                    sys.exit(-1)

            element['type'] = 'menu'
            element['text'] = text
            element['file'] = command[1] + '.json'
            if 'opt' in extras:
                element['style'] = extras.pop('opt')
            # Track all additional files that need to be parsed
            self.file_list.append(command[1] + '.config')
        # If nothing else this is a command
        else:
            cmd_text = self.concatenate(command)
            # Replace tabulators with spaces
            cmd_text = cmd_text.replace('\t', ' ')

            element['type'] = 'cmd'
            element['text'] = text.replace('"', r'\"')
            element['command'] = cmd_text
            if 'opt' in extras:
                element['style'] = extras.pop('opt')
        
        # Add the element dictionary to the list of menu items
        if element:
            # Check if one of the parameters is a help link
            if 'help' in extras:
                element['help-link'] = extras.pop('help')

            if extras:
                print('Inf: Skipping additional parameters "%s" in '
                      'file "%s", line %d'
                    % (extras.keys(), self.file_name, line_number))

            self.menu_items.append(element)

    def get_extra_param(self, items):
        """Return the extra parameters as a dict
        """
        d = {}
        css = {}
        for item in items:
            if not item:
                continue
            if item[0] == 'opt:':
                css.update(self.tkopt_to_css(item[1:]))
            elif item[0] == 'lvl:':
                level = self.levels.get(item[1])
                if level:
                    css.update(level)
                else:
                    print('Wrn: Unknown level name "%s"' % item[1])
            elif item[0] in ['obj:', 'fltr:', 'key:']:
                pass
            elif item[0] == ['help:']:
                d['help'] = self.concatenate(item[1:])
            else:
                d['help'] = self.concatenate(item[1:])

        opt = ''
        for k,v in css.items():
            opt += '%s: %s;' % (k ,v)
        if opt:
            d['opt'] = opt

        return d

    def to_json(self, out_path, overwrite=False):
        """Mehod to output internal data into the JSON file.

        This method outputs the parsed configuration data into the JSON
        file. If the file already exists the user is asked if it should
        be overwritten or not. The overwrite flag parameter specifies
        if the files should be overwritten without asking the user.
        """
        split = os.path.splitext(self.file_name)
        if not split[1]:
            print('Err: Unable to parse extension from file name: %s' % self.file_name)
            return

        out_file = os.path.join(out_path, split[0] + '.json')
        print('Inf: Writing file: %s' % out_file)

        if os.path.isdir(out_file):
            print('Err: Output file "%s" is a directory!' % out_file)
            return

        if os.path.isfile(out_file):
            if not overwrite:
                print('Wrn: Output file "%s" already exists!' % out_file)

                while True:
                    user_input = input('Overwrite? [y/N]:')
                    if user_input == 'y' or user_input == 'Y':
                        break
                    elif (user_input == 'n' or
                          user_input == 'N' or
                          not user_input):
                        return

        # Set the item list to the menu key in the top dictionary
        self.json_config['menu'] = self.menu_items

        with codecs.open(out_file, mode='w', encoding='utf-8') as output_file:
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

    def __init__(self, input_file, output_path, level_file=None, overwrite=False):

        # Split path into filename and directory path
        self.input_file_path, input_file_name = os.path.split(input_file)

        self.output_path = output_path
        self.overwrite = overwrite

        self.input_files = collections.OrderedDict()

        # Add the first input file to the dictionary
        self.input_files[input_file_name] = None

        # Parse launcher level file
        self.levels = {}
        if level_file is None:
            level_file = os.path.join(self.input_file_path, os.path.splitext(input_file_name)[0] + '.lvl')
        if os.path.exists(level_file):
            self.levels = LauncherLevelModel(level_file).levels

    # Parse requested files
    def parse(self, single=False, force=True):
        """Method for recursive file parsing and tracking files.

        This method starts by parsing the configuration file that the user
        provided and continues to parse its dependent files if recursive
        parsing is enabled (it is by default).
        """
        finished = False

        while not finished:

            input_file_name = None

            # Check if we parsed all files and get the next
            # in line to be parsed
            for key, value in self.input_files.items():
                if not value:
                    input_file_name = key
                    break

            # If we parsed all of them, stop
            if not input_file_name:
                finished = True
                print('Inf: Successfully finished parsing!')
                continue

            # Parse the current file
            menu_model = LauncherMenuModel(self.input_file_path,
                                           input_file_name,
                                           self.levels,
                                           force)

            # Store the file parsed model
            self.input_files[input_file_name] = menu_model

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
                           help='TCL configuration script to be converted')
    args_pars.add_argument('outputfolder',
                           help='folder where the converted json file will be stored')
    args_pars.add_argument('-o', '--overwrite', action='store_true',
                           help='overwrite output files that already exist')
    args_pars.add_argument('-s', '--single', action='store_true',
                           help='convert only a single file (nonrecursive)')
    args_pars.add_argument('-f', '--force', action='store_true',
                           help='continue even if some files cannot be found')
    args_pars.add_argument('--level',
                           help='launcher level definition file. (default: <inputfile>.lvl)')

    args = args_pars.parse_args()

    tickle_path = os.path.normpath(args.inputfile)
    output_path = os.path.normpath(args.outputfolder)

    if not os.path.isfile(tickle_path):
        print('TCL path "%s" is not a regular file!' % tickle_path)
        sys.exit(-1)

    if not os.path.isdir(output_path):
        print('Output path "%s" is not a directory!' % output_path)
        sys.exit(-1)

    parser = LauncherMenuModelParser(tickle_path, output_path, args.level, args.overwrite)
    parser.parse(args.single, args.force)
    parser.to_json()


if __name__ == '__main__':
    main()
