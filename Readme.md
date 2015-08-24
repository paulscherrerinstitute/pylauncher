# Overview

To configure and run luncher follow steps below.

1.  Modify configuration file (config/config.json) and properly specify following parameters for system you are using:

    launcher_base: path to direcotry where all launcher configurations are stored
    cmd:
        - command: prefix for commands that should be executed in shell (e.g. "bash -c")
        - caqtdm: SUPPORT NOT YET IMPLEMENTED (just prototype of possible configuration)

    ```
    {
        "Linux": {
            "launcher_base": "./menus/",
            "cmd": {
                "command": "bash -c"
            },
            "caqtdm":{
                "command": "caqtdm",
                "macro_flag": "-macro"
            }
        },
        "Windows": {
            "launcher_base": "./menus/",
            "cmd": {
                "command": ""
            },
            "caqtdm":{
                "command": "caqtdm",
                "macro_flag": "-macro"
            }
        },
        "OS_X": {
            "launcher_base": "./menus/",
            "cmd": {
                "command": ""
            },
            "caqtdm":{
                "command": "caqtdm",
                "macro_flag": "-macro"
            }
        }
    }
    ```

2.  Prepare menu configuration in json format (see example):
    ```
    {
        "menu-title": "F_L2",
        "file-choice": [
            {"text": "Load F_L1", "file": "menu_1.json"}
        ],
        "menu": [
            {"type": "title", "text": "Striptool"},
            {"type": "cmd", "text": "Strip Tool Generic", "param": "ls"},
            {"type": "separator"},
            {"type": "cmd", "text": "RF Startup", "param": "ls"},
            {"type": "cmd", "text": "Conditioning", "param": "ls"}
        ]
    }
    ```

3.  Start the launcher with following command:

    ```
    launcher.py <name-of-menu-file> <path-to-config-file>
    ```

    To run the launcher with example configuration run:

    ```
    launcher.py menu_1.json ./config/config.json
    ```

    Run `launcher -h` to access the help.

-----------------------------------------------
-----------------------------------------------

Currently json configuration format is supported (for details check examples in ./menus/ directory). The configuration file consists of 3 configurations to:
  1. set the menu title
    ```
    "menu-title": "This is menu title",
    ``` 

  2. To specify possible views of the launcher (e.g. exert, user, ...) [If no views leave empty]
    ```
    "file-choice": [
            {"text": "Expert", "file": "expert.json"}
            {"text": "Developer", "file": "dev.json"}
        ]
    ```
  3. Main section to specify launcher to define each launcher item. Following types of items are supported:

    - separator to visually separate menu items
    ```
    {"type": "separator"}
    ```

    - "title" is a special separator with text
    ```
    {"type": "title", "text": "This is button text"},
    ```

    - Button which executes shell command defined in parameter. parameter is combined with "cmd" parameter in configuration file (e.g. bash -c 'parameter').
    ```
    {"type": "cmd", "text": "This is command button", "param": "ls"},
    ```

    - Button which opens submenu defined in different file.
    ```
    {"type": "menu", "text": "Strip-tool", "file": "menu_2.json"}
    ```
