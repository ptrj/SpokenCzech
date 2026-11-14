#!/usr/bin/env python3
"""Overi balicek SpokenQuestsAudioGossip_csCZ.

Kontroluje:
  * tvar radku obou tabulek a to, ze jmena jsou hashe (pripadne s m-/f-),
  * ze ke kazdemu radku delek existuje .ogg a naopak,
  * ze titulky jsou podmnozinou delek,
  * ze hashe opravdu odpovidaji anglickemu balicku (jinak by Spoken soubor
    nikdy nehledal pod timto jmenem),
  * namatkou skutecnou delku nahravky proti deklarovane.

Spustenie:  python3 -I check_gossip_cscz.py [--sample N]
"""
import argparse, json, os, random, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenQuestsAudioGossip_csCZ")
NAME = re.compile(r"^(?:m-|f-)?[0-9a-f]{32}$")
ENGLISH = "SpokenQuestsAudioGossip"


def rows(path, pattern):
    out = {}
    with open(path, encoding="utf-8") as handle:
        for n, line in enumerate(handle, 1):
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
    print("radku delek:    %6d" % len(lengths))
    print("radku titulku:  %6d" % len(captions))

    wrong = [k for k in lengths if not NAME.match(k)]
    print("jmena mimo tvar hashe: %d %s" % (len(wrong), wrong[:3] or ""))
    bad += len(wrong)

    extra = set(captions) - set(lengths)
    print("titulek bez delky:     %d %s" % (len(extra), list(extra)[:3] or ""))
    bad += len(extra)

    sounds = os.path.join(PACK, "generated", "sounds", "gossip")
    files = {f[:-4] for f in os.listdir(sounds) if f.endswith(".ogg")}
    print("souboru .ogg:   %6d" % len(files))
    missing, orphan = set(lengths) - files, files - set(lengths)
    print("delka bez souboru:     %d %s" % (len(missing), list(missing)[:3] or ""))
    print("soubor bez delky:      %d %s" % (len(orphan), list(orphan)[:3] or ""))
    bad += len(missing) + len(orphan)

    empty = [n for n in files if os.path.getsize(os.path.join(sounds, n + ".ogg")) == 0]
    print("prazdnych souboru:     %d" % len(empty))
    bad += len(empty)

    # Hashe musi sedet s anglickym balickem, jinak je soubor nedosazitelny.
    known = None
    for root in (os.path.join(HERE, "_work", "spoken"),
                 os.environ.get("WOW_ADDONS", "")):
        p = os.path.join(root, ENGLISH, "generated", "npc_gossip_file_lookups.lua")
        if os.path.exists(p):
            known = set(re.findall(r'\] = "([0-9a-f]{32})"', open(p, encoding="utf-8").read()))
            break
    if known:
        unknown = {re.sub(r"^[mf]-", "", k) for k in lengths} - known
        print("hashu mimo anglicky balicek: %d %s" % (len(unknown), list(unknown)[:3] or ""))
        bad += len(unknown)
    else:
        print("hashu mimo anglicky balicek: nelze overit (anglicky balicek nenalezen)")

    probe = subprocess.run(["ffprobe", "-version"], capture_output=True)
    if probe.returncode == 0 and args.sample:
        random.seed(1)
        off = 0
        for name in random.sample(sorted(lengths), min(args.sample, len(lengths))):
            r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", os.path.join(sounds, name + ".ogg")],
                               capture_output=True, text=True)
            try:
                real = float(r.stdout.strip())
            except ValueError:
                off += 1
                continue
            if abs(real - float(lengths[name])) > 0.75:
                off += 1
        print("delka mimo toleranci (vzorek %d): %d" % (args.sample, off))
        bad += off

    print()
    print("VYSLEDEK: %s" % ("OK" if bad == 0 else "%d problemu" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
