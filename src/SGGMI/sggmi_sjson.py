## SJSON Handling
try:
    import sjson  # pip: SJSON
except ModuleNotFoundError:
    sjson = None
else:
    from collections import OrderedDict

## SJSON mapping

if sjson is not None:

    sjson_RESERVED_sequence = "_sequence"
    sjson_RESERVED_append = "_append"
    sjson_RESERVED_replace = "_replace"
    sjson_RESERVED_delete = "_delete"

    def sjson_safeget(data, key):
        if isinstance(data, list):
            if isinstance(key, int):
                if key < len(data) and key >= 0:
                    return data[key]
            return DNE

        if isinstance(data, OrderedDict):
            return data.get(key, DNE)

        return DNE

    def sjson_clearDNE(data):
        if isinstance(data, OrderedDict):
            for k, v in data.items():
                if v is DNE:
                    del data[k]
                    continue
                data[k] = sjson_clearDNE(v)

        if isinstance(data, list):
            L = []
            for i, v in enumerate(data):
                if v is DNE:
                    continue
                L.append(sjson_clearDNE(v))
            data = L

        return data

    def sjson_read(filename):
        try:
            with open(fiename, "r") as file_in:
                file_contents = file_in.read()
                return sjson.loads(file_contents.replace("\\", "\\\\"))
        except sjson.ParseException as e:
            alt_print(repr(e))
            return DNE

    def sjson_write(filename, content):
        if not isinstance(filename, str):
            return

        if isinstance(content, OrderedDict):
            content = sjson.dumps(content)
        else:
            content = ""

        with open(filename, "w") as file_out:
            curr_string = "{\n" + content + "}"
            output = ""

            # Indentation styling
            prev_char = ""
            for char in curr_string:
                if char in "{[" and prev_char in "{[":
                    output += "\n"

                if char in "}]" and prev_char in "}]":
                    output += "\n"

                output += char

                if char not in "{[\n" and prev_char in "{[":
                    output = output[:-1] + "\n" + output[-1]

                if char in "}]" and prev_char not in "}]\n":
                    output = output[:-1] + "\n" + output[-1]

                prev_char = char

            TEMP_output_split = output.replace(", ", "\n").split("\n")
            indent = 0
            output_lines = []
            for line in TEMP_output_split:
                for char in line:
                    if char in "}]":
                        indent -= 1

                output_lines.append("  " * indent + line)
                for char in line:
                    if char in "{[":
                        indent += 1

            final_output = "\n".join(output_lines)

            file_out.write(final_output)

    def sjson_map(indata, mapdata):
        if mapdata is DNE:
            return indata
        if sjson_safeget(mapdata, sjson_RESERVED_sequence):
            S = []
            for k, v in mapdata.items():
                try:
                    d = int(k) - len(S)
                    if d >= 0:
                        S.extend([DNE] * (d + 1))
                    S[int(k)] = v
                except ValueError:
                    continue
            mapdata = S
        if type(indata) == type(mapdata):
            if sjson_safeget(mapdata, 0) != sjson_RESERVED_append or isinstance(
                mapdata, OrderedDict
            ):
                if isinstance(mapdata, list):
                    if sjson_safeget(mapdata, 0) == sjson_RESERVED_delete:
                        return DNE
                    if sjson_safeget(mapdata, 0) == sjson_RESERVED_replace:
                        del mapdata[0]
                        return mapdata
                    indata.expand([DNE] * (len(mapdata) - len(indata)))
                    for k, v in enumerate(mapdata):
                        indata[k] = sjson_map(sjson_safeget(indata, k), v)
                else:
                    if sjson_safeget(mapdata, sjson_RESERVED_delete):
                        return DNE
                    if sjson_safeget(mapdata, sjson_RESERVED_replace):
                        del mapdata[sjson_RESERVED_replace]
                        return mapdata
                    for k, v in mapdata.items():
                        indata[k] = sjson_map(sjson_safeget(indata, k), v)
                return indata
            elif isinstance(mapdata, list):
                for i in range(1, len(mapdata)):
                    indata.append(mapdata[i])
                return indata
        else:
            return mapdata
        return mapdata

    def sjson_merge(infile, mapfile):
        indata = sjson_read(infile)
        if mapfile:
            mapdata = sjson_read(mapfile)
        else:
            mapdata = DNE
        indata = sjson_map(indata, mapdata)
        indata = sjson_clearDNE(indata)
        sjson_write(infile, indata)


else:

    sjson_safeget = None
    sjson_clearDNE = None
    sjson_read = None
    sjson_write = None
    sjson_map = None
    sjson_merge = None
