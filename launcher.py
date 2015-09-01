#!/usr/bin/env python

import sys
import os
import platform
import argparse
import subprocess
import json
import copy
import enum

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot, Qt

from launcher_model import *


class SearchOptions(enum.Enum):

    """ Enum with all search/filter options """

    sensitivity = 0
    text = 1
    cmd = 2


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

        self.menuModel = self._buildMenuModel(rootFilePath)
        self.setWindowTitle(self.menuModel.mainTitle)
        # QMainWindow has predefined layout. Content should be in the central
        # widget. Create widget with a QVBoxLayout and set it as central.

        _mainWidget = QtGui.QWidget(self)
        self._mainLayout = QtGui.QVBoxLayout(_mainWidget)
        self._mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(_mainWidget)
        # Main window consist of filter/serach entry and a main button which
        # pops up the root menu. Create a layout and add the items.

        self._launcherMenu = LauncherSubMenu(self.menuModel, self)
        # self._launcherMenu = LauncherSearchMenuView(self.menuModel, self)
        self.mainButton = LauncherMainButton(self._launcherMenu, self)
        # Create Filter/search item. Add it and main button to the layout.

        self._searchInput = LauncherFilterWidget(self._launcherMenu, self)
        self._mainLayout.addWidget(self._searchInput)
        self._mainLayout.addWidget(self.mainButton)
        # Create menu bar. In current visualization menu bar exposes all
        # LauncherFileChoiceItem items from the model. They are exposed in
        # File menu.

        _menuBar = self.menuBar()
        self._fileMenu = QtGui.QMenu("&File", _menuBar)
        for item in self.menuModel.fileChoices:
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
        del self.menuModel
        self.menuModel = self._buildMenuModel(rootMenuFile)
        self.setWindowTitle(self.menuModel.mainTitle)
        self.mainButton.setText(self.menuModel.mainTitle)
        self._launcherMenu = LauncherSubMenu(self.menuModel, self.mainButton)
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
        self.initFilterVisibility = True
        self.filterConditions = [False, True, False]

    def buildMenu(self, menuModel):
        """Visualize menu

        menuModel has a list of menuItems with models of items. Build buttons
        from it and add them to the menu.
        """
        sectionTitle = None
        for item in self.menuModel.menuItems:
            if item.__class__.__name__ == "LauncherCmdItem":
                self.appendToMenu(LauncherCmdButton(item, sectionTitle, self))
            elif item.__class__.__name__ == "LauncherSubMenuItem":
                self.appendToMenu(LauncherMenuButton(item, sectionTitle, self))
            elif item.__class__.__name__ == "LauncherTitleItem":
                sectionTitle = None
                titleButton = LauncherMenuTitle(item, sectionTitle, self)
                self.appendToMenu(titleButton)
                sectionTitle = titleButton
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

    def setFilterCondition(self, condition, value):
        self.filterConditions[condition.value] = value
        self.filterMenu(self.filterTerm)

    def filterMenu(self, filterTerm=None):
        """Filter menu items with filterTerm

        Shows/hides action depending on filterTerm. Returns true if has
        visible active (buttons) items.
        """

        self.filterTerm = filterTerm
        hasVisible = False
        # Read filters
        sensitivityFilter = self.filterConditions[
            SearchOptions.sensitivity.value]
        textFilter = self.filterConditions[SearchOptions.text.value]
        cmdFilter = self.filterConditions[SearchOptions.cmd.value]

        # Skip first item since it is either search entry or detach button.

        for action in self.actions()[1:len(self.actions())]:
            if action.__class__.__name__ == "LauncherMenuWidgetAction":
                widget = action.defaultWidget()
                widgetType = widget.__class__.__name__
            if not filterTerm:
                # Empty filter. Show depending on type. If submenu recursively
                # empty  filter.

                action.setVisibility(self.initFilterVisibility)
                if widgetType == "LauncherMenuButton":
                    action.defaultWidget().menu().filterMenu(filterTerm)
            elif widgetType == "LauncherMenuTitle":
                action.setVisibility(False)
            elif widgetType == "LauncherSubMenuAsTitle":
                action.setVisibility(False)
            elif widgetType == "LauncherMenuButton":
                # Recursively filter menus. Show only sub-menus that have
                # visible items.

                subMenu = action.defaultWidget().menu()
                subHasVisible = subMenu.filterMenu(filterTerm)
                hasVisible = hasVisible or subHasVisible
                action.setVisibility(subHasVisible)
            elif self.filterConditions[SearchOptions.text.value] and\
                    widget.text().contains(filterTerm, self.filterConditions[
                        SearchOptions.sensitivity.value]):
                # Filter term is found in the button text. For now filter only
                # cmd buttons.

                action.setVisibility(True)
                hasVisible = True
            elif textFilter and widget.text().contains(filterTerm,
                                                       sensitivityFilter):
                action.setVisibility(True)
                hasVisible = True
            elif widgetType == "LauncherCmdButton" and cmdFilter and\
                QtCore.QString(widget.cmd).contains(filterTerm,
                                                    sensitivityFilter):

                action.setVisibility(True)
                hasVisible = True
            else:
                action.setVisibility(False)
        return hasVisible

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

    def getRootAncestor(self):
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
        mainButton on main window. This way it will be closed only if the
        launcher is close or the root menu is changed.
        """

        detachedMenu = LauncherDetachedMenu(self.menuModel,
                                            self.getRootAncestor())
        # Put an existing filter to it and set property to open it as new
        # window.

        detachedMenu.setWindowTitle(self.menuModel.mainTitle)
        detachedMenu.searchInput.setText(self.filterTerm)
        detachedMenu.setWindowFlags(Qt.Window | Qt.Tool)
        detachedMenu.setAttribute(Qt.WA_DeleteOnClose, True)
        detachedMenu.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        detachedMenu.setEnabled(True)
        detachedMenu.show()
        detachedMenu.move(self.pos().x(), self.pos().y())
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
        self.searchInput = LauncherFilterWidget(self, self)
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
        self.searchWidget = LauncherSearchWidget(self)  # TODO add parent
        self.insertToMenu(self.searchWidget, 0)
        self.initFilterVisibility = False

    def buildMenu(self, menuModel):
        """Visualize menu

        Override this method and build different visualization.
        """
        cMenuItems = list(self.menuModel.menuItems)
        level = 0
        sectionTitle = None
        levelTitle = None
        for item in cMenuItems:
            levelPrefix = ""
            for i in xrange(0, item.parent.level):
                levelPrefix = "> " + levelPrefix
            if item.__class__.__name__ == "LauncherCmdItem":
                button = LauncherCmdButton(item, sectionTitle, self)
                self.appendToMenu(button)
            elif item.__class__.__name__ == "LauncherSubMenuItem":
                button = LauncherSubMenuAsTitle(
                    item, sectionTitle, self)
                self.appendToMenu(button)
                # Take subemnu model and build (visualize) it below

                levelTitle = button
                cSubMenuItems = copy.copy(item.subMenu.menuItems)
                index = cMenuItems.index(item) + 1
                cMenuItems[index:index] = cSubMenuItems
            elif item.__class__.__name__ == "LauncherTitleItem":
                button = LauncherMenuTitle(item, levelTitle, self)
                self.appendToMenu(button)
                sectionTitle = button

            if item.__class__.__name__ == "LauncherItemSeparator":
                self.addAction(LauncherSeparator(item, self))
            else:  # Add level prefix
                button.setText(levelPrefix + button.text())

    def exposeMenu(self, searchInput=None):
        """Open menu in new window.

        Creates  new menu and opens it as new window. Menu parent should be
        mainButton on launcherWindow. This way it will be closed only if the
        launcher is close or the root menu is changed.
        """

        self.setWindowTitle("Search")
        self.searchWidget.setText(searchInput)
        self.filterMenu(searchInput)
        self.setWindowFlags(Qt.Window | Qt.Tool)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        self.setEnabled(True)
        self.show()
        # self.move(self.pos().x(), self.pos().y()) TODO


class LauncherMenuWidgetAction(QtGui.QWidgetAction):

    """Wrap widgets to be added to menu.

    When QWidget needs to be appended to QMenu it must be "wrapped" into
    QWidgetAction. This class "wraps" LauncherButton in the same way.
    Further it also implements method to control the visibility of the menu
    item (both action and widget).
    """

    def __init__(self, widget, parent=None):
        QtGui.QWidgetAction.__init__(self, parent)
        self.widget = widget
        self.setDefaultWidget(self.widget)
        widget.setMyAction(self)  # Let widget know about action.

    def setVisibility(self, visibility):
        """Set visibility of both the widget action and the widget."""

        self.setVisible(visibility)
        self.widget.setVisible(visibility)
        if self.widget.sectionTitle and visibility:
            self.widget.sectionTitle.myAction.setVisibility(True)


class LauncherSearchWidget(QtGui.QWidget):

    """ Search menu widget

    Container with all visual elements to do a search. Some options are
    available as check boxes.
    """

    def __init__(self, menu, parent=None):
        QtGui.QWidget.__init__(self, parent)
        mainLayout = QtGui.QVBoxLayout(self)
        mainLayout.setMargin(0)
        self.setLayout(mainLayout)
        # Prepare components and add them to layout:
        #    - search field
        #    - options (case sensitive)
        #    - filters (text, cmd)
        #    - menu

        self.searchInput = LauncherFilterLineEdit(menu, self)
        caseSensitive = QtGui.QCheckBox("Case sensitive", self)
        caseSensitive.setChecked(False)
        menu.setFilterCondition(SearchOptions.sensitivity,
                                caseSensitive.isChecked())
        mainLayout.addWidget(self.searchInput)
        mainLayout.addWidget(caseSensitive)
        options = QtGui.QWidget(self)
        optionsLayout = QtGui.QHBoxLayout(options)
        searchText = QtGui.QCheckBox("Title search", options)
        searchText.setChecked(True)
        menu.setFilterCondition(SearchOptions.text, searchText.isChecked())
        searchCmd = QtGui.QCheckBox("Command search", options)
        searchCmd.setChecked(False)
        menu.setFilterCondition(SearchOptions.cmd, searchCmd.isChecked())
        optionsLayout.addWidget(searchText)
        optionsLayout.addWidget(searchCmd)
        options.setLayout(optionsLayout)
        mainLayout.addWidget(options)

        self.myAction = None
        self.searchInput.setPlaceholderText("Enter search term.")
        caseSensitive.stateChanged.connect(lambda: menu.setFilterCondition(
            SearchOptions.sensitivity, caseSensitive.isChecked()))
        searchText.stateChanged.connect(
            lambda: menu.setFilterCondition(SearchOptions.text,
                                            searchText.isChecked()))
        searchCmd.stateChanged.connect(
            lambda: menu.setFilterCondition(SearchOptions.cmd,
                                            searchCmd.isChecked()))

    def setText(self, text):
        self.searchInput.setText(text)

    def setMyAction(self, action):
        self.myAction = action


class LauncherFilterLineEdit(QtGui.QLineEdit):

    """Extended line edit tool.

    LauncherFilterLineEdit is QLineEdit which does filtering of menu items
    recursively by putting the filter  to child menus. It has a button to clear
    current input with one click. When enter button is pressed a search window
    with results is opened.
    """

    def __init__(self, menu, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        self.textChanged.connect(lambda: menu.filterMenu(self.text()))
        self.myAction = None
        self.setPlaceholderText("Enter filter term.")
        self.menu = menu
        # Create button to clear text and add it to the right edge of the
        # input.

        self.clearButton = QtGui.QToolButton(self)
        self.clearButton.resize(30, 30)
        self.setTextMargins(0, 0, 30, 0)
        icon = QtGui.QIcon("./images/delete-2x.png")
        self.clearButton.setIcon(icon)
        self.clearButton.setStyleSheet("background-color: transparent;")

        position = QtCore.QPoint(self.pos().x()+self.width(), 0)
        self.clearButton.move(position)
        self.clearButton.setCursor(Qt.ArrowCursor)
        self.clearButton.clicked.connect(lambda: self.clear())

    def setMyAction(self, action):
        self.myAction = action

    def resizeEvent(self, event):
        position = QtCore.QPoint(self.pos().x()+self.width() -
                                 self.clearButton.width(), 0)
        self.clearButton.move(position)


class LauncherFilterWidget(LauncherFilterLineEdit):

    """ Filter menu widget which opens search when return is pressed """

    def __init__(self, menu, parent=None):
        LauncherFilterLineEdit.__init__(self, menu, parent)

    def keyPressEvent(self, event):
        """Catch key pressed event.

        Catch return and enter key pressed and open search in new window.
        """

        if (event.key() == Qt.Key_Return) or (event.key() == Qt.Key_Enter):
            # Do a search on full menu (root menu).

            mainButton = self.menu.getRootAncestor()
            menu = mainButton.menu()
            searchMenu = LauncherSearchMenuView(menu.menuModel, launcherWindow)
            searchMenu.exposeMenu(self.text())
        # TODO set other  cases

        # elif event.key() == Qt.Key_Left:
        #    self.parent().hide()
        # elif event.key() == Qt.Key_Right:
        #    pass
        # elif event.key() == Qt.Key_Down:
        #    _candidate = self.nextInFocusChain()
        #    while isinstance(_candidate, LauncherMenuTitle):
        #        _candidate.focusNextChild()
        #        _candidate = _candidate.nextInFocusChain()
        #    _candidate.focusNextChild()
        # elif event.key() == Qt.Key_Up:
        #    _candidate = self.previousInFocusChain()
        #    while isinstance(_candidate, LauncherMenuTitle):
        #        _candidate.focusPreviousChild()
        #        _candidate = _candidate.previousInFocusChain()
        #    _candidate.focusPreviousChild()
        else:
            QtGui.QLineEdit.keyPressEvent(self, event)


class LauncherSeparator(QtGui.QAction):

    """Normal menu separator with a key option (key TODO)."""

    def __init__(self, itemModel, parent=None):
        QtGui.QAction.__init__(self, parent)
        self.setSeparator(True)

    def setVisibility(self, visibility):
        self.setVisible(visibility)


class LauncherMenuTitle(QtGui.QLabel):

    """Passive element with no action and no key focus."""

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: blue; }")
        self.myAction = None
        # For title element sectionTitle is menu button that owns menu with
        # this element.

        self.sectionTitle = sectionTitle

    def setMyAction(self, action):
        self.myAction = action


class LauncherSubMenuAsTitle(QtGui.QLabel):

    """Menu button as title

    Passive element with no action and no key focus.Used only in
    LauncherSearchMenuView"""

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: red; }")
        self.myAction = None
        self.sectionTitle = sectionTitle

    def setMyAction(self, action):
        self.myAction = action


class LauncherButton(QtGui.QPushButton):

    """Super class for active menu items (buttons).

    Parent class for all active menu items. To recreate the native menu
    behavior (when QActions are used) this class also handles keyboard
    events to navigate through the menu.

    Parent of any LauncherButton must be a QMenu and it must be paired with
    a LauncherMenuWidgetAction.
    """

    def __init__(self, sectionTitle=None, parent=None):
        QtGui.QPushButton.__init__(self, parent)
        self.setMouseTracking(True)
        self._parent = parent
        self.myAction = None
        self.sectionTitle = sectionTitle

        self.contextMenu = QtGui.QMenu(self)

    def contextMenuEvent(self, event):
        """ Show context menu if context exists"""

        if self.contextMenu.actions():
            self.contextMenu.exec_(QtGui.QCursor.pos())

    def setMyAction(self, action):
        self.myAction = action

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
        self._parent.setActiveAction(self.myAction)


class LauncherDetachButton(LauncherButton):

    """Button to detach menu and show it in new window.

    LauncherDetachButton is always shown as first item of popup menu. It
    builds new LauncherMenu from the model of parent menu and opens it in
    a new window.
    """

    def __init__(self, parent=None):
        LauncherButton.__init__(self, None, parent)
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

    def __init__(self, menu, parent=None):
        LauncherButton.__init__(self, None, parent)
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

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherButton.__init__(self, sectionTitle, parent)
        self.setText(itemModel.text)

        if itemModel.help_link:
            helpAction = QtGui.QAction("&Help", self)
            helpAction.setData(itemModel.help_link)
            self.contextMenu.addAction(helpAction)
            helpAction.triggered.connect(self.todo)

    def todo(self):

        url = QtCore.QUrl(
            self.sender().data().toString(), QtCore.QUrl.TolerantMode)
        QtGui.QDesktopServices.openUrl(url)


class LauncherFileChoiceButton(LauncherNamedButton):

    """Button to change the root menu of the launcher.

    LauncherFileChoiceButton causes the launcher to change the root menu and
    sets new view.
    """

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, None, parent)
        self._itemModel = itemModel
        self.clicked.connect(self.changeView)

    @pyqtSlot()
    def changeView(self):
        """Find LauncherWindow and set new view."""

        _candidate = self
        while _candidate.__class__.__name__ is not "LauncherWindow":
            _candidate = _candidate.parent()
        _candidate.setNewView(self._itemModel.rootMenuFile)
        self.parent().hide()  # When done hide popuped menu.


class LauncherCmdButton(LauncherNamedButton):

    """LauncherCmdButton executes shell command. """

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, sectionTitle, parent)
        self.cmd = itemModel.cmd
        self.clicked.connect(self.executeCmd)
        if itemModel.tip == None:
            toolTip = "Command: " + self.cmd
        else:
            toolTip = itemModel.tip
        self.setToolTip(toolTip)

    @pyqtSlot()
    def executeCmd(self):
        subprocess.Popen(self.cmd, stdout=subprocess.PIPE, shell=True)
        self.parent().hide()  # When done hide popuped menu.


class LauncherMenuButton(LauncherNamedButton):

    """Builds a new view from model.

    LauncherMenuButton builds new menu from model. When pressed the menu is
    popped up.
    """

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, sectionTitle, parent)
        menu = LauncherSubMenu(itemModel.subMenu, self)
        self.setMenu(menu)
        if itemModel.tip == None:
            toolTip = "Menu: " + menu.menuModel.mainTitle
        else:
            toolTip = itemModel.tip
        self.setToolTip(toolTip)

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

    # app.setStyle("cleanlooks")
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
                image: url(images/caret-right.png);
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
