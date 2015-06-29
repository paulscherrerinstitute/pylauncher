#!/usr/bin/python

import sys
import os
import copy

from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import pyqtSlot, Qt


class LauncherMenuModel:
    # LauncherMenuModel parses the configuration file and builds the listof
    # menu items. Each LauncherMenuModel object holds only a list of items
    # defined in its configuration file. If submenu is needed, new
    # LauncherMenuModel object is created and its reference is stored on the
    # calling object list menuItems.

    def __init__(self, filePath):
        self.filePath = filePath
        self._cfgFile = open(filePath, 'r')
        # File format specific. For testing the configuration files are just
        # simple text files with list of tuples.

        self._cfg = eval(self._cfgFile.read())
        # Each menu has:_items
        #   mainTitle: holding the title of the menu
        #   list of menuItems: list of all LauncherMenuModelItems
        #   TODO: in future it will also hold the styles, levels and list of
        #         possible pictures on the buttons

        self.menuItems = list()
        for tuple in self._cfg:
            if tuple[0] == "main-title":
                self.mainTitle = tuple[1]
            elif tuple[0] == "cmd":
                self._menuItem = LauncherCmdItem(tuple[1], tuple[2])
                self.menuItems.append(self._menuItem)
            elif tuple[0] == "menu":
                self._menuItem = LauncherSubMenuItem(tuple[1], tuple[2])
                self.menuItems.append(self._menuItem)
            elif tuple[0] == "title":
                self._menuItem = LauncherTitleItem(tuple[1])
                self.menuItems.append(self._menuItem)
            elif tuple[0] == "separator":
                self._menuItem = LauncherItemSeparator(tuple[1], tuple[2])
                self.menuItems.append(self._menuItem)
            elif tuple[0] == "file-choice":
                self._menuItem = LauncherFileChoiceItem(tuple[1], tuple[2])
                self.menuItems.append(self._menuItem)

    def getItemsOfType(self, itemsType):
        # Returns a list of all items of specified type.

        self._itemsOfType = filter(lambda x: x.itemType == itemsType,
                                   self.menuItems)
        return(self._itemsOfType)


class LauncherMenuModelItem:
    # LauncherMenuModelItem is a parent super class for menu items that needs
    # to be visualized, such as menu buttons, separators, titles. It implements
    # methods and parameters common to many subclasses.

    def __init__(self, text=None, style=None, helpLink=None, key=None):
        self.text = text
        self.style = style
        self.helpLink = helpLink
        self.key = key


