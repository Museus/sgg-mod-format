
# Private Globals

MSG_ConfigHelp = """
Create or configure a folder profile using:
 * config file (requires PyYAML): `profiles` in '{0}'
Or change the active folder profile using:
 * config file (requires PyYAML): `profile` in '{0}'
 * terminal option: --profile
Use and modify the special profile:
 * terminal options:
        --special
        --special-set <profile YAML> (requires PyYAML)
Override the game path temporarily:
 * terminal option: --game <path to game>
"""

MSG_MissingFolderProfile = (
    """
The selected profile is not a default or configured folder profile or is configured incorrectly.
Make sure the profile is configured to the actual game directory.
Alternatively, make sure this program is in the appropriate location.
"""
    + MSG_ConfigHelp
)

MSG_GameHasNoScope = """
The folder '{0}' does not exist.
Are you sure {1} is the game's proper location?
You may need to change the path 'game_dir_path' in the profile's config.
""" + MSG_ConfigHelp.format(
    "{2}"
)

MSG_DeployNotInScope = """
Deployment folder '{0}' is not a subfolder of '{1}'.
This means deploying mods is impossible!
Configure the deployment path 'folder_deployed' to be within the content.
""" + MSG_ConfigHelp.format(
    "{2}"
)

MSG_CommandLineHelp = """
    -h --help
        print this help text
    -m --modify
        modify the config and halt
    -o --overwrite
        overwrite the config with default
    -s --special
        use special profile
    -l --log
        disable logging
    -e --echo
        disable echo
    -i --input
        disable input (input gets passed defaults)
    -c --config <relative file path>
        choose config file
    -H --hashes <space separated hash names>
        hashes used to compare files in edit cache (ie, "md5 sha1")
    -g --game <relative folder path>
        temporarily use a different game directory
    -p --profile <profile name>
        use a particular folder profile
    -S --special-set <profile YAML>
        map YAML to the special profile (requires PyYAML)
        
"""

default_target = []
default_priority = 100

modfile = "modfile.txt"
modfile_mlcom_start = "-:"
modfile_mlcom_end = ":-"
modfile_comment = "::"
modfile_linebreak = ";"
modfile_delimiter = ","

KWRD_to = ["To"]
KWRD_load = ["Load"]
KWRD_priority = ["Priority"]
KWRD_include = ["Include"]
KWRD_deploy = ["Deploy"]
KWRD_import = ["Import"]
KWRD_xml = ["XML"]
KWRD_sjson = ["SJSON"]

scope = "Content"
importscope = "Scripts"
localsources = {"sggmodimp.py", "sjson.py", "cli", "yaml"}

profile_template = {
    "default_target": None,
    "game_dir_path": None,
    "folder_deployed": None,
    "folder_mods": None,
    "folder_basecache": None,
    "folder_editcache": None,
}

default_profiles = {
    "Hades": {
        "default_target": ["Scripts/RoomManager.lua"],
    },
    "Pyre": {
        "default_target": ["Scripts/Campaign.lua", "Scripts/MPScripts.lua"],
    },
    "Transistor": {
        "default_target": ["Scripts/AllCampaignScripts.txt"],
    },
    "Bastion": {},
}

for k, v in default_profiles.items():
    default_profiles[k] = dictmap(profile_template.copy(), v)

YML_framework = {
    "echo": True,
    "input": True,
    "log": True,
    "hashes": hashes,
    "profile": None,
    "profile_special": profile_template,
    "profiles": default_profiles,
    "log_folder": None,
    "log_prefix": None,
    "log_suffix": None,
}