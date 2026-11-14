#!/usr/bin/env python3
"""Vyrobi cesky balicek SpokenQuestsAudioGossip_csCZ pro Spoken Quests z dat WowfCZ.

Predloha: SpokenQuestsAudioGossip (DataModule, format verze 1).

Klic je tentokrat jiny nez u questu. Spoken pojmenovava repliku rozhovoru
hashem ANGLICKEHO textu a Spoken_Quests/DataModules.lua to u ResolveSoundFile
rika primo:

    "Its file is named for a hash of the English text in every language a pack
     is built in, so the fallback pack holds the same name."

Balicek proto zadnou vyhledavaci tabulku nenese: anglicky balicek uz mapuje
text na hash a ResolveSoundFile pak hleda soubor toho jmena v jazyce, ktery
hrac zvolil. Nam staci nahravky pojmenovane timze hashem.

Spojeni: ID NPC + anglicky text.
  Spoken  generated/npc_gossip_file_lookups.lua : [npcID]["<EN>"] = "<hash>"
  WowfCZ  Data/GreetingData.lua                 : { en=, cz=, field="gossipNN" }
          -> klip "n<npcID>-<field>" (s m-/f- variantami podle pohlavi HRACE,
             stejna konvence jako u questu)

Spustenie:  python3 -I build_gossip_cscz.py [--out ADRESAR] [--work ADRESAR]
"""

import argparse
import collections
import glob
import json
import os
import re
import sys

