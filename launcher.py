#!/usr/bin/env python

import sys
import os
import platform
import argparse
import subprocess
import json
import copy

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot, Qt

from launcher_model import *


class LauncherWindow(QtGui.QMainWindow):

    """Launcher main window.

    Main launcher window. At initialization recursively builds visualization
    of launcher menus, builds menu bar, ...
    """

    def __init__(self, rootFilePath, cfgFilePath, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        try:
            _cfgFile = open(cfgFilePath)
        except IOError:
            _errMsg = "Err: Configuration file \"" + cfgFilePath + \
                "\" not found."
            sys.exit(_errMsg)
        _cfg = json.load(_cfgFile)
        _cfgFile.close()
        # Get configuration for current system. platform.system() returns:
        #     - "Darwin" when OS X
        #     - "Linux" when Linux
        #     - "Windows" when Windows

        systemType = platform.system()
        if systemType == "Darwin":
            systemType = "OS_X"
        self.launcherCfg = _cfg.get(systemType)
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

        self._launcherMenu = LauncherSubMenu(self._menuModel, self)
        ########self._launcherMenu = LauncherSearchMenuView(self._menuModel, self)
        self.mainButton = LauncherMainButton(self._launcherMenu, self)
        # Create Filter/search item. Add it and main button to the layout.

        self._searchInput = LauncherSearchWidget(self._launcherMenu, self)
        self._mainLayout.addWidget(self._searchInput)
        self._mainLayout.addWidget(self.mainButton)
        # Create menu bar. In current visualization menu bar exposes all
        # LauncherFileChoiceItem items from the model. They are exposed in
        # File menu.

        _menuBar = self.menuBar()
        self._fileMenu = QtGui.QMenu("&File", _menuBar)
        for item in self._menuModel.fileChoices:
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
        _rootMeniFullPath = os.path.join(self.launcherCfg.get("launcher_base"),
                                         rootMenuPath)
        try:
            _rootMenuFile = open(_rootMeniFullPath)
        except IOError:
            _errMsg = "Err: File \"" + rootMenuPath + "\" not found."
            sys.exit(_errMsg)
        _rootMenu = LauncherMenuModel(_rootMenuFile, 0, self.launcherCfg)
        _rootMenuFile.close()
        return _rootMenu


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
        self.buildMenu(self.menuModel.menuItems)

    def buildMenu(self, menuModel):
        """Visualize menu

        menuModel has a list of menuItems with models of items. Build buttons
        from it and add them to the menu.
        """
        group = list()
        for item in self.menuModel.menuItems:
            if item.__class__.__name__ == "LauncherCmdItem":
                self.appendToMenu(LauncherCmdButton(item, group, self))
            elif item.__class__.__name__ == "LauncherSubMenuItem":
                self.appendToMenu(LauncherMenuButton(item, group, self))
            elif item.__class__.__name__ == "LauncherTitleItem":
                group = []
                titleButton = LauncherMenuTitle(item, group, self)
                self.appendToMenu(titleButton)
                group.append(titleButton)
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
        # Skip first item since it is either search entry or detach button.

        for action in self.actions()[1:len(self.actions())]:
            if action.__class__.__name__ == "LauncherMenuWidgetAction":
                _widget = action.defaultWidget()
                _type = _widget.__class__.__name__

            if not filterTerm:
                # Empty filter. Show all. If submenu recursively empty  filter.
                action.setVisibility(True)
                if _type == "LauncherMenuButton":
                    action.defaultWidget().menu().filterMenu(filterTerm)

            elif _type == "LauncherMenuTitle":
                # Visible actions below title are counted. If count > 0 then
                # show last title. Then reset counter and store current title
                # as last.

                action.setVisibility(False)

            elif _type == "LauncherMenuButton":
                # Recursively filter menus. Show only sub-menus that have
                # visible items.

                _subMenu = action.defaultWidget().menu()
                _subHasVisible = _subMenu.filterMenu(filterTerm)
                action.setVisibility(_subHasVisible)
                if _subHasVisible:
                    for item in _widget.group:
                        item._myAction.setVisibility(True)

            elif _widget.text().contains(filterTerm, Qt.CaseInsensitive):
                # Filter term is found in the button text. For now filter only
                # cmd buttons.

                action.setVisibility(True)
                _hasVisible = True
                for item in _widget.group:
                    item._myAction.setVisibility(True)

            else:
                action.setVisibility(False)
        return _hasVisible

    def showEvent(self, showEvent):
        """Catch event when menu is shown and move it by side of parent.

        Whenever show(), popup(), exec() are called this method is called.
        Move the menu to the left side of the button (default is bellow)
        """
        # TODO handle cases when to close to the edge of screen.
        position = self.pos()
        position.setX(position.x()+self.parent().width())
        position.setY(position.y()-self.parent().height())
        self.move(position)

        # Set focus on first button (skip detach button and titles)
        i = 1
        while isinstance(self.actions()[i].defaultWidget(),
                         LauncherMenuTitle):
            i += 1
        self.actions()[i].defaultWidget().setFocus()
        self.setActiveAction(self.actions()[i])

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
        self.detachButton = LauncherDetachButton(None, self)
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
        _detachedMenu.setWindowTitle(self.menuModel.mainTitle)
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
        """Catch escape (originally closes the window) and skip actions."""

        if event.key() == Qt.Key_Escape:
            pass
        else:
            LauncherMenu.keyPressEvent(self, event)


class LauncherSearchMenuView(LauncherMenu):

    """Search view

    A bit different visualization (without submenus) of menu for searching.
    """

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)

    def buildMenu(self, menuModel):
        """Visualize menu

        Override this method and build diffrent visualization.
        """
        cMenuItems = copy.copy(self.menuModel.menuItems)
        level = 0
        for item in cMenuItems:
            for i in xrange(0, item.parent.level):
                if item.__class__.__name__ != "LauncherItemSeparator":
                    item.text = "> " + item.text
            if item.__class__.__name__ == "LauncherCmdItem":
                self.appendToMenu(LauncherCmdButton(item, None, self))
            elif item.__class__.__name__ == "LauncherSubMenuItem":
                self.appendToMenu(LauncherSubMenuAsTitle(item, None, self))
                # Take subemnu model and build (visualize) it below

                cSubMenuItems = copy.copy(item.subMenu.menuItems)
                index = cMenuItems.index(item) + 1
                cMenuItems[index:index] = cSubMenuItems
            elif item.__class__.__name__ == "LauncherTitleItem":
                self.appendToMenu(LauncherMenuTitle(item, None, self))
            elif item.__class__.__name__ == "LauncherItemSeparator":
                self.addAction(LauncherSeparator(item, self))

    def filterMenu(self, filterTerm=None):
        """Filter menu items with filterTerm

        Shows/hides action depending on filterTerm. Returns true if has
        visible active (buttons) items.
        """

        self.filterTerm = filterTerm
        _hasVisible = False
        _visible_count = 0
        _last_title = None
        # Skip first item since it is either search entry or detach button.

        for action in self.actions()[1:len(self.actions())]:
            if action.__class__.__name__ == "LauncherMenuWidgetAction":
                _widget = action.defaultWidget()
                _type = _widget.__class__.__name__

            if not filterTerm:
                action.setVisibility(False)  # Hide all

            elif _type == "LauncherMenuTitle":
                # Visible actions below title are counted. If count > 0 then
                # show last title. Then reset counter and store current title
                # as last.

                if _last_title:
                    _last_title.setVisibility(_visible_count != 0)
                _visible_count = 0
                _last_title = action

            elif _type == "LauncherSubMenuAsTitle":
                # Visible actions form the submenu (are counted). The rest
                # of logic is same as form LauncherMenuTitle

                action.setVisibility(False)

            elif _widget.text().contains(filterTerm, Qt.CaseInsensitive):
                # Filter term is found in the button text. For now filter only
                # cmd buttons.

                action.setVisibility(True)
                _hasVisible = True
                _visible_count += 1
            else:
                action.setVisibility(False)

            if _last_title:  # Handle last title if exists
                _last_title.setVisibility(_visible_count != 0)

        return _hasVisible


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
        widget.setMyAction(self)  # Let widget know about action.

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
        self._myAction = None
        # Not supported on Qt 4.6.2
        self.setPlaceholderText("Enter filter term.")

    def setMyAction(self, action):
        self._myAction = action


