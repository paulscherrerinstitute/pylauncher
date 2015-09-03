#!/usr/bin/env python

import sys
import os
import platform
import argparse
import subprocess
import json
import copy
import enum
import urllib2

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot, Qt

from launcher_model import *


class SearchOptions(enum.Enum):

    """ Enum with all search/filter options """

    sensitivity = 0
    text = 1
    cmd = 2


class LauncherViewMenu(QtGui.QMenu):

    def __int__(self, text, parent=None):
        QtGui.QMenu.__init__(self, text, parent)

    def buildViewMenu(self, menuModel):
        self.clear()
        for view in menuModel.file_choices:
            button = LauncherFileChoiceButton(view, self)
            buttonAction = QtGui.QWidgetAction(self)
            buttonAction.setDefaultWidget(button)
            self.addAction(buttonAction)


class LauncherWindow(QtGui.QMainWindow):

    """Launcher main window.

    Main launcher window. At initialization recursively builds visualization
    of launcher menus, builds menu bar, ...
    """

    def __init__(self, rootFilePath, cfgFilePath, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        try:
            cfgFile = open_launcher_file(cfgFilePath)
        except IOError:
            errMsg = "Err: Configuration file \"" + cfgFilePath + \
                "\" not found."
            sys.exit(errMsg)
        cfg = json.load(cfgFile)
        cfgFile.close()
        # Get configuration for current system. platform.system() returns:
        #     - "Darwin" when OS X
        #     - "Linux" when Linux
        #     - "Windows" when Windows

        systemType = platform.system()
        if systemType == "Darwin":
            systemType = "OS_X"
        self.launcherCfg = cfg.get(systemType)
        # Load default theme

        style_file = open_launcher_file(
            self.launcherCfg.get("theme_base") + "default.qss")
        self.setStyleSheet(style_file.read())
        style_file.close()
        # Build menu model from rootMenuFile and set general parameters.

        self.menuModel = self.buildMenuModel(rootFilePath)
        self.setWindowTitle(self.menuModel.mainTitle)
        # QMainWindow has predefined layout. Content should be in the central
        # widget. Create widget with a QVBoxLayout and set it as central.

        mainWidget = QtGui.QWidget(self)
        self.mainLayout = QtGui.QVBoxLayout(mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(mainWidget)
        # Main window consist of filter/serach entry and a main button which
        # pops up the root menu. Create a layout and add the items.

        self.launcherMenu = LauncherSubMenu(self.menuModel, self)
        self.mainButton = LauncherMainButton(self.launcherMenu, self)
        # Create Filter/search item. Add it and main button to the layout.

        self.searchInput = LauncherFilterWidget(self.launcherMenu, self)
        self.mainLayout.addWidget(self.searchInput)
        self.mainLayout.addWidget(self.mainButton)
        # Create menu bar. In current visualization menu bar exposes all
        # LauncherFileChoiceItem items from the model. They are exposed in
        # File menu.

        menuBar = self.menuBar()
        self.viewMenu = LauncherViewMenu("&View", menuBar)
        self.viewMenu.buildViewMenu(self.menuModel)
        menuBar.addMenu(self.viewMenu)

    def setNewView(self, rootMenuFile):
        """Rebuild launcher from new config file.

        Destroy previous model and create new one. Build menus and edit main
        window elements.
        """
        del self.menuModel
        self.menuModel = self.buildMenuModel(rootMenuFile)
        self.setWindowTitle(self.menuModel.mainTitle)
        self.mainButton.setText(self.menuModel.mainTitle)
        # TODO restyle main Button
        del self.launcherMenu
        self.launcherMenu = LauncherSubMenu(self.menuModel, self.mainButton)
        self.mainButton.setMenu(self.launcherMenu)
        self.viewMenu.buildViewMenu(self.menuModel)

    def changeEvent(self, changeEvent):
        """Catch when main window is selected and set focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self.searchInput.setFocus()

    def buildMenuModel(self, rootMenuPath):
        """Return model of a menu defined in rootMenuFile."""

        rootMeniFullPath = os.path.join(self.launcherCfg.get("launcher_base"),
                                        rootMenuPath)
        try:
            rootMenuFile = open_launcher_file(rootMeniFullPath)
        except IOError:
            errMsg = "Err: File \"" + rootMenuPath + "\" not found."
            sys.exit(errMsg)
        rootMenu = launcher_menu_model(None, rootMenuFile, 0, self.launcherCfg)
        rootMenuFile.close()
        return rootMenu


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
        self.buildMenu(self.menuModel.menu_items)
        self.initFilterVisibility = True
        self.filterConditions = [False, True, False]

    def buildMenu(self, menuModel):
        """Visualize menu

        menuModel has a list of menu_items with models of items. Build buttons
        from it and add them to the menu.
        """
        sectionTitle = None
        for item in self.menuModel.menu_items:
            if item.__class__.__name__ == "launcher_cmd_item":
                self.appendToMenu(LauncherCmdButton(item, sectionTitle, self))
            elif item.__class__.__name__ == "launcher_sub_menu_item":
                self.appendToMenu(LauncherMenuButton(item, sectionTitle, self))
            elif item.__class__.__name__ == "launcher_title_item":
                sectionTitle = None
                titleButton = LauncherMenuTitle(item, sectionTitle, self)
                self.appendToMenu(titleButton)
                sectionTitle = titleButton
            elif item.__class__.__name__ == "launcher_item_separator":
                self.addAction(LauncherSeparator(item, self))

    def appendToMenu(self, widget):
        """Append action to menu.

        Create widget action for widget. Pair them and add to the menu.
        """

        self.action = LauncherMenuWidgetAction(widget, self)
        self.addAction(self.action)

    def insertToMenu(self, widget, index):
        """Insert action to specified position in menu.

        Create widget action for widget. Pair them and insert them to the
        specified position in menu.
        """

        self.action = LauncherMenuWidgetAction(widget, self)
        if self.actions()[index]:
            self.insertAction(self.actions()[index], self.action)
        else:
            self.addAction(self.action)

    def setFilterCondition(self, condition, value):
        """ Set one condition to given value."""

        self.filterConditions[condition.value] = value
        self.filterMenu(self.filterTerm)

    def filterMenu(self, filterTerm=None):
        """Filter menu items with filterTerm

        Shows/hides menu items depending on filterTerm. Returns true if has
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
        # TODO bug: not on right position. Because of styles inheritance, the
        # "parent button cannot be a parent. It must be e.g a parent menu"
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

    def getLauncherWindow(self):
        """ Search and return application main window object"""

        candidate = self
        while type(candidate) is not LauncherWindow:
            candidate = candidate.parent()

        return candidate

    def getMainMenu(self):
        """Return menu of mainButton from which all menus expand.

        All LauncherMenu menus visualized from the same root menu model
        have lowest common ancestor which is a menu of mainButton. If this menu
        is destroyed all other are also destroyed, and all detached menus are
        closed. Because each Qt element holds reference to its parent, this
        menu can be recursively determined.
        """

        return self.getLauncherWindow().mainButton.menu()


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
                                            self.getMainMenu())
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
        pass  # Detached menu should not be hidden at any action (left key).

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

    Different visualization of launcher for searching. Submenues do not
    expand, but are rather included at the bottom of the list.
    """

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)
        self.searchWidget = LauncherSearchWidget(self, self.getMainMenu())
        self.insertToMenu(self.searchWidget, 0)
        self.initFilterVisibility = False

    def buildMenu(self, menuModel):
        """Visualize menu

        Override this method and build different visualization.
        """
        cMenuItems = list(self.menuModel.menu_items)
        level = 0
        sectionTitle = None
        levelTitle = None
        for item in cMenuItems:
            levelPrefix = ""
            addPrefix = False
            for traceItem in item.trace:
                levelPrefix = levelPrefix + traceItem.text + " > "
            if item.__class__.__name__ == "launcher_cmd_item":
                button = LauncherCmdButton(item, sectionTitle, self)
                self.appendToMenu(button)
                addPrefix = True
            elif item.__class__.__name__ == "launcher_sub_menu_item":
                button = LauncherSubMenuAsTitle(
                    item, sectionTitle, self)
                self.appendToMenu(button)
                # Take subemnu model and build (visualize) it below

                levelTitle = button
                cSubMenuItems = copy.copy(item.sub_menu.menu_items)
                index = cMenuItems.index(item) + 1
                cMenuItems[index:index] = cSubMenuItems
            elif item.__class__.__name__ == "launcher_title_item":
                button = LauncherMenuTitle(item, levelTitle, self)
                self.appendToMenu(button)
                sectionTitle = button
            elif item.__class__.__name__ == "launcher_item_separator":
                self.addAction(LauncherSeparator(item, self))

            if addPrefix:  # Add level prefix
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
        caseSensitive.stateChanged.connect(lambda: menu.setFilterCondition(
            SearchOptions.sensitivity, caseSensitive.isChecked()))
        menu.setFilterCondition(SearchOptions.sensitivity,
                                caseSensitive.isChecked())
        mainLayout.addWidget(self.searchInput)
        mainLayout.addWidget(caseSensitive)
        options = QtGui.QWidget(self)
        optionsLayout = QtGui.QHBoxLayout(options)
        searchText = QtGui.QCheckBox("Title search", options)
        searchText.setChecked(True)
        searchText.stateChanged.connect(
            lambda: menu.setFilterCondition(SearchOptions.text,
                                            searchText.isChecked()))
        menu.setFilterCondition(SearchOptions.text, searchText.isChecked())
        searchCmd = QtGui.QCheckBox("Command search", options)
        searchCmd.setChecked(False)
        searchCmd.stateChanged.connect(
            lambda: menu.setFilterCondition(SearchOptions.cmd,
                                            searchCmd.isChecked()))
        menu.setFilterCondition(SearchOptions.cmd, searchCmd.isChecked())
        optionsLayout.addWidget(searchText)
        optionsLayout.addWidget(searchCmd)
        options.setLayout(optionsLayout)
        mainLayout.addWidget(options)

        self.searchInput.setPlaceholderText("Enter search term.")
        self.myAction = None

    def setText(self, text):
        self.searchInput.setText(text)

    def setMyAction(self, action):
        self.myAction = action


class LauncherFilterLineEdit(QtGui.QLineEdit):

    """Imput field with an option to clear it.

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
        icon = QtGui.QIcon("./images/delete-2x.png")  # add  icon
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

            menu = self.menu.getMainMenu()
            searchMenu = LauncherSearchMenuView(menu.menuModel, launcherWindow)
            searchMenu.exposeMenu(self.text())
        # TODO set other  cases

        # elif event.key() == Qt.Key_Left:
        #    self.parent().hide()
        # elif event.key() == Qt.Key_Right:
        #    pass
        # elif event.key() == Qt.Key_Down:
        #    candidate = self.nextInFocusChain()
        #    while isinstance(candidate, LauncherMenuTitle):
        #        candidate.focusNextChild()
        #        candidate = candidate.nextInFocusChain()
        #    candidate.focusNextChild()
        # elif event.key() == Qt.Key_Up:
        #    candidate = self.previousInFocusChain()
        #    while isinstance(candidate, LauncherMenuTitle):
        #        candidate.focusPreviousChild()
        #        candidate = candidate.previousInFocusChain()
        #    candidate.focusPreviousChild()
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
        self.myAction = None
        # For title element sectionTitle is menu button that owns menu with
        # this element.

        self.sectionTitle = sectionTitle
        # Apply custom styles

        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        self.setStyleSheet(style.style)

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
        # Apply custom styles

        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        self.setStyleSheet(style.style)

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
            candidate = self.nextInFocusChain()
            while isinstance(candidate, LauncherMenuTitle):
                candidate.focusNextChild()
                candidate = candidate.nextInFocusChain()
            candidate.focusNextChild()

        elif event.key() == Qt.Key_Up:
            candidate = self.previousInFocusChain()
            while isinstance(candidate, LauncherMenuTitle):
                candidate.focusPreviousChild()
                candidate = candidate.previousInFocusChain()
            candidate.focusPreviousChild()

        else:
            QtGui.QPushButton.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        self.setFocus()
        self.parent().setActiveAction(self.myAction)


class LauncherDetachButton(LauncherButton):

    """Button to detach menu and show it in new window.

    LauncherDetachButton is always shown as first item of popup menu. It
    builds new LauncherMenu from the model of parent menu and opens it in
    a new window.
    """

    def __init__(self, parent=None):
        LauncherButton.__init__(self, None, parent)
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

        # TODO apply styles

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

    """Parent class to menu all buttons with text."""

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherButton.__init__(self, sectionTitle, parent)
        self.setText(itemModel.text)
        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        self.setStyleSheet(style.style)

        if itemModel.help_link:
            helpAction = QtGui.QAction("&Help", self)
            helpAction.setData(itemModel.help_link)
            self.contextMenu.addAction(helpAction)
            helpAction.triggered.connect(self.openHelp)

    def openHelp(self):

        url = QtCore.QUrl(
            self.sender().data().toString(), QtCore.QUrl.TolerantMode)
        QtGui.QDesktopServices.openUrl(url)


class LauncherFileChoiceButton(LauncherNamedButton):
    # TODO reorganize to normal menu

    """Button to change the root menu of the launcher.

    LauncherFileChoiceButton causes the launcher to change the root menu and
    sets new view.
    """

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, None, parent)
        self.itemModel = itemModel
        self.clicked.connect(self.changeView)

    def changeView(self):
        """Find LauncherWindow and set new view."""

        candidate = self
        while candidate.__class__.__name__ is not "LauncherWindow":
            candidate = candidate.parent()
        self.parent().hide()  # When done hide popuped menu.
        candidate.setNewView(self.itemModel.rootMenuFile)


