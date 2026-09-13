import os
import subprocess
import sys

def fo_menu():
    os.system('cls' if os.name == 'nt' else 'clear')
    print("="*60)
    print(" 🎬 PROFESSZIONÁLIS KLIP GENERÁTOR MESTER SCRIPT 🎬")
    print("="*60)
    print("Válaszd ki a feldolgozni kívánt videó típusát:\n")
    print("  [1] Szövegközpontú videó (Podcast, Tech teszt, Beszélgetés)")
    print("      - Whisper + Gemini (Feliratokkal)")
    print("\n  [2] Akció/Vizuális videó (Játékmenet, Balesetek, Sport)")
    print("      - Vizuális AI elemzés")
    print("\n  [0] Kilépés")
    print("="*60)
    
    valasztas = input("Írd be a választott számot (0-2): ")
    return valasztas

def main():
    while True:
        valasztas = fo_menu()
        
        if valasztas == '1':
            video_url = input("Kérem a videó URL-jét vagy elérési útját: ")
            extra_instrukcio = input("Mit keressen az AI? (Opcionális, nyomj Entert, ha mindegy): ")
            
            print("\n[INFO] Szöveges AI feldolgozó indítása...")
            parancs = [sys.executable, "klip_keszito.py", video_url, extra_instrukcio]
            subprocess.run(parancs)
            break
            
        elif valasztas == '2':
            print("\n[INFO] Vizuális AI feldolgozó indítása...")
            # Meghívjuk az elkészült vizuális modult, ami majd bekéri a videót és a keresett akciót
            parancs = [sys.executable, "vizualis_klip.py"]
            subprocess.run(parancs)
            break
            
        elif valasztas == '0':
            print("\nKilépés... Szép napot!")
            break
        else:
            print("\nÉrvénytelen választás. Próbáld újra!")
            input("Nyomj Entert...")

if __name__ == "__main__":
    main()