class LauncherSeparator(QtGui.QAction):

    """Normal menu separator with a key option (key TODO)."""

    def __init__(self, itemModel, parent=None):
        QtGui.QAction.__init__(self, parent)
        self.setSeparator(True)

    def setVisibility(self, visibility):
        self.setVisible(visibility)


class LauncherMenuTitle(QtGui.QLabel):

    """Passive element with no action and no key focus."""

    def __init__(self, itemModel, group=None, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: blue; }")
        self._myAction = None
        # Group is list of "parent" items such as menu title and
        # menu button. This list enables visualization when filtering
        # or searching. TODO write better comment

        self.group = group

    def setMyAction(self, action):
        self._myAction = action


class LauncherSubMenuAsTitle(QtGui.QLabel):

    """Menu button as title

    Passive element with no action and no key focus.Used only in
    LauncherSearchMenuView"""

    def __init__(self, itemModel, group=None, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: red; }")
        self._myAction = None
        self.group = group

    def setMyAction(self, action):
        self._myAction = action


class LauncherButton(QtGui.QPushButton):

    """Super class for active menu items (buttons).

    Parent class for all active menu items. To recreate the native menu
    behavior (when QActions are used) this class also handles keyboard
    events to navigate through the menu.

    Parent of any LauncherButton must be a QMenu and it must be paired with
    a LauncherMenuWidgetAction.
    """

    def __init__(self, group=None, parent=None):
        QtGui.QPushButton.__init__(self, parent)
        self.setMouseTracking(True)
        self._parent = parent
        self._myAction = None
        self.group = group

    def setMyAction(self, action):
        self._myAction = action

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
            _candidate = self.nextInFocusChain()
            while isinstance(_candidate, LauncherMenuTitle):
                _candidate.focusNextChild()
                _candidate = _candidate.nextInFocusChain()
            _candidate.focusNextChild()
        elif event.key() == Qt.Key_Up:
            _candidate = self.previousInFocusChain()
            while isinstance(_candidate, LauncherMenuTitle):
                _candidate.focusPreviousChild()
                _candidate = _candidate.previousInFocusChain()
            _candidate.focusPreviousChild()
        else:
            QtGui.QPushButton.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        self.setFocus()
        self._parent.setActiveAction(self._myAction)


