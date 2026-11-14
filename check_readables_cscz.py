#!/usr/bin/env python3
"""Kontrola vygenerovaneho balicka SpokenReadablesAudio_csCZ.

1. Tvar suboru: kazdy riadok sekcie pages sedi na ocakavany vzor, zadny
   neuzavreny retezec, zadny holy novy radek.
2. Spravnost spojeni: v ceskem textu se maji objevit vlastni jmena
   z anglickeho originalu teze stranky (Goldshire, Morgan...). Kdyby byl
   join posunuty, shoda by spadla k nule.

Spustenie:  python3 -I check_readables_cscz.py
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenReadablesAudio_csCZ", "Data", "Sounds.lua")
BOOKS = os.path.join(HERE, "_work", "spoken", "Spoken_Readables", "Data", "Books.lua")
BOOKDATA = os.path.join(HERE, "_work", "wowfcz", "WowfCZ", "Data", "BookData.lua")

LUA_STRING = r'"((?:[^"\\]|\\.)*)"'
ROW = re.compile(r'^\t\t\[(\d+)\] = \{ file = "([^"]+)", len = ([0-9.]+), text = '
                 + LUA_STRING + r' \},$')
# slovo zacinajuce velkym pismenem, ktore nie je na zaciatku vety
NAME = re.compile(r'(?<![.!?]\s)(?<!^)\b([A-Z][a-zA-Z\']{3,})\b')
STOP = {"The", "This", "That", "They", "Then", "There", "When", "What", "With",
        "From", "Your", "Have", "Will", "Been", "Were", "Their", "These", "Those",
        "Lord", "Lady", "King", "Light"}


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def unescape(value):
    return (value.replace('\\"', '"').replace("\\n", "\n")
                 .replace("\\t", "\t").replace("\\\\", "\\"))


def skeleton(text):
    return re.sub(r"[^a-z]", "", text.lower())[:32]


def wowf_skeletons():
    """(bookId, strana) -> skeleton anglickeho textu, jak ho zapsal WowfCZ."""
    out = {}
    for line in read(BOOKDATA).splitlines():
        head = re.match(r'WowfCZ_BookData\[(-?\d+)\] = \{', line)
        if not head:
            continue
        marks = re.search(r'\bs = \{(.*)\}\s*\}\s*$', line)
        if not marks:
            continue
        for number, body in re.findall(r'\[(\d+)\] = ' + LUA_STRING, marks.group(1)):
            out[(int(head.group(1)), int(number))] = unescape(body)
    return out


def clip_source(clip):
    """Z nazvu klipu zpet (bookId, strana): b<id>-page<n> nebo b-<id>-page<n>."""
    found = re.match(r'^b(-?)(\d+)-page(\d+)$', clip)
    if not found:
        return None
    sign, book, number = found.groups()
    return (-int(book) if sign else int(book), int(number))


def english_pages():
    text = read(BOOKS)
    start = text.index("\tpages = {")
    end = text.index("\tbooks = {")
    out = {}
    pattern = r'^\t\t\[(-?\d+)\] = \{ book = -?\d+, number = \d+, text = ' + LUA_STRING
    for pid, body in re.findall(pattern, text[start:end], re.M):
        out[int(pid)] = unescape(body)
    return out


def main():
    if not os.path.exists(PACK):
        sys.exit("chyba: %s neexistuje, spusti najprv build_readables_cscz.py" % PACK)

    lines = read(PACK).splitlines()
    try:
        first = next(i for i, line in enumerate(lines) if line == "\tpages = {")
        last = next(i for i, line in enumerate(lines) if line == "\t},")
    except StopIteration:
        sys.exit("chyba: v subore nie je sekcia pages")

    rows, bad = {}, []
    for number, line in enumerate(lines[first + 1:last], start=first + 2):
        match = ROW.match(line)
        if not match:
            bad.append((number, line[:90]))
            continue
        page_id, clip, length, text = match.groups()
        rows[int(page_id)] = (clip, float(length), unescape(text))

    print("riadkov v pages:      %d" % len(rows))
    print("nevyhovujucich tvaru: %d" % len(bad))
    for number, line in bad[:5]:
        print("   r.%d: %s" % (number, line))

    dupe_clips = len(rows) - len({clip for clip, _, _ in rows.values()})
    print("duplicitnych klipov:  %d" % dupe_clips)
    zero = sum(1 for _, length, _ in rows.values() if length <= 0)
    print("nulova dlzka:         %d" % zero)
    empty = sum(1 for _, _, text in rows.values() if not text.strip())
    print("prazdny text:         %d" % empty)

    english = english_pages()
    missing = [pid for pid in rows if pid not in english]
    print("pageId mimo korpus:   %d" % len(missing))

    # Exaktna kontrola spojenia: skeleton anglickeho textu, ktory Spoken ma pod
    # tymto pageId, sa musi rovnat skeletonu, ktory si WowfCZ poznamenal ku klipu.
    marks = wowf_skeletons()
    exact_ok, exact_bad, no_mark = 0, [], 0
    for page_id, (clip, _, _) in sorted(rows.items()):
        source = clip_source(clip)
        mark = marks.get(source) if source else None
        if not mark or page_id not in english:
            no_mark += 1
            continue
        if skeleton(english[page_id]) == mark:
            exact_ok += 1
        else:
            exact_bad.append((page_id, clip, mark, skeleton(english[page_id])))

    print()
    print("exaktna kontrola spojenia (skeleton anglickeho textu):")
    print("  sedi:               %d" % exact_ok)
    print("  NESEDI:             %d" % len(exact_bad))
    print("  bez skeletonu:      %d (spojene podla nazvu knihy)" % no_mark)
    for page_id, clip, mark, got in exact_bad[:5]:
        print("    [%d] %s" % (page_id, clip))
        print("        WowfCZ: %s" % mark)
        print("        Spoken: %s" % got)

    checked = hit = 0
    worst = []
    for page_id, (clip, _, czech) in sorted(rows.items()):
        source = english.get(page_id)
        if not source:
            continue
        names = {n for n in NAME.findall(source) if n not in STOP}
        if len(names) < 2:
            continue
        checked += 1
        found = sum(1 for n in names if n in czech)
        share = found / len(names)
        if share >= 0.5:
            hit += 1
        else:
            worst.append((share, page_id, clip, sorted(names)[:4]))

    print()
    print("pomocna kontrola na vlastnych menach (orientacna - preklada sa aj")
    print("Emperor's Tomb -> Cisarovou hrobkou, takze nizke cislo nic nedokazuje):")
    print("  overenych stranek:  %d" % checked)
    print("  zhoda >= 50 %%:      %d (%.1f %%)"
          % (hit, 100.0 * hit / checked if checked else 0))

    ok = not bad and not missing and not empty and not exact_bad
    print()
    print("VYSLEDOK: %s" % ("v poriadku" if ok else "pozri vyssie"))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
