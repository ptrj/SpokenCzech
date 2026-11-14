local ADDON = ...

-- Lepidlo mezi ceskymi balicky WoWF.cz a addonem Spoken.
--
-- Nemeni ani jeden soubor Spokenu: vsechno dela za behu pres jeho vlastni
-- verejne plochy. Aktualizace Spokenu tedy nic neprepise a tenhle addon jde
-- kdykoli jen vypnout.
--
-- Vyzaduje Spoken 3.9.0 nebo novejsi. Od te verze ma Spoken registr jazyku
-- (Spoken/Languages.lua) a s nim i Spoken:DeclareLanguage, takze cestinu uz
-- neni potreba nikam propasovavat. Pred 3.9.0 si kazdy modul drzel seznam
-- jazyku v lokalni tabulce byCode, ke ktere se zvenci nedalo dostat, a
-- GetVoiceLanguage kazdy neznamy kod zahodil -- to uz neplati, IsCode se ted
-- diva jen na tvar kodu.
--
-- Co zbyva resit:
--   1. Pismo. Hernimu pismu chybi "r" a "e" s hackem. Registr si font vezme
--      z DeclareLanguage a nabidka jazyku ho pouzije sama (Options:LanguageFace),
--      ale okno vypravece a Kompendium se na nej ptaji jinudy -- pres clip
--      (present.font) a pres owner:FontFor.
--   2. Kompendium se stranky pta v jazyce KLIENTA, takze s nainstalovanym
--      anglickym balickem dostane anglicky text, i kdyz hrac posloucha cesky.
--   3. Quest si text bere z herni API, ktera na anglickem klientu zadny cesky
--      nema. Cesky balicek ho nese sam v CaptionByFileName.
--   4. Casovani slov: DataModules ho nasadi jen kdyz je jazyk balicku zaroven
--      jazykem klienta, takze cesky balicek by o ne vzdycky prisel.

local CODE = "csCZ"
local FONT = [[Interface\AddOns\]] .. ADDON .. [[\Fonts\FRIZQT__.ttf]]

--------------------------------------------------------------------------------
-- 0. Nacteni pisma
--------------------------------------------------------------------------------

-- Klient cte soubor pisma az ve chvili, kdy ho nekdo poprve nasadi, a ten uplne
-- prvni SetFont jeste selze. Spoken s tim pocita a sahne po hernim pismu
-- (Transcript:ApplyFont, vetev "A face the client cannot load") a vysledek si
-- zapamatuje. Prvni replika tak mela boxy a az dalsi vysla spravne. Nacteme si
-- pismo sami driv, nez o nej kdokoli pozada, a odkaz drzime, aby ho klient
-- nezahodil.
local warm

local function WarmFont()
    if not warm then
        warm = CreateFrame("Frame")
        warm:Hide()
        warm.text = warm:CreateFontString(nil, "BACKGROUND")
    end
    -- Dvakrat zamerne: prvni pokus soubor teprve otevre, druhy uz ho dostane.
    for _ = 1, 2 do
        if warm.text:SetFont(FONT, 12, "") ~= false and warm.text:GetFont() then
            warm.text:SetText("ěščřžýáíé ĚŠČŘŽÝÁÍÉ")
            return true
        end
    end
    return false
end

--------------------------------------------------------------------------------
-- 1. Jazyk
--------------------------------------------------------------------------------

-- Registr si jazyk drzi i s pismem, takze nabidka umi napsat "Čeština" spravne
-- (Options:LanguageFace vyzkousi pismo balicku, kdyz herni na nazev nestaci).
local function DeclareLanguage()
    if not (Spoken and Spoken.DeclareLanguage) then return false end
    Spoken:DeclareLanguage(CODE, ADDON, {
        name = "Czech",
        native = "Čeština",
        font = FONT,
    })
    return Spoken.Language and Spoken:Language(CODE) ~= nil
end

--------------------------------------------------------------------------------
-- 2. Knihy, cedule a Kompendium
--------------------------------------------------------------------------------

