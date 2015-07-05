#!/usr/bin/python

import sys
import os
import argparse
import csv

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot, Qt


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

    def __init__(self, menuFile, launcherCfg):

        # Parses comma separated files of defined format. Parser adds menu
        # objects to self.menuItems list.

        self.menuItems = list()
        self._parseCsv(menuFile, launcherCfg)

    def getItemsOfType(self, itemsType):
        """Returns a list of all items of specified type."""

        return filter(lambda x: x.__class__.__name__ ==
                      itemsType, self.menuItems)

    def _parseCsv(self, menuFile, launcherCfg):
        """Parses .csv Menu file and builds model.

        For each line checks if:
            -type of entry is valid
            -has enough attributes
            -if files exists (for submenus, and file-choice)

        Returns detailed error message and stops the program.
        """

        _parsed = list(csv.reader(menuFile, delimiter=","))
        _menu = list(_parsed)
        self.menuItems = list()
        _i = 1
        for _item in _menu:
            # Ignore comments and empty lines

            if _item and not _item[0].strip().startswith("#"):
                # Check item types and if they have enough arguments. Then
                # concentrate parameters with config file properties.

                _itemType = _item[0].strip()
                if _itemType == "main-title":
                    self.mainTitle = _item[1]
                elif _itemType == "cmd":
                    self._checkItemFormat(_item, 3, menuFile.name, _i)
                    _menuItem = LauncherCmdItem(
                        launcherCfg, _item[1], _item[2])
                    self.menuItems.append(_menuItem)
                elif _itemType == "menu":
                    self._checkItemFormat(_item, 3, menuFile.name, _i)
                    try:
                        _subMenuFile = open(launcherCfg["LAUNCHER_BASE"] +
                                            _item[2].strip())
                    except IOError:
                        _errMsg = "ParseErr:" + menuFile.name + \
                            " (line " + str(_i) + "): File \"" + \
                            _item[2].strip() + "\" not found."
                        sys.exit(_errMsg)

                    _menuItem = LauncherSubMenuItem(
                        launcherCfg, _item[1], _subMenuFile)
                    _subMenuFile.close()
                    self.menuItems.append(_menuItem)
                elif _itemType == "title":
                    self._checkItemFormat(_item, 2, menuFile.name, _i)
                    _menuItem = LauncherTitleItem(_item[1])
                    self.menuItems.append(_menuItem)

                elif _itemType == "separator":
                    _menuItem = LauncherItemSeparator()
                    self.menuItems.append(_menuItem)

                elif _itemType == "file-choice":
                    self._checkItemFormat(_item, 3, menuFile.name, _i)
                    # Do not open file just check if exists. Will be opened,
                    # in LauncherWindow._buildMenuModel

                    if not os.path.isfile(launcherCfg["LAUNCHER_BASE"] +
                                          _item[2].strip()):
                        _errMsg = "ParseErr:" + menuFile.name + \
                            " (line " + str(_i) + "): File \"" + \
                            _item[2].strip() + "\" not found."
                        sys.exit(_errMsg)
                    _menuItem = LauncherFileChoiceItem(
                        launcherCfg, _item[1], _item[2])
                    self.menuItems.append(_menuItem)
                else:
                    _errMsg = "ParseErr:" + menuFile.name + " (line " + \
                        str(_i) + "): Unknown type \"" + _item[0].strip() + \
                        "\"."
                    sys.exit(_errMsg)
            _i += 1

    def _checkItemFormat(self, item, minLength, fileName, line):
        """ Checks item format

        For now checks only number of attributes. When optional parameters will
        be implemented this function will be smarter.
        """

        if not len(item) >= minLength:
            _errMsg = "ParseErr:" + fileName + " (line " + str(line) + \
                "): \"" + item[0].strip() + "\" requires at least " + \
                str(minLength-1) + " attributes."
            sys.exit(_errMsg)


class LauncherMenuModelItem:

    """Super class for all items in menu model.

    LauncherMenuModelItem is a parent super class for menu items that needs
    to be visualized, such as menu buttons, separators, titles. It implements
    methods and parameters common to many subclasses.
    """

    def __init__(self, text=None, style=None, helpLink=None, key=None):
        self.text = text
        self.style = style
        self.helpLink = helpLink
        self.key = key


class LauncherItemSeparator(LauncherMenuModelItem):

    """Special LauncherMenuModelItem, with no text, style or help."""

    def __init__(self, key=None):
        LauncherMenuModelItem.__init__(self, text=None, style=None, key=key)


