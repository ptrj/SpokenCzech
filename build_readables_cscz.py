#!/usr/bin/env python3
"""Vyrobi cesky balicek SpokenReadablesAudio_csCZ pre Spoken Readables z dat WowfCZ.

Predloha: SpokenReadablesAudio_deDE (Data/Sounds.lua, format packu verzia 1).
Spojenie: anglicky nazov knihy + cislo strany -> Spokenove pageId.

Spustenie:
    python3 -I build_readables_cscz.py [--out ADRESAR] [--work ADRESAR]

Nic nekonvertuje ani nekopiruje zvuk; vypise, ktore .ogg treba previest na .mp3.
"""

import argparse
import glob
import json
import os
import re
import sys

PACK = "SpokenReadablesAudio_csCZ"
VERSION = "0.1.0"


# ---------------------------------------------------------------- nacitanie

def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def section(text, name, following):
    """Vrati telo sekcie `name = {` az po zaciatok nasledujucej sekcie."""
    start = text.index("\t%s = {" % name)
    end = text.index("\t%s = {" % following) if following else len(text)
    return text[start:end]


LUA_STRING = r'"((?:[^"\\]|\\.)*)"'


def unescape(value):
    return (value.replace('\\"', '"')
                 .replace("\\n", "\n")
                 .replace("\\t", "\t")
                 .replace("\\\\", "\\"))


def skeleton(text):
    """Kluc, ktorym WowfCZ oznacuje stranku: anglicky text, male pismena,
    len pismena, prvych 32 znakov (pole `s` v BookData.lua)."""
    return re.sub(r"[^a-z]", "", text.lower())[:32]


def spoken_pages(books_lua):
    """Mapy Spokenova korpusu: podla skeletonu, podla (nazov, strana), a text."""
    text = read(books_lua)
    books = {}
    for bid, title in re.findall(r'^\t\t\[(-?\d+)\] = \{ title = ' + LUA_STRING,
                                 section(text, "books", "owners"), re.M):
        books[int(bid)] = unescape(title)

    by_skeleton, by_title_page, english = {}, {}, {}
    pattern = (r'^\t\t\[(-?\d+)\] = \{ book = (-?\d+), number = (\d+), text = '
               + LUA_STRING)
    for pid, bid, number, body in re.findall(pattern,
                                             section(text, "pages", "books"), re.M):
        pid, bid, number = int(pid), int(bid), int(number)
        body = unescape(body)
        english[pid] = body
        by_skeleton.setdefault(skeleton(body), []).append(pid)
        title = books.get(bid)
        if title is not None:
            by_title_page.setdefault((title, number), []).append(pid)
    return books, by_skeleton, by_title_page, english


def wowf_books(book_data_lua):
    """WowfCZ id -> {"en", "cz", "pages": {n: cesky text}, "skel": {n: skeleton}}."""
    out = {}
    for line in read(book_data_lua).splitlines():
        if not line.startswith("WowfCZ_BookData["):
            continue
        head = re.match(r'WowfCZ_BookData\[(-?\d+)\] = \{', line)
        if not head:
            continue
        entry = {"en": None, "cz": None, "pages": {}, "skel": {}}
        found = re.search(r'\be = ' + LUA_STRING, line)
        if found:
            entry["en"] = unescape(found.group(1))
        found = re.search(r'\bt = ' + LUA_STRING, line)
        if found:
            entry["cz"] = unescape(found.group(1))
        pages = re.search(r'\bp = \{(.*?)\}, s = \{', line) or re.search(r'\bp = \{(.*)\}', line)
        if pages:
            for number, body in re.findall(r'\[(\d+)\] = ' + LUA_STRING, pages.group(1)):
                entry["pages"][int(number)] = unescape(body)
        marks = re.search(r'\bs = \{(.*)\}\s*\}\s*$', line)
        if marks:
            for number, body in re.findall(r'\[(\d+)\] = ' + LUA_STRING, marks.group(1)):
                entry["skel"][int(number)] = unescape(body)
        out[int(head.group(1))] = entry
    return out


