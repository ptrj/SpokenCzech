#!/usr/bin/env python3
"""Doplni zvuk do balicka SpokenQuestsAudio_csCZ.

Cita sounds-to-convert.json (zapsal ho build_quests_cscz.py) a sklada
generated/sounds/quests/<klip>.ogg.

Na rozdil od knih se tu neprekoduje vsechno: quest balicky Spokenu pouzivaji
.ogg stejne jako WowfCZ, takze
  * nahravka v jednom souboru se jen zkopiruje (beze ztraty, rychle),
  * rozrezana se slozi z useku <klip>_<k>.ogg pres ffmpeg (jedine misto,
    kde se prekoduje).

Spustenie:
    python3 -I fetch_quests_audio.py [--limit N] [--quality 3]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(HERE, "SpokenQuestsAudio_csCZ")


def human(size):
    for unit in ("B", "kB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return "%.1f %s" % (size, unit)
        size /= 1024.0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0,
                        help="zpracovat jen prvnich N klipu (na zkousku)")
    parser.add_argument("--quality", type=int, default=3,
                        help="kvalita libvorbis pro skladane useky (3 ~ 112 kbps)")
    parser.add_argument("--stage", default=os.path.join(HERE, "_work", "cscz-quest-parts"))
    args = parser.parse_args()

    manifest_path = os.path.join(PACK, "sounds-to-convert.json")
    if not os.path.exists(manifest_path):
        sys.exit("chyba: %s neexistuje, spust nejdriv build_quests_cscz.py" % manifest_path)
    with open(manifest_path, encoding="utf-8") as handle:
        manifest = json.load(handle)

    sounds = os.path.join(PACK, "generated", "sounds", "quests")
    os.makedirs(sounds, exist_ok=True)
    os.makedirs(args.stage, exist_ok=True)

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        sys.exit("chyba: ffmpeg nenalezen (sudo apt install ffmpeg)")

    total = sum(len(clips) for clips in manifest.values())
    if args.limit:
        total = min(total, args.limit)

    copied, joined, skipped, failed, missing = 0, 0, 0, [], []
    bytes_out, done = 0, 0

    for folder in sorted(manifest):
        # Jmeno zipu je jmeno adresare: at novy balicek WoWF.cz (Dabing_7...)
        # funguje bez zasahu do skriptu.
        archive = os.path.join(HERE, folder + ".zip")
        if not os.path.exists(archive):
            missing.append(folder)
            continue
        with zipfile.ZipFile(archive) as zf:
            names = set(zf.namelist())
            for clip, count in sorted(manifest[folder].items()):
                if args.limit and done >= args.limit:
                    break
                done += 1
                target = os.path.join(sounds, clip + ".ogg")
                if os.path.exists(target) and os.path.getsize(target) > 0:
                    skipped += 1
                    bytes_out += os.path.getsize(target)
                    continue

                if count == 1:
                    inside = "%s/Sounds/%s.ogg" % (folder, clip)
                    if inside not in names:
                        missing.append(inside)
                        continue
                    with zf.open(inside) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    copied += 1
                else:
                    pieces = []
                    for k in range(1, count + 1):
                        inside = "%s/Sounds/%s_%d.ogg" % (folder, clip, k)
                        if inside not in names:
                            missing.append(inside)
                            pieces = []
                            break
                        piece = os.path.join(args.stage, "%s_%d.ogg" % (clip, k))
                        with zf.open(inside) as src, open(piece, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        pieces.append(piece)
                    if not pieces:
                        continue
                    listing = os.path.join(args.stage, clip + ".txt")
                    with open(listing, "w", encoding="utf-8") as handle:
                        for path in pieces:
                            handle.write("file '%s'\n" % path.replace("'", r"'\''"))
                    result = subprocess.run(
                        [ffmpeg, "-nostdin", "-loglevel", "error", "-y",
                         "-f", "concat", "-safe", "0", "-i", listing,
                         "-codec:a", "libvorbis", "-qscale:a", str(args.quality),
                         "-ac", "1", target],
                        capture_output=True, text=True)
                    for path in pieces + [listing]:
                        try:
                            os.remove(path)
                        except OSError:
                            pass
                    if result.returncode != 0:
                        failed.append((clip, result.stderr.strip()[:100]))
                        continue
                    joined += 1

                if os.path.exists(target):
                    bytes_out += os.path.getsize(target)
                if done % 1000 == 0:
                    print("  %d / %d  (%s)" % (done, total, human(bytes_out)), flush=True)
        if args.limit and done >= args.limit:
            break

    print()
    print("zkopirovano v celku: %6d" % copied)
    print("slozeno z useku:     %6d" % joined)
    print("uz bylo hotovo:      %6d" % skipped)
    print("chybelo ve zdroji:   %6d" % len(missing))
    print("selhalo:             %6d" % len(failed))
    for clip, why in failed[:5]:
        print("   %s: %s" % (clip, why))
    for name in missing[:5]:
        print("   chybi %s" % name)
    print()
    print("v balicku: %s (%s)" % (sounds, human(bytes_out)))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
