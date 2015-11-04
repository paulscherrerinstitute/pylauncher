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
pylauncher [-h] [-m MAPPING] [-s STYLE] configuration

positional arguments:
  configuration              menu/configuration file

optional arguments:
  -h, --help            show this help message and exit
  -m MAPPING, --mapping MAPPING
                        overwrite default mapping
  -s STYLE, --style STYLE
                        overwrite default stylesheet (i.e. qss file)
```

## Configuration

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
Anaconda comes with all required packages for __pylauncher__. To install the package that was previously deployed on a central repository use

```bash
conda install pylauncher
```

If the package is not in a central repository use:

```bash
conda install <path_to_launcher_package>
```

## Standard Python
To use __pylauncher__ with a standard Python following requirements need to be met:

* Python 2.7 [Link](https://www.python.org/download/releases/2.7/)
* Qt 4 (4.8 or higher) [Link](http://www.qt.io/download/)
* PyQt4 (4.8 or higher) [Link](https://www.riverbankcomputing.com/software/pyqt/download)
* pyparsing [Link](http://pyparsing.wikispaces.com/Download+and+Installation)

To "install" the latest version clone Git repository

 ```bash
 git clone https://github.psi.ch/scm/cos/pylauncher.git
 ```

The code is then located in the `src/` directory.

# Development
## Anaconda Package
> This section assumes that one already has a working Anaconda environment on his machine and conda-build is installed.

To build an Anaconda package of the last stable version of __pylauncher__ do

* Clone Git repository

```bash
git clone https://github.psi.ch/scm/cos/pylauncher.git
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




## Defining a Launcher menu
Each menu can be configured using predefined key value pairs in json files (check full example: [./examples/menus/menu_example.json](https://github.psi.ch/projects/COS/repos/pylauncher/browse/examples/menus/menu_example.json) directory). On top level, configuration of the menu is divided in 3 sections:

 1. `menu-title` is an optional section to set the menu title. If no title is specified a file name is used instead.

    ``` json
    "menu-title": {
        "text": "This is menu title",
        "theme": "light-blue",
        "style": "color: #000000"
    }
    ```
    > `theme` and `style` are optional settings to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of main title button. We discourage usage of `theme`.

 2. `file-choice` is an optional section to specify possible views of the launcher (e.g. expert, user, ...) It can be skipped if no views are defined.

    ``` json
    "file-choice": [
            {"text": "This is view 1", "file": "menu1.json"},
            {"text": "This is view 2", "file": "menu2.json"}
        ]

    ```

    Once Launcher application is opened, one can select different view from **View** menu in menu bar. Selecting new view reloads Launcher from file specified in parameter `file`.

 3. `menu` is a main section to define launcher items

    ``` json
    "menu": [
        {
            "type": "menu",
            "text": "Submenu",
            "file": "submenu.json",
            "theme": "green",
            "style": "color: #000000"
        },
        {
            "type": "separator"
        },
        {

        ...

        }
    ]
    ```

    One can specify as many items as needed. Type of each item is defined with `type` property. All supported types with available parameters are described in section [Menu item types](#menu-item-types).

### Menu item types
Following types of items are currently supported in launcher application:

- **`separator`** to visually separate menu items with line.

    ``` json
    {"type": "separator"}
    ```

- **`title`** is a special separator with text. By default it is visually distinguishable from other items.

    ``` json
    {
        "type": "title",
        "text": "This is shown title",
        "theme": "red",
        "style":"color: #000000"
    }
    ```

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of title separator. We discourage usage of `theme`.


- **`menu`** is an element which opens sub-menu specified in a menu file defined with parameter `file`.

    ``` json
    {
        "type": "menu",
        "text": "This is shown text",
        "file": "menu_2.json",
        "tip": "Menu tip.",
        "help-link": "http://www.link.com/to/help",
        "theme": "green",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.

- **`cmd`** is a basic element which executes shell command defined with parameter `command`.

    ``` json
    {
        "type": "cmd",
        "text": "This is shown text",
        "command": "shell_command",
        "tip": "What command does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```
    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.


- **`caqtdm`** is an element which opens a caQtDM screen defined with parameter `panel`. Macros are defined with parameter `macros`. Additional arguments can be passed with parameter `param`.

    ``` json
    {
        "type": "caqtdm",
        "text": "This is shown text",
        "panel": "screen_name.ui",
        "macros": "MACRO1=M1,MACRO2=M2",
        "param": "-attach -dg +250+250",
        "tip": "What this screen does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.


- **`medm`** is an element which opens a medm screen defined with parameter `panel`. Macros are defined with parameter `macros`. Additional arguments can be passed with parameter `param`.

    ``` json
    {
        "type": "medm",
        "text": "This is shown text",
        "panel": "screen_name.adl",
        "macros": "MACRO1=M1,MACRO2=M2",
        "param": "-attach -dg +250+400",
        "tip": "What this screen does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.

- **`pep`** is an element which opens a pep screen defined with parameter `panel` (for .prc files) or/and `param` (for command line difintions).

    ``` json
    {
        "type": "pep",
        "text": "This is shown text",
        "panel": "screen_cfg.prc",
        "param": "-ws PV",
        "tip": "What this screen does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.

_Note:_ New, custom types can be  specified within configuration file. They can be defined with rules described in section [Defining custom types](#defining-custom-types).

### Styling of menu items
If needed one can do a per item customization of the menu appearance. For this purpose large majority of the item types (for specific item consult section [Menu item types](#menu-item-types)) exposes following parameters:
 1. `style` which enables very flexible customization with [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html) syntax.
 2. `theme` which enables customization using one of the predefined themes. How to define a theme is described in section [Write Launcher theme file](#write-launcher-theme-file).

 _Note:_ There are currently no themes defined.


If both parameters are defined, both are used but `style` has a higher priority.

**Example:**
One uses theme that defines `background-color: red` and text color `color: blue`. Then he can redefine text color with setting `style` to `color: black`. This setting will result in an item with red background and black text.
