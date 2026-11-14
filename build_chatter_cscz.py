#!/usr/bin/env python3
"""Vyrobi cesky balicek SpokenQuestsAudioChatter_csCZ -- to, co NPC rikaji
nahlas ve svete (Spoken: World Chatter, WoWF.cz: "say").

Spoken pozna repliku podle mluviciho a presneho textu (Spoken_Quests/
ChatterLines.lua) a prehraje ji pres Followup:Play, ktery soubor hleda pod
jmenem z FollowupLookup anglickeho balicku a s udalosti QuestFollowup
(Followup.lua, OwnClip). Stejne jako u rozhovoru tedy staci dodat nahravky
pojmenovane tak, jak je pojmenoval anglicky balicek -- zadna vyhledavaci
tabulka v ceskem balicku byt nemusi.

Spojeni: ID NPC + anglicky text.
  Spoken  Spoken_Quests/ChatterLines.lua        : [npcID] { id = <BT id>, text = "<EN>" }
  Spoken  generated/followup_lookups.lua        : FollowupLookup[npcID][<BT id>] = "<jmeno>"
  WowfCZ  Data/GreetingData.lua, sekce Says     : { en=, cz=, n=K } -> klip "n<npcID>-say<K>"

NPC kreslene vic telY maji u Spokenu jmeno na telo navic (FollowupLookupByNPCBody,
"1380-model-77"). Telo pojmenovavaji obe strany jinak, takze se pod vsechna jmena
dava tataz ceska nahravka -- jinak by takove NPC mluvilo anglicky.

Spustenie:  python3 -I build_chatter_cscz.py
"""

import argparse
import collections
import glob
import json
import os
import re
import sys

PACK = "SpokenQuestsAudioChatter_csCZ"
VERSION = "0.1.0"
GAME = os.environ.get("WOW_ADDONS", "")  # kde je nainstalovana hra; nenastaveno = preskoci se
LUA_STRING = r'"((?:[^"\\]|\\.)*)"'
SAY = re.compile(r"^(?:m-|f-)?n\d+-say\d+$")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def unescape(v):
    return v.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")


def lua_string(v):
    return v.replace("\\", "\\\\").replace('"', '\\"').replace("\r", "").replace("\n", "\\n")


def norm(t):
    t = t.lower().replace("\u2019", "'").replace("\u00a0", " ").replace("\u202f", " ")
    t = re.sub(r"\$b", " ", t)
    t = re.sub(r"[^\w\s]", " ", t, flags=re.U)
    return re.sub(r"\s+", " ", t).strip()


def chatter_lines(path):
    """[npcID][normalizovany EN] = id broadcast textu"""
    out, npc = collections.defaultdict(dict), None
    for line in read(path).splitlines():
        head = re.match(r"\s*\[(\d+)\] = \{ name", line)
        if head:
            npc = int(head.group(1))
            continue
        row = re.search(r'\{ id = (\d+), text = ' + LUA_STRING + r' \}', line)
        if row and npc is not None:
            out[npc][norm(unescape(row.group(2)))] = int(row.group(1))
    return out


def followup_stems(paths):
    """[npcID][id] = mnozina vsech jmen, pod kterymi to Spoken muze hledat"""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for path in paths:
        text = read(path)
        # FollowupLookup[npc][id] = "jmeno"
        npc = None
        for line in text.splitlines():
            head = re.match(r"\s*\[(\d+)\] = \{\s*$", line)
            if head:
                npc = int(head.group(1))
                continue
            row = re.match(r'\s*\[(\d+)\] = "([^"]+)"', line)
            if row and npc is not None:
                out[npc][int(row.group(1))].add(row.group(2))
        # FollowupLookupByNPCBody/Sex[npc][id][telo] = "jmeno"
        npc = lid = None
        for line in text.splitlines():
            head = re.match(r"\s*\[(\d+)\] = \{\s*$", line)
            if head:
                npc, lid = int(head.group(1)), None
                continue
            inner = re.match(r"\s*\[(\d+)\] = \s*\{\s*$", line)
            if inner and npc is not None:
                lid = int(inner.group(1))
                continue
            row = re.match(r'\s*\["[^"]+"\] = "([^"]+)"', line)
            if row and npc is not None and lid is not None:
                out[npc][lid].add(row.group(1))
    return out


