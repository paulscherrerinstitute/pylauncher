#!/usr/bin/env python
#
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

import platform
import argparse
import copy
import enum
import shlex
import subprocess
import hashlib
import sys

from PyQt5 import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDesktopServices, QIcon, QCursor, QKeySequence
from PyQt5.QtWidgets import QMainWindow, QMenu, QWidgetAction, QLineEdit, QWidget, QHBoxLayout, QToolButton, QVBoxLayout, QCheckBox, QAction, QLabel, QPushButton, QApplication, QInputDialog, QMessageBox

from .launcher_model import *

import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


def stringContains(string, substring, caseSensitive):
    if caseSensitive:
        return substring in string
    else:
        return substring.lower() in string.lower()


def convertPwdToHash(password):
    m = hashlib.md5()
    m.update(password.encode())
    return m.hexdigest()


def verifyPassword(object, password):
    passwordInput = showPasswordDialog(object)
    if passwordInput is not None:
        convertedPwd = convertPwdToHash(passwordInput)
        if convertedPwd == password:
            return True
        else:
            showWrongPasswordDialog(object)
    return False


def showPasswordDialog(object):

    password, ok = QInputDialog.getText(object.window(),
                                        'Password',
                                        'Enter password:',
                                         QLineEdit.Password)
    if ok:
        return password
    return None


def showWrongPasswordDialog(parent):
    messageBox = QMessageBox(parent.window())
    messageBox.setText("Wrong password")
    messageBox.setStandardButtons(QMessageBox.Ok)
    _ = messageBox.exec()


class SearchOptions(enum.Enum):

    """ Enum with all search/filter options """

    sensitivity = 0
    text = 1
    cmd = 2


