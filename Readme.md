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

# Configuration

# Mapping

# Stylesheet


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

## Configuration of Launcher
Launcher applications uses a configuration json file to specify the behavior of application on different systems (for now Linux, Windows and OS X are supported).

Full example of configuration can be found in [.examples/config/config.json](https://github.psi.ch/projects/COS/repos/pylauncher/browse/examples/config/config.json). Configuration is split into sections, one for each operating systems. An example of configuration for Linux operating system is shown bellow:

``` json
{

    "Linux": {
        "theme_base": "../themes/",
        "cmd": {
            "command": "{command}"
        },
        "caqtdm":{
            "command": "caqtdm {macros} {panel}",
            "arg_flags": {"macros": "-macro "}
        },
        "medm":{
            "command": "medm -x {macros} {panel}",
            "arg_flags": {"macros": "-macro "}
        }
    },
    "Windows": { ...
    },
    "OS_X": { ...
    }
}
```

Configuration for each operating system consists of:
 1. `theme_base` for defining a path to a directory where all possible themes are stored. For details about usage of themes consult section [Styling of menu items](#styling-of-menu-items).

 2. Any number of type definitions. In current example configuration following types are supported (custom types can be specified with rules described in section [Defining custom types](#defining-custom-types)):
  * `cmd` for defining a behavior of menu item which executes a shell command. Parameter `command` is used as a prefix to user specified command.

  > **Example:** If `command`is set to `"command": "bash -c {command} "` and item is defined as `{"type": "cmd", "command": "shell_command"}` following will be executed: `bash -c "shell_command"`.

  * `caqtdm` for defining a behavior of menu item which opens a caQtDM screen. Parameter `command` defines command which opens caQtDM and parameter `arg_flags` defines a macro prefix.

  > **Example:** If `command`is set to `"command": "caqtdm {macros} {panel}"`, `arg_flags` is set to `"arg_flags": ["macros ": "-macro"]` and item is defined as `{"type": "caqtdm", "panel": "caqtdm_screen.ui", "macros": "MACRO1=M1,MACRO2=M2"` following will be executed: `caqtdm -macro "MACRO1=M1,MACRO2=M2" "caqtd_screen.ui"`.

  * `medm` for defining a behavior of menu item which opens a medm screen. Parameter `command` defines command which opens medm and parameter `arg_flags` defines a macro prefix.

  > **Example:** If `command`is set to `"command": "medm -x {macros} {panel}"`, `arg_flags` is set to `"arg_flags": ["macros ": "-macro"]` and item is defined as {"type": "medm", "panel": "medm_screen.adl", "macros": ""` following will be executed: `medm -x "medm_screen.adl"`.

### Defining custom types
Launcher currently supports defining of optional number of types which follows rules described in this section. All so defined types are executed as shell commands. To add a new Launcher item type, configuration file must be extended with a key value pair, where key is the name of the type and value is an array with two parameters defining the command.

``` json
"my-type":{
    "command": "pylauncher {style} {config} {menu}",
    "arg_flags": {"arg1": "--style ", "arg2": "--config "}
}
```

Parameter `command` specifies the main layout of command, where each '{arg}' represents an argument which can be accessed with key word "arg". In addition parameter `arg_flags` specifies if any of this arguments has a flag (switch). Example above shows a definition of type "my-type" which opens a pylauncher application. So defined type will result in a shell command `pylauncher --style <style> --config <config> <menu>`.

> If `arg_flags` is not defined it equals to `arg_flags= {}`

So defined type can be used in a menu definition with following syntax.


``` json
{
    "type": "my-type",
    "text": "This is shown text",
    "style": "path/to/my/style.qss",
    "config": "example/config/config.json"
    "menu": "example/menus/menu_example.json",
}
```

> `"tip"`, `"style"`, `"theme"` and `"help-link"` can also be defined.


Example above will result in shell command `pylauncher --style "path/to/my/style.qss" --config "example/config/config.json" "example/menus/menu_example.json"`.

> Switches (like `--style` and --config) can be skipped with defining them as an empty string. For example if style is not defined `"style": ""` this results in shell command `pylauncher --config "example/config/config.json" "example/menus/menu_example.json"`.

## Customize Launcher appearance
To customize appearance of Launcher one must be familiar with [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html) syntax.

### Write Launcher style file
At startup of launcher default appearance of launcher can be set as mentioned in section [Installation and usage of Launcher in Anaconda python environment > Run Launcher](#run-launcher-1). Such styling (.qss) file must use class names that strongly depend on Launcher implementation. Example can be found bellow:

``` css
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
- `LauncherButton` is most general and defines appearance of main title button and menu items of type: `cmd`, `caqtdm`, `medm`, `menu` and possible custom types.

- `LauncherMenuTitle` defines appearance of menu item of type `title`.

- `LauncherDetachButton` defines appearance of detached button.


### Write Launcher theme file
For custom theme to work following must be done:

 1. Theme file must be created. Basic one should look similar to:

 ``` css
 LauncherButton, LauncherMenuTitle{
     background-color: #0f9d58
 }
 ```

 > Class names strongly depend on Launcher implementation so they should not be changed.

 2. Theme file must be saved into directory defined by configuration file (consult [Configuration of Launcher](#configuration-of-launcher)). File name defines a theme name.

 > **Example:** File named [green.qss] defines theme with name *green*.
