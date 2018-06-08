#!/usr/bin/env python
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

# ---------python 2/3 compatibility imports---------
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import sys
if sys.hexversion >= 0x03000000:
    from urllib.request import urlopen
    from urllib.parse import urljoin
    from urllib.error import URLError
else:
    from urllib2 import urlopen
    from urlparse import urljoin
    from urllib2 import URLError
# ------end of python 2/3 compatibility imports-----

import os
import json
import logging
import pyparsing

def join_launcher_path(base, file):
    # In case file is absolute path ora full url, base will be ignored
    try:
        urlopen(file)
        joined_path = file

    except (URLError, ValueError):
        try:
            urlopen(base)
            urljoin(base, file)
        except (URLError, ValueError):
            joined_path = os.path.join(base, file)

    return joined_path

def open_launcher_file(file_path):
    launcher_file = None
    try:
        launcher_file = urlopen(file_path)
    except (URLError, ValueError):
        # Change path to url style and try to open it
        launcher_file_path = os.path.normpath(file_path)
        launcher_file_path = os.path.abspath(launcher_file_path)
        launcher_file_path = 'file:///' + launcher_file_path
        launcher_file = urlopen(launcher_file_path)

    return launcher_file


class launcher_menu_model(object):

    """Parse configuration and build menu model.

    launcher_menu_model parses the configuration file and builds the list of
    menu items. Each launcher_menu_model object holds only a list of items
    defined in its configuration file. If submenu is needed, new
    launcher_menu_model object is created and its reference is stored on the
    calling object list menu_item.

    Each menu has:
        items: list of menu items
        main_title: holding the title of the menu
        level: holding the level of the menu (main = 0, sub of main = 1, ...)
        list of menu_items: list of all launcher_menu_model_items
    """

    def __init__(self, parent, menu_file_path, level, launcher_cfg):
        self.menu_items = list()
        self.parent = parent
        self.level = level
        self.menu_path = menu_file_path
        self.flags = {}

        # open file
        menu_file = open_launcher_file(menu_file_path)
        self.parse_menu_json(menu_file, launcher_cfg)
        menu_file.close()

    def parse_menu_json(self, menu_file, launcher_cfg):
        """Parse JSON type menu config file."""

        try:
            menu = json.loads(menu_file.read().decode('utf-8'))
        except Exception as e:
            err_msg = ("In file \"" + menu_file.geturl() + "\": " + e.args[0])
            logging.error(err_msg)
            sys.exit()

        if 0 == self.level:
            self.flags = menu.get("flags", dict())

        main_title_item = menu.get("menu-title", dict())
        self.main_title = launcher_main_title_item(
            main_title_item,
            os.path.splitext(os.path.basename(menu_file.geturl()))[0])

        # Create file choice element that represents this menu
        self.choice_element = launcher_file_choice_item(
                self, {"text": self.main_title.text, "file": menu_file.geturl()})
        # Get list of possible views (e.g. expert, user)

        list_of_views = menu.get("file-choice", list())
        self.file_choices = list()
        for view in list_of_views:
            self.check_item_format_json(view, "file-choice", ["text", "file"])
            # Do not open file just check if exists. Will be opened, in
            # LauncherWindow._buildMenuModel

            file_name = view.get("file").strip()
            file_path = join_launcher_path(os.path.dirname(self.menu_path),
                                           file_name)
            try:
                choice_file = open_launcher_file(file_path)
                choice_file.close()
                self.file_choices.append(launcher_file_choice_item(
                    self, view))
            except IOError:
                warn_msg = "Parser: " + menu_file.geturl() + ": File \"" +\
                    file_name + "\" not found. Skipped"
                logging.warning(warn_msg)

        # Build menu model. Report error if menu is not defined.

        list_of_menu_items = menu.get("menu", list())
        if not list_of_menu_items:
            err_msg = "Parser: " + menu_file.geturl() +\
                ": Launcher menu is empty."
            logging.error(err_msg)
            sys.exit()

        for item in list_of_menu_items:
            menu_item = None
            item_type = item.get("type", "")
            # For each check mandatory parameters and exit if not all.
            # Custom types can be defined in launcher main config.json file.
            # Custom types are predefine shell commands. First check if on of
            # custom types, then check standard types such as menu, title,
            # separator.

            if launcher_cfg.get(item_type):
                item_cfg = launcher_cfg.get(item_type)
                # self.check_item_format_json(item, item_type,
                #                            ["text", "params"])
                menu_item = launcher_cmd_item(self, item_cfg, item)

            elif item_type == "menu":
                self.check_item_format_json(item, item_type, ["text", "file"])
                try:
                    menu_item = launcher_sub_menu_item(self, launcher_cfg,
                                                       item)
                except IOError:
                    warn_msg = "Parser: " + menu_file.geturl() + \
                        ": File \"" + item.get("file") + "\" not found. " + \
                        "Skipped"
                    logging.warning(warn_msg)

            elif item_type == "title":
                self.check_item_format_json(item, item_type, ["text"])
                menu_item = launcher_title_item(self, item)

            elif item_type == "separator":
                menu_item = launcher_item_separator(self, item)

            else:
                warn_msg = "Parser:" + menu_file.geturl() + \
                    ": Unknown type \"" + item_type + "\". Skipped"
                logging.warning(warn_msg)

            if menu_item != None:
                self.menu_items.append(menu_item)

    def check_item_format_json(self, item, item_name, mandatory_param):
        """Check dictionary for mandatory keys.

        Check item (dictionary) if it holds all mandatory keys. If any key is
        missing, exit the program and report error.
        """

        for param in mandatory_param:
            if not item.get(param):
                err_msg = "Parser Parameter \"" + param + \
                    "\" is mandatory in configuration \"" + item_name + "\"."
                logging.error(err_msg)
                sys.exit()

    def __repr__(self):
        s = "{} (nelm: {})\n".format(self.main_title, len(self.menu_items))
        tabs = "\t" *self.level
        strings = map(repr,self.menu_items)
        strings = [tabs + str for str in strings]
        s += "\n".join(strings)
        return s