class LauncherWindow(QMainWindow):

    """Launcher main window.

    Main launcher window. At initialization recursively builds visualization
    of launcher menus, builds menu bar, ...
    """

    def __init__(self, rootFilePath, cfg, parent=None):
        QMainWindow.__init__(self, parent)
        # Get configuration for current system. platform.system() returns:
        #     - "Darwin" when OS X
        #     - "Linux" when Linux
        #     - "Windows" when Windows

        systemType = platform.system()
        if systemType == "Darwin":
            systemType = "OS_X"
        self.launcherCfg = cfg.get(systemType)
        # From menu file define root directory (launcher_base)

        path_tuple = os.path.split(rootFilePath)
        self.launcherCfg["launcher_base"] = path_tuple[0]
        rootFilePath = path_tuple[1]
        # Get defined theme base. If it is not url or absolute dir, make it
        # relative to config file.

        theme_base = self.launcherCfg["theme_base"]
        try:
            urlopen(theme_base)
        except (URLError, ValueError):
            # Not an url. Check if absolute path.

            if not os.path.isabs(theme_base):
                self.launcherCfg["theme_base"] = os.path.join(cfg["cfg_base"],
                                                              theme_base)

        self.menuModel = self.buildMenuModel(rootFilePath)

        self.setWindowTitle(self.menuModel.main_title.text)
        # QMainWindow has predefined layout. Content should be in the central
        # widget. Create widget with a QVBoxLayout and set it as central.

        mainWidget = QWidget(self)
        self.mainLayout = QVBoxLayout(mainWidget)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.setCentralWidget(mainWidget)
        # Main window consist of filter/search entry and a main button which
        # pops up the root menu. Create a layout and add the items.

        self.launcherMenu = LauncherSubMenu(self.menuModel, None, mainWidget)
        self.mainButton = LauncherMainButton(self.launcherMenu, mainWidget)
        self.launcherMenu.button = self.mainButton
        # Create Filter/search item. Add it and main button to the layout.

        self.use_sbox = self.menuModel.flags.get('search-box-enabled', True)
        if self.use_sbox:
            self.searchInput = LauncherFilterWidget(self.launcherMenu, mainWidget)
            self.mainLayout.addWidget(self.searchInput)
        self.mainLayout.addWidget(self.mainButton)
        # Create menu bar. In current visualization menu bar exposes all
        # LauncherFileChoiceItem items from the model. They are exposed in
        # File menu.

        menuBar = self.menuBar()

        self.viewMenu = LauncherViewMenu("&View", menuBar)
        self.viewMenu.buildViewMenu(self.menuModel)
        menuBar.addMenu(self.viewMenu)

        # Set mouse tracking
        self.setMouseTracking(True)
        mainWidget.setMouseTracking(True)
        self.mainButton.setMouseTracking(True)

        if self.use_sbox:
            self.searchInput.setMouseTracking(True)

        if self.menuModel.password is not None:
            if not verifyPassword(self, self.menuModel.password):
                sys.exit(-1)

    def setNewView(self, rootMenuFile, text=None):
        """Rebuild launcher from new config file.

        Destroy previous model and create new one. Build menus and edit main
        window elements.
        """
        self.menuModel.choice_element.text = self.windowTitle()
        self.viewMenu.addToHistory(self.menuModel.choice_element)
        del self.menuModel

        self.menuModel = self.buildMenuModel(rootMenuFile)

        if self.menuModel.password is not None:
            if not verifyPassword(self, self.menuModel.password):
                return

        if text:
            self.setWindowTitle(text)
        else:
            self.setWindowTitle(self.menuModel.main_title.text)
        self.mainButton.restyle(self.menuModel.main_title)
        self.launcherMenu.deleteLater()
        self.launcherMenu = LauncherSubMenu(self.menuModel, self.mainButton,
                                            self)
        self.mainButton.setMenu(self.launcherMenu)
        self.viewMenu.buildViewMenu(self.menuModel)

        self.use_sbox = self.menuModel.flags.get('search-box-enabled', True)
        if self.use_sbox:
           self.searchInput.setMenu(self.launcherMenu)

    def changeEvent(self, changeEvent):
        """Catch when main window is selected and set focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow() and self.use_sbox:
            self.searchInput.setFocus()

    def mouseMoveEvent(self, event):
        """ Activate window whenever mouse is over to get keyboard focus and show tooltips """
        if not self.isActiveWindow():
            self.activateWindow()
            self.raise_()  # Raise above other windows

    def buildMenuModel(self, rootMenuPath):
        """Return model of a menu defined in rootMenuFile."""
        rootMenuFullPath = join_launcher_path(self.launcherCfg.get("launcher_base"),
                                        rootMenuPath)

        self.launcherCfg["launcher_base"] = os.path.dirname(rootMenuFullPath)

        try:
            rootMenu = launcher_menu_model(None, rootMenuFullPath, 0, self.launcherCfg)
        except IOError:
            errMsg = "File \"" + rootMenuPath + "\" not found."
            logging.error(errMsg)
            sys.exit()
        return rootMenu


class LauncherMenu(QMenu):

    """Super class of all menu visualizations.

    Is a parent super class which takes the model of menu as an argument and
    builds a "vital" part of the menu. It also implements methods for menu
    manipulation.
    """

    def __init__(self, menuModel, button=None, parent=None):
        QMenu.__init__(self, parent)
        self.setSeparatorsCollapsible(False)
        self.filterTerm = ""
        self.menuModel = menuModel
        self.buildMenu(self.menuModel.menu_items)
        self.initFilterVisibility = True
        self.filterConditions = [False, True, False]
        self.button = button

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
        if (len(self.actions()) > index):
            self.insertAction(self.actions()[index], self.action)
        else:
            self.addAction(self.action)

    def setFilterCondition(self, condition, value):
        """ Set one condition to given value."""

        self.filterConditions[condition.value] = value
        self.filterMenu(self.filterTerm)

    def getLauncherWindow(self):
        """ Search and return application main window object"""

        candidate = self
        while type(candidate) != LauncherWindow:
            candidate = candidate.parent()

        return candidate

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
                # Search is always only on NamedButtons. Get text from their
                # models to avoid searching also the prefixes added later (in
                # search view).

                if isinstance(widget, LauncherNamedButton):
                    text = widget.itemModel.text

                widgetType = widget.__class__.__name__
            else:
                widget = None
                widgetType = None
                text = ""

            if action.__class__.__name__ == "LauncherSeparator":
                action.setVisibility(not filterTerm and self.initFilterVisibility)
            elif not filterTerm:
                # Empty filter. Show depending on type. If submenu recursively
                # empty  filter.

                action.setVisibility(self.initFilterVisibility)
                if widgetType == "LauncherMenuButton":
                    widget.menu().filterMenu(filterTerm)

            elif widgetType == "LauncherMenuTitle":
                action.setVisibility(False)

            elif widgetType == "LauncherSubMenuAsTitle":
                action.setVisibility(False)

            elif widgetType == "LauncherMenuButton":
                # Recursively filter menus. Show only sub-menus that have
                # visible items.
                subMenu = widget.menu()
                subHasVisible = subMenu.filterMenu(filterTerm)
                hasVisible = hasVisible or subHasVisible
                action.setVisibility(subHasVisible)

            elif textFilter and stringContains(text, filterTerm,
                                              sensitivityFilter):
                action.setVisibility(True)
                hasVisible = True

            elif widgetType == "LauncherCmdButton" and cmdFilter and\
                stringContains(widget.cmd, filterTerm, sensitivityFilter):

                action.setVisibility(True)
                hasVisible = True

            else:
                action.setVisibility(False)

        return hasVisible

    def showEvent(self, showEvent):
        """Catch event when menu is shown and move it by side.

        Whenever show(), popup(), exec() are called this method is called.
        Move the menu to the left side of the button (default is bellow)
        """
        # TODO handle cases when to close to the edge of screen.

        # Do nothing if the event comes from outside the application
        if not showEvent.spontaneous():
            if self.button:
                width = self.button.width()
                height = self.button.height()
            else:
                width = self.parent().width()
                height = self.parent().height()
            position = self.pos()
            position.setX(position.x()+width)
            position.setY(position.y()-height)
            self.move(position)

            # Set focus on first button (skip separators (also titles) and detach
            # button) If empty menu focus on detach button
            i = 1
            try:
                while self.actions()[i].isSeparator():
                    i += 1

            except LookupError:
                i = 0

            self.actions()[i].defaultWidget().setFocus()
            self.setActiveAction(self.actions()[i])

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

    def __init__(self, menuModel, button, parent=None):
        LauncherMenu.__init__(self, menuModel, button, parent)
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
        detachedMenu.setWindowTitle(self.menuModel.main_title.text)
        detachedMenu.searchInput.setText(self.filterTerm)
        detachedMenu.show()
        # Takes care of showing on the right place with right size
        detachedMenu.popup(QtCore.QPoint(self.pos().x(), self.pos().y()))
        self.hideAll()

    def hideAll(self):
        """ Recursively hide all popuped menus"""

        self.hide()
        candidate = self.parent()
        if isinstance(candidate, LauncherSubMenu):
            candidate.hideAll()


class LauncherDetachedMenu(LauncherMenu):

    """Visualization of detached menu.

    Creates detached menu. Adds find/search input to menu. Also overrides the
    hide() method of the menu, because it should not be hidden  when action
    is performed.

    Removes detach button and filter/search widget but do not add them to
    the menu.
    """

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, None, parent)
        self.searchInput = LauncherFilterWidget(self, self)
        self.insertToMenu(self.searchInput, 0)
        self.setWindowFlags(Qt.Window)
        self.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        self.setEnabled(True)

    def hide(self):
        pass  # Detached menu should not be hidden at any action (left key).

    def hideAll(self):
        pass

    def changeEvent(self, changeEvent):
        """Catch when menu window is selected and focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self.searchInput.setFocus()

    def keyPressEvent(self, event):
        """Catch escape (originally closes the window) and skip actions."""

        if event.key() == Qt.Key_Escape or event.key() == Qt.Key_Alt:
            pass
        else:
            LauncherMenu.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        # Activate window whenever mouse is over to get keyboard focus and show tooltips
        if not self.isActiveWindow():
            self.activateWindow()
            self.raise_()  # Raise above other windows

