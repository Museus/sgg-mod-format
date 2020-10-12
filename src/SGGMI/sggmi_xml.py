import xml.etree.ElementTree as xml

## XML mapping
xml_RESERVED_replace = "_replace"
xml_RESERVED_delete = "_delete"


def xml_safeget(data, key):
    if isinstance(data, list):
        if isinstance(key, int):
            if 0 <= key < len(data):
                return data[key]
        return DNE

    if isinstance(data, xml.ElementTree):
        root = data.getroot()
        if root:
            return root.get(k, DNE)

    if isinstance(data, xml.Element):
        return data.get(key, DNE)
    return DNE


def xml_read(filename):
    try:
        return xml.parse(filename)
    except xml.ParseError:
        return DNE


def xml_write(filename, content, start=None):
    if not isinstance(filename, str):
        return
    if not isinstance(content, xml.ElementTree):
        return

    content.write(filename)

    # Indentation styling
    data = start or ""

    with open(filename, "r") as file:
        indent = 0

        for line in file:
            line_no_whitespace = line.translate(str.maketrans("", "", " \t"))

            if len(line_no_whitespace) > 1:
                quoted = False
                prev_char = ""

                for char in line:
                    if char == '"':
                        quoted = not quoted

                    if prev_char == "<" and not quoted:
                        if char == "/":
                            indent -= 1
                            data = data[:-1]
                        else:
                            indent += 1
                        data += p

                    if (prev_char, char) == ("/", ">") and not quoted:
                        indent -= 1

                    if (
                        prev_char in (" ")
                        or (prev_char, char) == ('"', ">")
                        and not quoted
                    ):
                        data += "\n" + "\t" * (indent - (char == "/"))

                    if char not in (" ", "\t", "<") or quoted:
                        data += char

                    prev_char = char
    open(filename, "w").write(data)


def xml_map(indata, mapdata):
    if mapdata is DNE:
        return indata
    if type(indata) == type(mapdata):
        if isinstance(mapdata, dict):
            for k, v in mapdata.items():
                indata[k] = xml_map(indata.get(k), v)
            return indata
        if isinstance(mapdata, xml.ElementTree):
            root = xml_map(indata.getroot(), mapdata.getroot())
            if root:
                indata._setroot(root)
            return indata
        elif isinstance(mapdata, xml.Element):
            mtags = dict()
            for v in mapdata:
                if not mtags.get(v.tag, False):
                    mtags[v.tag] = True
            for tag in mtags:
                mes = mapdata.findall(tag)
                ies = indata.findall(tag)
                for i, me in enumerate(mes):
                    ie = xml_safeget(ies, i)
                    if ie is DNE:
                        indata.append(me)
                        continue
                    if me.get(xml_RESERVED_delete, None) not in {
                        None,
                        "0",
                        "false",
                        "False",
                    }:
                        indata.remove(ie)
                        continue
                    if me.get(xml_RESERVED_replace, None) not in {
                        None,
                        "0",
                        "false",
                        "False",
                    }:
                        ie.text = me.text
                        ie.tail = me.tail
                        ie.attrib = me.attrib
                        del ie.attrib[xml_RESERVED_replace]
                        continue
                    ie.text = xml_map(ie.text, me.text)
                    ie.tail = xml_map(ie.tail, me.tail)
                    ie.attrib = xml_map(ie.attrib, me.attrib)
                    xml_map(ie, me)
            return indata
        return mapdata
    else:
        return mapdata
    return mapdata


def xml_merge(infile, mapfile):
    start = ""
    with open(infile, "r") as file:
        for line in file:
            if line[:5] == "<?xml" and line[-3:] == "?>\n":
                start = line
                break
    indata = xml_read(infile)
    if mapfile:
        mapdata = xml_read(mapfile)
    else:
        mapdata = DNE
    indata = xml_map(indata, mapdata)
    xml_write(infile, indata, start)