local function HookReadables()
    -- Spoken_Readables/Core.lua vystavuje modul zamerne: "Other addons reach
    -- the module here."
    local R = _G.SpokenReadables
    if type(R) ~= "table" or R.__spokenCzech then return false end
    -- Hotovo hlasime az kdyz je napojene vsechno, co potrebujeme; jinak to
    -- zkusime znovu pri dalsi udalosti (moduly se nacitaji v nejistem poradi).
    if not (R.ClipFor and R.PackPageText and R.GetVoiceLanguage and R.GetClientLanguage) then
        return false
    end
    R.__spokenCzech = true

    -- Pismo pro pohledy, ktere se na nej ptaji ownera (Spoken/UI/TextView.lua,
    -- funkce FontFile) -- Kompendium vcetne nadpisu stranky. Implementuje to
    -- jinak jen Spoken Places.
    if not R.FontFor then
        function R:FontFor(fontObject)
            if self:GetVoiceLanguage() == CODE then return FONT end
            return fontObject and fontObject.GetFont and fontObject:GetFont()
        end
    end

    -- Pismo pro titulky v okne vypravece. Clip uz vi, v jakem jazyce hraje.
    local clipFor = R.ClipFor
    function R:ClipFor(pageId)
        local clip = clipFor(self, pageId)
        if clip and clip.present and clip.language == CODE then
            clip.present.font = FONT
        end
        return clip
    end

    -- Kompendium (Spoken_Readables/UI/Readables.lua) si rika o stranku v jazyce
    -- klienta, takze s nainstalovanym anglickym balickem dostane anglicky text
    -- driv, nez se vubec dojde k dalsimu zdroji.
    --
    -- Pro titulky je to bezpecne: CaptionText dava cestinu na prvni misto samo
    -- (IsClientLanguage(csCZ) je false, zadny klient cesky nebezi), takze na
    -- jazyk klienta dojde teprve tehdy, kdyz cesky text neni -- a tehdy ho
    -- nenajde ani tenhle doplnek.
    local packText = R.PackPageText
    function R:PackPageText(pageId, language)
        if language ~= CODE and self:GetVoiceLanguage() == CODE
                and language == self:GetClientLanguage() then
            local czech = packText(self, pageId, CODE)
            if czech and czech ~= "" then return czech end
        end
        return packText(self, pageId, language)
    end
    return true
end

--------------------------------------------------------------------------------
-- 3. Questy, rozhovory a hlasky NPC
--------------------------------------------------------------------------------

local function HookQuests()
    local V = _G.VoiceOver
    if type(V) ~= "table" or V.__spokenCzech then return false end
    if not (V.Player and V.Player.Prepare) then return false end
    V.__spokenCzech = true

    -- Prepare bezi az po PrepareSound, takze soundData.module i fileName jsou
    -- vyplnene.
    local prepare = V.Player.Prepare
    function V.Player:Prepare(soundData)
        local result = prepare(self, soundData)
        local module = soundData and soundData.module
        local captions = module and module.CaptionByFileName
        local caption = captions and soundData.fileName and captions[soundData.fileName]
        if caption and caption ~= "" and soundData.present then
            -- Par replik nese tokeny serveru ($N, $G muz:zena;, $B), protoze
            -- jejich text pochazi ze stranky, ne z nahravky. Spoken je sam
            -- nerozbaluje -- v jeho vlastnim textu uz rozbalene jsou.
            if V.Utils and V.Utils.FillPlayerTokens and caption:find("%$") then
                caption = V.Utils:FillPlayerTokens(caption)
            end
            soundData.present.transcript = caption
            soundData.present.font = module.Font or FONT
            local times = module.WordTimesByFileName
            local at = times and times[soundData.fileName]
            if at then soundData.present.timings = at end
        end
        return result
    end
    return true
end

--------------------------------------------------------------------------------
-- Spusteni
--------------------------------------------------------------------------------

-- Moduly Spokenu se nacitaji v poradi, ktere neurcujeme, a Quests sve balicky
-- dopocitava az po prihlaseni. Zkousime proto dokud to nesedne, ne jen jednou.
local done = { font = false, language = false, readables = false, quests = false }

local function Apply()
    if not done.font then done.font = WarmFont() end
    if not done.language then done.language = DeclareLanguage() end
    if not done.readables then done.readables = HookReadables() end
    if not done.quests then done.quests = HookQuests() end
    return done.font and done.language and done.readables and done.quests
end

Apply()

local frame = CreateFrame("Frame")
frame:RegisterEvent("ADDON_LOADED")
frame:RegisterEvent("PLAYER_LOGIN")
frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:SetScript("OnEvent", function(self, event)
    if Apply() and event ~= "ADDON_LOADED" then
        self:UnregisterAllEvents()
    end
end)

-- /spokencz -- co se povedlo napojit
SLASH_SPOKENCZECH1 = "/spokencz"
SlashCmdList.SPOKENCZECH = function()
    local function state(value) return value and "ano" or "NE" end
    print("|cffb48cffSpoken|r Czech:")
    if not (Spoken and Spoken.DeclareLanguage) then
        print("  |cffff5555Spoken je starsi nez 3.9.0 -- tenhle addon ho nepodpori.|r")
    end
    print("  pismo nacteno:        " .. state(done.font))
    print("  jazyk csCZ v registru:" .. state(done.language))
    print("  knihy a Kompendium:   " .. state(done.readables))
    print("  questy a rozhovory:   " .. state(done.quests))
    -- Napojeni samo o sobe nic nedokazuje: rozhoduje jazyk, na kterem se
    -- moduly nakonec shodnou.
    local R = _G.SpokenReadables
    if R and R.GetVoiceLanguage then
        print("  knihy hraji v:        " .. tostring(R:GetVoiceLanguage())
            .. " / zaloha " .. tostring(R:GetFallbackLanguage()))
    end
    local V = _G.VoiceOver
    if V and V.Language and V.Language.GetVoiceLanguage then
        print("  questy hraji v:       " .. tostring(V.Language:GetVoiceLanguage())
            .. " / zaloha " .. tostring(V.Language:GetFallbackLanguage()))
    end
end
