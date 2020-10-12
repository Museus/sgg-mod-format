"""
Mod Importer for SuperGiant Games' Games

https://github.com/MagicGonads/sgg-mod-format
"""

__all__ = [
    # functions
    "main",
    "configure_globals",
    "start",
    "preplogfile",
    "cleanup",
    "safeget",
    "safeset",
    "dictmap",
    "hashfile",
    "lua_addimport",
    "xml_safeget",
    "xml_read",
    "xml_write",
    "xml_map",
    "xml_merge",
    "sjson_safeget",
    "sjson_clearDNE",
    "sjson_read",
    "sjson_write",
    "sjson_map",
    "sjson_merge",
    # variables
    "configfile",
    "logfile_prefix",
    "logfile_suffix",
    "edited_suffix",
    "scopemods",
    "modsrel",
    "baserel",
    "editrel",
    "logsrel",
    "gamerel",
    "do_log",
    "cfg_modify",
    "cfg_overwrite",
    "profile_use_special",
    # modules
    "logging",
    "xml",
    "sjson",
    "yaml",
    "hashlib",
    # other
    "DNE",
]
__version__ = "1.0a-r4"
__author__ = "Andre Issa"

# Dependencies

import os, sys, stat
import logging
import warnings
import hashlib
from getopt import getopt
from pathlib import Path
from shutil import copyfile, rmtree
from datetime import datetime
from collections import defaultdict
from distutils.dir_util import copy_tree
from distutils.errors import DistutilsFileError

## Importer Config

try:
    import yaml  # pip: PyYAML
except ModuleNotFoundError:
    yaml = None

## XML Handling

# Configurable Globals

configfile = "miconfig.yml"
#### These are better configured using the config file to be specific to different installs
scopemods = "Deploy"  # Must be accessible to game scope
modsrel = "Mods"
baserel = "Base Cache"
editrel = "Edit Cache"
logsrel = "Logs"
logfile_prefix = "log-modimp "
logfile_suffix = ".txt"
edited_suffix = ".hash"

# Data Functionality

DNE = ()  # 'Does Not Exist' singleton


def safeget(data, key, default=DNE, skipnone=True):
    if data is None:
        data = globals()
    if isinstance(data, list) or isinstance(data, tuple):
        if isinstance(key, int):
            if key < len(data) and key >= 0:
                ret = data[key]
                return default if skipnone and ret is None else ret
        return default
    if isinstance(data, dict):
        ret = data.get(key, default)
        return default if skipnone and ret is None else ret
    return default


def safeset(data, key, value):
    if data is None:
        data = globals()
    if isinstance(data, list):
        if isinstance(key, int):
            if key < len(data) and key >= 0:
                data[key] = value
    if isinstance(data, dict):
        data[key] = value


def dictmap(indict, mapdict):
    if mapdict is DNE or mapdict is indict:
        return indict
    if type(indict) == type(mapdict):
        if isinstance(mapdict, dict):
            for k, v in mapdict.items():
                indict[k] = dictmap(safeget(indict, k), v)
            return indict
    return mapdict


## LUA import statement adding


def lua_addimport(base, path):
    with open(base, "a") as basefile:
        basefile.write('\nImport "../' + path + '"')


# Main Process
def start(*args, **kwargs):

    configsetup(kwargs.get("predict", {}), kwargs.get("postdict", {}))

    global codes
    codes = defaultdict(list)
    global todeploy
    todeploy = {}

    # remove anything in the base cache that is not in the edit cache
    alt_print("Cleaning edits... (if there are issues validate/reinstall files)")
    restorebase()

    # remove the edit cache and base cache from the last run
    def onerror(func, path, exc_info):
        if not os.access(path, os.W_OK):
            os.chmod(path, stat.S_IWUSR)
            func(path)
        else:
            raise

    rmtree(editdir, onerror)
    Path(editdir).mkdir(parents=True, exist_ok=True)
    rmtree(basedir, onerror)
    Path(basedir).mkdir(parents=True, exist_ok=True)
    Path(modsdir).mkdir(parents=True, exist_ok=True)
    Path(deploydir).mkdir(parents=True, exist_ok=True)

    alt_print("\nReading mod files...")
    for mod in os.scandir(modsdir):
        modfile_load(mod.path.replace("\\", "/") + "/" + modfile)

    deploy_mods()

    alt_print("\nModified files for " + folderprofile + " mods:")
    for base, mods in codes.items():
        sort_mods(base, mods)
        make_base_edits(base, mods)

    bs = len(codes)
    ms = sum(map(len, codes.values()))

    alt_print(
        "\n"
        + str(bs)
        + " file"
        + ("s are", " is")[bs == 1]
        + " modified by"
        + " a total of "
        + str(ms)
        + " mod file"
        + "s" * (ms != 1)
        + "."
    )


def main_action(*args, **kwargs):
    try:
        start(*args, **kwargs)
    except Exception as e:
        alt_print("There was a critical error, now attempting to display the error")
        alt_print(
            "(if this doesn't work, try again in a terminal"
            + " which doesn't close, or check the log files)"
        )
        logging.getLogger("MainExceptions").exception(e)
        alt_input("Press any key to see the error...")
        raise RuntimeError("Encountered uncaught exception during program") from e
    alt_input("Press any key to end program...")


def main(*args, **kwargs):
    predict = {}
    postdict = {}

    opts, _ = getopt(
        args,
        "hmsoleic:g:p:S:H:",
        [
            "config=",
            "log_folder=",
            "echo",
            "input",
            "special",
            "log",
            "log-prefix=",
            "log-suffix=",
            "profile=,help",
            "special-set=",
            "game=",
            "modify",
            "overwrite",
            "--hash=",
        ],
    )

    global cfg_modify, cfg_overwrite, profile_use_special, configfile, gamerel

    for k, v in opts:
        if k in {"-h", "--help"}:
            print(MSG_CommandLineHelp)
            return
        elif k in {"-m", "--modify"}:
            cfg_modify = True
            if yaml is None:
                alt_warn("PyYAML module not found! Config cannot be written.")
        elif k in {"-o", "--overwrite"}:
            cfg_overwrite = True
        elif k in {"-s", "--special"}:
            profile_use_special = True
        elif k in {"-l", "--log"}:
            postdict["log"]
        elif k in {"-e", "--echo"}:
            postdict["echo"] = False
        elif k in {"-i", "--input"}:
            postdict["input"] = False
        elif k in {"-c", "--config"}:
            configfile = v
        elif k in {"-g", "--game"}:
            gamerel = v
        elif k in {"-p", "--profile"}:
            postdict["profile"] = v
        elif k in {"-p", "--profile"}:
            postdict["hashes"] = v.split(" ")
        elif k in {"-S", "--special-set"}:
            if yaml is not None:
                predict.setdefault("profile_special", {})
                predict["profile_special"] = yaml.load(v, Loader=yaml.FullLoader)
            else:
                alt_warn("PyYAML module not found! cannot parse command.")

    main_action(*args, predict=predict, postdict=postdict)


do_log = True
cfg_modify = False
cfg_overwrite = False
profile_use_special = False
gamerel = ".."

if __name__ == "__main__":
    do_echo = True
    do_input = True
    main(*sys.argv[1:])
else:
    do_echo = False
    do_input = False
