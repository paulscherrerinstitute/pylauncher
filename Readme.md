[![Build status](https://ci.appveyor.com/api/projects/status/cs8vtkbqk1qp5799?svg=true)](https://ci.appveyor.com/project/simongregorebner/pylauncher)

# Overview

The Launcher is a Python based, menu oriented application which allows users to launch applications and execute scripts. The Launcher is a customizable tool which builds its appearance (e.g. for different facilitates) depending on (menu) configuration files.


# Usage

The Launcher can be started as follows:

```bash
pylauncher <configuration>
```

where __configuration__ is the configuration file that defines the Launcher menu e.g. for a specific facility, beamline, setup, etc. .

It is possible to override the Launchers default mapping and/or default color scheme (style). This can be done using the options:

* `-m (--mapping) <mapping_file>`
* `-s (--style) <style_qss_file>`

For all available options and detailed help run

```bash
~$ pylauncher -h
usage: pylauncher [-h] [-m MAPPING] [-s STYLE] [--position X Y] configuration

positional arguments:
  configuration         menu/configuration file

optional arguments:
  -h, --help            show this help message and exit
  -m MAPPING, --mapping MAPPING
                        overwrite default mapping file
  -s STYLE, --style STYLE
                        overwrite default style (qss file)
  --position X Y        set initial position on the screen
```

_Note:_ `--position` - 0 0 is on the top left, -1 -1 is on the lower right.

## Configuration
Launcher menus are defined via JSON configuration file(s). On top level, the configuration of the menu is divided in the following 3 sections:

* __menu-title__ - An optional section to set the menu title. If no title is specified a file name is used instead.

```json
"menu-title": {
  "text": "This is the menu title",
}
```

* __file-choice__ - An optional section to specify possible views of the launcher (e.g. expert, user, ...) It can be omitted if no views need to be defined. Once the Launcher application is opened, one can select the different views from the __View__ menu in menu bar. Selecting new view reloads Launcher from file specified in the parameter _file_.

```json
"file-choice": [
  { "text": "This is view 1", "file": "menu1.json" },
  { "text": "This is view 2", "file": "menu2.json" }
]
```

* __menu__ - Main section to define launcher items. The type of each item is defined with the `type` property. All supported types with available parameters are described in the next section.

```json
"menu": [
    {
        "type": "menu",
        "text": "Submenu",
        "file": "submenu.json",
        "tip": "Menu tip.",
        "help-link": "http://www.link.com/to/help"
    },
    {
        "type": "separator"
    },
    { ...
    }
]
```

An detailed example can be found at [examples/menus/menu_example.json](examples/menus/menu_example.json).

### Menu Items

#### Help
For any menu item the two optional parameters __help_link__ and __tip__ can be specified to provide user help.

* __tip__ - Shows as standard tool-tip (on mouse hover). If not defined, default tool-tip is applied, showing text representation of corresponding command.
* __help-link__ - Can be accessed with right mouse click on an item


#### Styles
The appearance of a menu item can be customized via styles and themes. Therefore each menu item has following 2 optional paramters:

* __style__ - Enables very flexible customization with [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html) syntax
* __theme__ - Enables customization using one of the predefined themes. How to define a theme is described in section [Stylesheet](#stylesheet). However we strongly discourage the use of theme on a per menu item basis.

 _Note:_ There are currently no themes defined.

If both parameters are defined, both are used but `style` has a higher priority.

```json
{
  "type": "title",
  "text": "Title 2 - changed style",
  "style":"color: #ff0000",
  "theme":"green"
}
```


#### Types
There are 2 classes of item types, build-in item types and types specified in the launcher mapping file.

Other/New, custom types can be specified within a launcher mapping file. See section [Mapping](#mapping) for details.

##### Build-in

* __separator__ - Visually separate menu items with line.

```json
{
  "type": "separator"
}
```

* __title__ - A special separator with text. By default it is visually distinguishable from other items.

```json
{
  "type": "title",
  "text": "This is shown title"
}
```

* __menu__ - An element which opens a sub-menu that is specified in an external menu file that is defined with parameter _file_.

```json
{
  "type": "menu",
  "text": "This is shown text",
  "file": "menu_2.json"
}
```

##### Default
The default mapping file of __pylauncher__ specifies following types.

* __cmd__ - Executes a shell command defined with parameter __command__.

```json
{
  "type": "cmd",
  "text": "This is shown text",
  "command": "shell_command",
  "tip": "What command does.",
  "help-link": "http://www.link.com/to/help"
}
```

* __caqtdm__ - Opens a caQtDM screen defined with parameter __panel__. Macros are defined with parameter __macros__. Additional arguments can be passed with parameter __param__.

```json
{
  "type": "caqtdm",
  "text": "This is shown text",
  "panel": "screen_name.ui",
  "macros": "MACRO1=M1,MACRO2=M2",
  "param": "-attach -dg +250+250",
  "tip": "What this screen does.",
  "help-link": "http://www.link.com/to/help"
}
```

* __medm__ - Opens a medm screen defined with parameter __panel__. Macros are defined with parameter __macros__. Additional arguments can be passed with parameter __param__.

```json
{
  "type": "medm",
  "text": "This is shown text",
  "panel": "screen_name.adl",
  "macros": "MACRO1=M1,MACRO2=M2",
  "param": "-attach -dg +250+400",
  "tip": "What this screen does.",
  "help-link": "http://www.link.com/to/help"
}
```

* __pep__ - Opens a PEP screen defined with parameter __panel__ (i.e. .prc file). Additional arguments can be passed with parameter __param__.

```json
{
  "type": "pep",
  "text": "This is shown text",
  "panel": "screen_cfg.prc",
  "param": "-ws PV",
  "tip": "What this screen does.",
  "help-link": "http://www.link.com/to/help"
}
```



## Mapping
__pylauncher__ uses a mapping (json) file to specify the behavior of specific menu items on different systems. The default mapping file can be overwritten with the __-m <mapping__ option.

The mapping file has sections for each operating system, for Linux, Windows and OS_X right now.

```json
{
    "Linux": { ...
    },
    "Windows": { ...
    },
    "OS_X": { ...
    }
}
```

For each operating system following options can be configured:

* `theme_base` for defining a path to a directory where applicable themes are stored
* Any number of menu item type definitions that are according to following rules.

A new menu item type is defined by adding a key value pair, where key is the name of the type and value is a structure with two parameters defining the command to be executed on the shell as well as possible arguments.

```json
"my-type":{
    "command": "my-awsome-program {arg1} {arg2} {configuration}",
    "arg_flags": {"arg1": "--option ", "arg2": "--macro "}
}
```

The parameter __command__ specifies the main layout of command, where each _{arg}_ represents an argument which can be accessed with the keyword _arg_. In addition to this, the parameter __arg_flags__ specifies if any of this arguments has a flag (switch). If `arg_flags` is not defined it equals to `arg_flags= {}`

__Note:__ The example above shows a definition of type "my-type" which opens the _my-awsome-program_ application with argument _arg1_ and _arg2_. So defined type will result in a shell command

```bash
my-awsome-program --option <arg1> --macro <arg2> <configuration>
```

Menu items defined like this can be used in a launcher configuration as follows:

```json
{
    "type": "my-type",
    "text": "This is the text shown as label",
    "arg1": "myoption",
    "arg2": "example/my-macros.json"
    "configuration": "example/menus/menu_example.json"
}
```

Besides the attributes shown also _"tip"_, _"style"_, _"theme"_ and _"help-link"_ can be defined as well.

A full example of a mapping file can be found in [examples/mapping/mapping.json](examples/mapping/mapping.json).

## Stylesheet
The appearance of the Launcher or individual menu items can be customized via a [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html). The default appearance style can be overwritten at startup via the __--style__ option.


The class names used in the qss file strongly depend on the Launcher implementation.
There are 3 major classes that are used:

* __LauncherButton__ - Defines the appearance of main title button and menu items of type: _cmd_, _caqtdm_, _medm_, _menu_ and possible custom types
* __LauncherMenuTitle__ - Defines the appearance of menu item of type _title_
* __LauncherDetachButton__ -  Defines the appearance of detached button

The style configuration needs to be saved to a file with the suffix .qss. The file name of the file defines the theme name that can be used in the menu item configuration. For example, the stylesheed named __green.qss__ defines the theme with name __green__.

Example:

```css
LauncherButton{
    background-color: #e9e9e9;
    text-align:left;
    border-image: none;
    border: none;
}

LauncherButton:focus, LauncherButton:pressed {
    background-color: #bdbdbd;
    outline: none
}

LauncherMenuTitle{
    background-color: #e9e9e9;
    text-align:left;
    color: #0000FF
}

LauncherDetachButton{
    background-color: #666666;
}
```

# Installation
## Anaconda
Anaconda comes with all required packages for __pylauncher__. To install the package use

```bash
conda install -c https://conda.anaconda.org/paulscherrerinstitute pylauncher
```

## Standard Python
To use __pylauncher__ with a standard Python following requirements need to be met:

* [Qt 4](http://www.qt.io/download/) (4.8 or higher)
* [PyQt4](https://www.riverbankcomputing.com/software/pyqt/download) (4.8 or higher)
* [pyparsing](http://pyparsing.wikispaces.com/Download+and+Installation)

To "install" the latest version clone Git repository

 ```bash
 git clone https://github.com/paulscherrerinstitute/pylauncher.git
 ```

The code is then located in the `src/` directory.

# Development
## Anaconda Package
> This section assumes that one already has a working Anaconda environment on his machine and conda-build is installed.

To build an Anaconda package of the last stable version of __pylauncher__ do

* Clone Git repository

```bash
git clone https://github.com/paulscherrerinstitute/pylauncher.git
```

* Build package

``` bash
cd ./utils/conda_package
conda build pylauncher
```

_Note:_ To be able to build the Anaconda package you need to have the `patchelf` package installed in your Anaconda installation. If it is not provided in the central installation, create a new Anaconda environment and install the package in there before building

```bash
conda create -n build_environment python patchelf
source activate build_environment
```