class LauncherSearchMenuView(LauncherMenu):

    """Search view

    Different visualization of launcher for searching. Submenues do not
    expand, but are rather included at the bottom of the list.
    """

    def __init__(self, menuModel, button=None, parent=None):
        LauncherMenu.__init__(self, menuModel, button, parent)
        self.searchWidget = LauncherSearchWidget(self, self.getMainMenu())
        self.insertToMenu(self.searchWidget, 0)
        self.initFilterVisibility = False

    def buildMenu(self, menuModel):
        """Visualize menu

        Override this method and build different visualization.
        """
        cMenuItems = list(self.menuModel.menu_items)
        sectionTitle = None
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
                # Take subemnu model and build (visualize) it below

                cSubMenuItems = copy.copy(item.sub_menu.menu_items)
                cMenuItems.extend(cSubMenuItems)
            elif item.__class__.__name__ == "launcher_title_item":
                button = LauncherMenuTitle(item, None, self)
                self.appendToMenu(button)
                sectionTitle = button
                addPrefix = True
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
        self.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        self.setEnabled(True)
        self.show()
        self.searchWidget.setFocus()
        #self.move(self.pos().x(), self.pos().y()) TODO

    def changeEvent(self, changeEvent):
        """Catch when menu window is selected and focus to search."""

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self.searchWidget.setFocus()

    def hide(self):
        pass  # Search menu should not be hidden at any action (left key).

    def hideAll(self):
        pass


