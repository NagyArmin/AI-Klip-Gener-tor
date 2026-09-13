import os
import json
import subprocess
import time
from pathlib import Path
from google import genai
from google.genai import types

# --- BEÁLLÍTÁSOK ---
GEMINI_MODEL = "gemini-3.6-flash"

def vizualis_elemzes(video_path, keresett_akcio):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("HIBA: Nincs beállítva a GEMINI_API_KEY környezeti változó!")
        return []

    client = genai.Client(api_key=api_key)
    
    print("\n[1/3] Videó feltöltése a felhőbe elemzésre (ez eltarthat egy ideig)...")
    try:
        video_file = client.files.upload(file=video_path)
        print(f"Sikeres feltöltés! Fájl azonosító: {video_file.name}")
    except Exception as e:
        print(f"Hiba a feltöltés során: {e}")
        return []

    print("[2/3] Várakozás a videó feldolgozására a szerveren...")
    while video_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(5)
        # Frissítjük a fájl állapotát
        video_file = client.files.get(name=video_file.name)
    print("\nFeldolgozás kész!")

    if video_file.state.name == "FAILED":
        print("HIBA: A videó feldolgozása sikertelen volt a szerveren.")
        return []

    print(f"[3/3] Akció keresése: '{keresett_akcio}' ...")
    
    rendszerutasitas = f"""
Egy videót kapsz. A feladatod, hogy keresd meg benne az alábbi eseményeket: {keresett_akcio}.
Add meg az ÖSSZES ilyen akció pontos kezdő és végpontját másodpercben.

FONTOS SZABÁLYOK A VÁGÁSHOZ:
- A kezdő és végpontok PONTOSAN az adott eseményt (jelenetet) fedjék le!
- Szigorúan vágd el a klipet ott, ahol a jelenet véget ér (vágókép jön)!
- NE lógjon át a klip a következő, teljesen más jelenetbe! Ha egy akció csak 4 másodperces, akkor a klip is pontosan 4 másodperces legyen.

Válaszolj KIZÁRÓLAG egy JSON tömbbel, a következő formátumban:
[
  {{"start": 12.3, "end": 16.5, "cim": "Rövid, ütős cím", "indoklas": "Mi történik a képen?"}}
]
"""
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[video_file, "Keresd meg az eseményeket és add vissza a JSON-t!"],
            config=types.GenerateContentConfig(
                system_instruction=rendszerutasitas,
                response_mime_type="application/json",
                temperature=0.2
            )
        )
        nyers_valasz = response.text.strip()
    except Exception as e:
        print(f"HIBA az elemzéskor: {e}")
        return []

    # Opcionális, de ajánlott: Töröljük a fájlt a felhőből, ha már nincs rá szükség
    client.files.delete(name=video_file.name)

    try:
        highlightok = json.loads(nyers_valasz)
        print(f"\nSiker! A modell {len(highlightok)} db akciószakaszt talált.")
        return highlightok
    except json.JSONDecodeError:
        print("HIBA: A Gemini válasza nem volt érvényes JSON.")
        return []

def vizualis_klipek_vagasa(video_path, highlightok):
    if not highlightok:
        return

    kimeneti_mappa = Path(video_path).parent / "vizualis_klipek"
    kimeneti_mappa.mkdir(exist_ok=True)
    
    print(f"\n[4/4] Videók vágása indul a(z) {kimeneti_mappa} mappába...")
    
    for sorszam, klip in enumerate(highlightok, 1):
        start = float(klip['start'])
        end = float(klip['end'])
        
        # Biztonságos fájlnév generálása a klip címéből
        biztonsagos_cim = "".join(c for c in klip['cim'] if c.isalnum() or c in " _-").strip()
        biztonsagos_cim = biztonsagos_cim.replace(" ", "_")
        
        kimeneti_fajl = kimeneti_mappa / f"{sorszam:02d}_{biztonsagos_cim}.mp4"
        
        # FFmpeg vágás 9:16-os vertikális (TikTok/Shorts) méretre fókuszálva a közepére
        # FFmpeg vágás: Eredeti videó középen, elhomályosított háttérrel a 9:16-os kitöltéshez
        # FFmpeg vágás: Eredeti videó középen LOGÓMENTESÍTVE (felső 15% levágva), elhomályosított háttérrel
        # FFmpeg vágás: Logómentesítés (felső 15% levágva), homályosított háttér, TELJESEN NÉMÍTVA
        # FFmpeg PRECÍZ VÁGÁSSAL (-i az -ss előtt), logómentesítve, homályosítva, némítva
        parancs = [
            "ffmpeg", "-y", 
            "-i", str(video_path),
            "-ss", str(start), 
            "-to", str(end),
            "-vf", "split[bg][fg];[bg]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,gblur=sigma=25[bg_blurred];[fg]crop=iw:ih*0.85:0:ih*0.15,scale=1080:1920:force_original_aspect_ratio=decrease[fg_scaled];[bg_blurred][fg_scaled]overlay=(W-w)/2:(H-h)/2",
            "-c:v", "libx264", "-an",
            str(kimeneti_fajl)
        ]
        
        print(f"  -> {sorszam}. klip vágása: {biztonsagos_cim}...")
        subprocess.run(parancs, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    print("\n✅ Minden klip sikeresen kivágva!")   

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
    teszt_video = input("Kérem a videó elérési útját: ").strip('"' + "'")
    mit_keresunk = input("Mit keressen a modell? (pl. 'Autóbalesetek és ütközések'): ")
    
    eredmeny = vizualis_elemzes(teszt_video, mit_keresunk)
    vizualis_klipek_vagasa(teszt_video, eredmeny)