PACK = "SpokenQuestsAudioGossip_csCZ"
VERSION = "0.1.0"
ENGLISH_PACK = "SpokenQuestsAudioGossip"
LUA_STRING = r'"((?:[^"\\]|\\.)*)"'
# n<npcID>-<pole>, volitelne s prefixem pohlavi hrace
CLIP = re.compile(r"^(?:m-|f-)?n\d+-(?:gossip\d*|greeting)$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def unescape(value):
    return (value.replace('\\"', '"').replace("\\n", "\n")
                 .replace("\\t", "\t").replace("\\\\", "\\"))


def lua_string(value):
    out = value.replace("\\", "\\\\").replace('"', '\\"')
    return out.replace("\r", "").replace("\n", "\\n")


def norm(text):
    """Porovnatelna podoba repliky. Tokeny serveru ($B, $N, $G...) obe strany
    drzi, takze se nerozbaluji -- jen $B, ktery je jen zalomeni radku a jedna
    strana misto nej nekdy ma primo novy radek."""
    text = text.lower()
    text = text.replace("’", "'").replace(" ", " ").replace(" ", " ")
    text = re.sub(r"\$b", " ", text)
    text = re.sub(r"[^\w\s]", " ", text, flags=re.U)
    return re.sub(r"\s+", " ", text).strip()


def spoken_lookup(path):
    """[npcID][normalizovany EN] = hash"""
    out = collections.defaultdict(dict)
    npc = None
    for line in read(path).splitlines():
        head = re.match(r"\s*\[(\d+)\] = \{", line)
        if head:
            npc = int(head.group(1))
            continue
        row = re.match(r'\s*\[' + LUA_STRING + r'\] = "([0-9a-f]+)"', line)
        if row and npc is not None:
            out[npc][norm(unescape(row.group(1)))] = row.group(2)
    return out


def wowf_texts(path):
    """[npcID][normalizovany EN] = (pole, cesky text)"""
    out = collections.defaultdict(dict)
    npc, section = None, None
    for line in read(path).splitlines():
        head = re.match(r"WowfCZ_GreetingData\[(\d+)\]", line)
        if head:
            npc, section = int(head.group(1)), None
            continue
        start = re.match(r"\s{4}(\w+) = \{", line)
        if start:
            section = start.group(1)
            continue
        if npc is None or section not in ("Gossip", "QuestGreeting"):
            continue
        row = re.search(r'\{ en = ' + LUA_STRING + r', cz = ' + LUA_STRING
                        + r', field = "(\w+)"', line)
        if row:
            out[npc][norm(unescape(row.group(1)))] = (row.group(3), unescape(row.group(2)))
    return out


def voice_data(paths):
    """klip -> (delka, adresar), klip -> titulek, klip -> pocet useku"""
    lengths, captions, parts = {}, {}, {}
    for path in paths:
        folder = os.path.basename(os.path.dirname(path))
        text = read(path)
        for clip, length in re.findall(r'^D\["([^"]+)"\] = \{ ([0-9.]+)', text, re.M):
            if CLIP.match(clip):
                lengths[clip] = (float(length), folder)
        for clip, body in re.findall(r'^WowfCZ_VoiceCaptions\["([^"]+)"\] = ' + LUA_STRING,
                                     text, re.M):
            if CLIP.match(clip):
                captions[clip] = unescape(body)
        for clip, body in re.findall(r'^S\["([^"]+)"\] = \{\s*([0-9][0-9.,\s]*)\}', text, re.M):
            if CLIP.match(clip):
                cuts = [piece for piece in body.split(",") if piece.strip()]
                if cuts:
                    parts[clip] = len(cuts) + 1
    return lengths, captions, parts


MODULE = '''if not VoiceOver or not VoiceOver.DataModules then return end

{pack} = {{}}

function {pack}:GetSoundPath(fileName, event)
    setfenv(1, VoiceOver)
    if Enums.SoundEvent:IsGossipEvent(event) then
        return format([[generated\\sounds\\gossip\\%s.ogg]], fileName)
    end
end

VoiceOver.DataModules:Register("{pack}", {pack})
'''

TOC = '''## X-SpokenQuests-Language: csCZ

## Interface: 11509, 20506, 16001
## Title: |cffb48cffSpoken|r Czech Audio: Gossip
## Notes: Cesky dabing a titulky rozhovoru s NPC pro Spoken Quests.|n|nNahravky a text: WoWF.cz (WowfCZ).|n|nJe v poradku, kdyz se addon tvari "disabled" nebo "out of date" - Spoken Quests ho nacte stejne.
## Version: {version}
## IconTexture: Interface\\AddOns\\{pack}\\Textures\\AddonIcon.tga
## LoadOnDemand: 1
## Group: Spoken
## X-Part-Of: Spoken
## X-Child-Of: Spoken_Quests
## Dependencies: SpokenCzech
## X-SpokenQuests-DataModule-Version: 1
## X-SpokenQuests-DataModule-Priority: 100
## X-VoiceOver-DataModule-Version: 1
## X-VoiceOver-DataModule-Priority: 100
## X-Credits: Cesky preklad a dabing WoWF.cz (WowfCZ, autor Fejac).

Module.lua

generated\\sound_length_table.lua
generated\\captions.lua
'''

LENGTH_HEAD = """-- VYGENEROVANE build_gossip_cscz.py. Needitovat rucne.
--
-- Delky nahravek v sekundach, klicem je hash anglickeho textu -- totez jmeno,
-- jake ma replika v anglickem balicku. Tahle tabulka je zaroven to, podle ceho
-- Spoken pozna, ze balicek repliku ma (DataModules:ResolveSoundFile).

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.SoundLengthLookupByFileName = {{
"""

CAPTION_HEAD = """-- VYGENEROVANE build_gossip_cscz.py. Needitovat rucne.
--
-- Cesky text ke kazde nahravce. Hra ho na anglickem klientu nema, takze ho
-- nese balicek; do okna vypravece ho zaradi SpokenCzech v Player:Prepare.

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.CaptionByFileName = {{
"""


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--work", default=os.path.join(here, "_work"))
    parser.add_argument("--out", default=os.path.join(here, PACK))
    parser.add_argument("--spoken", default=os.path.join(here, "_work", "spoken"),
                        help="rozbaleny Spoken (hleda se v nem anglicky balicek rozhovoru)")
    args = parser.parse_args()

    lookup_path = None
    for root in (args.spoken, os.environ.get("WOW_ADDONS", "")):
        candidate = os.path.join(root, ENGLISH_PACK, "generated", "npc_gossip_file_lookups.lua")
        if os.path.exists(candidate):
            lookup_path = candidate
            break
    if not lookup_path:
        sys.exit("chyba: nenasiel som %s/generated/npc_gossip_file_lookups.lua" % ENGLISH_PACK)

    wowf = os.path.join(args.work, "wowfcz")
    greeting = os.path.join(wowf, "WowfCZ", "Data", "GreetingData.lua")
    sources = [os.path.join(wowf, "WowfCZ", "VoiceData.lua")]
    sources += sorted(glob.glob(os.path.join(wowf, "WowfCZ_Dabing_*", "Data.lua")))
    for path in [greeting] + sources:
        if not os.path.exists(path):
            sys.exit("chyba: nenasiel som %s" % path)

    spoken = spoken_lookup(lookup_path)
    texts = wowf_texts(greeting)
    lengths, captions, parts = voice_data(sources)

    rows, caption_rows, manifest = {}, {}, {}
    stats = collections.Counter()
    # Serazene, aby byl build reprodukovatelny: tutez repliku rika vic NPC
    # a hash je spolecny, takze o nahravku rozhoduje poradi.
    for npc, lines in sorted(spoken.items()):
        known = texts.get(npc)
        if not known:
            continue
        for english, digest in sorted(lines.items()):
            found = known.get(english)
            if not found:
                continue
            stats["sparovano"] += 1
            field, czech = found
            base = "n%d-%s" % (npc, field)
            variants = [(prefix + base, prefix + digest)
                        for prefix in ("m-", "f-") if prefix + base in lengths]
            if not variants and base in lengths:
                variants = [(base, digest)]
            if not variants:
                stats["bez nahravky"] += 1
                continue
            stats["s nahravkou"] += 1
            for clip, name in variants:
                if name in rows:
                    continue
                length, folder = lengths[clip]
                rows[name] = length
                # Titulek primo od nahravky ma prednost pred textem ze stranky:
                # mluvene zneni se obcas lisi od psaneho.
                text = captions.get(clip) or czech
                if text:
                    caption_rows[name] = text
                manifest.setdefault(folder, {})[clip] = {
                    "parts": parts.get(clip, 1), "out": name}

    if not rows:
        sys.exit("chyba: nic sa nesparovalo")

    os.makedirs(os.path.join(args.out, "generated"), exist_ok=True)
    with open(os.path.join(args.out, "generated", "sound_length_table.lua"),
              "w", encoding="utf-8") as handle:
        handle.write(LENGTH_HEAD.format(pack=PACK))
        for name in sorted(rows):
            handle.write('    ["%s"] = %.2f,\n' % (name, rows[name]))
        handle.write("}\n")

    with open(os.path.join(args.out, "generated", "captions.lua"),
              "w", encoding="utf-8") as handle:
        handle.write(CAPTION_HEAD.format(pack=PACK))
        for name in sorted(rows):
            if name in caption_rows:
                handle.write('    ["%s"] = "%s",\n' % (name, lua_string(caption_rows[name])))
        handle.write("}\n")

    with open(os.path.join(args.out, "Module.lua"), "w", encoding="utf-8") as handle:
        handle.write(MODULE.format(pack=PACK))
    with open(os.path.join(args.out, "%s.toc" % PACK), "w", encoding="utf-8") as handle:
        handle.write(TOC.format(version=VERSION, pack=PACK))
    with open(os.path.join(args.out, "sounds-to-convert.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, ensure_ascii=False)

    total = sum(len(v) for v in spoken.values())
    files = sum(entry["parts"] for clips in manifest.values() for entry in clips.values())
    print("replik rozhovoru u Spokenu: %6d" % total)
    print("  sparovano s WoWF.cz:      %6d (%.1f %%)" % (stats["sparovano"],
          100.0 * stats["sparovano"] / total))
    print("  z toho s nahravkou:       %6d (%.1f %%)" % (stats["s nahravkou"],
          100.0 * stats["s nahravkou"] / total))
    print("  sparovano bez nahravky:   %6d" % stats["bez nahravky"])
    print()
    print("souboru v balicku:          %6d" % len(rows))
    print("  s ceskym titulkem:        %6d" % len(caption_rows))
    print("zdrojovych souboru:         %6d" % files)
    print()
    for folder in sorted(manifest):
        print("  %-22s %6d klipu" % (folder, len(manifest[folder])))
    print()
    print("balicek: %s" % args.out)


if __name__ == "__main__":
    main()