def wowf_says(path):
    """[npcID][normalizovany EN] = (poradi, cesky text)"""
    out, npc, section = collections.defaultdict(dict), None, None
    for line in read(path).splitlines():
        head = re.match(r"WowfCZ_GreetingData\[(\d+)\]", line)
        if head:
            npc, section = int(head.group(1)), None
            continue
        start = re.match(r"\s{4}(\w+) = \{", line)
        if start:
            section = start.group(1)
            continue
        if section != "Says" or npc is None:
            continue
        row = re.search(r'\{ en = ' + LUA_STRING + r', cz = ' + LUA_STRING + r', n = (\d+)', line)
        if row:
            out[npc][norm(unescape(row.group(1)))] = (int(row.group(3)), unescape(row.group(2)))
    return out


def voice_data(paths):
    lengths, captions, parts = {}, {}, {}
    for path in paths:
        folder = os.path.basename(os.path.dirname(path))
        text = read(path)
        for clip, length in re.findall(r'^D\["([^"]+)"\] = \{ ([0-9.]+)', text, re.M):
            if SAY.match(clip):
                lengths[clip] = (float(length), folder)
        for clip, body in re.findall(r'^WowfCZ_VoiceCaptions\["([^"]+)"\] = ' + LUA_STRING, text, re.M):
            if SAY.match(clip):
                captions[clip] = unescape(body)
        for clip, body in re.findall(r'^S\["([^"]+)"\] = \{\s*([0-9][0-9.,\s]*)\}', text, re.M):
            if SAY.match(clip):
                cuts = [p for p in body.split(",") if p.strip()]
                if cuts:
                    parts[clip] = len(cuts) + 1
    return lengths, captions, parts


MODULE = '''if not VoiceOver or not VoiceOver.DataModules then return end

{pack} = {{}}

function {pack}:GetSoundPath(fileName, event)
    setfenv(1, VoiceOver)
    -- Hlasky NPC ve svete se hledaji jako QuestFollowup, i kdyz se hraji jako
    -- NPCChatter: Followup.lua, OwnClip, zkousi soubor prave timhle eventem.
    if Enums.SoundEvent.QuestFollowup and event == Enums.SoundEvent.QuestFollowup then
        return format([[generated\\sounds\\followup\\%s.ogg]], fileName)
    end
end

VoiceOver.DataModules:Register("{pack}", {pack})
'''

