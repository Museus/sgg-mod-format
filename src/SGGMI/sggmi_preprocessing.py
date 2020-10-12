# Global Preprocessing


def thetime():
    return datetime.now().strftime("%d.%m.%Y-%I.%M%p-%S.%f")


def preplogfile():
    if do_log:
        Path(logsdir).mkdir(parents=True, exist_ok=True)
        logging.basicConfig(
            filename=logsdir + "/" + logfile_prefix + thetime() + logfile_suffix,
            level=logging.INFO,
        )
    logging.captureWarnings(do_log and not do_echo)


def update_scope(rel=".."):
    global gamedir
    gamedir = os.path.join(os.path.realpath(rel), "").replace("\\", "/")[:-1]
    global scopeparent
    scopeparent = gamedir.split("/")[-1]
    global scopedir
    scopedir = gamedir + "/" + scope


def configure_globals(condict={}, flow=True):

    global do_echo, do_log, do_input
    do_echo = safeget(condict, "echo", do_echo)
    do_log = safeget(condict, "log", do_log)
    do_input = safeget(condict, "input", do_input)

    global logsrel, logfile_prefix, logfile_suffix
    logsrel = safeget(condict, "log_folder", logsrel)
    logfile_prefix = safeget(condict, "log_prefix", logfile_prefix)
    logfile_suffix = safeget(condict, "log_suffix", logfile_suffix)

    global logsdir
    logsdir = os.path.join(os.path.realpath(logsrel), "").replace("\\", "/")
    preplogfile()

    global hashes
    hashes = safeget(condict, "hashes", hashes)

    global thisfile, localdir, localparent
    thisfile = os.path.realpath(__file__).replace("\\", "/")
    localdir = "/".join(thisfile.split("/")[:-1])
    localparent = localdir.split("/")[-2]

    global profiles, profile, folderprofile
    profiles = {}
    profiles.update(safeget(condict, "profiles", {}))
    profile = None

    folderprofile = safeget(condict, "profile", localparent)
    if profile_use_special:
        profile = safeget(condict, "profile_special", profile)
    while profile is None:
        profile = safeget(profiles, folderprofile, None)
        if profile is None:
            if not flow:
                alt_warn(MSG_MissingFolderProfile.format(configfile))
                profile = {}
                break
            folderprofile = alt_input(
                "Type the name of a profile, " + "or leave empty to cancel:\n\t> "
            )
            if not folderprofile:
                alt_warn(MSG_MissingFolderProfile.format(configfile))
                alt_exit(1)

    update_scope(safeget(profile, "game_dir_path", gamerel))

    global default_target
    default_target = profile.get("default_target", default_target)

    global scopemods, modsrel, modsabs, baserel, baseabs, editrel, editabs
    scopemods = safeget(profile, "folder_deployed", scopemods)
    modsrel = safeget(profile, "folder_mods", modsrel)
    baserel = safeget(profile, "folder_basecache", baserel)
    editrel = safeget(profile, "folder_editcache", editrel)

    global basedir
    basedir = (scopedir + "/" + baserel).replace("\\", "/")
    if not os.path.isabs(basedir):
        basedir = os.path.join(os.path.realpath(basedir), "").replace("\\", "/")[:-1]

    global editdir
    editdir = (scopedir + "/" + editrel).replace("\\", "/")
    if not os.path.isabs(editdir):
        editdir = os.path.join(os.path.realpath(editdir), "").replace("\\", "/")[:-1]

    global modsdir
    modsdir = (scopedir + "/" + modsrel).replace("\\", "/")
    if not os.path.isabs(modsdir):
        modsdir = os.path.join(os.path.realpath(modsdir), "").replace("\\", "/")[:-1]

    global deploydir
    deploydir = (scopedir + "/" + scopemods).replace("\\", "/")
    if not os.path.isabs(deploydir):
        deploydir = os.path.join(os.path.realpath(deploydir), "").replace("\\", "/")[
            :-1
        ]

    global local_in_scope, base_in_scope, edit_in_scope, mods_in_scope, deploy_in_scope, game_has_scope
    local_in_scope = (
        base_in_scope
    ) = edit_in_scope = mods_in_scope = deploy_in_scope = None

    game_has_scope = in_scope(scopedir).message == "DirInScope"
    local_in_scope = in_scope(thisfile).message == "FileInScope"

    if not game_has_scope:
        alt_warn(MSG_GameHasNoScope.format(scopedir, scopeparent, configfile))
        if flow:
            alt_exit(1)

    base_in_scope = in_scope(basedir, True).message == "DirInScope"
    edit_in_scope = in_scope(editdir, True).message == "DirInScope"
    mods_in_scope = in_scope(basedir, True).message == "DirInScope"
    deploy_in_scope = in_scope(deploydir, True).message == "DirInScope"

    if not deploy_in_scope:
        alt_warn(MSG_DeployNotInScope.format(deploydir, scopedir, configfile))
        if flow:
            alt_exit(1)

    global deploy_from_scope
    deploy_from_scope = deploydir[
        len(os.path.commonprefix([scopedir, deploydir])) + 1 :
    ]


def configsetup(predict={}, postdict={}):
    condict = YML_framework
    if yaml is not None and not cfg_overwrite:
        try:
            with open(configfile) as f:
                condict.update(yaml.load(f, Loader=yaml.FullLoader))
        except FileNotFoundError:
            pass

    dictmap(condict, predict)
    if cfg_modify:
        dictmap(condict, postdict)

    if yaml is not None:
        with open(configfile, "w") as f:
            yaml.dump(condict, f)

    if cfg_modify:
        alt_print("Config modification successful.")
        alt_exit(0)

    dictmap(condict, postdict)
    configure_globals(condict)