class LauncherCmdButton(LauncherNamedButton):

    """LauncherCmdButton executes shell command. """

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, sectionTitle, parent)
        self.cmd = itemModel.cmd
        self.clicked.connect(self.executeCmd)
        if not itemModel.tip:
            toolTip = "Command: " + self.cmd
        else:
            toolTip = itemModel.tip
        self.setToolTip(toolTip)

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
        menu = LauncherSubMenu(itemModel.sub_menu, self.parent())
        self.setMenu(menu)
        if not itemModel.tip:
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


class LauncherStyle:

    def __init__(self, item, theme=None, style=None):
        self.item = item
        self.styleString = ""
        self.style = QtCore.QLatin1String(self.styleString)
        if theme:
            self.appendThemeStyle(theme)
        if style and item:
            self.appendStyle(style, item)

    def appendThemeStyle(self, theme):
        mainWindow = self.item.parent().getLauncherWindow()
        theme_file = open_launcher_file(
            mainWindow.launcherCfg.get("theme_base") + theme + ".qss")
        self.styleString = self.styleString + theme_file.read()
        theme_file.close()
        self.style = QtCore.QLatin1String(self.styleString)

    def appendStyle(self, style, item):
        self.styleString = self.styleString + item.__class__.__name__ +\
            "{" + style + "}"
        self.style = QtCore.QLatin1String(self.styleString)


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

    launcherWindow = LauncherWindow(sys.argv[1], sys.argv[2])
    launcherWindow.setGeometry(0, 0, 150, 0)
    launcherWindow.show()
    sys.exit(app.exec_())
