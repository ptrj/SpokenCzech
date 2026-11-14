#!/usr/bin/env python3
"""Vyrobi zipy pro GitHub Release z hotovych balicku.

GitHub pusti jako prilohu releasu soubor **do 2 GiB**. Questovy balicek je vetsi,
takze se rozdeli na nekolik normalnich zipu, ktere se rozbaluji do stejne slozky
a v Interface/AddOns se slozi dohromady. Zadne skladani .z01 souboru, zadny 7-Zip.

  python3 -I make_release.py                 # do dist/release/
  python3 -I make_release.py --part-size 800 # jemnejsi deleni (MB)
"""
import argparse
import hashlib
import os
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VERSION = "0.1.0"

# Lepidlo prvni - bez nej se zadny datovy balicek nechyti.
PACKS = [
    "SpokenCzech",
    "SpokenReadablesAudio_csCZ",
    "SpokenQuestsAudio_csCZ",
    "SpokenQuestsAudioGossip_csCZ",
    "SpokenQuestsAudioChatter_csCZ",
]

# Jen pro build, hrac to nepotrebuje.
SKIP = {"sounds-to-convert.json"}

AUDIO = (".ogg", ".mp3")


def listing(pack_dir):
    """Vrati (nezvukove, zvukove) jako (relativni cesta, velikost), setridene."""
    plain, audio = [], []
    for root, dirs, names in os.walk(pack_dir):
        dirs.sort()
        for name in sorted(names):
            if name in SKIP:
                continue
            full = os.path.join(root, name)
            rel = os.path.relpath(full, os.path.dirname(pack_dir))
            row = (rel, os.path.getsize(full))
            (audio if name.lower().endswith(AUDIO) else plain).append(row)
    return plain, audio


def split(plain, audio, limit):
    """Rozdeli soubory na casti do `limit` bajtu. Nezvukove patri do prvni casti."""
    parts = [list(plain)]
    used = sum(size for _, size in plain)
    for row in audio:
        if used + row[1] > limit and parts[-1]:
            parts.append([])
            used = 0
        parts[-1].append(row)
        used += row[1]
    return parts


def write_zip(path, rows, base):
    # Zvuk se ulozi, jak je - .ogg/.mp3 uz komprimovane je a zabalit se neda.
    # Vsechno ostatni (tabulky, pismo, TOC) se komprimuje, je to cisty text.
    with zipfile.ZipFile(path, "w", zipfile.ZIP_STORED, allowZip64=True) as z:
        for rel, _ in rows:
            stored = rel.lower().endswith(AUDIO)
            z.write(os.path.join(base, rel), rel,
                    compress_type=zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED)


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "dist", "release"))
    ap.add_argument("--part-size", type=int, default=1200,
                    help="maximalni velikost jednoho zipu v MB (GitHub pusti 2 GiB)")
    ap.add_argument("--only", action="append",
                    help="jen tenhle balicek, lze zadat vickrat")
    args = ap.parse_args()

    limit = args.part_size * 1000 * 1000
    if limit > 1900 * 1000 * 1000:
        sys.exit("chyba: --part-size nad 1900 MB se na GitHub nevejde")
    os.makedirs(args.out, exist_ok=True)

    made = []
    for pack in args.only or PACKS:
        pack_dir = os.path.join(HERE, pack)
        if not os.path.isdir(pack_dir):
            print("preskakuji %-32s (neni postaveny)" % pack)
            continue
        plain, audio = listing(pack_dir)
        parts = split(plain, audio, limit)
        for index, rows in enumerate(parts, 1):
            if len(parts) == 1:
                name = "%s-%s.zip" % (pack, VERSION)
            else:
                name = "%s-%s-cast%dz%d.zip" % (pack, VERSION, index, len(parts))
            path = os.path.join(args.out, name)
            write_zip(path, rows, os.path.dirname(pack_dir))
            size = os.path.getsize(path)
            print("%-48s %6.0f MB  %5d souboru" % (name, size / 1e6, len(rows)))
            if size > 2 * 1024 ** 3:
                sys.exit("chyba: %s je nad 2 GiB, GitHub ho nepusti" % name)
            made.append((name, path))

    sums = os.path.join(args.out, "SHA256SUMS.txt")
    with open(sums, "w", encoding="utf-8") as handle:
        for name, path in made:
            handle.write("%s  %s\n" % (sha256(path), name))
    print("\n%d zipu + SHA256SUMS.txt v %s" % (len(made), args.out))


if __name__ == "__main__":
    main()