def wowf_voice(paths):
    """clip -> (dlzka, adresar balicka) a clip -> titulok."""
    clips, captions = {}, {}
    for path in paths:
        folder = os.path.basename(os.path.dirname(path))
        text = read(path)
        for clip, length in re.findall(r'^D\["([^"]+)"\] = \{ ([0-9.]+)', text, re.M):
            clips[clip] = (float(length), folder)
        for clip, body in re.findall(r'^WowfCZ_VoiceCaptions\["([^"]+)"\] = ' + LUA_STRING,
                                     text, re.M):
            captions[clip] = unescape(body)
    return clips, captions


# ---------------------------------------------------------------- vystup

def lua_string(value):
    out = value.replace("\\", "\\\\").replace('"', '\\"')
    return out.replace("\r", "").replace("\n", "\\n")


def clip_name(book_id, number):
    """Klip knihy vo WowfCZ: b<itemID>-page<N>, pre herny objekt b-<objectID>-page<N>."""
    return "b%d-page%d" % (book_id, number) if book_id > 0 else "b-%d-page%d" % (-book_id, number)


TOC = """## X-SpokenReadables-Language: csCZ

## Interface: 11509, 20506, 16001
## Title: |cffb48cffSpoken|r Czech Audio: Readables
## Notes: Ceske namluvene knihy, dopisy a cedule pro Spoken Readables.|n|nNahravky a text: WoWF.cz (WowfCZ). Nechej zapnute: nacita se se hrou a Spoken Readables z nej prehrava.
## Version: {version}
## IconTexture: Interface\\AddOns\\{pack}\\Textures\\AddonIcon.tga
## Group: Spoken
## X-Part-Of: Spoken
## X-Child-Of: Spoken_Readables
## Dependencies: SpokenCzech
## X-Credits: Cesky preklad a dabing WoWF.cz (WowfCZ, autor Fejac).

Data/Sounds.lua
"""

HEADER = """-- VYGENEROVANE build_readables_cscz.py. Needitovat rucne.
--
-- Cesky balicek pro Spoken Readables, postaveny podle predlohy SpokenReadablesAudio_deDE.
-- Text i nahravky pochazeji z addonu WoWF.cz (WowfCZ); spojeni je anglicky nazev knihy
-- plus cislo stranky -> pageId, ktere pouziva Spoken_Readables/Data/Books.lua.
--
-- Stranka bez nahravky tu proste neni: Spoken ji precte v jazyce nastavenem pod
-- "If a Voice Is Missing" (vychozi anglictina), stranku po strance.
--
-- Globals rather than a private namespace: a data addon cannot reach into SpokenReadables's.

local ADDON_NAME = ...

local pack = {
\tversion = 1,
\taddon = ADDON_NAME,
\tquality = "high",
\t-- Zdrojova .ogg od WoWF.cz maji ~75 kbps; prepis do 128 kbps by soubor jen
\t-- nafoukl a kvalitu nevrati. 80 kbps mono je to, co tu opravdu je.
\tbitrate = 80,
\tlanguage = "csCZ",
\tpages = {
"""

