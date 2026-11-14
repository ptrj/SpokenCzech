# Čeština pro Spoken

> ## ⚠️ Toto je DEMO UKÁZKA
>
> Jde o **demo ukázku**, nikoli hotový a odladěný addon. Vznikla proto, aby se dalo
> na vlastní oči a vlastní uši vyzkoušet, **jak by český dabing z WoWF.cz zněl
> uvnitř Spokenu** — a aby bylo o čem se v komunitě bavit.
>
> Co to znamená v praxi:
>
> - není to otestované na všem, co hra nabízí — testovalo se hlavně na začátečních
>   oblastech a na knihách;
> - některé repliky zůstanou anglicky, protože k nim český dabing není (viz tabulka níž);
> - čísla verzí jsou `0.1.0` a vůbec nic nezaručují;
> - **nic z toho není oficiální** — není to vydání Spokenu ani vydání WoWF.cz.
>
> Zpětná vazba, nálezy a nápady jsou vítané. Když se ukáže, že to komunita chce,
> dá se z demo ukázky udělat něco udržovaného.

Dva projekty, které se nikdy nepotkaly:

- **[Spoken](https://spoken.quest)** — addon, který ve World of Warcraft přečte nahlas
  questy, knihy a rozhovory s NPC. Dodává k tomu vlastní anglický dabing.
- **[WoWF.cz](https://wowf.cz)** — český překlad a kompletní český dabing WoW,
  roky práce českých fanoušků.

Tenhle repozitář je **spojka** mezi nimi. Vezme český zvuk a český text z addonu
`WowfCZ` a naskládá ho do formátu, který Spoken umí přehrát. Výsledek: Spokenovo
okno vypravěče běží česky, českým hlasem.

---

## Co je v repozitáři

| | |
| --- | --- |
| `SpokenCzech/` | samotný addon — 219 řádků Lua, které češtinu napojí na Spoken |
| `build_*.py`, `fetch_*.py` | z balíčků WoWF.cz vyrobí datové addony se zvukem |
| `check_*.py` | ověří, že jména souborů a tabulky souhlasí se Spokenem |
| `make_release.py` | zabalí hotové balíčky do zipů pro Releases (včetně dělení) |
| [`INSTALL.md`](INSTALL.md) | návod pro hráče |
| [`BUILD.md`](BUILD.md) | návod pro toho, kdo to bude stavět a udržovat |
| [`RELEASE.md`](RELEASE.md) | text pro popis releasu |

**Zvukové balíčky nejsou ve zdrojácích, ale v [Releases](../../releases)** — 3,2 GB zvuku
do gitu nepatří. Questový balíček je tam rozdělený na tři zipy, protože GitHub pustí jako
přílohu nejvýš 2 GiB na soubor; rozbalují se do stejné složky a žádné skládání předem
nepotřebují. Postavit se dají i znovu ze zdrojů WoWF.cz — postup je v [`BUILD.md`](BUILD.md).

## Co umí

| | |
| --- | --- |
| okno vypravěče — text i hlas | **česky** |
| questy | **česky** — 21 119 nahrávek |
| knihy, dopisy, cedule | **česky** — 997 stránek |
| rozhovory s NPC (gossip) | **česky** — 93 % replik |
| co NPC říkají nahlas ve světě | **česky** — 62 % replik |
| zvýrazňování slov podle hlasu | **ano** — 99,8 % questových nahrávek |
| Compendium: Quests, Places, Bosses | anglicky — český zdroj neexistuje |
| rozhraní Spokenu (nastavení) | anglicky — **záměrně** |

Co česky není, se přehraje anglicky. Spoken se rozhoduje replika po replice, takže
nedodělaný balíček nic nerozbije.

## Jak to nesahá na Spoken

**Žádný soubor Spokenu se nemění.** To je hlavní pravidlo celého projektu.

`SpokenCzech` se napojuje až za běhu, a jen přes plochy, které Spoken sám nabízí
veřejně — `Spoken:DeclareLanguage`, `SpokenReadables`, `VoiceOver.Player`.
Důsledky:

- aktualizace Spokenu nic nepřepíše a nic nerozbije;
- vypnutím `SpokenCzech` se Spoken vrátí k angličtině, jako by tu čeština nikdy nebyla;
- nehrozí, že by si někdo omylem rozbil funkční instalaci Spokenu.

Potřebuje **Spoken 3.9.0 nebo novější**. Na starším se nic nerozbije, jen se čeština
nenapojí — příkaz `/spokencz` to napíše.

## Jak to zkusit

Krátce: rozbalit do `Interface/AddOns`, **restartovat hru** (ne `/reload`), v nastavení
Spokenu přepnout **Voice Language → Čeština**, `/spokencz` ověří stav.
Celý návod je v [`INSTALL.md`](INSTALL.md).

## Původ a práva

- **Český překlad a dabing: [WoWF.cz](https://wowf.cz)** (addon `WowfCZ`, autor Fejac).
  Nahrávky a texty jsou jejich práce a jejich majetek. Tenhle repozitář je nevydává,
  jen popisuje, jak je přeskládat.
- **Addon [Spoken](https://spoken.quest)**: rusty. Jeho kód tu není a nijak se nemění.
- Písmo `FRIZQT__.ttf` v `SpokenCzech/Fonts/` pochází z balíčku WoWF.cz. Je potřeba
  proto, že hernímu písmu chybí `ř` a `ě` — bez něj by byl na jejich místě box.
- Kód spojky (`SpokenCzech.lua` a skripty v `tools/`) si může kdokoli vzít a použít.

Žádná ze stran o tomhle demu nerozhodovala. Pokud by si kterákoli z nich nepřála, aby
takhle vznikalo a šířilo se, stačí ozvat se — zmizí to.