class LauncherCmdItem(LauncherMenuModelItem):
    # LauncherCmdItem holds the shell command together with its arguments.

    itemType = "cmd"

    def __init__(self, text=None, cmd=None, style=None, helpLink=None,
                 key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.cmd = cmd


class LauncherSubMenuItem(LauncherMenuModelItem):
    # LauncherSubMenuItem builds new menu which is defined in subMenuFile.
    # If detach == True this sub-menu should be automaticaly detached if
    # detachment is supported in view.

    itemType = "menu"

    def __init__(self, text=None, subMenuFile=None, style=None,
                 helpLink=None, detach=False, key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.subMenu = LauncherMenuModel(subMenuFile)
        self.detach = detach


class LauncherFileChoiceItem(LauncherMenuModelItem):
    # Launcher can be "rebuild" from new root menu file. LauncherFileChoiceItem
    # holds the file of the new root menu (rootMenuFile).

    itemType = "file-choice"

    def __init__(self, text=None, rootMenuFile=None, style=None,
                 helpLink=None, key=None):
        LauncherMenuModelItem.__init__(self, text, style, key)
        self.rootMenuFile = rootMenuFile


class LauncherTitleItem(LauncherMenuModelItem):
    # Special LauncherMenuModelItem with no extra parameters.

    itemType = "title"

    def __init__(self, text=None, style=None, helpLink=None, key=None):
        self._style = style
        LauncherMenuModelItem.__init__(self, text, self._style, key)


class LauncherWindow(QtGui.QMainWindow):
    # Main launcher window. At initialization recursively builds visualisation
    # of launcher menus, builds menu bar, ...

    def __init__(self, rootMenuFile, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        # Build menu model from rootMenuFile and set general parameters.

        self._menuModel = self._buildMenuModel(rootMenuFile)
        self.setWindowTitle(self._menuModel.mainTitle)
        # QMainWindow has predefined layout. Content should be in the central
        # widget. Create widget with a QVBoxLayout and set it as central.

        self._mainWidget = QtGui.QWidget(self)
        self._mainLayout = QtGui.QVBoxLayout(self._mainWidget)
        self._mainLayout.setContentsMargins(0,0,0,0)
        self.setCentralWidget(self._mainWidget)
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
        self._menuBar = self.menuBar()
        self._fileMenu = QtGui.QMenu("&File", self._menuBar)
        self._fileChoiceItems = self._menuModel.getItemsOfType(
            "file-choice"
        )
        for item in self._fileChoiceItems:
            self._button = LauncherFileChoiceButton(item, self._fileMenu)
            self._buttonAction = QtGui.QWidgetAction(self._fileMenu)
            self._buttonAction.setDefaultWidget(self._button)
            self._fileMenu.addAction(self._buttonAction)
        self._menuBar.addMenu(self._fileMenu)

    def setNewView(self, rootMenuFile):
        # Destroy prevoisu model and create new one. Build menus and edit main
        # window elements.

        del self._menuModel
        self._menuModel = self._buildMenuModel(rootMenuFile)
        self.setWindowTitle(self._menuModel.mainTitle)
        self.mainButton.setText(self._menuModel.mainTitle)
        self._launcherMenu = LauncherSubMenu(self._menuModel, self.mainButton)
        self.mainButton.setMenu(self._launcherMenu)

    def changeEvent(self, changeEvent):
        # When top-level window is changed to detached menu window set focus to
        # search.

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self._searchInput.setFocus()

    def _buildMenuModel(self, rootMenuFile):
        # Return model of a menu defined in rootMenuFile.

        self._menu = LauncherMenuModel(rootMenuFile)
        return self._menu


class LauncherMenu(QtGui.QMenu):
    # Is a parent super class which takes the model of menu as an argument and
    # builds a "vital" part of the menu. It aslo implements methods for menu
    # manipulation.

    def __init__(self, menuModel, parent=None):
        QtGui.QMenu.__init__(self, parent)
        self.filterTerm = ""
        self.menuModel = menuModel
        # menuModel has a list of menuItems with models of items. Build buttons
        # from it and add them to the menu.

        for item in self.menuModel.menuItems:
            if item.itemType == "cmd":
                self._button = LauncherCmdButton(item, self)
                self.addToMenu(self._button)

            elif item.itemType == "menu":
                # Make new menu and append its reference to the button.
                self._button = LauncherMenuButton(item, self)
                self.addToMenu(self._button)

            elif item.itemType == "title":
                self._button = LauncherMenuTitle(item, self)
                self.addToMenu(self._button)

    def addToMenu(self, widget):
        # Create widget action for widget. Pair them and add to the menu.

        self._action = LauncherMenuWidgetAction(widget, self)
        self.addAction(self._action)

    def insertToMenu(self, widget, index):
        # Create widget action for widget. Pair them and insert them to the
        # specified position in menu.

        self._action = LauncherMenuWidgetAction(widget, self)
        if self.actions()[index]:
            self.insertAction(self.actions()[index], self._action)
        else:
            self.addAction(self._action)

    def filterMenu(self, filterTerm=None):
        # Shows/hides action depending on filterTerm. Returns true if has
        # visible active (buttons) items.

        self.filterTerm = filterTerm
        self._hasVisible = False
        self._visible_count = 0
        self._last_title = None
        for action in self.actions():
            self._widget = action.defaultWidget()
            self._type = self._widget.itemType
            if not filterTerm:  # Empty filter. Show all.
                action.setVisibility(True)
                self._hasVisible = True
            elif self._type is "search" or self._type is "detach":
                # Filter/search and detach are allway visible.

                action.setVisibility(True)

            elif self._type is "title":
                # Visible actions below title are counted. If count > 0 then
                # show last title. Then reset counter and store current title
                # as last.

                if self._last_title:
                    self._last_title.setVisibility(self._visible_count != 0)
                self._visible_count = 0
                self._last_title = action

            elif self._type is "menu":
                # Recursively filter menus. Show only sub-menus that have
                # visible items.

                self._subMenu = action.defaultWidget().menu()
                self._subHasVisible = self._subMenu.filterMenu(filterTerm)
                action.setVisibility(self._subHasVisible)
                if self._subHasVisible:
                    self._visible_count += 1
                self._hasVisible = self._hasVisible or self._subHasVisible

            elif filterTerm in self._widget.text():
                # Filter term is found in the button text. For now filter only
                # cmd buttons.

                if self._type is "cmd":
                    action.setVisibility(True)
                    self._hasVisible = True
                    self._visible_count += 1
                else:
                    action.setVisibility(False)
            else:
                action.setVisibility(False)

            if self._last_title:  # Handle last title if exists
                self._last_title.setVisibility(self._visible_count != 0)

        return self._hasVisible

    def showEvent(self, showEvent):
        # Whenever show(), popup(), exec() are called this method is called.
        # Move the menu to the leftside of the button (default is bellow)
        # TODO handle cases when to close to the edge of screen.

        self.position = self.pos()
        self.position.setX(self.position.x()+self.parent().width())
        self.position.setY(self.position.y()-self.parent().height())
        self.move(self.position)

        # Set focus on first button (skip detach button)
        self.actions()[1].defaultWidget().setFocus()

    def _getRootAncestor(self):
        # All LauncherMenu menus visualized from the same root menu model
        # have lowest common ancestor which is a mainButton of the
        # LauncherWindow. If this button is destroyed all menus are also
        # destroyed, and all detached menus are closed. Because each Qt element
        # holds reference to its parent, mainButton of LauncherWindow can be
        # recursevly determined.

        self._object = self
        while type(self._object) is not LauncherWindow:
            self._object = self._object.parent()
        return self._object.mainButton


class LauncherSubMenu(LauncherMenu):
    # Implements a visualization of the menu when used as a sub menu. Popuped
    # from the main menu or button.
    #
    # Creates detach button and adds it to the menu.

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)
        self.detachButton = LauncherDetachButton(self)
        self.insertToMenu(self.detachButton, 0)

    def detach(self):
        # Create  new menu and open it as new window. Menu parent should be
        # mainButton on launcherWindow. This way it will be closed only if the
        # launcher is close or the root menu is changed.

        self._launcherWindow = self._getRootAncestor()
        self._detachedMenu = LauncherDetachedMenu(self.menuModel,
                                                  self._launcherWindow)
        # Put an existing filter to it and set propertys to open it as new
        # window.

        self._detachedMenu.searchInput.setText(self.filterTerm)
        self._detachedMenu.setWindowFlags(Qt.Window | Qt.Tool)
        self._detachedMenu.setAttribute(Qt.WA_DeleteOnClose, True)
        self._detachedMenu.setAttribute(Qt.WA_X11NetWmWindowTypeMenu, True)
        self._detachedMenu.setEnabled(True)
        self._detachedMenu.show()
        self._detachedMenu.move(self.pos().x(), self.pos().y())
        self.hide()


class LauncherDetachedMenu(LauncherMenu):
    # Creates detached menu. It adds find/search input. It also overrides the
    # hide() method of the menu, because it should not be hidden  when action
    # is performed.
    #
    # Removes detach button and filter/search widget but do not add them to
        # the menu.

    def __init__(self, menuModel, parent=None):
        LauncherMenu.__init__(self, menuModel, parent)
        self.searchInput = LauncherSearchWidget(self, self)
        self.insertToMenu(self.searchInput, 0)

    def hide(self):  # Detached menu cannot be hiden by left arrow.
        pass

    def changeEvent(self, changeEvent):
        # When top-level window is changed to detached menu window set focus to
        # search.

        if changeEvent.type() == QtCore.QEvent.ActivationChange and \
                self.isActiveWindow():
            self.searchInput.setFocus()

    def keyPressEvent(self, event):
        # Catch escape (originaly closes the menu window) and skip actions.

        if event.key() == Qt.Key_Escape:
            pass
        else:
            LauncherMenu.keyPressEvent(self, event)


class LauncherMenuWidgetAction(QtGui.QWidgetAction):
    # When QWidget needs to be appended to QMenu it must be "wrapped" into
    # QWidgetAction. This class "wrapps" LauncherButton in the smae way.
    # Further it also implements method to control the visibility of the menu
    # item (both action and widget).

    def __init__(self, widget, parent=None):
        QtGui.QWidgetAction.__init__(self, parent)
        self.setDefaultWidget(widget)

    def setVisibility(self, visibility):
        # Set visibility of both the widget action and the widget.

        self._widget = self.defaultWidget()
        self.setVisible(visibility)
        self._widget.setVisible(visibility)


class LauncherSearchWidget(QtGui.QLineEdit):
    # LauncherSearchWidget is QLineEdit which does filtering of menu items
    # recursevly by putting the filter  to child menus. When enter button is
    # pressed a search window with results is oppned (TODO).

    itemType = "search"

    def __init__(self, menu, parent=None):
        QtGui.QLineEdit.__init__(self, parent)
        self.textChanged.connect(lambda: menu.filterMenu(self.text()))


class LauncherItemSeparator(QtGui.QFrame):
    # Special LauncherMenuModelItem, with no text or help

    itemType = "separator"

    def __init__(self, style=None, key=None):
        LauncherMenuModelItem.__init__(self, None, style, key)


class LauncherMenuTitle(QtGui.QLabel):
    # Passive element with no action and no key focus.

    itemType = "title"

    def __init__(self, itemModel, parent=None):
        QtGui.QLabel.__init__(self, itemModel.text, parent)
        self.setStyleSheet("QLabel { color: blue; }")


class LauncherButton(QtGui.QPushButton):
    # Parent class for all active menu items. To recreate th enative menu
    # behaviour (when QActions are used) this class also handles keyboard
    # events to navigate through the menu.
    #
    # Parent of any LauncherButton must be a QMenu.

    def __init__(self, parent=None):
        QtGui.QPushButton.__init__(self, parent)
        self.setMouseTracking(True)

    def keyPressEvent(self, event):
        # Catch return and enter key pressed. Send clicked command to execute
        # action.
        #
        # Catch left arow button pressed on any of the menu buttons, to hide
        # the whole menu (parent) and return to previous level menu.
        #
        # Catch right arow button and skip it.

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
    # LauncherDetachButton is always shown as first item of popup menu. It
    # builds new LauncherMenu from the model of parent menu and opens it in
    # a new window.

    itemType = "detach"

    def __init__(self, parent=None):
        LauncherButton.__init__(self, parent)
        self.setStyleSheet("height: 2px")
        self.clicked.connect(parent.detach)


class LauncherNamedButton(LauncherButton):
    # LauncherNamedButton is a parent class to all buttons with text on them.

    def __init__(self, itemModel, parent=None):
        LauncherButton.__init__(self, parent)
        self.setText(itemModel.text)


class LauncherFileChoiceButton(LauncherNamedButton):
    # LauncherFileChoiceButton causes the launcher to change the root menu.

    itemType = "file-choice"

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        self._itemModel = itemModel
        self.clicked.connect(self._changeView)

    @pyqtSlot()
    def _changeView(self):
        # Find LauncherWindow and set new view.

        _candidate = self
        while _candidate.__class__.__name__ is not "LauncherWindow":
            _candidate = _candidate.parent()
        _candidate.setNewView(self._itemModel.rootMenuFile)
        self.parent().hide()  # When done hide popuped menu.


class LauncherCmdButton(LauncherNamedButton):
    # LauncherCmdButton executes shell command

    itemType = "cmd"

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        self._cmd = itemModel.cmd
        self.clicked.connect(self._executeCmd)

    @pyqtSlot()
    def _executeCmd(self):
        os.system(self._cmd)
        self.parent().hide()  # When done hide popuped menu.


class LauncherMenuButton(LauncherNamedButton):
    # LauncherMenuButton builds new menu from model. When pressed the menu is
    # popuped up.

    itemType = "menu"

    def __init__(self, itemModel, parent=None):
        LauncherNamedButton.__init__(self, itemModel, parent)
        self._menu = LauncherSubMenu(itemModel.subMenu, self)
        self.setMenu(self._menu)

    def keyPressEvent(self, event):
        # Submenu can be opened and closed with arrow keys

        if event.key() == Qt.Key_Right:
            self.click()
        elif event.key() == Qt.Key_Left:
            self.menu().hide()
        else:
            LauncherNamedButton.keyPressEvent(self, event)


if __name__ == '__main__':

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
        """)
    launcherWindow = LauncherWindow(sys.argv[1])
    launcherWindow.setGeometry(0, 0, 150, 0)
    launcherWindow.show()
    sys.exit(app.exec_())