FOOTER = """\t},
}

SpokenReadablesAudioPacks = SpokenReadablesAudioPacks or {}
SpokenReadablesAudioPacks[ADDON_NAME] = pack
"""


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--work", default=os.path.join(here, "_work"),
                        help="adresar s rozbalenymi addonmi (_work)")
    parser.add_argument("--out", default=os.path.join(here, PACK),
                        help="kam zapisat balicek")
    args = parser.parse_args()

    spoken_dir = os.path.join(args.work, "spoken")
    wowf_dir = os.path.join(args.work, "wowfcz")

    books_lua = os.path.join(spoken_dir, "Spoken_Readables", "Data", "Books.lua")
    book_data = os.path.join(wowf_dir, "WowfCZ", "Data", "BookData.lua")
    voice_files = [os.path.join(wowf_dir, "WowfCZ", "VoiceData.lua")]
    # Glob, ne pevny rozsah: novy balicek WoWF.cz se pak najde sam.
    voice_files += sorted(glob.glob(os.path.join(wowf_dir, "WowfCZ_Dabing_*", "Data.lua")))

    for path in [books_lua, book_data] + voice_files:
        if not os.path.exists(path):
            sys.exit("chyba: nenasiel som %s" % path)

    spoken_titles, by_skeleton, by_title_page, english = spoken_pages(books_lua)
    wowf = wowf_books(book_data)
    clips, captions = wowf_voice(voice_files)

    rows, unmatched, no_text, rejected = [], [], [], []
    seen_pages, used_from = {}, {}
    how_many = {"skeleton": 0, "nazev": 0}

    for book_id, entry in sorted(wowf.items()):
        title = entry["en"]
        for number in sorted(entry["pages"]):
            clip = clip_name(book_id, number)
            if clip not in clips:
                continue                      # ceska nahravka neexistuje
            length, folder = clips[clip]
            text = captions.get(clip) or entry["pages"].get(number)
            if not text:
                no_text.append(clip)
                continue

            # Prednost ma skeleton (prvych 32 pismen anglickeho textu): dve ruzne
            # knihy se stejnym nazvem se podle nazvu rozlisit nedaji.
            mark = entry["skel"].get(number)
            page_id, how = None, None
            if mark:
                found = by_skeleton.get(mark, [])
                if len(found) == 1:
                    page_id, how = found[0], "skeleton"
                elif len(found) > 1:
                    narrow = set(by_title_page.get((title, number), []))
                    same = [pid for pid in found if pid in narrow]
                    if len(same) == 1:
                        page_id, how = same[0], "skeleton"
            if page_id is None and title:
                found = by_title_page.get((title, number), [])
                if len(found) == 1:
                    # Skeleton, ktery nesedi, znamena jinou knihu tehoz nazvu.
                    if mark and skeleton(english[found[0]]) != mark:
                        rejected.append((clip, title, number))
                        continue
                    page_id, how = found[0], "nazev"
            if page_id is None:
                unmatched.append((clip, title, number))
                continue
            if page_id in seen_pages:         # dve knihy WowfCZ na tutez stranku
                continue

            seen_pages[page_id] = clip
            how_many[how] += 1
            used_from.setdefault(folder, []).append(clip)
            rows.append((page_id, clip, length, text))

    rows.sort(key=lambda row: row[0])

    os.makedirs(os.path.join(args.out, "Data"), exist_ok=True)
    sounds = os.path.join(args.out, "Data", "Sounds.lua")
    with open(sounds, "w", encoding="utf-8") as handle:
        handle.write(HEADER.replace("{pack}", PACK))
        for page_id, clip, length, text in rows:
            handle.write('\t\t[%d] = { file = "%s", len = %.3f, text = "%s" },\n'
                         % (page_id, clip, length, lua_string(text)))
        handle.write(FOOTER)

    with open(os.path.join(args.out, "%s.toc" % PACK), "w", encoding="utf-8") as handle:
        handle.write(TOC.format(version=VERSION, pack=PACK))

    manifest = {folder: sorted(names) for folder, names in used_from.items()}
    with open(os.path.join(args.out, "sounds-to-convert.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, ensure_ascii=False)

    total_spoken = len(english)
    print("Spoken Readables: %d knih, %d stranek s textem" % (len(spoken_titles), total_spoken))
    print("WowfCZ:           %d knih, %d ceskych nahravek stranek"
          % (len(wowf), sum(1 for c in clips if re.match(r"^b-?\d+-page\d+$", c))))
    print()
    print("ZAPSANO:          %d stranek (%.1f %% Spokenova korpusu)"
          % (len(rows), 100.0 * len(rows) / total_spoken if total_spoken else 0))
    print("  podla skeletonu %d" % how_many["skeleton"])
    print("  podla nazvu     %d (WowfCZ k nim nema skeleton)" % how_many["nazev"])
    print("nesparovane:      %d (ceska nahravka je, Spoken stranku nezna)" % len(unmatched))
    print("odmietnute:       %d (rovnaky nazov, iny text - jina kniha)" % len(rejected))
    print("bez textu:        %d" % len(no_text))
    print()
    print("zvuk k prevodu .ogg -> .mp3 (Sounds/<klip>.mp3):")
    for folder in sorted(manifest):
        print("  %-22s %d klipu" % (folder, len(manifest[folder])))
    if unmatched:
        print()
        print("ukazka nesparovanych:")
        for clip, title, number in unmatched[:8]:
            print("  %-22s strana %-3d %s" % (clip, number, title))
    print()
    print("balicek: %s" % args.out)


if __name__ == "__main__":
    main()