class LauncherMenuWidgetAction(QWidgetAction):

    """Wrap widgets to be added to menu.

    When QWidget needs to be appended to QMenu it must be "wrapped" into
    QWidgetAction. This class "wraps" LauncherButton in the same way.
    Further it also implements method to control the visibility of the menu
    item (both action and widget).
    """

    def __init__(self, widget, parent=None):
        QWidgetAction.__init__(self, parent)
        self.widget = widget
        self.setDefaultWidget(self.widget)
        widget.setMyAction(self)  # Let widget know about action.

    def setVisibility(self, visibility):
        """Set visibility of both the widget action and the widget."""

        self.setVisible(visibility)
        self.widget.setVisible(visibility)
        if self.widget.sectionTitle and visibility:
            self.widget.sectionTitle.myAction.setVisibility(True)


class LauncherFilterLineEdit(QLineEdit):

    """Input field with an option to clear it.

    LauncherFilterLineEdit is QLineEdit which does filtering of menu items
    recursively by putting the filter  to child menus. It has a button to clear
    current input with one click. When enter button is pressed a search window
    with results is opened.
    """

    def __init__(self, menu, parent=None):
        QLineEdit.__init__(self, parent)
        self.menu = menu
        self.textChanged.connect(lambda: self.menu.filterMenu(self.text()))
        self.myAction = None
        self.setPlaceholderText("Enter filter term.")
        self.setClearButtonEnabled(True)
        # Create button to clear text and add it to the right edge of the
        # input.
        self.setMinimumWidth(200)
        # Set search policy (default False). If True it opens search when
        # Enter is pressed

        self.searchPolicy = False

    def setMyAction(self, action):
        self.myAction = action

    def keyPressEvent(self, event):
        """Catch key pressed event.

        Catch return and enter key pressed and open search in new window.
        """

        if self.searchPolicy is True and \
                ((event.key() == Qt.Key_Return) or
                    (event.key() == Qt.Key_Enter)):
            self.openSearch()

        elif event.key() == Qt.Key_Down:
            self.focusNextPrevChild(True)

        elif event.key() == Qt.Key_Up:
            self.focusNextPrevChild(False)
        else:
            QLineEdit.keyPressEvent(self, event)

    def openSearch(self):
        """ Do a search on full menu (root menu)."""
        menu = self.menu.getMainMenu()
        searchMenu = LauncherSearchMenuView(menu.menuModel, menu.button,
                                            menu)
        searchMenu.exposeMenu(self.text())

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)


class LauncherFilterWidget(QWidget):

    """ Filter menu widget which opens search when return is pressed"""

    def __init__(self, menu, parent=None):
        QWidget.__init__(self, parent)
        mainLayout = QHBoxLayout(self)

        self.setLayout(mainLayout)

        self.searchInput = LauncherFilterLineEdit(menu, self)
        self.searchInput.searchPolicy = True
        self.searchButton = QToolButton(self)
        self.searchButton.setMouseTracking(True)

        self.searchButton.setFixedSize(27, 27)
        currDir = os.path.dirname(os.path.realpath(__file__))
        icon = QIcon(os.path.join(currDir,
                                        "resources/images/magnifying-glass-2x.png"))
        self.searchButton.setIcon(icon)

        self.searchButton.setFocusPolicy(Qt.ClickFocus)

        self.searchButton.clicked.connect(
            lambda: self.searchInput.openSearch())
        mainLayout.addWidget(self.searchInput)
        mainLayout.addWidget(self.searchButton)
        # Focus policy: get focus when tabing/arrow key and pass it to
        # search input

        self.setFocusPolicy(Qt.TabFocus)
        self.setFocusProxy(self.searchInput)

    def setMenu(self, menu):
        self.searchInput.menu = menu

    def setMyAction(self, action):
        self.myAction = action

    def setText(self, text):
        self.searchInput.setText(text)

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)