class LauncherCmdItem(LauncherMenuModelItem):

    """LauncherCmdItem holds the whole shell command."""

    def __init__(self, launcherCfg, text=None, cmd=None, style=None, helpLink=None,
                 key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.cmd = launcherCfg["cmd"] + " " + cmd


class LauncherSubMenuItem(LauncherMenuModelItem):

    """Menu item with reference to submenu model.

    LauncherSubMenuItem builds new menu which is defined in subMenuFile.
    If detach == True this sub-menu should be automatically detached if
    detachment is supported in view.
    """

    def __init__(self, launcherCfg, text=None, subMenuFile=None, style=None,
                 helpLink=None, detach=False, key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.subMenu = LauncherMenuModel(subMenuFile, launcherCfg)


class LauncherFileChoiceItem(LauncherMenuModelItem):

    """Holds new root menu config file.

    Launcher can be "rebuild" from new root menu file. LauncherFileChoiceItem
    holds the file of the new root menu (rootMenuFile).
    """

    def __init__(self, launcherCfg, text=None, rootMenuFile=None, style=None,
                 helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.rootMenuFile = launcherCfg["cmd"] + rootMenuFile


class LauncherTitleItem(LauncherMenuModelItem):

    """Text menu separator."""

    def __init__(self, text=None, style=None, helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)


class LauncherWindow(QtGui.QMainWindow):

    """Launcher main window.

    Main launcher window. At initialization recursively builds visualization
    of launcher menus, builds menu bar, ...
    """

    def __init__(self, rootFilePath, cfgFilePath, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        try:
            _cfgFile = open(cfgFilePath)  # Catch exception outside.
        except IOError:
            _errMsg = "Err: Configuration file \"" + cfgFilePath + \
                "\" not found."
            sys.exit(_errMsg)
        self.launcherCfg = self._parseLauncherCfg(_cfgFile)

        # Build menu model from rootMenuFile and set general parameters.
        self._menuModel = self._buildMenuModel(rootFilePath)

        self.setWindowTitle(self._menuModel.mainTitle)
        # QMainWindow has predefined layout. Content should be in the central
        # widget. Create widget with a QVBoxLayout and set it as central.

        _mainWidget = QtGui.QWidget(self)
        self._mainLayout = QtGui.QVBoxLayout(_mainWidget)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(_mainWidget)
        # Main window consist of filter/serach entry and a main button which
        # pops up the root menu. Create a layout and add the items.

        self.mainButton = QtGui.QPushButton(self._menuModel.mainTitle, self)
        # Visualize the menus by recursively creating LauncherSubMenu objects
        # for each LauncherMenuModel from model. Append it to the button.

        self._launcherMenu = LauncherSubMenu(self._menuModel, self.mainButton)
        self.mainButton.setMenu(self._launcherMenu)

        # create Filter/search item. Add it and main button to the layout.
        self._searchInput = LauncherSearchWidget(self._launcherMenu, self)
        self._mainLayout.addWidget(self._searchInput)
        self._mainLayout.addWidget(self.mainButton)
        # Create menu bar. In current visualization menu bar also exposes all
        # LauncherFileChoiceItem items from the model. They are exposed in
        # File menu.
        _menuBar = self.menuBar()
        self._fileMenu = QtGui.QMenu("&File", _menuBar)
        self._fileChoiceItems = self._menuModel.getItemsOfType(
            "LauncherFileChoiceItem"
        )
        for item in self._fileChoiceItems:
            _button = LauncherFileChoiceButton(item, self._fileMenu)
            _buttonAction = QtGui.QWidgetAction(self._fileMenu)
            _buttonAction.setDefaultWidget(_button)
            self._fileMenu.addAction(_buttonAction)
        _menuBar.addMenu(self._fileMenu)

    def setNewView(self, rootMenuFile):
        """Rebuild launcher from new config file.

        Destroy previous model and create new one. Build menus and edit main
        window elements.
        """

        del self._menuModel
        self._menuModel = self._buildMenuModel(rootMenuFile)
        self.setWindowTitle(self._menuModel.mainTitle)
        self.mainButton.setText(self._menuModel.mainTitle)
        self._launcherMenu = LauncherSubMenu(self._menuModel, self.mainButton)
        self.mainButton.setMenu(self._launcherMenu)

    def changeEvent(self, changeEvent):
        """Catch when main window is selected and set focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self._searchInput.setFocus()

    def _buildMenuModel(self, rootMenuPath):
        """Return model of a menu defined in rootMenuFile."""
        _rootMeniFullPath = self.launcherCfg["LAUNCHER_BASE"] + \
            "/" + rootMenuPath
        try:
            _rootMenuFile = open(_rootMeniFullPath)
        except IOError:
            _errMsg = "Err: File \"" + rootMenuPath + "\" not found."
            sys.exit(_errMsg)
        _rootMenu = LauncherMenuModel(_rootMenuFile, self.launcherCfg)
        _rootMenuFile.close()
        return _rootMenu

    def _parseLauncherCfg(self, cfgFile):
        valid = ["cmd", "LAUNCHER_BASE"]
        cfg = dict()
        i = 0
        for line in cfgFile:
            line = line.strip()
            if line and not line.startswith("#"):
                cfgPair = line.split(":")
                if cfgPair[0].strip()not in valid:
                    raise SyntaxError("Unknown parameter.", cfgFilePath, i)
                else:
                    cfg[cfgPair[0].strip()] = cfgPair[1].strip()
        i += 1
        cfgFile.close()
        return cfg


class LauncherMenu(QtGui.QMenu):

    """Super class of all menu visualizations.

    Is a parent super class which takes the model of menu as an argument and
    builds a "vital" part of the menu. It also implements methods for menu
    manipulation.
    """

    def __init__(self, menuModel, parent=None):
        QtGui.QMenu.__init__(self, parent)
        self.filterTerm = ""
        self.menuModel = menuModel
        # menuModel has a list of menuItems with models of items. Build buttons
        # from it and add them to the menu.

        for item in self.menuModel.menuItems:
            if item.__class__.__name__ == "LauncherCmdItem":
                self.appendToMenu(LauncherCmdButton(item, self))
            elif item.__class__.__name__ == "LauncherSubMenuItem":
                self.appendToMenu(LauncherMenuButton(item, self))
            elif item.__class__.__name__ == "LauncherTitleItem":
                self.appendToMenu(LauncherMenuTitle(item, self))
            elif item.__class__.__name__ == "LauncherItemSeparator":
                self.addAction(LauncherSeparator(item, self))

    def appendToMenu(self, widget):
        """Append action to menu.

        Create widget action for widget. Pair them and add to the menu."""

        self._action = LauncherMenuWidgetAction(widget, self)
        self.addAction(self._action)

    def insertToMenu(self, widget, index):
        """Insert action to specified position in menu.

        Create widget action for widget. Pair them and insert them to the
        specified position in menu.
        """

        self._action = LauncherMenuWidgetAction(widget, self)
        if self.actions()[index]:
            self.insertAction(self.actions()[index], self._action)
        else:
            self.addAction(self._action)

    def filterMenu(self, filterTerm=None):
        """Filter menu items with filterTerm

        Shows/hides action depending on filterTerm. Returns true if has
        visible active (buttons) items.
        """

        self.filterTerm = filterTerm
        _hasVisible = False
        _visible_count = 0
        _last_title = None
        for action in self.actions():
            if action.__class__.__name__ != "LauncherSeparator":
                _widget = action.defaultWidget()
                _type = _widget.__class__.__name__
            if not filterTerm:
                # Empty filter. Show all, but handle separator differently.
                action.setVisibility(True)
                _hasVisible = True
            elif _type == "LauncherSearchWidget" or \
                    _type == "LauncherDetachButton":
                # Filter/search and detach are allway visible.

                action.setVisibility(True)

            elif action.__class__.__name__ == "LauncherSeparator":
                action.setVisibility(False)

            elif _type == "LauncherMenuTitle":
                # Visible actions below title are counted. If count > 0 then
                # show last title. Then reset counter and store current title
                # as last.

                if _last_title:
                    _last_title.setVisibility(_visible_count != 0)
                _visible_count = 0
                _last_title = action

            elif _type == "LauncherMenuButton":
                # Recursively filter menus. Show only sub-menus that have
                # visible items.

                _subMenu = action.defaultWidget().menu()
                _subHasVisible = _subMenu.filterMenu(filterTerm)
                action.setVisibility(_subHasVisible)
                if _subHasVisible:
                    _visible_count += 1
                _hasVisible = _hasVisible or _subHasVisible

            elif filterTerm in _widget.text():
                # Filter term is found in the button text. For now filter only
                # cmd buttons.

                if _type == "LauncherCmdButton":
                    action.setVisibility(True)
                    _hasVisible = True
                    _visible_count += 1
                else:
                    action.setVisibility(False)
            else:
                action.setVisibility(False)

            if _last_title:  # Handle last title if exists
                _last_title.setVisibility(_visible_count != 0)

        return _hasVisible

    def showEvent(self, showEvent):
        """Catch event when menu is showed and move it by side of parent.

        Whenever show(), popup(), exec() are called this method is called.
        Move the menu to the left side of the button (default is bellow)
        """
        # TODO handle cases when to close to the edge of screen.
        position = self.pos()
        position.setX(position.x()+self.parent().width())
        position.setY(position.y()-self.parent().height())
        self.move(position)

        # Set focus on first button (skip detach button)
        self.actions()[1].defaultWidget().setFocus()

    def _getRootAncestor(self):
        """Return mainButton from which all menus expand.

        All LauncherMenu menus visualized from the same root menu model
        have lowest common ancestor which is a mainButton of the
        LauncherWindow. If this button is destroyed all menus are also
        destroyed, and all detached menus are closed. Because each Qt element
        holds reference to its parent, mainButton of LauncherWindow can be
        recursively determined.
        """

        _object = self
        while type(_object) is not LauncherWindow:
            _object = _object.parent()
        return _object.mainButton


class LauncherSubMenu(LauncherMenu):

    """Visualization of sub-menu.

    Implements a visualization of the menu when used as a sub menu. Popuped
    from the main menu or button.

    Creates detach button and adds it to the menu.
    """

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)
        self.detachButton = LauncherDetachButton(self)
        self.insertToMenu(self.detachButton, 0)

    def detach(self):
        """Open menu in new window.

        Creates  new menu and opens it as new window. Menu parent should be
        mainButton on launcherWindow. This way it will be closed only if the
        launcher is close or the root menu is changed.
        """

        _launcherWindow = self._getRootAncestor()
        _detachedMenu = LauncherDetachedMenu(self.menuModel, _launcherWindow)
        # Put an existing filter to it and set property to open it as new
        # window.

        _detachedMenu.searchInput.setText(self.filterTerm)
        _detachedMenu.setWindowFlags(Qt.Window | Qt.Tool)
        _detachedMenu.setAttribute(Qt.WA_DeleteOnClose, True)
        _detachedMenu.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        _detachedMenu.setEnabled(True)
        _detachedMenu.show()
        _detachedMenu.move(self.pos().x(), self.pos().y())
        self.hide()


class LauncherDetachedMenu(LauncherMenu):

    """Visualization of detached menu.

    Creates detached menu. Adds find/search input to menu. Also overrides the
    hide() method of the menu, because it should not be hidden  when action
    is performed.

    Removes detach button and filter/search widget but do not add them to
    the menu.
    """

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)
        self.searchInput = LauncherSearchWidget(self, self)
        self.insertToMenu(self.searchInput, 0)

    def hide(self):
        pass  # Detached menu should not be hidden by left arrow.

    def changeEvent(self, changeEvent):
        """Catch when menu window is selected and focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self.searchInput.setFocus()

    def keyPressEvent(self, event):
        """Catch escape (originally closes the menu window) and skip actions."""

        if event.key() == Qt.Key_Escape:
            pass
        else:
            LauncherMenu.keyPressEvent(self, event)


class LauncherMenuWidgetAction(QtGui.QWidgetAction):

    """Wrap widgets to be added to menu.

    When QWidget needs to be appended to QMenu it must be "wrapped" into
    QWidgetAction. This class "wraps" LauncherButton in the same way.
    Further it also implements method to control the visibility of the menu
    item (both action and widget).
    """

    def __init__(self, widget, parent=None):
        QtGui.QWidgetAction.__init__(self, parent)
        self.setDefaultWidget(widget)

    def setVisibility(self, visibility):
        """Set visibility of both the widget action and the widget."""

        self._widget = self.defaultWidget()
        self.setVisible(visibility)
        self._widget.setVisible(visibility)


class LauncherSearchWidget(QtGui.QLineEdit):

    """Filter/search menu widget.

    LauncherSearchWidget is QLineEdit which does filtering of menu items
    recursively by putting the filter  to child menus. When enter button is
    pressed a search window with results is opened (TODO).
    """

    def __init__(self, menu, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        self.textChanged.connect(lambda: menu.filterMenu(self.text()))


class LauncherSeparator(QtGui.QAction):

    """Normal menu separator with a key option (key TODO)."""

    def __init__(self, itemModel, parent=None):
        QtGui.QAction.__init__(self, parent)
        self.setSeparator(True)

    def setVisibility(self, visibility):
        self.setVisible(visibility)


class LauncherMenuTitle(QtGui.QLabel):

    """Passive element with no action and no key focus."""

    def __init__(self, itemModel, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: blue; }")


class LauncherButton(QtGui.QPushButton):

    """Super class for active menu items (buttons).

    Parent class for all active menu items. To recreate the native menu
    behavior (when QActions are used) this class also handles keyboard
    events to navigate through the menu.

    Parent of any LauncherButton must be a QMenu.
    """

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        """Catch key pressed event.

        Catch return and enter key pressed. Send clicked command to execute
        action.

        Catch left arrow button pressed on any of the menu buttons, to hide
        the whole menu (parent) and return to previous level menu.

        Catch right arrow button and skip it.
        """

        if (event.key() == Qt.Key_Return) or (event.key() == Qt.Key_Enter):
            self.click()
        elif event.key() == Qt.Key_Left:
            self.parent().hide()
        elif event.key() == Qt.Key_Right:
            pass
        elif event.key() == Qt.Key_Down:
            self.focusNextChild()
        elif event.key() == Qt.Key_Up:
            self.focusPreviousChild()
        else:
            QtGui.QPushButton.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        self.setFocus()  # Set focus when mouse is over.


class LauncherDetachButton(LauncherButton):

    """Button to detach menu and show it in new window.

    LauncherDetachButton is always shown as first item of popup menu. It
    builds new LauncherMenu from the model of parent menu and opens it in
    a new window.
    """

    def __init__(self, parent=None):
        LauncherButton.__init__(self, parent)
        self.setStyleSheet("""
            QPushButton{
                height: 2px;
                background-color: #666666
            }
            QPushButton:focus {
                background-color: #bdbdbd;
                outline: none
            }
        """)
        self.clicked.connect(parent.detach)


class LauncherNamedButton(LauncherButton):

    """Parent class to all buttons with text."""

    def __init__(self, itemModel, parent=None):
        LauncherButton.__init__(self, parent)
        self.setText(itemModel.text)


class LauncherFileChoiceButton(LauncherNamedButton):

    """Button to change the root menu of the launcher.

    LauncherFileChoiceButton causes the launcher to change the root menu and
    sets new view.
    """

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        self._itemModel = itemModel
        self.clicked.connect(self._changeView)

    @pyqtSlot()
    def _changeView(self):
        """Find LauncherWindow and set new view."""

        _candidate = self
        while _candidate.__class__.__name__ is not "LauncherWindow":
            _candidate = _candidate.parent()
        _candidate.setNewView(self._itemModel.rootMenuFile)
        self.parent().hide()  # When done hide popuped menu.


class LauncherCmdButton(LauncherNamedButton):

    """LauncherCmdButton executes shell command. """

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        self._cmd = itemModel.cmd
        self.clicked.connect(self._executeCmd)

    @pyqtSlot()
    def _executeCmd(self):
        os.system(self._cmd)
        self.parent().hide()  # When done hide popuped menu.


class LauncherMenuButton(LauncherNamedButton):

    """Builds a new model from a view.

    LauncherMenuButton builds new menu from model. When pressed the menu is
    popped up.
    """

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        _menu = LauncherSubMenu(itemModel.subMenu, self)
        self.setMenu(_menu)

    def keyPressEvent(self, event):
        """Submenu can be opened and closed with arrow keys."""

        if event.key() == Qt.Key_Right:
            self.click()
        elif event.key() == Qt.Key_Left:
            self.menu().hide()
        else:
            LauncherNamedButton.keyPressEvent(self, event)


if __name__ == '__main__':

    # Usage: launcher.py menu config
    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('launcher',
                          help="Launcher menu file.")
    argsPars.add_argument('config',
                          help='Launcher configuration file')
    # argsPars.add_argument('LAUNCHER_BASE',
    #                      help='Directory containing launcher menus \
    #                      specifications.')

    args = argsPars.parse_args()

    app = QtGui.QApplication(sys.argv)
    # With no style applied detached menu does not get window frame on SL6

    app.setStyle("cleanlooks")
    app.setStyleSheet("""
            QPushButton{
                background-color: #e9e9e9;
                border-image: none;
                border: none;
                padding: 4px;
                text-align:left;
            }
            QPushButton:focus {
                background-color: #bdbdbd;
                outline: none
            }
            QPushButton:menu-indicator {
                image: url(./images/arrow_bc.png);
                subcontrol-position: right center;
            }
            QLabel{
                background-color: #e9e9e9;
                padding: 4px;
                text-align:left;
            }
            QMenu {
                background-color: #e9e9e9
            }
            QMenu::separator {
                height: 1px;
                background: b0b0b0;
            }
        """)

    rootMenuFile = sys.argv[1]
    cfgFile = sys.argv[2]

    launcherWindow = LauncherWindow(rootMenuFile, cfgFile)
    launcherWindow.setGeometry(0, 0, 150, 0)
    launcherWindow.show()
    sys.exit(app.exec_())
