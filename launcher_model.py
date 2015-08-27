#!/usr/bin/env python

import sys
import os
import json


class LauncherMenuModel:

    """Parse configuration and build menu model.

    LauncherMenuModel parses the configuration file and builds the list of
    menu items. Each LauncherMenuModel object holds only a list of items
    defined in its configuration file. If submenu is needed, new
    LauncherMenuModel object is created and its reference is stored on the
    calling object list menuItems.

    Each menu has:
        _items
        mainTitle: holding the title of the menu
        list of menuItems: list of all LauncherMenuModelItems
        TODO: in future it will also hold the styles, levels and list of
        possible pictures on the buttons
    """

    def __init__(self, menuFile, level, launcherCfg):
        self.menuItems = list()
        self.level = level
        self._parseMenuJson(menuFile, launcherCfg)

    def getItemsOfType(self, itemsType):
        """Returns a list of all items of specified type."""

        return filter(lambda x: x.__class__.__name__ ==
                      itemsType, self.menuItems)

    def _parseMenuJson(self, menuFile, launcherCfg):
        """Parse JSON type menu config file."""

        _menu = json.load(menuFile)
        self.mainTitle = _menu.get("menu-title",
                                   os.path.basename(menuFile.name))
        # Get list of possible views (e.g. expert, user)

        _listOfViews = _menu.get("file-choice", list())
        self.fileChoices = list()
        for _view in _listOfViews:
            self._checkItemFormatJson(_view, ["text", "file"])  # exits if not
            _text = _view.get("text").strip()
            _fileName = _view.get("file").strip()
            # Do not open file just check if exists. Will be opened, in
            # LauncherWindow._buildMenuModel

            _filePath = os.path.join(launcherCfg.get("launcher_base"),
                                     _fileName)
            _filePath = os.path.normpath(_filePath)
            if not os.path.isfile(_filePath):
                _errMsg = "ParseErr: " + menuFile.name + ": File \"" +\
                    _fileName + "\" not found."
                sys.exit(_errMsg)
            self.fileChoices.append(LauncherFileChoiceItem(self, launcherCfg, _text,
                                                           _fileName))
        # Build menu model. Report error if menu is not defined.

        _listOfMenuItems = _menu.get("menu", list())
        if not _listOfMenuItems:
            errMsg = "ParseErr: " + menuFile.name + ": Launcher menu is not "\
                "defined."
            sys.exit(_errMsg)
        for _item in _listOfMenuItems:
            _type = _item.get("type", "")
            # For each check mandatory parameters and exit if not all.

            if _type == "cmd":
                self._checkItemFormatJson(_item, ["text", "param"])
                _text = _item.get("text").strip()
                _param = _item.get("param").strip()
                _menuItem = LauncherCmdItem(self, launcherCfg, _text, _param)
            elif _type == "menu":
                self._checkItemFormatJson(_item, ["text", "file"])
                _text = _item.get("text").strip()
                _fileName = _item.get("file").strip()
                try:
                    _file = open(launcherCfg.get("launcher_base") + _fileName)
                except IOError:
                    _errMsg = "ParseErr: " + menuFile.name + ": File \"" + \
                              _fileName + "\" not found."
                    sys.exit(_errMsg)
                _menuItem = LauncherSubMenuItem(self, launcherCfg, _text, _file)
                _file.close()
            elif _type == "title":
                self._checkItemFormatJson(_item, ["text"])
                _text = _item.get("text").strip()
                _menuItem = LauncherTitleItem(self, _text)

            elif _type == "separator":
                _menuItem = LauncherItemSeparator(self)

            else:
                _errMsg = "ParseErr:" + menuFile.name + " (line " + \
                    str(_i) + "): Unknown type \"" + _item[0].strip() + \
                    "\"."
                sys.exit(_errMsg)

            self.menuItems.append(_menuItem)

    def _checkItemFormatJson(self, item, mandatoryParam):
        """Check dictionary for mandatory keys.

        Check item (dictionary) if it holds all mandatory keys. If any key is
        missing, exit the program and report error.
        """

        for _param in mandatoryParam:
            if not item.get(_param):
                _errMsg = "ParseErr: Parameter \"" + _param + \
                    "\" is mandatory in configuration \"" + item + "\"."
                sys.exit(_errMsg)


class LauncherMenuModelItem:

    """Super class for all items in menu model.

    LauncherMenuModelItem is a parent super class for menu items that needs
    to be visualized, such as menu buttons, separators, titles. It implements
    methods and parameters common to many subclasses.
    """

    def __init__(self, parent, text=None, style=None, helpLink=None, key=None):
        self.text = text
        self.parent = parent
        self.style = style
        self.helpLink = helpLink
        self.key = key


class LauncherItemSeparator(LauncherMenuModelItem):

    """Special LauncherMenuModelItem, with no text, style or help."""

    def __init__(self, parent, key=None):
        LauncherMenuModelItem.__init__(self, parent, text=None, style=None, key=key)


class LauncherCmdItem(LauncherMenuModelItem):

    """LauncherCmdItem holds the whole shell command."""

    def __init__(self, parent, launcherCfg, text=None, cmd=None, style=None,
                 helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, parent, text, style, key)
        _itemCfg = launcherCfg.get("cmd")
        _prefix = _itemCfg.get("command")
        self.cmd = _prefix + " " + cmd


class LauncherSubMenuItem(LauncherMenuModelItem):

    """Menu item with reference to submenu model.

    LauncherSubMenuItem builds new menu which is defined in subMenuFile.
    If detach == True this sub-menu should be automatically detached if
    detachment is supported in view.
    """

    def __init__(self, parent, launcherCfg, text=None, subMenuFile=None, style=None,
                 helpLink=None, detach=False, key=None):
        LauncherMenuModelItem.__init__(self, parent, text, style, key)
        self.subMenu = LauncherMenuModel(subMenuFile, parent.level+1,
                                         launcherCfg)


class LauncherFileChoiceItem(LauncherMenuModelItem):

    """Holds new root menu config file.

    Launcher can be "rebuild" from new root menu file. LauncherFileChoiceItem
    holds the file of the new root menu (rootMenuFile).
    """

    def __init__(self, parent, launcherCfg, text=None, rootMenuFile=None, style=None,
                 helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, parent, text, style, key)
        self.rootMenuFile = launcherCfg.get("launcher_base") + rootMenuFile


class LauncherTitleItem(LauncherMenuModelItem):

    """Text menu separator."""

    def __init__(self, parent, text=None, style=None, helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, parent, text, style, key)