class LauncherSearchWidget(QWidget):

    """ Search menu widget

    Container with all visual elements to do a search. Some options are
    available as check boxes.
    """

    def __init__(self, menu, parent=None):
        QWidget.__init__(self, parent)
        mainLayout = QVBoxLayout(self)
        mainLayout.setContentsMargins(0,0,0,0)
        self.setLayout(mainLayout)
        # Prepare components and add them to layout:
        #    - search field
        #    - options (case sensitive)
        #    - filters (text, cmd)
        #    - menu

        self.searchInput = LauncherFilterLineEdit(menu, self)
        caseSensitive = QCheckBox("Case sensitive", self)
        caseSensitive.setChecked(False)
        caseSensitive.stateChanged.connect(lambda: menu.setFilterCondition(
            SearchOptions.sensitivity, caseSensitive.isChecked()))
        menu.setFilterCondition(SearchOptions.sensitivity,
                                caseSensitive.isChecked())
        mainLayout.addWidget(self.searchInput)
        mainLayout.addWidget(caseSensitive)
        options = QWidget(self)
        optionsLayout = QHBoxLayout(options)
        optionsLayout.setContentsMargins(0, 0, 0, 0)
        searchText = QCheckBox("Title search", options)
        searchText.setChecked(True)
        searchText.stateChanged.connect(
            lambda: menu.setFilterCondition(SearchOptions.text,
                                            searchText.isChecked()))
        menu.setFilterCondition(SearchOptions.text, searchText.isChecked())
        searchCmd = QCheckBox("Command search", options)
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
        # Focus policy: get focus when tabing/arrow key and pass it to
        # search input

        self.setFocusPolicy(Qt.TabFocus)
        self.setFocusProxy(self.searchInput)

    def setText(self, text):
        self.searchInput.setText(text)

    def setMyAction(self, action):
        self.myAction = action


class LauncherSeparator(QAction):

    """Just wrapped normal menu separator."""

    def __init__(self, itemModel, parent=None):
        QAction.__init__(self, parent)
        self.setSeparator(True)

    def setVisibility(self, visibility):
        self.setVisible(visibility)


class LauncherMenuTitle(QLabel):

    """Passive element with no action and no key focus."""

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        QLabel.__init__(self, itemModel.text, parent)
        self.myAction = None
        self.setFocusPolicy(Qt.NoFocus)
        # For title element sectionTitle is menu button that owns menu with
        # this element.

        self.sectionTitle = sectionTitle
        # Apply custom styles

        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        self.setStyleSheet(style.style)

    def setMyAction(self, action):
        self.myAction = action
        self.myAction.setSeparator(True)


class LauncherButton(QPushButton):

    """Super class for active menu items (buttons).

    Parent class for all active menu items. To recreate the native menu
    behavior (when QActions are used) this class also handles keyboard
    events to navigate through the menu.

    Parent of any LauncherButton must be a QMenu and it must be paired with
    a LauncherMenuWidgetAction.
    """

    def __init__(self, sectionTitle=None, parent=None):
        QPushButton.__init__(self, parent)
        self.setMouseTracking(True)
        self.myAction = None
        self.sectionTitle = sectionTitle

        self.contextMenu = QMenu(self)

    def contextMenuEvent(self, event):
        """ Show context menu if context exists"""

        if self.contextMenu.actions():
            self.contextMenu.exec_(QCursor.pos())

    def mousePressEvent(self, event):
        """ Catch right menu clicks, to override closing of menu """
        if event.button() == Qt.RightButton:
            pass  # contexMenuEvent is still emitted and handled
        else:
            super(QPushButton, self).mousePressEvent(event)

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
            self.parent().button.activate()

        elif event.key() == Qt.Key_Right:
            pass

        elif event.key() == Qt.Key_Down:
            self.focusNextPrevChild(True)

        elif event.key() == Qt.Key_Up:
            self.focusNextPrevChild(False)

        else:
            QPushButton.keyPressEvent(self, event)

    def mouseMoveEvent(self, event):
        self.activate()
        self.parent().mouseMoveEvent(event)

    def activate(self):
        self.setFocus()
        if isinstance(self.parent(), QMenu):
            # only menus have actions
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

    """Main Launcher button to expand menu

    This class extends LauncherButton similar as LauncherMenuButton, but
    with a different inputs.
    """

    def __init__(self, menu, parent=None):
        LauncherButton.__init__(self, None, parent)
        self.restyle(menu.menuModel.main_title)
        self.setMenu(menu)

    def restyle(self, itemModel):
        self.setText(itemModel.text.replace('&', '&&'))  # For QButton &X means that X is shortcut, && gives &
        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        # Add menu arrow indicator. Added here to use right path and avoid
        # compiling python code

        currDir = os.path.dirname(os.path.realpath(__file__))
        indicator = os.path.join(currDir, "resources/images/caret-right.png")
        indicator = os.path.normpath(indicator)
        # Even on windows a path to the image must be with forward slashes.

        indicator = re.sub(r'\\', '/', indicator)
        indicatorStyle = "LauncherButton:menu-indicator {image: url(" +\
            indicator + ");subcontrol-position: right center}"
        style.appendClassStyle(indicatorStyle)
        self.setStyleSheet(style.style)

    def mouseMoveEvent(self, event):
        self.parent().mouseMoveEvent(event)
        self.setFocus()

    def keyPressEvent(self, event):
        """Open main menu

        Open menu also with right arrow key. Override option to hide parent
        with left arrow key, because main button is not part of popuped window.
        """

        if event.key() == Qt.Key_Right:
            self.setFocus()
            self.click()
        elif event.key() == Qt.Key_Left:
            pass
        else:
            LauncherButton.keyPressEvent(self, event)


