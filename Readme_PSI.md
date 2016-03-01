# Overview

At PSI, the __pylauncher__ is distributed as an [Anaconda](http://continuum.io/downloads) package and is installed by default in the PSI Controls central Python installation located at `/opt/gfa/`. For the time being the Launcher can be used by bringing this Python into your PATH as follows:

```bash
source /opt/gfa/python
```

Please refer to the generic [Readme](Readme.md) regarding the usage.

# Converter
__pylauncher__ provides a tool, __pylauncher-convert__, to convert old PSI Launcher configurations. To convert configurations use:

``` bash
pylauncher-convert <original_config_file> <output_dir>
```

__pylauncher-convert__ offers multiple features such as converting whole menu or single file, overriding converted files, etc. For detailed help run

```bash
~$ pylauncher-convert -h
usage: pylauncher-convert [-h] [-o] [-s] [-f] inputfile outputfolder

positional arguments:
  inputfile        TCL configuration script to be converted
  outputfolder     folder where the converted json file will be stored

optional arguments:
  -h, --help       show this help message and exit
  -o, --overwrite  overwrite output files that already exist
  -s, --single     convert only a single file (nonrecursive)
  -f, --force      continue even if some files cannot be found
```

__Note:__ Because of dependencies __pylauncher-convert__ skips any style specific configuration.
