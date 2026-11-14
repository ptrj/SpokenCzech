# Čeština pro Spoken — návod pro hráče

> **Je to demo ukázka, ne hotový addon.** Není to otestované na všem a nic to nezaručuje.
> Co přesně to znamená, je v [`README.md`](README.md).

Addony, které do **[Spokenu](https://spoken.quest)** přinesou český dabing a český text
z **[WoWF.cz](https://wowf.cz)** (`WowfCZ`).

**Potřebuje Spoken 3.9.0 nebo novější.** Na starším se nic nerozbije, jen se čeština
nenapojí — `/spokencz` to napíše.

**Žádný soubor Spokenu se nemění.** Všechno se napojuje za běhu přes jeho vlastní veřejné
plochy, takže aktualizace Spokenu nic nepřepíše a vypnutím `SpokenCzech` se všechno vrátí
k angličtině.

## Co nainstalovat

| ke stažení | velikost | co dělá |
| --- | --- | --- |
| **`SpokenCzech-0.1.0.zip`** | 43 kB | lepidlo — **povinné**, bez něj se balíčky nechytí |
| `SpokenReadablesAudio_csCZ-0.1.0.zip` | 277 MB | knihy, dopisy, cedule — 997 stránek |
| `SpokenQuestsAudio_csCZ-0.1.0-cast1z3.zip` | 1,2 GB | questy — 21 119 nahrávek, |
| `SpokenQuestsAudio_csCZ-0.1.0-cast2z3.zip` | 1,2 GB | rozdělené na tři soubory, |
| `SpokenQuestsAudio_csCZ-0.1.0-cast3z3.zip` | 940 MB | protože GitHub pustí nejvýš 2 GiB |
| `SpokenQuestsAudioGossip_csCZ-0.1.0.zip` | 604 MB | rozhovory s NPC — 5 636 nahrávek |
| `SpokenQuestsAudioChatter_csCZ-0.1.0.zip` | 15 MB | co NPC říkají nahlas ve světě — 374 nahrávek |

Datové balíčky jsou na sobě nezávislé: můžeš nainstalovat jen některé. Dohromady je to
**3,2 GB**, protože dabing je dabing.

### Ty tři části questů

Jsou to **tři normální zipy**. Nic se nemusí skládat předem a není potřeba 7-Zip —
rozbal všechny tři do `Interface/AddOns` a potvrď spojení/přepsání složky. Složí se
do jediné složky `SpokenQuestsAudio_csCZ`.

Když některou část nestáhneš, nic se nerozbije: co chybí, se přehraje anglicky.
Část 1 ale stáhnout musíš — jsou v ní tabulky, bez kterých se addon vůbec nenačte.

## Postup

1. Rozbal do `Interface/AddOns`, názvy složek nech, jak jsou — Spoken z nich skládá cesty
   ke zvuku.
2. **Restartuj hru**, ne jen `/reload`: nové zvukové soubory klient načte až při startu.
3. V nastavení Spokenu → **Language**:
   - **Voice Language** → **Čeština**
   - **If a Voice Is Missing** → angličtina
4. `/spokencz` vypíše, co se podařilo napojit.

Replika, kterou balíček nepokrývá, se přehraje anglicky — Spoken se rozhoduje replika po
replice, takže nedodělaný balíček nic nerozbije.

## Co bude česky a co ne

| | |
| --- | --- |
| okno vypravěče — text i hlas | **česky** |
| Azeroth's Compendium, záložka Readables | **česky** (stránky, které balíček má) |
| rozhraní Spokenu (nastavení, tlačítka) | anglicky — záměrně |
| text knihy v herním okně | anglicky — to okno kreslí hra, ne Spoken |
| rozhovory s NPC (gossip) | **česky** (93 % replik) |
| co NPC říkají nahlas (World Chatter) | **česky** (62 % replik) |
| zvýrazňování slov podle hlasu u questů | **ano** (99,8 % nahrávek) |
| Compendium: Quests, Places, Bosses | anglicky — tam český zdroj není |

## Diakritika

Hernímu písmu chybí `ř` a `ě`, takže by český text měl místo nich boxy. `SpokenCzech` proto
dodává Spokenu písmo `FRIZQT__.ttf` z WoWF.cz — vypadá jako herní Friz Quadrata a pokrývá
celou českou abecedu. Dodá ho třemi cestami, které Spoken sám nabízí: registru jazyků
(nabídka), `present.font` na klip (okno vypravěče) a `owner:FontFor` na pohled (Compendium).

## Jak to funguje uvnitř

`SpokenCzech` nesahá na soubory, ale za běhu:

- ohlásí češtinu přes `Spoken:DeclareLanguage` — i s písmem, takže se jazyk objeví v nabídce
  a napíše se správně;
- načte písmo dřív, než o ně Spoken požádá (klient otevře soubor až při prvním použití
  a ten první pokus selže — bez toho by první replika měla místo diakritiky boxy);
- doplní `SpokenReadables:FontFor` — háček, který Spoken volá, ale Readables ho
  neimplementuje (Places ano);
- obalí `SpokenReadables:ClipFor`, aby okno vypravěče dostalo naše písmo;
- obalí `SpokenReadables:PackPageText`, aby Compendium vidělo český text i tehdy, když je
  nainstalovaný anglický balíček;
- obalí `VoiceOver.Player:Prepare` kvůli českému textu questů a rozhovorů a kvůli časování
  slov, které by Spoken jinak u cizojazyčného balíčku zahodil.

Modul je vystavený záměrně: `Spoken_Readables/Core.lua` u něj má komentář
*„Other addons reach the module here."*

## Původ

Český překlad a dabing: **[WoWF.cz](https://wowf.cz)** (`WowfCZ`, autor Fejac).
Addon **[Spoken](https://spoken.quest)**: rusty. Tyhle balíčky obě strany jen propojují.