class LauncherNamedButton(LauncherButton):

    """Parent class to menu all buttons with text."""

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherButton.__init__(self, sectionTitle, parent)
        self.setText(itemModel.text.replace('&', '&&'))  # For QButton &X means that X is shortcut, && gives &
        style = LauncherStyle(self, itemModel.theme, itemModel.style)
        # Add menu arrow indicator. Added here to use right path and avoid
        # compiling python code

        currDir = os.path.dirname(os.path.realpath(__file__))
        indicator = os.path.join(currDir, "resources/images/caret-right.png")
        indicator = os.path.normpath(indicator)
        # Even on windows a path to the image must be with forward slashes.

        indicator = re.sub(r'\\', '/', indicator)
        indicatorStyle = "LauncherButton:menu-indicator {image: url(" +\
            indicator + ");subcontrol-position: right center}"
        style.appendClassStyle(indicatorStyle)
        self.setStyleSheet(style.style)

        if itemModel.help_link:
            helpAction = QAction("&Help", self)
            helpAction.setData(itemModel.help_link)
            self.contextMenu.addAction(helpAction)
            helpAction.triggered.connect(self.openHelp)

        self.itemModel = itemModel

    def openHelp(self):
        """ Open help link in default browser. """

        url = QtCore.QUrl(
            self.sender().data(), QtCore.QUrl.TolerantMode)
        QDesktopServices.openUrl(url)


class LauncherCmdButton(LauncherNamedButton):

    """ LauncherCmdButton executes shell command. """

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, sectionTitle, parent)
        self.cmd = itemModel.cmd
        self.pwd = itemModel.pwd
        self.clicked.connect(self.executeCmd)

        toolTip = ""
        if itemModel.tip:
            toolTip = itemModel.tip + " "
        toolTip = toolTip + "[Command: " + self.cmd + "]"

        self.setToolTip(toolTip)

        copyAction = QAction("Copy command", self)
        copyAction.triggered.connect(self.copyCmd)
        # If actions (Help) already exist put above them
        if self.contextMenu.actions():
            self.contextMenu.insertAction(self.contextMenu.actions()[0], copyAction)
        else:
            self.contextMenu.addAction(copyAction)

    def copyCmd(self):
        cb = QApplication.clipboard()
        cb.clear(mode=cb.Clipboard)
        cb.setText(self.cmd, mode=cb.Clipboard)


    def executeCmd(self, itemModel):
        """ Run specified command as a separate process

        Runs commands from the same environment ($PATH) as the launcher was
        started. Apart from "bash" it aboarts scripts without shebang on
        first line (strictly).
        """

        self.parent().hideAll()  # When done hide all popuped menus
        try:
            if self.pwd is not None:
                """passwordInput = showPasswordDialog(self)
                if passwordInput is not None:
                    convertedPwd = convertPwdToHash(passwordInput)
                    if convertedPwd != self.pwd:
                        showWrongPasswordDialog()
                        return"""
                if verifyPassword(self, self.pwd):
                    subprocess.Popen(shlex.split(self.cmd))
            else:
                subprocess.Popen(shlex.split(self.cmd))

        except OSError:
            warn_msg = "Command \"" + self.cmd + "\" cannot be executed. " + \
                "Wrong path or bad/no interpreter."
            logging.warning(warn_msg)


