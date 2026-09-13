"""
AI Klip Készítő
================
Bemenet: egy hosszú videó (amit te már letöltöttél)
Kimenet: több, 9:16 arányú, beégetett feliratos highlight klip

Telepítendő csomagok:
    pip install faster-whisper anthropic

FFmpeg:
    Telepítve kell legyen és elérhetőnek kell lennie a PATH-ban.
    (https://www.gyan.dev/ffmpeg/builds/ -> "essentials" build, majd a bin
    mappát add hozzá a rendszer PATH-jához)

API kulcs:
    Állítsd be környezeti változóként:
        setx ANTHROPIC_API_KEY "sk-ant-..."
    (Ezután indíts új terminált, hogy érvénybe lépjen.)

Használat:
    python klip_keszito.py "videok/valami.mp4"
"""

import sys
import os
import json
import subprocess
import textwrap
from pathlib import Path

from faster_whisper import WhisperModel
from google import genai
from google.genai import types

# ---------------------------------------------------------------------------
# BEÁLLÍTÁSOK
# ---------------------------------------------------------------------------

WHISPER_MODEL_MERET = "medium"     # tiny / base / small / medium / large-v3
WHISPER_NYELV = None                 # pl. "hu" vagy "en", None = auto-detektál

GEMINI_MODEL = "gemini-3.6-flash"  # Gyors és költséghatékony modell

MIN_KLIP_HOSSZ = 15                  # másodperc
MAX_KLIP_HOSSZ = 90                  # másodperc

# Fix szószám helyett maximális karakterhossz a dinamikus tördeléshez
MAX_KARAKTER_SORONKENT = 25          

FUGGOLEGES_SZELESSEG = 1080
FUGGOLEGES_MAGASSAG = 1920


# ---------------------------------------------------------------------------
# 1. LÉPÉS - ÁTIRAT KÉSZÍTÉSE (szó szintű időbélyegekkel és százalékkal)
# ---------------------------------------------------------------------------

def atirat_keszitese(video_path):
    print("Átirat készítése (Whisper)...")
    model = WhisperModel(WHISPER_MODEL_MERET, device="auto", compute_type="auto")

    segments, info = model.transcribe(
        video_path,
        language=WHISPER_NYELV,
        word_timestamps=True,
        vad_filter=True,
    )

    szavak = []       
    mondatok = []      
    teljes_hossz = info.duration

    print(f"Detektált nyelv: {info.language} | Videó hossza: {teljes_hossz:.1f} mp")
    print("Feldolgozás: 0%", end="", flush=True)

    for seg in segments:
        mondatok.append({
            "start": round(seg.start, 2),
            "end": round(seg.end, 2),
            "text": seg.text.strip(),
        })
        if seg.words:
            for w in seg.words:
                szavak.append({
                    "start": round(w.start, 2),
                    "end": round(w.end, 2),
                    "word": w.word.strip(),
                })
        
        # Százalék kiszámítása és kiírása ugyanarra a sorra
        szazalek = min(100, int((seg.end / teljes_hossz) * 100))
        print(f"\rFeldolgozás: {szazalek}%", end="", flush=True)

    print(f"\nÁtirat kész. ({len(mondatok)} mondat, {len(szavak)} szó)")
    return mondatok, szavak

# ---------------------------------------------------------------------------
# 2. LÉPÉS - HIGHLIGHT SZAKASZOK KIVÁLASZTÁSA GEMINI-VEL
# ---------------------------------------------------------------------------

