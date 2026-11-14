#!/usr/bin/env python3
"""Doplni zvuk do balicka SpokenReadablesAudio_csCZ.

Cita sounds-to-convert.json (zapisal ho build_readables_cscz.py), vytiahne
prislusne .ogg zo zipov WowfCZ a prevedie je na Sounds/<klip>.mp3 -- Spoken
Readables si cestu sklada napevno s priponou .mp3 (Spoken_Readables/Audio.lua).

Dlouhe nahravky WowfCZ nedodava v celku: jsou rozrezane na useky
<klip>_<k>.ogg (k od 1), protoze klient neumi pustit soubor od pulky
(WowfCZ/Voice.lua, WowfCZ_VoiceSegments[klip] = { rez1, rez2, ... }).
N rezu znamena N+1 souboru; Spoken ceka jeden soubor na stranku, takze se
useky zase spoji za sebe.

Bez ffmpeg se soubory jen vytahnou a skript rekne, co doinstalovat.

Spustenie:  python3 -I fetch_readables_audio.py [--bitrate 128]
"""

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenReadablesAudio_csCZ")
WORK = os.path.join(HERE, "_work", "wowfcz")

# Glob, ne pevny rozsah: novy balicek WoWF.cz se pak najde sam.
VOICE_DATA = [os.path.join(WORK, "WowfCZ", "VoiceData.lua")] + sorted(
    glob.glob(os.path.join(WORK, "WowfCZ_Dabing_*", "Data.lua")))

# adresar v balicku -> zip, v ktorom lezi

def segment_counts():
    """klip -> pocet suborov useku (1 = cela nahravka v jednom souboru).

    Rezy jsou zapsane jako S["klip"] = { 5.353, 14.368 } a teprve na konci
    souboru se kopiruji do WowfCZ_VoiceSegments. Nazev `S` nese v temze souboru
    i jina tabulka (sady pozdravu), ta ale ma uvnitr klice - proto bereme jen
    zapisy, jejichz telo je ciste seznam cisel.
    """
    parts = {}
    for path in VOICE_DATA:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8", errors="replace") as handle:
            text = handle.read()
        for clip, body in re.findall(r'^S\["([^"]+)"\] = \{\s*([0-9][0-9.,\s]*)\}',
                                     text, re.M):
            cuts = [piece for piece in body.split(",") if piece.strip()]
            if cuts:
                parts[clip] = len(cuts) + 1
    return parts


def human(size):
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f %s" % (size, unit)
        size /= 1024.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--bitrate", type=int, default=80,
                        help="bitrate mp3; zdrojova .ogg maji ~75 kbps, "
                             "vyssi cislo soubor jen nafoukne (balicek se hlasi jako 80)")
    parser.add_argument("--stage", default=os.path.join(HERE, "_work", "cscz-ogg"),
                        help="kam vytahnout puvodni .ogg")
    args = parser.parse_args()

    manifest_path = os.path.join(PACK, "sounds-to-convert.json")
    if not os.path.exists(manifest_path):
        sys.exit("chyba: %s neexistuje, spusti najprv build_readables_cscz.py" % manifest_path)
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    os.makedirs(args.stage, exist_ok=True)
    sounds = os.path.join(PACK, "Sounds")
    os.makedirs(sounds, exist_ok=True)

    # ---------------------------------------------------------- vytiahnutie
    parts_of = segment_counts()
    pieces = {}            # klip -> [cesty k .ogg v poradi]
    missing, bytes_in, split = [], 0, 0

    for folder, clips in sorted(manifest.items()):
        # Jmeno zipu je jmeno adresare: at novy balicek WoWF.cz (Dabing_7...)
        # funguje bez zasahu do skriptu.
        archive = os.path.join(HERE, folder + ".zip")
        if not os.path.exists(archive):
            missing.extend("%s/%s" % (folder, clip) for clip in clips)
            print("chyba zip %s - preskakujem %d klipu" % (folder + ".zip", len(clips)))
            continue
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            for clip in clips:
                count = parts_of.get(clip, 1)
                if count > 1:
                    split += 1
                wanted = ([clip] if count == 1
                          else ["%s_%d" % (clip, k) for k in range(1, count + 1)])
                got = []
                for name in wanted:
                    target = os.path.join(args.stage, name + ".ogg")
                    inside = "%s/Sounds/%s.ogg" % (folder, name)
                    if not os.path.exists(target):
                        if inside not in names:
                            missing.append(inside)
                            continue
                        with zf.open(inside) as src, open(target, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                    got.append(target)
                    bytes_in += os.path.getsize(target)
                if len(got) == len(wanted):
                    pieces[clip] = got
        print("  %-18s hotovo" % folder)

    print()
    print("klipu:           %d, z toho rozrezanych na useky: %d" % (len(pieces), split))
    print("vytiahnute .ogg: %d (%s) -> %s"
          % (sum(len(v) for v in pieces.values()), human(bytes_in), args.stage))
    if missing:
        print("nenajdene:       %d" % len(missing))
        for name in missing[:5]:
            print("   %s" % name)

    # ---------------------------------------------------------- prevod
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print()
        print("ffmpeg nie je nainstalovany, prevod preskakujem.")
        print("v Debian distroboxe:  sudo apt install ffmpeg")
        print("potom znovu:          python3 -I fetch_readables_audio.py")
        return 0

    done, failed, bytes_out = 0, [], 0
    total = len(pieces)
    lists = os.path.join(args.stage, "_concat")
    os.makedirs(lists, exist_ok=True)

    for index, (clip, files) in enumerate(sorted(pieces.items()), start=1):
        target = os.path.join(sounds, clip + ".mp3")
        newest = max(os.path.getmtime(path) for path in files)
        if os.path.exists(target) and os.path.getmtime(target) >= newest:
            done += 1
            bytes_out += os.path.getsize(target)
            continue

        encode = ["-codec:a", "libmp3lame", "-b:a", "%dk" % args.bitrate, "-ac", "1"]
        if len(files) == 1:
            command = [ffmpeg, "-nostdin", "-loglevel", "error", "-y",
                       "-i", files[0]] + encode + [target]
        else:
            # concat demuxer: useky za sebou, prekryv 0,03 s je ticho za vetou
            listing = os.path.join(lists, clip + ".txt")
            with open(listing, "w", encoding="utf-8") as handle:
                for path in files:
                    handle.write("file '%s'\n" % path.replace("'", r"'\''"))
            command = [ffmpeg, "-nostdin", "-loglevel", "error", "-y",
                       "-f", "concat", "-safe", "0", "-i", listing] + encode + [target]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode != 0:
            failed.append((clip, result.stderr.strip()[:120]))
            continue
        done += 1
        bytes_out += os.path.getsize(target)
        if index % 100 == 0:
            print("  prevedeno %d / %d" % (index, total))

    print()
    print("mp3 v balicku:   %d (%s) -> %s" % (done, human(bytes_out), sounds))
    if failed:
        print("zlyhalo:         %d" % len(failed))
        for name, why in failed[:5]:
            print("   %s: %s" % (name, why))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