class LauncherMenuButton(LauncherNamedButton):

    """Builds a new view from model.

    LauncherMenuButton builds new menu from model. When pressed the menu is
    popped up.
    """

    def __init__(self, itemModel, sectionTitle=None, parent=None):
        LauncherNamedButton.__init__(self, itemModel, sectionTitle, parent)
        menu = LauncherSubMenu(itemModel.sub_menu, self, self.parent())
        self.setMenu(menu)

        toolTip = ""
        if itemModel.tip:
            toolTip = itemModel.tip + " "
        toolTip = toolTip + "[Menu: " + menu.menuModel.main_title.text + "]"

        self.setToolTip(toolTip)

    def keyPressEvent(self, event):
        """Submenu can also be opened with right arrow key."""

        if event.key() == Qt.Key_Right:
            if self.itemModel.sub_menu.password is not None:
                if not verifyPassword(self, self.itemModel.sub_menu.password):
                    return
            self.click()
        else:
            LauncherNamedButton.keyPressEvent(self, event)

    def mousePressEvent(self, event):
        """ Ask for password (if set) before opening the sub-menu"""

        if self.itemModel.sub_menu.password is not None:
            if not verifyPassword(self, self.itemModel.sub_menu.password):
                return
        LauncherButton.mousePressEvent(self, event)

class LauncherViewMenu(QMenu):

    """ View menu for menu bar """

    def __init__(self, text, parent=None):
        QMenu.__init__(self, text, parent)
        self.historyMenu = QMenu("History", self)
        self.initHistoryMenu()
        self.maxHistoryLength = 10

        # When creating menu first time (for the main root menu), a special
        # menu entry should be created, which will allow user to alwayas return
        # to that very first/main menu. It should always be the top choice in the
        # View menu, except when main menu is already loaded.
        self.rootMenuElement = None


    def buildViewMenu(self, menuModel):
        self.menuModel = menuModel
        if not self.rootMenuElement:
            # This executes only first time
            self.rootMenuElement = self.menuModel.choice_element
        self.clear()

        # Option to go to the root menu if not already at it.
        if not self.menuModel.choice_element.root_menu_file == self.rootMenuElement.root_menu_file:
            action = LauncherFileChoiceAction(self.rootMenuElement, self)
            self.addAction(action)
            self.addSeparator()

        for view in menuModel.file_choices:
            action = LauncherFileChoiceAction(view, self)
            self.addAction(action)

        self.addSeparator()
        self.addMenu(self.historyMenu)
        self.addSeparator()

        searchAction = QAction("Search", self)
        searchAction.setShortcuts(QKeySequence("Ctrl+F"))
        searchAction.setStatusTip("Search launcher items")
        searchAction.triggered.connect(self.openSearch)
        self.addAction(searchAction)

    def initHistoryMenu(self):
        self.historyMenu.clear()
        self.historyMenu.addSeparator()
        clearHistory = self.historyMenu.addAction("Clear history")
        clearHistory.triggered.connect(self.initHistoryMenu)
        self.historyMenu.menuAction().setVisible(False)

    def addToHistory(self, itemModel):
        action = LauncherFileChoiceAction(itemModel, self)
        history_list = self.historyMenu.actions()
        if len(history_list)-2 >= self.maxHistoryLength:
            # Remove first action which is not separator or clear action
            self.historyMenu.removeAction(history_list[-3])
        self.historyMenu.insertAction(self.historyMenu.actions()[0], action)
        self.historyMenu.menuAction().setVisible(True)

    def openSearch(self):
        searchMenu = LauncherSearchMenuView(self.menuModel,
                                            self.parent().parent().mainButton,
                                            self.parent().parent().launcherMenu)
        searchMenu.exposeMenu("")


class LauncherFileChoiceAction(QAction):

    """Action to change the root menu of the launcher.

    LauncherFileChoiceAction causes the launcher to change the root menu and
    sets new view. It is placed in a View menu.
    """

    def __init__(self, itemModel, parent=None):
        # For QAction &X means that X is shortcut, && gives &
        QAction.__init__(self, itemModel.text.replace('&', '&&'), parent)
        self.itemModel = itemModel
        self.triggered.connect(self.changeView)

    def changeView(self):
        """Find LauncherWindow and set new view."""

        candidate = self
        while candidate.__class__.__name__ !=  "LauncherWindow":
           candidate = candidate.parent()
        candidate.setNewView(self.itemModel.root_menu_file, self.itemModel.text)


