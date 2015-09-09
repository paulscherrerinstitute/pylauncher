# Overview
> All packages needed by launcher application are distributed in Anaconda [1] with python version 2.7. Anaconda can be found here: [Anaconda](http://continuum.io/downloads)

## Run pyLauncher application
Start the launcher with following command:

```
launcher.py <path_to_config_file> <path_to_menu_file>
```

To run the launcher with example configuration run:

```
launcher.py ./config/config.json ./menus/menu_1.json
```

For detailed help run  `launcher -h`.

Application may fail with the example configuration. Instructions how to set-up application for specific system can be found in the section [Configuration of launcher application]().
## Defining launcher menus
Each menu can be configured using predefined key value pairs in json files (for details check examples in ./menus/ directory). On top level configuration of the menu is divided in 3 sections:
 
 1. `menu-title`to set the menu title

    ```
    "menu-title": "This is menu title",
    ``` 

 2. `file-choice` to specify possible views of the launcher (e.g. exert, user, ...) [If no views leave empty]

    ```
    "file-choice": [
            {"text": "Expert", "file": "expert.json"}
            {"text": "Developer", "file": "dev.json"}
        ]

    ```
    > Possible views are shown in View menu in menu bar.

 3. `menu`, main section to define launcher items

    ```
    "menu": [
        {...},
        {...},
    ]
    ```

### Menu item types
Following types of items are supported in launcher application:
- **`separator`** to visually separate menu items with line.
    
    ```
    {"type": "separator"}
    ```

- **`title`** is a special separator with text.
    
    ```
    {"type": "title", "text": "This is button text", "theme": "green", "style":"color: #000000"}
    ```

    > `theme` and `style` and optional settings to modify apperance (explained in [Button styles]()). We discourage usage of `theme`.


- **`menu`** is a button which opens sub menu defined in `file`.
    
    ```
    {"type": "menu", "text": "Strip-tool", "file": "menu_2.json"}
    ```
    
- **`cmd`** is a basic button which executes shell command defined in `param`.

    ```
    {"type": "cmd", "text": "This is command button", "param": "myScript.sh", "theme": "blue", "style": "color: #000000", "tip": "What my script does.", "help-link": "http://www.link.com/to/help"}
    ```

    > `theme` and `style` and optional settings to modify appearance (explained in [Button styles]()). We discourage usage of `theme`.
    
    > `help_link` and `tip` are optional settings to specify user's help

    
- **`caqtdm`** is a button which opens a qt file screen in `file` with macros defined in `param`.

    ```
    {"type": "cmd", "text": "This is caqtdm button", "file": "submenu.json", "param": "MACRO1=M1,MACRO2=M2", "theme": "blue", "style": "color: #000000", "tip": "What this screen does.", "help-link": "http://www.link.com/to/help"}
    ```

    > `theme` and `style` and optional settings to modify appearance (explained in [Button styles]()). We discourage usage of `theme`.
    
    > `help_link` and `tip` are optional settings to specify user's help

    
- **`medm`** is a button which opens a medm screen defined in `file` with macros defined in `param`.

    ```
    {"type": "cmd", "text": "This is caqtdm button", "file": "submenu.json", "param": "MACRO1=M1,MACRO2=M2", "theme": "blue", "style": "color: #000000", "tip": "What this screen does.", "help-link": "http://www.link.com/to/help"}
    ```

    > `theme` and `style` and optional settings to modify appearance (explained in [Button styles]()). We discourage usage of `theme`.
    
    > `help_link` and `tip` are optional settings to specify user's help
    
### Button styles
Style definition follows [QSS](http://doc.qt.io/qt-4.8/stylesheet-syntax.html) syntax.

To simplify styling of launcher menu items, a set of predefined themes is available in folder defined in configuration file (see [Configuration of launcher application]()). Name of each file (e.g. green.qss) also presents the theme name (e.g. using `"theme": "green"` in configuration will apply configuration defined in green.qss).

User can has also possibility to apply desired qss configuration as a string in menu item definition (e.g.  `"style": "color: #000000"` will set the colour of the text to black.

## Configuration of launcher application
Launcher applications uses a configuration json file to specify the behavior of application on different systems (for now Linux, Windows and OS X are supported).

Example of configuration can be found in ./config/config.json. Configuration is split for different os systems with key value pairs, where key can be `Linux`, `Windows` or `OS_X` and value is an array of settings. See an example of configuration for Linux operating system bellow:

```
{
    "Linux": {
        "theme_base": "./qss/",
        "cmd": {
            "command": ""
        },
        "caqtdm":{
            "command": "caqtdm",
            "macro_flag": "-macro"
        },
        "medm":{
            "command": "medm -x",
            "macro_flag": "-macro"
        }
    },
    "Windows": { ... 
    },
    "OS_X": { ...
    }
}
```

### Configuration explanation:
- `theme_base` should be a path to folder where all possible themes are defined (if needed). For details see section [Button styles]().

Launcher application has 3 types of 'active' buttons (details in section [Defining launcher menus]()). To execute shell command, to open a qt screen and to open a medm screen. They are all executed as shell commands. How to call programs as caqtdm and medm must be defined in the configuration screen. Each of this button type has its own key with array of values.
- `command` is either a prefix to user specified shell command for `cmd` (e.g 'bash -c') or actual command to call a caqtdm or medem program in case of `caqtdm` and `medm`.
- `macro_flag`is flag after which macros are defined (usually '-macro')

>**Example:** On current PSI infrastructure caqtdm screen can be opened with command:

```
caqtdm -macro "MACRO1=M1,MACRO2=M2" this_is_my_gui.ui
```
> To enable same functionality on launcher following must be set:
```
"caqtdm":{
    "command": "caqtdm",
    "macro_flag": "-macro"
}
```