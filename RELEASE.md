# Text pro popis releasu

Zkopíruj do popisu releasu na GitHubu (`Releases` → `Draft a new release`).
Tag: `v0.1.0`, název: `0.1.0 — demo ukázka`.

---

## ⚠️ Demo ukázka

Tohle **není hotový addon**. Je to ukázka, aby se dalo vyzkoušet, **jak zní český dabing
z [WoWF.cz](https://wowf.cz) uvnitř addonu [Spoken](https://spoken.quest)**.

Není to otestované na všem, co hra nabízí, a **není to oficiální** — ani vydání Spokenu,
ani vydání WoWF.cz. Zpětná vazba je vítaná.

**Potřebuje Spoken 3.9.0 nebo novější.** Na starším se nic nerozbije, jen se čeština
nenapojí — `/spokencz` to napíše.

## Co stáhnout

| soubor | velikost | co přidá |
| --- | --- | --- |
| **`SpokenCzech-0.1.0.zip`** | 43 kB | **povinné** — bez něj se ostatní balíčky nechytí |
| `SpokenReadablesAudio_csCZ-0.1.0.zip` | 277 MB | knihy, dopisy, cedule (997 stránek) |
| `SpokenQuestsAudio_csCZ-0.1.0-cast1z3.zip` | 1,2 GB | questy (21 119 nahrávek), |
| `SpokenQuestsAudio_csCZ-0.1.0-cast2z3.zip` | 1,2 GB | rozdělené na tři soubory, |
| `SpokenQuestsAudio_csCZ-0.1.0-cast3z3.zip` | 940 MB | protože GitHub pustí nejvýš 2 GiB |
| `SpokenQuestsAudioGossip_csCZ-0.1.0.zip` | 604 MB | rozhovory s NPC (5 636 nahrávek) |
| `SpokenQuestsAudioChatter_csCZ-0.1.0.zip` | 15 MB | co NPC říkají nahlas ve světě (374) |

Balíčky jsou na sobě nezávislé — klidně jen knihy, nebo jen questy. Dohromady 3,2 GB.

**Ty tři části questů jsou tři normální zipy.** Nic se neskládá předem, 7-Zip není potřeba:
rozbal všechny tři do `Interface/AddOns` a potvrď spojení složek. Část 1 je povinná, jsou
v ní tabulky.

`SHA256SUMS.txt` je na ověření, že se stahování nerozbilo:
`sha256sum -c SHA256SUMS.txt`

## Instalace

1. Rozbal do `Interface/AddOns`, názvy složek nech, jak jsou.
2. **Restartuj hru** — ne `/reload`. Nové zvuky klient načte až při startu.
3. Nastavení Spokenu → **Language** → **Voice Language: Čeština**,
   **If a Voice Is Missing: English**.
4. `/spokencz` vypíše, co se napojilo.

Celý návod: [`INSTALL.md`](INSTALL.md)

## Co je česky

questy · knihy a Azeroth's Compendium · rozhovory s NPC (93 %) · co NPC říkají nahlas
(62 %) · zvýrazňování slov podle hlasu (99,8 % questů)

Anglicky zůstává rozhraní Spokenu (záměrně) a Compendium → Places a Bosses, k nim
český zdroj není. Co česky není, se přehraje anglicky.

## Žádný soubor Spokenu se nemění

Čeština se napojuje až za běhu, přes veřejná rozhraní Spokenu. Aktualizace Spokenu nic
nepřepíše a vypnutím `SpokenCzech` se všechno vrátí k angličtině.

## Původ

Český překlad a dabing: **[WoWF.cz](https://wowf.cz)** (addon `WowfCZ`, autor Fejac) —
nahrávky a texty jsou jejich práce a jejich majetek.
Addon **[Spoken](https://spoken.quest)**: rusty.