def highlightok_keresese(mondatok, extra_instrukcio=""):
    print("Highlight szakaszok keresése (Gemini)...")

    atirat_szoveg = "\n".join(
        f"[{m['start']:.1f}-{m['end']:.1f}] {m['text']}" for m in mondatok
    )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("HIBA: Nincs beállítva a GEMINI_API_KEY környezeti változó!")
        return []

    client = genai.Client(api_key=api_key)

    rendszerutasitas = f"""Egy videó időbélyegzett átiratát kapod.
Feladatod: találd meg az ÖSSZES olyan szakaszt, ami önmagában is jó, érdekes,
figyelemfelkeltő rövid klip (TikTok/Reels/Shorts stílusban) lehetne.

Szempontok:
- A klip {MIN_KLIP_HOSSZ}-{MAX_KLIP_HOSSZ} másodperc hosszú legyen.
- Erős, figyelemfelkeltő mondattal / gondolattal induljon (hook).
- Önmagában is érthető legyen, ne kezdődjön/végződjön félmondat közepén.
- Ne legyen két klip között jelentős átfedés.
- Csak azokat add meg, amik tényleg megállnák a helyüket önálló klipként -
  ha egy videóban kevés ilyen van, kevesebbet adj vissza, ha sok, többet.

Válaszolj KIZÁRÓLAG egy JSON tömbbel! A JSON felépítése pontosan ilyen legyen:
[
  {{"start": 12.3, "end": 45.6, "cim": "Rövid cím", "indoklas": "Indok", "kulcsszavak": ["Gaming", "Laptop", "Performance"]}}
]
    """

    # ÚJ RÉSZ: Hozzáadjuk a felhasználó kérését, ha írt be valamit
    if extra_instrukcio.strip():
        rendszerutasitas += f"\n\n[KÜLÖNLEGES FELHASZNÁLÓI UTASÍTÁS - EZ FELÜLÍR MINDEN MÁST]: {extra_instrukcio}"
        rendszerutasitas += "\nFIGYELEM: Szigorúan kövesd a fenti felhasználói utasítást! Ha a felhasználó konkrét témát jelöl meg, csak arról keress! HA A FELHASZNÁLÓ KONKRÉT DARABSZÁMOT KÉR (pl. csak 1 klipet), AKKOR PONTOSAN ANNYIT ADJ VISSZA, kiválasztva a legeslegjobbat! Ne generálj többet a kértnél!"

    print("Átirat elküldése a modellnek...")
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=atirat_szoveg,
            config=types.GenerateContentConfig(
                system_instruction=rendszerutasitas,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        nyers_valasz = response.text.strip()
    except Exception as e:
        print(f"HIBA a Gemini API hívásakor: {e}")
        return []

    try:
        highlightok = json.loads(nyers_valasz)
    except json.JSONDecodeError:
        print("HIBA: A Gemini válasza nem volt érvényes JSON. Nyers válasz:")
        print(nyers_valasz)
        return []

    print(f"{len(highlightok)} highlight szakasz található.")
    return highlightok

# ---------------------------------------------------------------------------
# 3. LÉPÉS - SRT FELIRAT GENERÁLÁSA EGY ADOTT SZAKASZHOZ
# ---------------------------------------------------------------------------

def srt_ido_formatum(masodperc):
    ora = int(masodperc // 3600)
    perc = int((masodperc % 3600) // 60)
    mp = int(masodperc % 60)
    ezred = int(round((masodperc - int(masodperc)) * 1000))
    return f"{ora:02d}:{perc:02d}:{mp:02d},{ezred:03d}"

def srt_generalas(szavak, klip_start, klip_end, kimeneti_fajl, kulcsszavak):
    klip_szavak = [w for w in szavak if w["start"] >= klip_start and w["end"] <= klip_end]
    if not klip_szavak:
        return False

    # Kulcsszavak kisbetűsítve a pontos egyezéshez
    kulcsszavak_lower = [k.lower() for k in (kulcsszavak or [])]
    KIEMELO_SZIN = "#FF0000" # Itt állíthatod a kiemelés színét (Hex kód)

    sorok = []
    idx = 1
    jelenlegi_csoport = []
    jelenlegi_hossz = 0

    for w in klip_szavak:
        eredeti_szo = w["word"]
        # Írásjelek levágása a vizsgálathoz
        tiszta_szo = eredeti_szo.strip(".,?!\"'()").lower()
        
        formazott_szo = eredeti_szo
        if tiszta_szo in kulcsszavak_lower:
            formazott_szo = f'<font color="{KIEMELO_SZIN}">{eredeti_szo}</font>'

        # A tördelésnél az eredeti szó hosszát számoljuk, nem a HTML tagekkel növelt hosszt
        if jelenlegi_csoport and jelenlegi_hossz + len(eredeti_szo) + 1 > MAX_KARAKTER_SORONKENT:
            sor_start = jelenlegi_csoport[0]["start"] - klip_start
            sor_end = jelenlegi_csoport[-1]["end"] - klip_start
            szoveg = " ".join(cw["formazott"] for cw in jelenlegi_csoport)

            sorok.append(f"{idx}")
            sorok.append(f"{srt_ido_formatum(sor_start)} --> {srt_ido_formatum(sor_end)}")
            sorok.append(szoveg)
            sorok.append("")
            idx += 1

            jelenlegi_csoport = [{"start": w["start"], "end": w["end"], "formazott": formazott_szo}]
            jelenlegi_hossz = len(eredeti_szo)
        else:
            jelenlegi_csoport.append({"start": w["start"], "end": w["end"], "formazott": formazott_szo})
            jelenlegi_hossz += len(eredeti_szo) + (1 if len(jelenlegi_csoport) > 1 else 0)

    if jelenlegi_csoport:
        sor_start = jelenlegi_csoport[0]["start"] - klip_start
        sor_end = jelenlegi_csoport[-1]["end"] - klip_start
        szoveg = " ".join(cw["formazott"] for cw in jelenlegi_csoport)

        sorok.append(f"{idx}")
        sorok.append(f"{srt_ido_formatum(sor_start)} --> {srt_ido_formatum(sor_end)}")
        sorok.append(szoveg)
        sorok.append("")

    with open(kimeneti_fajl, "w", encoding="utf-8") as f:
        f.write("\n".join(sorok))

    return True


# ---------------------------------------------------------------------------
# 4. LÉPÉS - KLIP KIVÁGÁSA, FÜGGŐLEGESRE VÁGÁS, FELIRAT BEÉGETÉSE
# ---------------------------------------------------------------------------

def biztonsagos_fajlnev(szoveg):
    tiltott = '<>:"/\\|?*'
    for ch in tiltott:
        szoveg = szoveg.replace(ch, "")
    return szoveg.strip()[:60]


def klip_letrehozasa(video_path, highlight, szavak, kimeneti_mappa, sorszam):
    start = float(highlight["start"])
    end = float(highlight["end"])
    cim = highlight.get("cim", f"klip_{sorszam}")
    kulcsszavak = highlight.get("kulcsszavak", []) # Kinyerjük a kulcsszavakat

    fajlnev = biztonsagos_fajlnev(f"{sorszam:02d}_{cim}")
    ideiglenes_srt = Path(kimeneti_mappa) / f"_tmp_{sorszam}.srt"
    kimeneti_video = Path(kimeneti_mappa) / f"{fajlnev}.mp4"

    # Átadjuk a listát a generálónak
    van_felirat = srt_generalas(szavak, start, end, ideiglenes_srt, kulcsszavak)
    # ... (a kód többi része változatlan marad)

    # Középre vágás 9:16 arányra, majd skálázás. A subtitles filternek
    # a windows-os elérési útban a backslash-eket escape-elni kell.
    srt_path_ffmpeg = str(ideiglenes_srt).replace("\\", "/").replace(":", "\\:")

    crop_scale = (
        f"crop='if(gt(iw/ih,{FUGGOLEGES_SZELESSEG}/{FUGGOLEGES_MAGASSAG}),"
        f"ih*{FUGGOLEGES_SZELESSEG}/{FUGGOLEGES_MAGASSAG},iw)':"
        f"'if(gt(iw/ih,{FUGGOLEGES_SZELESSEG}/{FUGGOLEGES_MAGASSAG}),ih,"
        f"iw*{FUGGOLEGES_MAGASSAG}/{FUGGOLEGES_SZELESSEG})',"
        f"scale={FUGGOLEGES_SZELESSEG}:{FUGGOLEGES_MAGASSAG}"
    )

    if van_felirat:
        felirat_stilus = (
            "FontName=Arial,FontSize=16,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=1,Outline=2,"
            "Alignment=2,MarginV=80,Bold=1"
        )
        vf = f"{crop_scale},subtitles='{srt_path_ffmpeg}':force_style='{felirat_stilus}'"
    else:
        vf = crop_scale

    # Kiszámoljuk, hány másodperces lesz a klip
    hossz = float(end) - float(start)

    parancs = [
        "ffmpeg", "-y",
        "-ss", str(start),      # Gyors beugrás a kezdőponthoz
        "-i", str(video_path),  # A videófájl beolvasása
        "-t", str(hossz),       # A kivágandó klip hossza
        "-vf", vf,              # Itt marad a te feliratos filtered!
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "128k",
        str(kimeneti_video),
    ]

    print(f"\nKlip #{sorszam}: {cim} ({start:.1f}s - {end:.1f}s)")
    eredmeny = subprocess.run(parancs, capture_output=True, text=True)

    if ideiglenes_srt.exists():
        os.remove(ideiglenes_srt)

    if eredmeny.returncode != 0:
        print(f"HIBA a(z) {sorszam}. klip elkészítésekor:")
        print(eredmeny.stderr[-1500:])
        return None

    print(f"  -> Kész: {kimeneti_video}")
    return kimeneti_video


# ---------------------------------------------------------------------------
# FŐ FOLYAMAT
# ---------------------------------------------------------------------------

def main():
    # 1. Ellenőrizzük, hogy megkaptuk-e a videót az indito.py-től
    if len(sys.argv) < 2:
        print("Használat: python klip_keszito.py <videó_elérési_útja> [extra_utasítás]")
        sys.exit(1)

    video_path = sys.argv[1]

    # 2. Ellenőrizzük, hogy kaptunk-e extra utasítást (3. argumentum)
    if len(sys.argv) > 2:
        extra_instrukcio = sys.argv[2]
    else:
        extra_instrukcio = ""

    # 3. Fájl létezésének ellenőrzése
    if not os.path.exists(video_path):
        print(f"A megadott videó nem található: {video_path}")
        sys.exit(1)

    kimeneti_mappa = Path(video_path).parent / "klipek"
    kimeneti_mappa.mkdir(exist_ok=True)

    mondatok, szavak = atirat_keszitese(video_path)
    if not mondatok:
        print("Nem sikerült átiratot készíteni, kilépés.")
        sys.exit(1)

    highlightok = highlightok_keresese(mondatok)
    if not highlightok:
        print("Nem talált a modell highlight szakaszt, kilépés.")
        sys.exit(1)

    keszult_klipek = []
    for i, h in enumerate(highlightok, start=1):
        eredmeny = klip_letrehozasa(video_path, h, szavak, kimeneti_mappa, i)
        if eredmeny:
            keszult_klipek.append(eredmeny)

    print(f"\nKész! {len(keszult_klipek)} klip elkészült ide: {kimeneti_mappa}")

    # --- ÖSSZEFOGLALÓ STATISZTIKA ---
    mp4_fajlok = list(kimeneti_mappa.glob("*.mp4"))
    darabszam = len(mp4_fajlok)
    ossz_meret_byte = sum(f.stat().st_size for f in mp4_fajlok)
    ossz_meret_mb = ossz_meret_byte / (1024 * 1024)

    print("\n" + "═"*50)
    print("📊 FELDOLGOZÁSI ÖSSZEFOGLALÓ")
    print("═"*50)
    print(f"🎬 Elkészült klipek: {darabszam} db")
    print(f"💾 Összes foglalt hely: {ossz_meret_mb:.2f} MB")
    print(f"📁 Mentés helye: {kimeneti_mappa}")
    print("═"*50 + "\n")

if __name__ == "__main__":
    main()



