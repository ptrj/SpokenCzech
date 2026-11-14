#!/usr/bin/env python3
"""Doplni do ceskych balicku casovani slov z WoWF.cz.

Spoken zvyrazni slovo prave kdyz zazni, pokud klip nese present.timings
(Spoken/UI/Transcript.lua, ApplyTimings). Format je jeden retezec zacatku slov:

    WoWF.cz:  { {"Citim", 0.24, 0.82}, {"ve", 0.88, 0.98}, ... }
    Spoken:   ".24 .88 ..."

Spoken seznam zahodi, kdyz pocet casu nesedi s poctem slov titulku
("A timings list that does not fit the words exactly is ignored"), takze se
shoda overuje uz tady a nesedici radek se nezapise. Dal plati, ze casy musi
byt neklesajici a zadny nesmi presahnout delku nahravky.

Pozor: DataModules timings sam nenasadi, kdyz jazyk balicku neni jazyk
klienta. Nasadi ho SpokenCzech v Player:Prepare.

Spustenie:  python3 -I build_timings_cscz.py
"""

import glob
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKS = ("SpokenQuestsAudio_csCZ", "SpokenQuestsAudioGossip_csCZ")
ENTRY = re.compile(r'\{"(?:[^"\\]|\\.)*",\s*(-?[0-9.]+),\s*(-?[0-9.]+)\}')

HEAD = """-- VYGENEROVANE build_timings_cscz.py. Needitovat rucne.
--
-- Zacatky slov v sekundach, jeden retezec na nahravku: Spoken z nej udela
-- tabulku az pro klip, ktery zrovna hraje (Spoken/UI/Transcript.lua).
-- Zapsane jsou jen nahravky, u kterych pocet casu sedi s poctem slov titulku;
-- jinak by Spoken seznam stejne zahodil.

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.WordTimesByFileName = {{
"""


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def seconds(value):
    """Jako to zapisuji anglicke balicky: bez nadbytecnych nul a bez vedouci nuly."""
    out = ("%.2f" % value).rstrip("0").rstrip(".")
    if out.startswith("0."):
        out = out[1:]
    elif out.startswith("-0."):
        out = "-" + out[2:]
    return out or "0"


def wowf_timings(paths):
    out = {}
    for path in paths:
        for clip, body in re.findall(
                r'^WowfCZ_WordTimings\["([^"]+)"\] = \{(.*)\}\s*$', read(path), re.M):
            starts = [float(m.group(1)) for m in ENTRY.finditer(body)]
            if starts:
                out[clip] = starts
    return out


def pack_rows(pack):
    """outName -> (klip WoWF.cz, titulek, delka)"""
    manifest = json.load(open(os.path.join(pack, "sounds-to-convert.json"), encoding="utf-8"))
    out_of = {}
    for clips in manifest.values():
        for clip, entry in clips.items():
            out_of[entry["out"] if isinstance(entry, dict) else clip] = clip

    captions = {}
    for line in read(os.path.join(pack, "generated", "captions.lua")).splitlines():
        m = re.match(r'^    \["([^"]+)"\] = "((?:[^"\\]|\\.)*)",$', line)
        if m:
            captions[m.group(1)] = m.group(2).replace("\\n", "\n").replace('\\"', '"')

    lengths = {}
    for line in read(os.path.join(pack, "generated", "sound_length_table.lua")).splitlines():
        m = re.match(r'^    \["([^"]+)"\] = ([0-9.]+),$', line)
        if m:
            lengths[m.group(1)] = float(m.group(2))

    rows = {}
    for name, clip in out_of.items():
        if name in captions and name in lengths:
            rows[name] = (clip, captions[name], lengths[name])
    return rows


def main():
    work = os.path.join(HERE, "_work", "wowfcz")
    sources = [os.path.join(work, "WowfCZ", "VoiceData.lua")]
    sources += sorted(glob.glob(os.path.join(work, "WowfCZ_Dabing_*", "Data.lua")))
    sources = [p for p in sources if os.path.exists(p)]
    if not sources:
        sys.exit("chyba: nenasiel som data WowfCZ v %s" % work)

    timings = wowf_timings(sources)
    print("casovani u WoWF.cz: %d nahravek" % len(timings))
    print()

    for pack in PACKS:
        path = os.path.join(HERE, pack)
        if not os.path.exists(path):
            print("%-30s preskoceno (neexistuje)" % pack)
            continue
        rows = pack_rows(path)
        written, no_timing, mismatch, bad = 0, 0, 0, 0
        lines = []
        for name in sorted(rows):
            clip, caption, length = rows[name]
            starts = timings.get(clip)
            if not starts:
                no_timing += 1
                continue
            if len(starts) != len(caption.split()):
                mismatch += 1
                continue
            if any(starts[i] < starts[i - 1] for i in range(1, len(starts))) \
                    or starts[0] < 0 or starts[-1] > length:
                bad += 1
                continue
            lines.append('    ["%s"] = "%s",\n' % (name, " ".join(seconds(s) for s in starts)))
            written += 1

        total = len(rows)
        target = os.path.join(path, "generated", "word_times_table.lua")
        if not written:
            # WoWF.cz ma casovani jen u questu. Prazdnou tabulku balicku
            # nevnucujeme -- jen by se nacitala pro nic.
            if os.path.exists(target):
                os.remove(target)
            print("%s\n  casovani WoWF.cz nema, preskoceno (%d nahravek)\n" % (pack, total))
            continue
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(HEAD.format(pack=pack))
            handle.writelines(lines)
            handle.write("}\n")

        toc = os.path.join(path, "%s.toc" % pack)
        text = read(toc)
        if "word_times_table.lua" not in text:
            text = text.replace("generated\\captions.lua",
                                "generated\\captions.lua\ngenerated\\word_times_table.lua")
            with open(toc, "w", encoding="utf-8") as handle:
                handle.write(text)

        print("%s" % pack)
        print("  nahravek v balicku:     %6d" % total)
        print("  s casovanim:            %6d (%.1f %%)" % (written, 100.0 * written / max(total, 1)))
        print("  WoWF.cz casovani nema:  %6d" % no_timing)
        print("  nesedi pocet slov:      %6d" % mismatch)
        print("  casy mimo rozsah:       %6d" % bad)
        print("  soubor: %s (%.1f kB)" % (target, os.path.getsize(target) / 1024.0))
        print()


if __name__ == "__main__":
    main()
