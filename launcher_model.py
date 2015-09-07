#!/usr/bin/env python

import sys
import os
import json
import urllib2


def open_launcher_file(file_path):
    launcher_file = None
    try:
        launcher_file = urllib2.urlopen(file_path)
    except ValueError:
        try:
            launcher_file_path = os.path.normpath(file_path)
            launcher_file_path = os.path.abspath(launcher_file_path)
            launcher_file_path = 'file://' + urllib2.quote(launcher_file_path)
            launcher_file = urllib2.urlopen(launcher_file_path)
        except IOError:
            raise IOError
    except IOError:
        raise IOError

    return launcher_file


class launcher_menu_model:

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

    def __init__(self, parent, menu_file, level, launcher_cfg):
        self.menu_items = list()
        self.parent = parent
        self.level = level
        self.parse_menu_json(menu_file, launcher_cfg)

    def parse_menu_json(self, menu_file, launcher_cfg):
        """Parse JSON type menu config file."""

        menu = json.loads(menu_file.read())
        self.mainTitle = menu.get("menu-title", os.path.basename(
            menu_file.geturl()))
        # Get list of possible views (e.g. expert, user)

        list_of_views = menu.get("file-choice", list())
        self.file_choices = list()
        for view in list_of_views:
            self.check_item_format_json(view, ["text", "file"])  # exits if not
            text = view.get("text").strip()
            file_name = view.get("file").strip()
            # Do not open file just check if exists. Will be opened, in
            # LauncherWindow._buildMenuModel

            file_path = os.path.join(launcher_cfg.get("launcher_base"),
                                     file_name)
            try:
                open_launcher_file(file_path)
            except IOError:
                err_msg = "ParseErr: " + menu_file.geturl() + ": File \"" +\
                    file_name + "\" not found."
                sys.exit(err_msg)
            self.file_choices.append(launcher_file_choice_item(self,
                                                               launcher_cfg,
                                                               text,
                                                               file_name))
        # Build menu model. Report error if menu is not defined.

        list_of_menu_items = menu.get("menu", list())
        if not list_of_menu_items:
            err_msg = "ParseErr: " + menu_file.geturl() +\
                ": Launcher menu is not defined."
            sys.exit(err_msg)
        for item in list_of_menu_items:
            item_type = item.get("type", "")
            # For each check mandatory parameters and exit if not all.

            theme = item.get("theme", None)
            style = item.get("style", None)

            if item_type == "cmd":
                self.check_item_format_json(item, ["text", "param"])
                text = item.get("text").strip()
                param = item.get("param").strip()
                tip = item.get("tip")
                help_link = item.get("help-link")
                menu_item = launcher_cmd_item(self, launcher_cfg, text, param,
                                              theme, style, tip, help_link,
                                              None)
            elif item_type == "caqtdm":
                self.check_item_format_json(item, ["text", "file"])
                text = item.get("text").strip()
                file_name = item.get("file").strip()
                param = item.get("param")
                tip = item.get("tip")
                help_link = item.get("help-link")
                menu_item = launcher_caqtdm_item(self, launcher_cfg, text,
                                                 file_name, param, theme,
                                                 style, tip, help_link, None)
            elif item_type == "medm":
                self.check_item_format_json(item, ["text", "file"])
                text = item.get("text").strip()
                file_name = item.get("file").strip()
                param = item.get("param")
                tip = item.get("tip")
                help_link = item.get("help-link")
                menu_item = launcher_medm_item(self, launcher_cfg, text,
                                               file_name, param, theme,
                                               style, tip, help_link, None)
            elif item_type == "menu":
                self.check_item_format_json(item, ["text", "file"])
                text = item.get("text").strip()
                file_name = item.get("file").strip()
                tip = item.get("tip")
                try:
                    file_path = os.path.join(launcher_cfg.get("launcher_base"),
                                             file_name)

                    sub_file = open_launcher_file(file_path)
                except IOError:
                    err_msg = "ParseErr: " + menu_file.geturl() + \
                        ": File \"" + file_name + "\" not found."
                    sys.exit(err_msg)
                menu_item = launcher_sub_menu_item(self, launcher_cfg, text,
                                                   sub_file, theme, style, tip,
                                                   None, None, None)
                sub_file.close()
            elif item_type == "title":
                self.check_item_format_json(item, ["text"])
                text = item.get("text").strip()
                menu_item = launcher_title_item(self, text, theme, style)

            elif item_type == "separator":
                menu_item = launcher_item_separator(self, theme, style)

            else:
                err_msg = "ParseErr:" + menu_file.geturl() + \
                          ": Unknown type \"" + item_type + "\"."
                sys.exit(err_msg)

            self.menu_items.append(menu_item)

    def check_item_format_json(self, item, mandatory_param):
        """Check dictionary for mandatory keys.

        Check item (dictionary) if it holds all mandatory keys. If any key is
        missing, exit the program and report error.
        """

        for param in mandatory_param:
            if not item.get(param):
                err_msg = "ParseErr: Parameter \"" + param + \
                    "\" is mandatory in configuration \"" + item + "\"."
                sys.exit(err_msg)


