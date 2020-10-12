# FILE/MOD LOADING
def modfile_startswith(tokens, keyword, n):
    return tokens[: len(keyword)] == keyword and len(tokens) >= len(keyword) + 1


def modfile_loadcommand(reldir, tokens, to, n, mode, cfg={}, **load):
    for scopepath in to:
        path = scopedir + "/" + scopepath
        if in_scope(path):
            args = [tokens[i::n] for i in range(n)]
            for i in range(len(args[-1])):
                sources = [
                    reldir + "/" + arg[i].replace('"', "").replace("\\", "/")
                    for arg in args
                ]
                paths = []
                num = -1
                for source in sources:
                    if os.path.isdir(modsdir + "/" + source):
                        tpath = []
                        for file in os.scandir(source):
                            file = file.path.replace("\\", "/")
                            if in_scope(file):
                                tpath.append(file)
                        paths.append(tpath)
                        if num > len(tpath) or num < 0:
                            num = len(tpath)
                    elif in_scope(modsdir + "/" + source):
                        paths.append(source)
                if paths:
                    for j in range(abs(num)):
                        sources = [x[j] if isinstance(x, list) else x for x in paths]
                        for src in sources:
                            todeploy[src] = dictmap(todeploy.get(src, cfg), cfg)
                        f = lambda x: map(lambda y: deploy_from_scope + "/" + y, x)
                        codes[scopepath].append(
                            Mod(
                                "\n".join(sources),
                                tuple(f(sources)),
                                mode,
                                scopepath,
                                len(codes[scopepath]),
                                **load
                            )
                        )


def modfile_load(filename, echo=True):
    sig = is_subfile(filename, modsdir)
    if sig:
        prefix = os.path.commonprefix([filename, modsdir])
        relname = filename[len(prefix) + 1 :]
        try:
            file = open(filename, "r")
        except IOError:
            return
        if echo:
            alt_print(relname)

        reldir = "/".join(relname.split("/")[:-1])
        p = default_priority
        to = default_target
        cfg = {}

        with file:
            for line in modfile_splitlines(file.read()):
                tokens = modfile_tokenise(line)
                if len(tokens) == 0:
                    continue

                elif modfile_startswith(tokens, KWRD_to, 0):
                    to = [s.replace("\\", "/") for s in tokens[1:]]
                    if len(to) == 0:
                        to = default_target
                elif modfile_startswith(tokens, KWRD_load, 0):
                    n = len(KWRD_load) + len(KWRD_priority)
                    if tokens[len(KWRD_load) : n] == KWRD_priority:
                        if len(tokens) > n:
                            try:
                                p = int(tokens[n])
                            except ValueError:
                                pass
                        else:
                            p = default_priority
                if modfile_startswith(tokens, KWRD_include, 1):
                    for s in tokens[1:]:
                        modfile_load(
                            reldir + "/" + s.replace('"', "").replace("\\", "/"), echo
                        )
                elif modfile_startswith(tokens, KWRD_deploy, 1):
                    for s in tokens[1:]:
                        check = is_subfile(s, modsdir)
                        if check:
                            todeploy[s] = dictmap(todeploy.get(s, cfg), cfg)
                        elif check.message == "SubDir":
                            for f in os.scandir(s):
                                S = f.path.replace("\\", "/")
                                todeploy[S] = dictmap(todeploy.get(S, cfg), cfg)

                elif modfile_startswith(tokens, KWRD_import, 1):
                    modfile_loadcommand(
                        reldir,
                        tokens[len(KWRD_import) :],
                        to,
                        1,
                        "lua",
                        cfg,
                        priority=p,
                    )
                elif modfile_startswith(tokens, KWRD_xml, 1):
                    modfile_loadcommand(
                        reldir, tokens[len(KWRD_xml) :], to, 1, "xml", cfg, priority=p
                    )
                elif modfile_startswith(tokens, KWRD_sjson, 1):
                    if sjson:
                        modfile_loadcommand(
                            reldir,
                            tokens[len(KWRD_sjson) :],
                            to,
                            1,
                            "sjson",
                            cfg,
                            priority=p,
                        )
                    else:
                        alt_warn("SJSON module not found! Skipped command: " + line)

    elif sig.message == "SubDir":
        for file in os.scandir(filename):
            modfile_load(file.path.replace("\\", "/"), echo)


def is_edited(base):
    if os.path.isfile(editdir + "/" + base + edited_suffix):
        efile = open(editdir + "/" + base + edited_suffix, "r")
        data = efile.read()
        efile.close()
        return data == hashfile(scopedir + "/" + base)
    return False


def deploy_mods():
    for fs, cfg in todeploy.items():
        Path(deploydir + "/" + "/".join(fs.split("/")[:-1])).mkdir(
            parents=True, exist_ok=True
        )
        copyfile(modsdir + "/" + fs, deploydir + "/" + fs)


def sort_mods(base, mods):
    codes[base].sort(key=lambda x: x.load["priority"])
    for i in range(len(mods)):
        mods[i].id = i


def make_base_edits(base, mods, echo=True):
    Path(basedir + "/" + "/".join(base.split("/")[:-1])).mkdir(
        parents=True, exist_ok=True
    )
    copyfile(scopedir + "/" + base, basedir + "/" + base)
    if echo:
        i = 0
        alt_print("\n" + base)

    try:
        for mod in mods:
            if mod.mode == "lua":
                lua_addimport(scopedir + "/" + base, mod.data[0])
            elif mod.mode == "xml":
                xml_merge(scopedir + "/" + base, mod.data[0])
            elif mod.mode == "sjson":
                sjson_merge(scopedir + "/" + base, mod.data[0])
            if echo:
                k = i + 1
                for s in mod.src.split("\n"):
                    i += 1
                    alt_print(
                        " #"
                        + str(i)
                        + " +" * (k < i)
                        + " " * ((k >= i) + 5 - len(str(i)))
                        + s
                    )
    except Exception as e:
        copyfile(basedir + "/" + base, scopedir + "/" + base)
        raise RuntimeError(
            "Encountered uncaught exception while implementing mod changes"
        ) from e

    Path(editdir + "/" + "/".join(base.split("/")[:-1])).mkdir(
        parents=True, exist_ok=True
    )
    hashfile(scopedir + "/" + base, editdir + "/" + base + edited_suffix)


def cleanup(folder=None, echo=True):
    if not os.path.exists(folder):
        return True
    if os.path.isdir(folder):
        empty = True
        for content in os.scandir(folder):
            if cleanup(content, echo):
                empty = False
        if empty:
            os.rmdir(folder)
            return False
        return True
    if isinstance(folder, str):
        return None
    folderpath = folder.path.replace("\\", "/")
    path = folderpath[len(basedir) + 1 :]
    if os.path.isfile(scopedir + "/" + path):
        if is_edited(path):
            copyfile(folderpath, scopedir + "/" + path)
        if echo:
            alt_print(path)
        os.remove(folderpath)
        return False
    return True


def restorebase(echo=True):
    if not cleanup(basedir, echo):
        try:
            copy_tree(basedir, scopedir)
        except DistutilsFileError:
            pass
