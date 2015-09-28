# Launcher

Launcher is a python based menu oriented application which allows users to access controls software on PSI. Launcher is very customizable tool which builds its appearance for different facilitates depending on menu-configuration files.

It is distributed over PSI as an [Anaconda](http://continuum.io/downloads) package which can be found [here](https://github.psi.ch/projects/AN).


## Table of content
- [Installation and usage of Launcher in Anaconda python environment](#installation-and-usage-of-launcher-in-anaconda-python-environment)
   - [Install Launcher](#install-launcher1)
   - [Run Launcher](#run-launcher1)
      - [Run Launcher with custom color scheme](#run-launcher-with-custom-color-scheme)
   - [Run menu converter](#run-menu-converter1)
   - [Buidling Launcher as Anaconda package](#buidling-launcher-as-anaconda-package)
- [Installation and usage of Launcher as none-conda application](#installation-and-usage-of-Launcher-as-none-conda-application)
   - [Install Launcher](#install-launcher2)
   - [Run Launcher](#run-launcher2)
   - [Run menu converter](#run-menu-converter2)
- [Defining a Launcher menu](#defining-a-launcher-menu)
   - [Menu item types](#menu-item-types)
   - [Styling of menu items](#styling-of-menu-items)
- [Configuration of Launcher](#configuration-of-launcher)
   - [Defining custom types](#defining-custom-types)
- [Customize Launcher appearance](#customize-launcher-appearance)
   - [Write Launcher style file](#write-launcher-style-file)
   - [Write Launcher theme file](#write-launcher-theme-file)

## Installation and usage of Launcher in Anaconda python environment

> To use Launcher as none-conda application consult section [Installation and usage of launcher as none-conda application](#instalaltion-and-usage-of-launcher-as-none-conda-application)

Generally PSI user does not need to install neither Anaconda or Launcher by himself because they are already part of PSI infrastructure. To use it on standard PSI machine one must just execute following command, to set Anaconda python as default python environment.

``` bash
export PATH=/opt/gfa/python-2.7/2.3.0/bin:$PATH
```

If one still needs to install Launcher application locally consult section [Install Launcher](#install-launcher).

### Install Launcher
_Note:_ All launcher dependencies are already part of standard Anaconda (Python 2.7. version) distribution which can be found here: [Anaconda](http://continuum.io/downloads)

> This section assumes that one already has a working Anaconda environment on his machine. To additionally install Launcher following steps must be made:

 1. Download prebuilt [Launcher package from PSI git](https://github.psi.ch/projects/AN)

 > To build Launcher as Anaconda package manually consult section [Buidling Launcher as Anaconda package](#buidling-launcher-as-anaconda-package).

 2. Execute `conda install <path_to_launcher_package>`


### Run Launcher
> This section assumes that Launcher is installed as Anaconda package and Anaconda is selected as default python environment.

Launcher can be started with following command:

``` bash
launcher <config_file> <menu_file>
```
> `<config_file>` is a file which defines general behavior of Launcher on different systems. For detailed information see section [Configuration of Launcher](#configuration-of-launcher).
>
> `<menu_file>` defines a Launcher 'menu' for specific facility, beamline, etc. To prepare menu files consult section [Defining a Launcher menu](#defining-a-launcher-menu)

For detailed help run  `launcher -h`.

#### Run Launcher with custom color scheme
If one wants to run Launcher with custom color scheme there is a `-s (--style)` flag available to pass a new color scheme file. Color scheme must be defined in a file that follows [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html) syntax. For details about styling a Launcher consult section [Write Launcher style file](#write-launcher-style-file).

To run a launcher with custom color scheme execute following command:

``` bash
launcher --style <style__qss_file> <config_file> <menu_file>
```

### Run menu converter
> This section assumes that Launcher is installed as Anaconda package and Anaconda is selected as default python environment.

Launcher also provides a tool to convert old PSI Launcher menu configurations to new one.

> Because of dependencies it skips any style specific configuration.

Converter can be started with following command:

``` bash
launcher-convert <original_config_file> <output_dir>
```

Converter offers multiple additional features such as converting whole menu or single file, overriding converted files, etc.
For detailed help run  `launcher -h`.

### Buidling Launcher as Anaconda package
> This section assumes that one already has a working Anaconda environment on his machine and conda-build is installed.

To build a last stable version of Launcher as Anaconda package one should execute following steps:

 1. Clone git repository:

 ``` bash
 git clone https://github.psi.ch/scm/cos/pylauncher.git
 ```

 2. Navigate to [./utils/conda_package]() and build:

 ``` bash
 cd ./utils/conda_package/
 conda build pylauncher
 ```

 _Note:_ To be able to build the anaconda package you need to have the `patchelf` package installed in your anaconda installation. If it is not provided in the central installation, create a new anaconda environment and install the package in there before building:

 ```bash
 conda create -n mybuildenvironment anaconda
 conda install patchelf
 ```

## Installation and usage of Launcher as none-conda application

If one wants to use Launcher with standard Python installation he must be aware that Launcher requires:
- Python 2.7 [Link](https://www.python.org/download/releases/2.7/)
- Qt 4 (4.8 or higher) [Link](http://www.qt.io/download/)
- PyQt4 (4.8 or higher) [Link](https://www.riverbankcomputing.com/software/pyqt/download)
- pyparsing [Link](http://pyparsing.wikispaces.com/Download+and+Installation)

### Install Launcher
To get a stable version of Launcher one should execute following steps:

 1. Clone git repository:

 ``` bash
 git clone https://github.psi.ch/scm/cos/pylauncher.git
 ```

 2. List version (tag) names:

 ``` bash
 git tag -l
 ```

 3. Select version:

  ``` bash
 git checkout tags/<tag_name>
 ```

Launcher application is located in the ./src/ directory.


### Run Launcher
> This section assumes that all dependencies are properly installed.

Launcher can be started with following command:

``` bash
<launcher-git-dir>/src/launcher.py <config_file> <menu_file>
```

> Detailed explanation of Launcher options can be found in section [Installation and usage of Launcher in Anaconda python environment > Run Launcher](#run-launcher-1).

### Run menu converter
> This section assumes that all dependencies are properly installed.

Launcher also provides a tool to convert old PSI Launcher menu configurations to new one.

> Because of dependencies it skips any style specific configuration.

Converter can be started with following command:

``` bash
<launcher-git-dir>/src/convert/convert.py <original_config_file> <output_dir>
```

Converter offers multiple additional features such as converting whole menu or single file, overriding converted files, etc.
For detailed help run  `launcher -h`.

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
Following types of items are supported in launcher application:
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

- **`cmd`** is a basic element which executes shell command defined with parameter `param`.

    ``` json
    {
        "type": "cmd",
        "text": "This is shown text",
        "params": ["shell_command"],
        "tip": "What command does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```
    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.


- **`caqtdm`** is an element which opens a caQtDM screen defined with parameter `file`. Optionally one can also define macros with parameter `param`.

    ``` json
    {
        "type": "caqtdm",
        "text": "This is shown text",
        "params": ["MACRO1=M1,MACRO2=M2", "screen_name"],
        "tip": "What this screen does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.


- **`medm`** is an element which opens a medm screen defined with parameter `file`. Optionally one can also define macros with parameter `param`.

    ``` json
    {
        "type": "medm",
        "text": "This is shown text",
        "params": ["MACRO1=M1,MACRO2=M2", "screen_name"],
        "tip": "What this screen does.",
        "help-link": "http://www.link.com/to/help",
        "theme": "blue",
        "style": "color: #000000"
    }
    ```

    > `help_link` and `tip` are optional parameters to specify user's help. `tip` is shown as standard tool-tip (on mouse hover) and `help-link`can be accessed with right mouse click on an item.

    > `theme` and `style` are optional parameters to modify appearance (consult [Styling of menu items](#styling-of-menu-items)) of element. We discourage usage of `theme`.

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
            "command": "{}"
        },
        "caqtdm":{
            "command": "caqtdm {} {}",
            "arg_flags": ["-macro ", ""]
        },
        "medm":{
            "command": "medm -x {} {}",
            "arg_flags": ["-macro ", ""]
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

  > **Example:** If `command`is set to `"command": "bash -c {} "` and item is defined as `{"type": "cmd", "params": ["shell_command"}]` following will be executed: `bash -c "shell_command"`.

  * `caqtdm` for defining a behavior of menu item which opens a caQtDM screen. Parameter `command` defines command which opens caQtDM and parameter `arg_flags` defines a macro prefix.

  > **Example:** If `command`is set to `"command": "caqtdm"`, `arg_flags` is set to `"arg_flags": ["-macro ", ""]` and item is defined as `{"type": "caqtdm", "params": ["MACRO1=M1,MACRO2=M2", "caqtdm_screen.ui"]` following will be executed: `caqtdm -macro "MACRO1=M1,MACRO2=M2" "caqtd_screen.ui"`.

  * `medm` for defining a behavior of menu item which opens a medm screen. Parameter `command` defines command which opens medm and parameter `arg_flags` defines a macro prefix.

  > **Example:** If `command`is set to `"command": "medm -x"`, `arg_flags` is set to `"arg_flags": ["-macro ", ""]` and item is defined as `{"type": "caqtdm", "params": ["MACRO1=M1,MACRO2=M2", "medm_screen.adl"]` following will be executed: `medm -x -macro "MACRO1=M1,MACRO2=M2" "medm_screen.adl"`.

### Defining custom types
Launcher currently supports defining of optional number of types which follows rules described in this section and are executed as shell commands. To add a new Launcher item type, configuration file must be extended with a key value pair, where key is the name of the type and value is an array with two parameters defining the command.

``` json
"my-type":{
    "command": "pylauncher {} {} {}",
    "arg_flags": ["--style ", "", ""]
}
```

Parameter `command` specifies the main layout of command, where each '{}' represents a configurable argument. In addition `arg_flags` specifies if any of this arguments has a flag (switch). Example above shows a definition of type "my-type" which opens a pylauncher application. So defined type will result in a shell command `pylauncher --style <arg1> <arg2> <arg3>`.

When preparing a menu, custom item type can be included using following syntax.


``` json
{
    "type": "my-type",
    "text": "This is shown text",
    "params": ["path/to/my/style.qss", "example/config/config.json", "example/menus/menu_example.json"],
}
```

> Tip, style, theme and help-link can also be defined.


Example above will result in shell command `pylauncher --style "path/to/my/style.qss" "example/config/config.json" "example/menus/menu_example.json"` which opens an [example_menu.json]() in Launcher with custom appearance defined in file [path/to/my/style.qss](). 

> Parameter `--style` can easily be skipped with defining `params` as `"params": ["", "example/config/config.json", "example/menus/menu_example.json"]`

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
- `LauncherButton` is most general and defines appearance of main title button and menu items of type: `cmd`, `caqtdm`, `medm` and `menu`.

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