class LauncherDetachButton(LauncherButton):

    """Button to detach menu and show it in new window.

    LauncherDetachButton is always shown as first item of popup menu. It
    builds new LauncherMenu from the model of parent menu and opens it in
    a new window.
    """

    def __init__(self, group=None, parent=None):
        LauncherButton.__init__(self, group, parent)
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


class LauncherMainButton(LauncherButton):

    """ Main Launcher button to expand menu

    This class extends LauncherButton similar as LauncherMenuButton, but
    with a different inputs.
    """

    def __init__(self, menu, group=None, parent=None):
        LauncherButton.__init__(self, group, parent)
        self.setText(menu.menuModel.mainTitle)
        self.setMenu(menu)

    def mouseMoveEvent(self, event):
        self.setFocus()

    def keyPressEvent(self, event):
        """Open main menu

        Open menu also with right arrow key. Override option to hide parent 
        with left arrow key, because main button is not part of popuped window.
        """

        if event.key() == Qt.Key_Right:
            self.click()
        elif event.key() == Qt.Key_Left:
            pass
        else:
            LauncherButton.keyPressEvent(self, event)


class LauncherNamedButton(LauncherButton):

    """Parent class to all buttons with text."""

    def __init__(self, itemModel, group=None, parent=None):
        LauncherButton.__init__(self, group, parent)
        self.setText(itemModel.text)


class LauncherFileChoiceButton(LauncherNamedButton):

    """Button to change the root menu of the launcher.

    LauncherFileChoiceButton causes the launcher to change the root menu and
    sets new view.
    """

    def __init__(self, itemModel, group=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, group, parent)
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

    def __init__(self, itemModel, group=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, group, parent)
        self._cmd = itemModel.cmd
        self.clicked.connect(self._executeCmd)

    @pyqtSlot()
    def _executeCmd(self):
        subprocess.Popen(self._cmd, stdout=subprocess.PIPE, shell=True)
        self.parent().hide()  # When done hide popuped menu.


class LauncherMenuButton(LauncherNamedButton):

    """Builds a new view from model.

    LauncherMenuButton builds new menu from model. When pressed the menu is
    popped up.
    """

    def __init__(self, itemModel, group=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, group, parent)
        _menu = LauncherSubMenu(itemModel.subMenu, self)
        self.setMenu(_menu)

    def keyPressEvent(self, event):
        """Submenu can also be opened with right arrow key."""

        if event.key() == Qt.Key_Right:
            self.click()
        else:
            LauncherNamedButton.keyPressEvent(self, event)


if __name__ == '__main__':

    # Usage: launcher.py menu config
    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('launcher',
                          help="Launcher menu file.")
    argsPars.add_argument('config',
                          help='Launcher configuration file')

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
                background: #b0b0b0;
            }
        """)

    rootMenuFile = sys.argv[1]
    cfgFile = os.path.normpath(sys.argv[2])

    launcherWindow = LauncherWindow(rootMenuFile, cfgFile)
    launcherWindow.setGeometry(0, 0, 150, 0)
    launcherWindow.show()
    sys.exit(app.exec_())