class launcher_menu_model_item:

    """Super class for all items in menu model.

    launcher_menu_model_item is a parent super class for menu items that needs
    to be visualized, such as menu buttons, separators, titles. It implements
    methods and parameters common to many subclasses.
    """

    def __init__(self, parent, text=None, theme=None, style=None, tip=None,
                 help_link=None, key=None):
        self.text = text
        self.parent = parent
        self.theme = theme
        self.style = style
        self.help_link = help_link
        self.key = key
        self.tip = tip

        # Track history of menus to reach this item in the tree. Every item has
        # a parent which is menu, and each menu that is not root menu, has a
        # parent which is submenu item. This list contains trace of submenu
        # items to reach this item.
        if parent.__class__.__name__ == "launcher_menu_model" and\
                parent.parent.__class__.__name__ == "launcher_sub_menu_item":
            self.trace = list(parent.parent.trace)
            self.trace.append(parent.parent)
        else:
            self.trace = list()


class launcher_item_separator(launcher_menu_model_item):

    """Special launcher_menu_model_item, with no text, style or help."""

    def __init__(self, parent, theme=None, style=None, key=None):
        launcher_menu_model_item.__init__(self, parent, None, theme, style,
                                          None, None, key)


class launcher_cmd_item(launcher_menu_model_item):

    """launcher_cmd_item holds the whole shell command."""

    def __init__(self, parent, launcher_cfg, text=None, cmd=None, theme=None,
                 style=None, tip=None, help_link=None, key=None):
        launcher_menu_model_item.__init__(self, parent, text, theme, style,
                                          tip, help_link, key)
        item_cfg = launcher_cfg.get("cmd")
        prefix = item_cfg.get("command")
        self.cmd = prefix + " " + cmd


class launcher_caqtdm_item(launcher_menu_model_item):

    """launcher_caqtdm_item holds the call for caqtdm screen."""

    def __init__(self, parent, launcher_cfg, text=None, caqtdm_file=None,
                 macro=None, theme=None, style=None, tip=None, help_link=None,
                 key=None):
        launcher_menu_model_item.__init__(self, parent, text, theme, style,
                                          tip, help_link, key)
        item_cfg = launcher_cfg.get("caqtdm")
        prefix = item_cfg.get("command")
        macro_flag = item_cfg.get("macro_flag")

        if macro:
            self.cmd = prefix + " " + macro_flag + " \"" + macro + "\" " + \
                caqtdm_file
        else:
            self.cmd = prefix + " " + caqtdm_file


class launcher_medm_item(launcher_menu_model_item):

    """launcher_med_item holds the call for medm screen."""

    def __init__(self, parent, launcher_cfg, text=None, medm_file=None,
                 macro=None, theme=None, style=None, tip=None, help_link=None,
                 key=None):
        launcher_menu_model_item.__init__(self, parent, text, theme, style,
                                          tip, help_link, key)
        item_cfg = launcher_cfg.get("medm")
        prefix = item_cfg.get("command")
        macro_flag = item_cfg.get("macro_flag")

        if macro:
            self.cmd = prefix + " " + macro_flag + " \"" + macro + "\" " + \
                medm_file
        else:
            self.cmd = prefix + " " + medm_file


class launcher_sub_menu_item(launcher_menu_model_item):

    """Menu item with reference to submenu model.

    launcher_sub_menu_item builds new menu which is defined in sub_menu_file.
    If detach == True this sub-menu should be automatically detached if
    detachment is supported in view.
    """

    def __init__(self, parent, launcher_cfg, text=None, sub_menu_file=None,
                 theme=None, style=None, tip=None, help_link=None,
                 detach=False, key=None):
        launcher_menu_model_item.__init__(self, parent, text, style, theme,
                                          tip, help_link, key)
        self.sub_menu = launcher_menu_model(self, sub_menu_file,
                                            parent.level+1, launcher_cfg)


class launcher_file_choice_item(launcher_menu_model_item):

    """Holds new root menu config file.

    Launcher can be "rebuild" from new root menu file.
    launcher_file_choice_item holds the file of the new root menu
    (root_menu_file).
    """

    def __init__(self, parent, launcher_cfg, text=None, root_menu_file=None,
                 tip=None, help_link=None, key=None):
        launcher_menu_model_item.__init__(self, parent, text, None, None, tip,
                                          help_link, key)
        self.root_menu_file = root_menu_file


class launcher_title_item(launcher_menu_model_item):

    """Text menu separator."""

    def __init__(self, parent, text=None, theme=None, style=None, tip=None,
                 help_link=None, key=None):
        launcher_menu_model_item.__init__(self, parent, text, theme, style,
                                          tip, help_link, key)
