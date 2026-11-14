#!/usr/bin/env python3
"""Overi balicek SpokenQuestsAudioChatter_csCZ.

Kontroluje tvar tabulek, uplnost proti souborum, delky namatkou a hlavne to,
ze kazde jmeno zna anglicky balicek -- pod jinym by Spoken soubor nehledal.

Spustenie:  python3 -I check_chatter_cscz.py [--sample N]
"""
import argparse, glob, os, random, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenQuestsAudioChatter_csCZ")
GAME = os.environ.get("WOW_ADDONS", "")  # kde je nainstalovana hra; nenastaveno = preskoci se


def rows(path, pattern):
    out = {}
    for n, line in enumerate(open(path, encoding="utf-8"), 1):
        if line.startswith("    ["):
            m = pattern.match(line)
            if not m:
                sys.exit("chyba: %s:%d neprecteny radek: %s" % (path, n, line.strip()))
            out[m.group(1)] = m.group(2)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=60)
    args = ap.parse_args()
    bad = 0

    lengths = rows(os.path.join(PACK, "generated", "sound_length_table.lua"),
                   re.compile(r'^    \["([^"]+)"\] = ([0-9.]+),$'))
    captions = rows(os.path.join(PACK, "generated", "captions.lua"),
                    re.compile(r'^    \["([^"]+)"\] = "((?:[^"\\]|\\.)*)",$'))
    sounds = os.path.join(PACK, "generated", "sounds", "followup")
    files = {f[:-4] for f in os.listdir(sounds) if f.endswith(".ogg")}
    print("radku delek:  %5d   titulku: %5d   souboru: %5d" % (len(lengths), len(captions), len(files)))

    for label, group in (("titulek bez delky", set(captions) - set(lengths)),
                         ("delka bez souboru", set(lengths) - files),
                         ("soubor bez delky", files - set(lengths))):
        print("%-22s %d %s" % (label + ":", len(group), list(group)[:3] or ""))
        bad += len(group)

    empty = [n for n in files if os.path.getsize(os.path.join(sounds, n + ".ogg")) == 0]
    print("%-22s %d" % ("prazdnych souboru:", len(empty)))
    bad += len(empty)

    known = set()
    for root in (os.path.join(HERE, "_work", "spoken"), GAME):
      for path in glob.glob(os.path.join(root, "SpokenQuestsAudio*", "generated",
                                         "*followup_lookups.lua")):
        if "_csCZ" in path:
            continue
        known |= set(re.findall(r'\] = "([^"]+)"', open(path, encoding="utf-8").read()))
    if known:
        unknown = {re.sub(r"^[mf]-", "", k) for k in lengths} - known
        print("%-22s %d %s" % ("jmen mimo anglicky balicek:", len(unknown), list(unknown)[:3] or ""))
        bad += len(unknown)
    else:
        print("jmen mimo anglicky balicek: nelze overit")

    if subprocess.run(["ffprobe", "-version"], capture_output=True).returncode == 0 and args.sample:
        random.seed(1)
        off = 0
        for name in random.sample(sorted(lengths), min(args.sample, len(lengths))):
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", os.path.join(sounds, name + ".ogg")],
                               capture_output=True, text=True)
            try:
                if abs(float(r.stdout.strip()) - float(lengths[name])) > 0.75:
                    off += 1
            except ValueError:
                off += 1
        print("%-22s %d" % ("delka mimo toleranci:", off))
        bad += off

    print()
    print("VYSLEDEK: %s" % ("OK" if bad == 0 else "%d problemu" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