TOC = '''## X-SpokenQuests-Language: csCZ

## Interface: 11509, 20506, 16001
## Title: |cffb48cffSpoken|r Czech Audio: World Chatter
## Notes: Cesky dabing toho, co NPC rikaji nahlas ve svete, pro Spoken Quests.|n|nNahravky a text: WoWF.cz (WowfCZ).|n|nJe v poradku, kdyz se addon tvari "disabled" nebo "out of date" - Spoken Quests ho nacte stejne.
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

LENGTH_HEAD = """-- VYGENEROVANE build_chatter_cscz.py. Needitovat rucne.
--
-- Delky nahravek v sekundach pod jmeny, ktera replikam dal anglicky balicek.
-- Podle teto tabulky Spoken pozna, ze balicek repliku ma.

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.SoundLengthLookupByFileName = {{
"""

CAPTION_HEAD = """-- VYGENEROVANE build_chatter_cscz.py. Needitovat rucne.
--
-- Cesky text ke kazde nahravce; do okna vypravece ho zaradi SpokenCzech.

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.CaptionByFileName = {{
"""


def main():
    ap = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    ap.add_argument("--work", default=os.path.join(here, "_work"))
    ap.add_argument("--out", default=os.path.join(here, PACK))
    ap.add_argument("--spoken", default=os.path.join(here, "_work", "spoken"))
    args = ap.parse_args()

    root = None
    for candidate in (args.spoken, GAME):
        if os.path.exists(os.path.join(candidate, "Spoken_Quests", "ChatterLines.lua")):
            root = candidate
            break
    if not root:
        sys.exit("chyba: nenasiel som Spoken_Quests/ChatterLines.lua")
    # Anglicke balicky se stahuji zvlast, takze nemusi lezet tam, kde Spoken sam.
    lookups = []
    for candidate in (args.spoken, GAME):
        lookups += sorted(glob.glob(os.path.join(candidate, "SpokenQuestsAudio*", "generated",
                                                 "*followup_lookups.lua")))
    lookups = [p for p in lookups if "_csCZ" not in p]
    if not lookups:
        sys.exit("chyba: nenasiel som followup_lookups.lua v anglickych balickoch")

    wowf = os.path.join(args.work, "wowfcz")
    greeting = os.path.join(wowf, "WowfCZ", "Data", "GreetingData.lua")
    sources = [os.path.join(wowf, "WowfCZ", "VoiceData.lua")]
    sources += sorted(glob.glob(os.path.join(wowf, "WowfCZ_Dabing_*", "Data.lua")))
    for path in [greeting] + sources:
        if not os.path.exists(path):
            sys.exit("chyba: nenasiel som %s" % path)

    chat = chatter_lines(os.path.join(root, "Spoken_Quests", "ChatterLines.lua"))
    stems = followup_stems(lookups)
    says = wowf_says(greeting)
    lengths, captions, parts = voice_data(sources)

    rows, caption_rows, manifest = {}, {}, {}
    stats = collections.Counter()
    for npc in sorted(chat):
        if npc not in says:
            continue
        for english in sorted(chat[npc]):
            found = says[npc].get(english)
            if not found:
                continue
            stats["sparovano"] += 1
            order, czech = found
            base = "n%d-say%d" % (npc, order)
            variants = [(prefix + base, prefix) for prefix in ("m-", "f-")
                        if prefix + base in lengths]
            if not variants and base in lengths:
                variants = [(base, "")]
            if not variants:
                stats["bez nahravky"] += 1
                continue
            names = stems.get(npc, {}).get(chat[npc][english])
            if not names:
                stats["bez jmena od Spokenu"] += 1
                continue
            stats["pouzito"] += 1
            for stem in sorted(names):
                stats["jmen celkem"] += 1
                for clip, prefix in variants:
                    out = prefix + stem
                    if out in rows:
                        continue
                    length, folder = lengths[clip]
                    rows[out] = length
                    text = captions.get(clip) or czech
                    if text:
                        caption_rows[out] = text
                    manifest.setdefault(folder, {})[out] = {
                        "parts": parts.get(clip, 1), "src": clip}

    if not rows:
        sys.exit("chyba: nic sa nesparovalo")

    os.makedirs(os.path.join(args.out, "generated"), exist_ok=True)
    with open(os.path.join(args.out, "generated", "sound_length_table.lua"), "w",
              encoding="utf-8") as handle:
        handle.write(LENGTH_HEAD.format(pack=PACK))
        for name in sorted(rows):
            handle.write('    ["%s"] = %.2f,\n' % (name, rows[name]))
        handle.write("}\n")
    with open(os.path.join(args.out, "generated", "captions.lua"), "w",
              encoding="utf-8") as handle:
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

    total = sum(len(v) for v in chat.values())
    print("replik World Chatter:       %6d" % total)
    print("  sparovano s WoWF.cz:      %6d (%.1f %%)" % (stats["sparovano"],
          100.0 * stats["sparovano"] / max(total, 1)))
    print("  pouzito:                  %6d" % stats["pouzito"])
    print("  bez ceske nahravky:       %6d" % stats["bez nahravky"])
    print("  bez jmena od Spokenu:     %6d" % stats["bez jmena od Spokenu"])
    print()
    print("jmen, pod kterymi Spoken hleda: %6d" % stats["jmen celkem"])
    print("souboru v balicku:              %6d" % len(rows))
    print("  s ceskym titulkem:            %6d" % len(caption_rows))
    print()
    print("balicek: %s" % args.out)


if __name__ == "__main__":
    main()
