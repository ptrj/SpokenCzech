#!/usr/bin/env python3
"""Vyrobi cesky balicek SpokenQuestsAudio_csCZ pro Spoken Quests z dat WowfCZ.

Predloha: SpokenQuestsAudioAlliance_deDE (DataModule, format verze 1).

Pojmenovani sedi 1:1, coz je stesti, ne zasluha:
  * Spoken sklada zaklad jako "<questID>-<accept|progress|complete>"
    (Spoken_Quests/DataModules.lua, QuestFile) -- WowfCZ take;
  * varianty podle pohlavi HRACE resi Spoken prefixem "m-" / "f-"
    (DataModules:AddPlayerGenderToFilename) -- WowfCZ take.

Text: hra na anglickem klientu zadny cesky nema, takze ho nese balicek sam
v CaptionByFileName a patch v Player:Prepare ho zaradi do okna vypravece.

Spustenie:  python3 -I build_quests_cscz.py [--out ADRESAR] [--work ADRESAR]
"""

import argparse
import glob
import json
import os
import re
import sys

PACK = "SpokenQuestsAudio_csCZ"
VERSION = "0.1.0"
FONT = r"Interface\AddOns\SpokenQuestsAudio_csCZ\Fonts\FRIZQT__.ttf"

# klip questu: volitelny prefix pohlavi hrace, questID, cast
CLIP = re.compile(r"^(?:m-|f-)?\d+-(?:accept|progress|complete)$")
LUA_STRING = r'"((?:[^"\\]|\\.)*)"'


def read(path):
    with open(path, encoding="utf-8", errors="replace") as handle:
        return handle.read()


def unescape(value):
    return (value.replace('\\"', '"').replace("\\n", "\n")
                 .replace("\\t", "\t").replace("\\\\", "\\"))


def lua_string(value):
    out = value.replace("\\", "\\\\").replace('"', '\\"')
    return out.replace("\r", "").replace("\n", "\\n")


def voice_data(paths):
    """klip -> (dlzka, adresar balicka), klip -> titulok, klip -> poc. useku."""
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
        # Rezy dlouhe nahravky: S["klip"] = { 5.35, 14.36 }; soubory <klip>_<k>.
        # Jmeno S nese v temze souboru i jina tabulka, ta ma ale uvnitr klice.
        for clip, body in re.findall(r'^S\["([^"]+)"\] = \{\s*([0-9][0-9.,\s]*)\}',
                                     text, re.M):
            if CLIP.match(clip):
                cuts = [piece for piece in body.split(",") if piece.strip()]
                if cuts:
                    parts[clip] = len(cuts) + 1
    return lengths, captions, parts


MODULE = '''if not VoiceOver or not VoiceOver.DataModules then return end

{pack} = {{}}

function {pack}:GetSoundPath(fileName, event)
    setfenv(1, VoiceOver)
    if Enums.SoundEvent:IsQuestEvent(event) then
        return format([[generated\\sounds\\quests\\%s.ogg]], fileName)
    end
end

VoiceOver.DataModules:Register("{pack}", {pack})
'''

TOC = '''## X-SpokenQuests-Language: csCZ

## Interface: 11509, 20506, 16001
## Title: |cffb48cffSpoken|r Czech Audio: Quests
## Notes: Cesky dabing a titulky questu pro Spoken Quests.|n|nNahravky a text: WoWF.cz (WowfCZ).|n|nJe v poradku, kdyz se addon tvari "disabled" nebo "out of date" - Spoken Quests ho nacte stejne.
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

LENGTH_HEAD = """-- VYGENEROVANE build_quests_cscz.py. Needitovat rucne.
--
-- Delky nahravek v sekundach. Tahle tabulka je zaroven to, podle ceho Spoken
-- pozna, ze balicek klip ma (DataModules:ResolveSoundFile).

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.SoundLengthLookupByFileName = {{
"""

CAPTION_HEAD = """-- VYGENEROVANE build_quests_cscz.py. Needitovat rucne.
--
-- Cesky text ke kazde nahravce. Hra ho na anglickem klientu nema, takze ho
-- nese balicek; do okna vypravece ho zaradi patch v Player:Prepare.

if not VoiceOver or not VoiceOver.DataModules then return end
{pack}.CaptionByFileName = {{
"""


def main():
    parser = argparse.ArgumentParser()
    here = os.path.dirname(os.path.abspath(__file__))
    parser.add_argument("--work", default=os.path.join(here, "_work"))
    parser.add_argument("--out", default=os.path.join(here, PACK))
    args = parser.parse_args()

    wowf = os.path.join(args.work, "wowfcz")
    sources = [os.path.join(wowf, "WowfCZ", "VoiceData.lua")]
    # Glob, ne pevny rozsah: novy balicek WoWF.cz se pak najde sam.
    sources += sorted(glob.glob(os.path.join(wowf, "WowfCZ_Dabing_*", "Data.lua")))
    for path in sources:
        if not os.path.exists(path):
            sys.exit("chyba: nenasiel som %s" % path)

    lengths, captions, parts = voice_data(sources)
    if not lengths:
        sys.exit("chyba: ziadne questove klipy")

    os.makedirs(os.path.join(args.out, "generated"), exist_ok=True)

    with open(os.path.join(args.out, "generated", "sound_length_table.lua"),
              "w", encoding="utf-8") as handle:
        handle.write(LENGTH_HEAD.format(pack=PACK))
        for clip in sorted(lengths):
            handle.write('    ["%s"] = %.2f,\n' % (clip, lengths[clip][0]))
        handle.write("}\n")

    with_text = 0
    with open(os.path.join(args.out, "generated", "captions.lua"),
              "w", encoding="utf-8") as handle:
        handle.write(CAPTION_HEAD.format(pack=PACK))
        for clip in sorted(lengths):
            text = captions.get(clip)
            if not text:
                continue
            with_text += 1
            handle.write('    ["%s"] = "%s",\n' % (clip, lua_string(text)))
        handle.write("}\n")

    with open(os.path.join(args.out, "Module.lua"), "w", encoding="utf-8") as handle:
        handle.write(MODULE.format(pack=PACK))
    with open(os.path.join(args.out, "%s.toc" % PACK), "w", encoding="utf-8") as handle:
        handle.write(TOC.format(version=VERSION, pack=PACK))

    manifest, files = {}, 0
    for clip, (_, folder) in sorted(lengths.items()):
        count = parts.get(clip, 1)
        manifest.setdefault(folder, {})[clip] = count
        files += count
    with open(os.path.join(args.out, "sounds-to-convert.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=1, ensure_ascii=False)

    gendered = sum(1 for clip in lengths if clip[:2] in ("m-", "f-"))
    split = sum(1 for clip in lengths if clip in parts)
    print("klipu questu:        %6d" % len(lengths))
    print("  z toho m-/f-:      %6d (varianty podle pohlavi hrace)" % gendered)
    print("  rozrezanych:       %6d" % split)
    print("s ceskym titulkem:   %6d (%.1f %%)"
          % (with_text, 100.0 * with_text / len(lengths)))
    print("zdrojovych souboru:  %6d" % files)
    print()
    for folder in sorted(manifest):
        print("  %-22s %6d klipu" % (folder, len(manifest[folder])))
    print()
    print("balicek: %s" % args.out)


if __name__ == "__main__":
    main()
