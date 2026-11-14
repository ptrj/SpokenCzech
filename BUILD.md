# Čeština pro Spoken — jak se to staví

Tenhle repozitář není jen addon, ale **dílna**. Vyrábí se tu pět addonů, které do
[Spokenu](https://spoken.quest) přinesou český dabing a text
z [WoWF.cz](https://wowf.cz) (`WowfCZ`). Hotové zipy jsou v `dist/`.

Pro hráče je návod v `INSTALL.md`. Tenhle soubor je o tom, **co udělat, až vyjde
nová verze Spokenu nebo WoWF.cz**.

---

## Co se tu vyrábí

| addon | co dělá | zdroj jmen souborů |
| --- | --- | --- |
| `SpokenCzech` | lepidlo — napojí češtinu na Spoken za běhu | — (ruční kód) |
| `SpokenReadablesAudio_csCZ` | knihy, dopisy, cedule | `pageId` ze Spokenu |
| `SpokenQuestsAudio_csCZ` | questy + časování slov | `<questID>-<událost>` |
| `SpokenQuestsAudioGossip_csCZ` | rozhovory s NPC | **hash anglického textu** z anglického balíčku |
| `SpokenQuestsAudioChatter_csCZ` | co NPC říkají nahlas | **jméno** z `FollowupLookup` anglického balíčku |

Poslední sloupec je to důležité. Questy si jméno souboru odvodí samy, takže na Spokenu
nezávisí vůbec. Rozhovory a chatter naopak **přebírají jména od anglických balíčků** — když
je Spoken přegeneruje, naše soubory se přestanou hledat. Právě na to se ptají `check_*`
skripty.

## Co je potřeba

```sh
sudo apt install ffmpeg python3        # v Debian distroboxu
```

Python bez závislostí. Skripty se pouštějí s `-I`, protože čtou rozbalené cizí addony:

```sh
python3 -I build_neco.py
```

Kde máš nainstalovanou hru, řekneš proměnnou `WOW_ADDONS`. Žádný skript ji nepotřebuje —
hledá se v ní jen anglický balíček, když není rozbalený v `_work/spoken/`:

```sh
export WOW_ADDONS="/cesta/k/World of Warcraft/_forever_/Interface/AddOns"
```

## Zdroje

Zipy leží **v kořeni tohohle adresáře** a rozbalují se do `_work/`:

| zip | rozbalit do |
| --- | --- |
| `Spoken-X.Y.Z.zip` | `_work/spoken/` |
| anglické balíčky `SpokenQuestsAudio*`, `SpokenReadablesAudio` | `_work/spoken/` (jen `.lua`) |
| `WowfCZ.zip`, `WowfCZ_Dabing_2..N.zip` | `_work/wowfcz/` |

```sh
unzip -q -o 'Spoken-*.zip' -d _work/spoken
unzip -q -o 'WowfCZ*.zip'  -d _work/wowfcz

# z anglických balíčků stačí vyhledávací tabulky, ne gigabajty zvuku
for z in SpokenQuestsAudio*-*.zip SpokenReadablesAudio-*.zip; do
    unzip -q -o "$z" '*/generated/*.lua' '*/*.lua' '*/*.toc' -d _work/spoken
done
```

**Když `Spoken-*.zip` chybí** (stahuje se z CurseForge zvlášť a v projektu nemusí být),
vezmi jádro rovnou z herního adresáře — je to táž verze, kterou hraješ:

```sh
G="/run/media/games/Wine/World of Warcraft/_forever_/Interface/AddOns"
for a in Spoken Spoken_Quests Spoken_Readables Spoken_Places Spoken_Bosses SpokenContributions; do
    rsync -a --exclude '*.ogg' --exclude '*.mp3' "$G/$a" _work/spoken/
done
```

Z `_work` se čtou **jen datové soubory** (`.lua`). Zvuk se bere přímo ze zipů v kořeni —
fetchery si v nich otevřou jen to, co potřebují, takže se nikam nerozbaluje 5 GB `.ogg`.

Anglické balíčky Spokenu (`SpokenQuestsAudioGossip`, `SpokenQuestsAudio*`) se hledají
nejdřív v `_work/spoken/`, a když tam nejsou, **přímo v herním adresáři AddOns**. Stahují se
zvlášť, takže v zipu Spokenu nebývají.

Nový balíček WoWF.cz (`WowfCZ_Dabing_7` a dál) se najde sám — skripty jdou přes `glob`,
nikde není pevný počet.

**`WowfCZ_Kronika*.zip` se záměrně nečtou.** Je v nich 10 652 nahrávek, ale je to vlastní
pořad WoWF.cz — `<N>-summary`, `l<N>-part<N>`, `c<N>-intro/outro`. Spoken pro ně nemá
protějšek: zná jen stránky podle `pageId`, questy podle `<questID>-<událost>`, rozhovory
podle hashe a hlášky podle broadcast textu. Nahrávky knih (`b<N>-page`) jsou v balíčcích
`Dabing`, ne v Kronice, takže nic nechybí.

---

## Když vyjde nová verze WoWF.cz

Tohle je ten běžný případ: přibyly nahrávky, jména souborů se nemění.

```sh
unzip -q -o 'WowfCZ*.zip' -d _work/wowfcz     # 1. nová data

python3 -I build_readables_cscz.py            # 2. přestavět tabulky
python3 -I build_quests_cscz.py
python3 -I build_gossip_cscz.py
python3 -I build_chatter_cscz.py

python3 -I fetch_readables_audio.py           # 3. doplnit zvuk
python3 -I fetch_quests_audio.py
python3 -I fetch_gossip_audio.py
python3 -I fetch_chatter_audio.py

python3 -I build_timings_cscz.py              # 4. časování AŽ NAKONEC

python3 -I check_readables_cscz.py            # 5. ověřit
python3 -I check_quests_cscz.py
python3 -I check_gossip_cscz.py
python3 -I check_chatter_cscz.py
```

Tři věci, na kterých záleží:

- **`build_timings_cscz.py` jde až po všem ostatním.** Nečte WoWF.cz napřímo, ale porovnává
  časy s titulky, které jsou už v balíčcích. Spuštěný dřív by počítal proti starým titulkům.
- **Fetchery jsou přírůstkové.** Soubor, který už existuje a není prázdný, přeskočí — takže
  druhý běh trvá vteřiny. Hlášení `uz bylo hotovo` je normální.
- **Fetchery nic nemažou.** Když nahrávka ze zdroje zmizí, zůstane v balíčku ležet. Najde ji
  `check_*` jako `soubor bez delky`. Smazat ručně, nebo zahodit celou složku se zvukem
  a nechat ji natéct znovu.

## Když vyjde nová verze Spokenu

```sh
unzip -q -o 'Spoken-*.zip' -d _work/spoken
```

Pak podle toho, co se změnilo:

| co se změnilo | co s tím |
| --- | --- |
| korpus knih (`Spoken_Readables/Data/Books.lua`) | `build_readables_cscz.py` + `fetch_readables_audio.py` |
| anglický balíček rozhovorů (nové hashe) | `build_gossip_cscz.py` + `fetch_gossip_audio.py` |
| `ChatterLines.lua` nebo `followup_lookups.lua` | `build_chatter_cscz.py` + `fetch_chatter_audio.py` |
| jen kód Spokenu | nic přestavovat, ale **zkontrolovat lepidlo** (níž) |

Questů se aktualizace Spokenu netýká: jméno souboru je `<questID>-<událost>` a to si balíček
odvodí sám.

**Jak poznáš, že se jména rozešla.** Spusť `check_gossip_cscz.py` a `check_chatter_cscz.py`
a dívej se na tyhle dva řádky:

```
hashu mimo anglicky balicek:  0
jmen mimo anglicky balicek:   0
```

Nenulové číslo znamená, že balíček nese soubory pod jmény, která Spoken už nehledá — je
potřeba přestavět a dotáhnout zvuk. `soubor bez delky` zase ukazuje osiřelé nahrávky po
jménech, která zmizela.

### Lepidlo je ta křehká část

`SpokenCzech/SpokenCzech.lua` je jediné ruční místo. Sahá Spokenu na vnitřnosti, a i když
jsou to všechno veřejné metody, **nikdo je nedrží zpětně kompatibilní**. Aktualizace Spokenu
žádný náš soubor nepřepíše, ale může některou z nich přejmenovat nebo zrušit.

**Vyžaduje Spoken 3.9.0 nebo novější.** Od té verze má Spoken registr jazyků
(`Spoken/Languages.lua`) a veřejné `Spoken:DeclareLanguage`, takže čeština se jen ohlásí
a o zbytek se postará sám. Na starším Spokenu se lepidlo nenapojí a `/spokencz` to řekne.

Na čem stojí:

| kde | co potřebuje |
| --- | --- |
| `Spoken` | `DeclareLanguage`, `Language` |
| `SpokenReadables` | `ClipFor`, `PackPageText`, `GetVoiceLanguage`, `GetClientLanguage` |
| `VoiceOver` | `Player.Prepare`, `Utils.FillPlayerTokens` |
| pole na klipu | `present.transcript`, `present.font`, `present.timings` |

`Spoken:DeclareLanguage(code, folder, meta)` bere i `font` jako plnou cestu, takže nabídka
jazyků umí napsat **Čeština** správně — `Options:LanguageFace` si ověří, že herní písmo na
název nestačí, a sáhne po tom našem. ASCII náhrada „Cestina" už není potřeba.

Balíček se umí představit i sám: jazyk hlásí v TOC (`X-SpokenQuests-Language`,
`X-SpokenReadables-Language`) a `Languages:Scan` ho při startu přečte.

Lepidlo si samo hlídá, že všechno existuje, než se napojí — chybí-li něco, prostě se
nenapojí a mlčí. **Proto po každé aktualizaci Spokenu ve hře napiš `/spokencz`:**

```
Spoken Czech:
  pismo nacteno:        ano
  jazyk csCZ v nabidce: ano
  knihy a Kompendium:   ano
  questy:               ano
  balicku pro knihy:    2
  knihy hraji v:        csCZ / zaloha enUS
  questy hraji v:       csCZ / zaloha enUS
```

Poslední dva řádky jsou ty, co opravdu něco dokazují. `ano` u háčku znamená jen, že se
podařilo navázat; teprve `csCZ` znamená, že se podle toho i hraje.

## Co se změnilo ve Spokenu 3.9.0

Stojí za zapamatování, protože to zrušilo většinu lepidla:

- **Registr jazyků.** `Spoken/Languages.lua` + `Spoken:DeclareLanguage`. Dřív si každý modul
  držel seznam v **lokální** tabulce `byCode`, ke které se zvenku nedalo dostat, a
  `GetVoiceLanguage` každý neznámý kód zahodil a vrátil jazyk klienta. Stálo nás to půl dne:
  nabídka ukazovala Čeština, ale hrálo se anglicky. Dnes `IsCode` kouká jen na tvar kódu
  (`^%l%l%u%u$`), takže osm přepisů jazykových funkcí šlo zahodit.
- **Kompendium se ptá balíčku dřív.** `UI/Readables.lua` volá
  `PackPageText(pageId, GetClientLanguage())` jako první zdroj. S nainstalovaným anglickým
  balíčkem by tedy dostalo angličtinu. Lepidlo proto obaluje `PackPageText`, ne už
  `ClientPageText`.
- **Jména replik v `followup_lookups.lua` se prořídla** (2.6.0 → 2.7.1). Náš chatter spadl
  ze 472 souborů na 374; 98 nahrávek osiřelo a smazalo se ručně. Přesně na tohle je v
  kontrolách řádek `soubor bez delky`.

Co se nezměnilo: `present.font` / `present.timings` v `Transcript`, háček `owner:FontFor`
v `TextView`, a to, že balíčky nemají jak dodat vlastní titulky — ty pořád vkládá lepidlo
v `Player:Prepare`.

---

## Vydání

```sh
# 1. do hry na zkoušku
G="${WOW_ADDONS:?nastav WOW_ADDONS}"
for p in SpokenCzech SpokenReadablesAudio_csCZ SpokenQuestsAudio_csCZ \
         SpokenQuestsAudioGossip_csCZ SpokenQuestsAudioChatter_csCZ; do
    rsync -a --delete --exclude sounds-to-convert.json "$p/" "$G/$p/"
done

# 2. zipy do dist/release/
python3 -I make_release.py
```

`make_release.py` dělá tři věci, na které se dá zapomenout:

- **ukládá bez komprese** — `.ogg` se zmenšit nedá, takže by komprimování jen žralo čas;
- **vynechá `sounds-to-convert.json`** — je to buildovní manifest, hráč ho nepotřebuje;
- **rozdělí, co je nad limit.** GitHub pustí jako přílohu releasu soubor **do 2 GiB**
  ([dokumentace](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)),
  a questový balíček má 3,1 GiB. Rozdělí se tedy na `-cast1z3`, `-cast2z3`, `-cast3z3`.

Části jsou **obyčejné zipy**, které se rozbalují do stejné složky a v `Interface/AddOns`
se složí dohromady — žádné `.z01`, žádný 7-Zip, žádné skládání předem. TOC a všechny
`.lua` tabulky jsou vždy v části 1, takže částečně stažený balíček se nenačte celý, ale
nenačte se **křivě**: chybějící nahrávka se přehraje anglicky. Velikost částí se dá změnit
(`--part-size 800`); skript sám zkontroluje, že se žádná nad 2 GiB nedostala, a dopíše
`SHA256SUMS.txt`.

### Nahrání na GitHub

`RELEASE.md` je **přímo text popisu releasu**, nic se z něj nemaže:

```sh
cd github
gh release create v0.1.0 ../dist/release/* \
    -R ptrj/SpokenCzech --target main \
    --title "0.1.0 - demo ukazka" --notes-file RELEASE.md --draft
```

- `--draft` nechá release neveřejný, dokud si ho neprohlédneš. Zveřejní se pak
  `gh release edit v0.1.0 -R ptrj/SpokenCzech --draft=false`.
- Když se jeden soubor při nahrávání pretrhne, nemusí se dělat všechno znovu:
  `gh release upload v0.1.0 ../dist/release/<soubor> -R ptrj/SpokenCzech --clobber`.
- `-R` a `--target` jsou potřeba jen tehdy, když adresář není klon toho repozitáře.

Po přidání zvuků je potřeba **úplný restart hry**, ne `/reload`: nové zvukové soubory klient
načte až při startu. Lepidlu samotnému `/reload` stačí.

Čísla verzí jsou na jednom místě v každém builderu (`VERSION = "0.1.0"`); u `SpokenCzech`
v `SpokenCzech.toc`. Nový klient může chtít doplnit `## Interface`.

## Co v repozitáři záměrně není

- **Zvukové balíčky** (`SpokenReadablesAudio_csCZ` a spol., přes 4 GB) ani `dist/`.
  Vyrobí se postupem výš, na GitHub nepatří.
- **Zdrojové zipy** WoWF.cz a Spokenu. Stahují se zvlášť, viz oddíl o zdrojích.
- **Pracovní `_work/`.** Je celé přestavitelné ze zipů.
- `build_locale_cscz.py` — české rozhraní Spokenu (527 řetězců). V dílně existuje,
  ale **záměrně se nepoužívá**: menu má zůstat anglicky.
- `patch_spoken_cscz.py` — původní řešení, které měnilo soubory Spokenu. Nahradilo ho
  lepidlo a do repozitáře se nepřidávalo, aby si ho nikdo omylem nespustil.

## Původ

Český překlad a dabing: **[WoWF.cz](https://wowf.cz)** (`WowfCZ`, autor Fejac).
Addon **[Spoken](https://spoken.quest)**: rusty. Tyhle balíčky obě strany jen propojují.

Celé je to **demo ukázka** — co to znamená, je v `README.md`.