class launcher_menu_model_item(object):

    """Super class for all items in menu model.

    launcher_menu_model_item is a parent super class for menu items that needs
    to be visualized, such as menu buttons, separators, titles. It implements
    methods and parameters common to many subclasses.
    """

    def __init__(self, parent, item):
        self.parent = parent
        self.text = item.get("text", None)
        self.help_link = item.get("help-link", None)
        self.tip = item.get("tip", "").strip()
        self.theme = item.get("theme", None)
        self.style = item.get("style", None)
        # Track history of menus to reach this item in the tree. Every item has
        # a parent which is menu, and each menu that is not root menu, has a
        # parent which is submenu item. This list contains trace of submenu
        # items to reach this item.

        if parent:
            if parent.__class__.__name__ == "launcher_menu_model" and\
                    parent.parent.__class__.__name__ == "launcher_sub_menu_item":
                self.trace = list(parent.parent.trace)
                self.trace.append(parent.parent)
            else:
                self.trace = list()

    def __repr__(self):
        return "{}: {}".format(self.__class__.__name__, self.text)

class launcher_main_title_item(launcher_menu_model_item):

    """ Holds description of main menu button. """

    def __init__(self, item, file_name):
        launcher_menu_model_item.__init__(self, None, item)
        if not self.text:
            self.text = file_name


class launcher_item_separator(launcher_menu_model_item):

    """Special launcher_menu_model_item, with no text, style or help."""

    def __init__(self, parent, item):
        launcher_menu_model_item.__init__(self, parent, item)


class launcher_cmd_item(launcher_menu_model_item):

    """ launcher_cmd_item holds the whole shell command."""

    def __init__(self, parent, item_cfg, item):
        launcher_menu_model_item.__init__(self, parent, item)
        self.cmd = item_cfg.get("command")
        arg_flags = item_cfg.get("arg_flags", dict())
        expr = pyparsing.nestedExpr('{', '}', ignoreExpr=None)
        args = expr.parseString("{" + self.cmd + "}")

        params = dict()
        for arg in args[0]:
            
            arg = arg[0]
            if item.get(arg):
                params[arg] = arg_flags.get(arg, "") + " " + item.get(arg)
            else:
                params[arg] = ""
        self.cmd = self.cmd.format(**params)


class launcher_sub_menu_item(launcher_menu_model_item):

    """Menu item with reference to submenu model.

    launcher_sub_menu_item builds new menu which is defined in sub_menu_file.
    If detach == True this sub-menu should be automatically detached if
    detachment is supported in view (TODO).
    """

    def __init__(self, parent, launcher_cfg, item):

        launcher_menu_model_item.__init__(self, parent, item)
        file_name = item.get("file").strip()

        # relative paths to the menu file where this item is defined
        file_path = join_launcher_path(os.path.dirname(parent.menu_path), file_name)

        self.sub_menu = launcher_menu_model(self, file_path,
                                            parent.level+1, launcher_cfg)

    def __repr__(self):
        return repr(launcher_menu_model_item.__repr__(self))+" : "+repr(self.sub_menu)


class launcher_file_choice_item(launcher_menu_model_item):

    """Holds new root menu config file.

    Launcher can be "rebuild" from new root menu file.
    launcher_file_choice_item holds the file of the new root menu
    (root_menu_file).
    """

    def __init__(self, parent, item):
        launcher_menu_model_item.__init__(self, parent, item)
        self.root_menu_file = item.get("file").strip()


class launcher_title_item(launcher_menu_model_item):

    """Text menu separator."""

    def __init__(self, parent, item):
        launcher_menu_model_item.__init__(self, parent, item)
