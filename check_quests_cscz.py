#!/usr/bin/env python3
"""Kontrola balicka SpokenQuestsAudio_csCZ.

1. Tvar vygenerovanych souboru: kazdy radek sedi na ocekavany vzor.
2. Soudrznost: ke kazdemu titulku existuje delka; jmena klipu maji tvar,
   ktery Spoken opravdu hleda (<questID>-<cast>, volitelne m-/f-).
3. Zvuk: ke kazde delce existuje soubor, a na vzorku se overi, ze skutecna
   delka nahravky sedi na deklarovanou (spatne slozene useky by se poznaly).

Spustenie:  python3 -I check_quests_cscz.py [--sample 60]
"""

import argparse
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenQuestsAudio_csCZ")

CLIP = re.compile(r"^(?:m-|f-)?\d+-(?:accept|progress|complete)$")
LEN_ROW = re.compile(r'^    \["([^"]+)"\] = ([0-9.]+),$')
CAP_ROW = re.compile(r'^    \["([^"]+)"\] = "((?:[^"\\]|\\.)*)",$')


def rows(path, pattern):
    out, bad = {}, []
    if not os.path.exists(path):
        sys.exit("chyba: %s neexistuje" % path)
    started = False
    for number, line in enumerate(open(path, encoding="utf-8"), 1):
        line = line.rstrip("\n")
        if line.endswith("= {"):
            started = True
            continue
        if not started or line == "}" or not line.strip():
            continue
        found = pattern.match(line)
        if not found:
            bad.append((number, line[:80]))
            continue
        out[found.group(1)] = found.group(2)
    return out, bad


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=nw=1:nk=1", path],
                         capture_output=True, text=True)
    try:
        return float(out.stdout.strip())
    except ValueError:
        return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", type=int, default=60)
    args = parser.parse_args()

    lengths, bad_len = rows(os.path.join(PACK, "generated", "sound_length_table.lua"), LEN_ROW)
    captions, bad_cap = rows(os.path.join(PACK, "generated", "captions.lua"), CAP_ROW)

    print("delek:                %6d  (nevyhovujicich radku: %d)" % (len(lengths), len(bad_len)))
    print("titulku:              %6d  (nevyhovujicich radku: %d)" % (len(captions), len(bad_cap)))
    for number, line in (bad_len + bad_cap)[:5]:
        print("   r.%d: %s" % (number, line))

    shape = [clip for clip in lengths if not CLIP.match(clip)]
    orphan = [clip for clip in captions if clip not in lengths]
    print("klipu se spatnym tvarem jmena: %d" % len(shape))
    print("titulku bez delky:             %d" % len(orphan))
    for clip in (shape + orphan)[:5]:
        print("   %s" % clip)

    sounds = os.path.join(PACK, "generated", "sounds", "quests")
    have = set()
    if os.path.isdir(sounds):
        have = {name[:-4] for name in os.listdir(sounds) if name.endswith(".ogg")}
    missing = [clip for clip in lengths if clip not in have]
    empty = [clip for clip in have
             if os.path.getsize(os.path.join(sounds, clip + ".ogg")) == 0]
    print()
    print("nahravek v balicku:   %6d z %d" % (len(have), len(lengths)))
    print("chybejicich:          %6d" % len(missing))
    print("prazdnych souboru:    %6d" % len(empty))

    checked = ok = 0
    worst = []
    if have and subprocess.run(["which", "ffprobe"], capture_output=True).returncode == 0:
        random.seed(11)
        for clip in random.sample(sorted(have), min(args.sample, len(have))):
            want = float(lengths.get(clip, 0) or 0)
            if want <= 0:
                continue
            got = duration(os.path.join(sounds, clip + ".ogg"))
            if got is None:
                continue
            checked += 1
            if abs(got - want) <= max(0.5, want * 0.03):
                ok += 1
            else:
                worst.append((got - want, clip, want, got))
        print()
        print("delky nahravek, vzorek %d: sedi %d, mimo %d" % (checked, ok, len(worst)))
        for diff, clip, want, got in sorted(worst, key=lambda r: -abs(r[0]))[:6]:
            print("   %-24s deklarovano %6.2f, skutecnost %6.2f, rozdil %+5.2f"
                  % (clip, want, got, diff))

    good = (not bad_len and not bad_cap and not shape and not orphan
            and not empty and not worst)
    complete = not missing
    print()
    if good and complete:
        print("VYSLEDOK: v poriadku")
        return 0
    if good and not complete:
        print("VYSLEDOK: data v poriadku, zvuk jeste nekompletni (%d chybi)" % len(missing))
        return 0
    print("VYSLEDOK: pozri vyssie")
    return 1


if __name__ == "__main__":
    sys.exit(main())
