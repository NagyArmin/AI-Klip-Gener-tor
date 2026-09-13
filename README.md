# 🎬 Profi AI Klip Generátor (TikTok / Shorts / Reels)

Egy teljesen automatizált, Python-alapú videóvágó és tartalomgyártó rendszer. A projekt mesterséges intelligencia (Gemini AI, Whisper) és az FFmpeg segítségével készít hosszú YouTube videókból rövid, figyelemfelkeltő, 9:16-os formátumú klipeket.

A rendszer két fő modullal rendelkezik, amelyek a tartalom típusához (beszéd vagy akció) optimalizálva működnek.

## 🚀 Fő funkciók

### 1. Szövegközpontú modul (`klip_keszito.py`)
Ideális podcastokhoz, tech tesztekhez és beszélgetős videókhoz.
* **Intelligens keresés:** A Gemini AI átnézi a videó átiratát, és megkeresi a legütősebb, önmagukban is megálló gondolatmeneteket.
* **Dinamikus fókusz:** A felhasználó futás közben megadhat egyedi instrukciókat az AI-nak.
* **Automatikus feliratozás:** A Whisper modell generálja a szöveget, amit a rendszer dinamikus, piros kiemelésű feliratként éget a videóra.
* **Gyorsított vágás:** Optimalizált FFmpeg ("fast seek" módszer) biztosítja, hogy a többórás videókból is másodpercek alatt megtörténjen a vágás.

### 2. Akció és Vizuális modul (`vizualis_klip.py`)
Ideális sportösszefoglalókhoz, játékmenetekhez, stream részletekhez.
* **Copyright védelem:** A rendszer a 9:16-os konverzió során levágja az eredeti videó felső 15%-át (ahol az eredményjelzők és TV logók találhatók), így "szélesvásznú" hatást kelt.
* **Háttér kitöltés:** Az üresen maradó alsó és felső részeket az eredeti videó elhomályosított (blur) verziójával tölti ki.
* **Precíz vágás és Némítás:** Tizedmásodperc pontos vágás a kulcsjeleneteknél. Az eredeti hangsávot automatikusan eltávolítja (`-an`), így a CapCutban azonnal alá lehet tenni a felkapott zenéket.

## 🛠️ Architektúra és Fájlszerkezet

* `indito.py` - A fő vezérlőpult (Master Script). Egy CLI menüből teszi lehetővé a modulok indítását, bekéri az útvonalakat és az AI instrukciókat, majd paraméterként (`sys.argv`) továbbítja a feldolgozó scripteknek.
* `klip_keszito.py` - A szöveges videók feldolgozásáért felelős modul.
* `vizualis_klip.py` - A sport és akció videók feldolgozásáért felelős modul.

## 💻 Követelmények (Prerequisites)

A projekt futtatásához az alábbiak szükségesek:
* **Python 3.8+**
* **FFmpeg** (Telepítve és a rendszer PATH változójához adva)
* **API Kulcsok:** 
  * Google Gemini API kulcs (Környezeti változóként beállítva: `GEMINI_API_KEY`)

## 🛠️ Részletes Telepítési és Beállítási Útmutató (Windows)

### 1. Python telepítése
1. Töltsd le a [Python hivatalos oldaláról](https://www.python.org/downloads/) a legújabb verziót.
2. **Kritikus lépés:** A telepítő elindításakor, még az *Install Now* gomb megnyomása előtt, mindenképpen pipáld be az ablak alján az **"Add Python to PATH"** (vagy *Add python.exe to PATH*) opciót!

### 2. FFmpeg letöltése és beállítása
Mivel a rendszer az FFmpeg motort használja a gyorsított videóvágáshoz, ezt külön fel kell telepíteni a rendszerre.
1. Töltsd le az FFmpeg Windows verzióját (ajánlott: [gyan.dev FFmpeg git full kiadás] (https://www.gyan.dev/ffmpeg/builds/)).
2. Csomagold ki a letöltött ZIP fájl tartalmát egy végleges, biztonságos helyre a gépeden (például: `C:\FFmpeg\`).
3. Nyisd meg a Windows Start menüt, és keress rá erre: **"Környezeti változók szerkesztése"** (Edit the system environment variables).
4. A felugró ablakban kattints a **Környezeti változók...** gombra az alján.
5. Az alsó (*Rendszerváltozók*) listában keresd meg a **Path** nevű sort, jelöld ki, és kattints a **Szerkesztés** gombra.
6. Kattints az **Új** gombra, és illeszd be az FFmpeg `bin` mappájának pontos útvonalát (pl. `C:\FFmpeg\bin`).
7. Nyomj OK-t minden nyitott ablakon a mentéshez.

### 3. Szükséges Python könyvtárak telepítése
Nyiss egy Parancssort (CMD) vagy PowerShellt a projekt mappájában, és futtasd le az alábbi parancsot, ami letölti a Google AI és a Whisper csomagokat:

pip install google-generativeai openai-whisper


4. Az AI Agyának Bekötése (Gemini API Kulcs)
Ahhoz, hogy a script ne csak vakon vagdalkozzon, hanem profi vágóként ténylegesen értse is a videó tartalmát, be kell röffentenünk a Gemini nyelvi modellt. Ez adja a rendszer intelligenciáját.

1. **Szerezd meg a kulcsot:** Kérj egy ingyenes API tokent a [Google AI Studio](https://aistudio.google.com/) felületén. Ez lesz a VIP belépőd a modellhez.
2. Hívd elő a Windows **Környezeti változók** (Environment Variables) menüjét.
3. A felső (Felhasználói változók) blokkban csapj rá az **Új...** gombra.
4. **Változó neve:** Itt nincs apelláta, a kód szigorúan ezt keresi: `GEMINI_API_KEY`
5. **Változó értéke:** Dobd be azt a brutál hosszú karaktersort, amit a Google generált neked. (Ez a privát hozzáférésed, kezeld jelszóként!)
6. Nyomj OK-t mindenhol, hogy a Windows kőbe vésse a változást.

**⚠️Pro Tipp:** Ha a terminálod (CMD/PowerShell) vagy a kódszerkesztőd nyitva volt a beállítás közben, lődd ki és nyisd újra! A gépnek kell egy újraindított ablak ahhoz, hogy érzékelje az új szuperképességet és rá tudjon csatlakozni a Google szervereire.


5. Rendszer indítása (Használat)
Minden készen áll. Nyiss egy új terminált a mappában, és indítsd el a mester scriptet:

python indito.py