class LauncherStyle(object):

    """ Class which handles qss style sheet from multiple sources """

    def __init__(self, item, theme=None, style=None):
        self.item = item
        self.styleString = ""
        self.style = self.styleString
        if theme:
            self.appendThemeStyle(theme)
        if style and item:
            self.appendStyle(style, item)

    def appendThemeStyle(self, theme):
        mainWindow = self.item
        while type(mainWindow) is not LauncherWindow:
            mainWindow = mainWindow.parent()

        try:
            theme_file = open_launcher_file(
                os.path.join(mainWindow.launcherCfg.get("theme_base"),
                             theme + ".qss"))
            self.styleString = self.styleString + theme_file.read().decode('utf-8')

            theme_file.close()
            self.style = self.styleString

        except IOError:
            warnMsg = "Theme \"" + theme + \
                "\" was not found. Theme ignored."
            logging.warning(warnMsg)

    def appendStyle(self, style, item):
        self.styleString = self.styleString + item.__class__.__name__ +\
            "{" + style + "}"
        self.style = self.styleString

    def appendClassStyle(self, style):
        self.styleString = self.styleString + style
        self.style = self.styleString


def main():
    """ Main logic """

    argsPars = argparse.ArgumentParser()
    argsPars.add_argument('configuration',
                          help="menu/configuration file")
    argsPars.add_argument('-m', '--mapping',
                          help='overwrite default mapping file')
    argsPars.add_argument('-s', '--style',
                          help="overwrite default style (qss file)")
    argsPars.add_argument('--position', type=int, nargs=2, metavar=('X', 'Y'),
                          help="set initial position on the screen")
    args = argsPars.parse_args()


    app = QApplication(sys.argv)

    # Load configuration. Use default configuration defined inside package if
    # --config is not specified
    currDir = os.path.dirname(os.path.realpath(__file__))
    cfgPath = os.path.join(currDir, "resources/mapping/mapping.json")
    cfgFile = open_launcher_file(cfgPath)
    cfgString = cfgFile.read(-1).decode('utf-8')
    defaultCfg = json.loads(cfgString)
    defaultCfg["cfg_base"] = os.path.dirname(cfgPath)
    cfgFile.close()

    default = True
    logMsg = ""
    if args.mapping:
        try:
            cfgFile = open_launcher_file(args.mapping)
            cfgString = cfgFile.read(-1).decode('utf-8')
            cfg = json.loads(cfgString)
            cfg["cfg_base"] = os.path.dirname(args.mapping)
            cfgFile.close()
            default = False
        except:
            logMsg = "Problems opening \"" + args.mapping + "\". "

    if default:
        cfg = defaultCfg
        logMsg += "Launcher will be loaded with default mapping."
        logging.warning(logMsg)


    # Create Launcher Window and load default style and theme
    launcherWindow = LauncherWindow(args.configuration, cfg)

    app.setStyle("cleanlooks")
    styleFile = open_launcher_file(os.path.join(currDir,
                                                "resources/qss/default.qss"))
    app.setStyleSheet(styleFile.read().decode('utf-8'))
    styleFile.close()
    if args.style:
        try:
            userStyle = open_launcher_file(args.style)
            launcherWindow.setStyleSheet(userStyle.read().decode('utf-8'))
            userStyle.close()
        except:
            logging.warning("Problems opening \"" + args.style + "\". Launcher will be opened with default style.")

    launcherWindow.setMinimumWidth(250)
    launcherWindow.show()
    geometry = launcherWindow.geometry()

    # Set to desired position
    position = args.position

    if not position:  # Set defaults
        position = [0, 0]

    screenGeometry = app.desktop().geometry()
    # Negative values should be treated as starting from oposite corner
    if position[0] < 0:  # X
        position[0] = screenGeometry.width()-geometry.width()+position[0]

    if position[1] < 0:  # Y
        position[1] = screenGeometry.height()-geometry.height()+position[1]

    # Update x/y coordinates of window
    launcherWindow.move(position[0], position[1])

    sys.exit(app.exec_())


# Start program here
if __name__ == '__main__':
    main()
