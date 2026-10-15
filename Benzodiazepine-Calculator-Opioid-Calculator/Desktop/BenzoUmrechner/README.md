# Medizinischer Umrechner (Benzodiazepine & Opioide)

Dieses Tool ermöglicht die Umrechnung von Benzodiazepinen in Diazepam-Äquivalente sowie von verschiedenen Opioiden in die orale Morphin-Äquivalenzdosis (OME).

## Disclaimer
**WICHTIG:** Alle berechneten Werte sind Richtwerte und dienen lediglich der Orientierung. Sie ersetzen keine ärztliche Beratung oder klinische Einschätzung. Bei der Umstellung von Opioiden muss immer die individuelle Situation des Patienten sowie das Risiko einer unvollständigen Kreuztoleranz berücksichtigt werden.

## Funktionen
- Umrechnung gängiger Benzodiazepine (Referenz: 10mg Diazepam).
- Umrechnung gängiger Opioide in OME (Morphin oral).
- Speziallogik für Methadon (nicht-lineare Umrechnung basierend auf OME).
- **NEU:** Variabler Sicherheitsabschlag (Cross-Tolerance-Faktor) von 0-100%.
- **NEU:** Benutzerdefinierte Medikamente hinzufügen und dauerhaft speichern.
- **NEU:** Toleranz-Geschwindigkeits-Modell zur Prognose der Dosisentwicklung.
- **NEU:** Versionskontrolle der Äquivalenzdaten und Historie aller Änderungen.
- Grafische Benutzeroberfläche (GUI) mit Tabs und Kommandozeilen-Interface (CLI).

## Installation
1. Repository klonen oder Dateien kopieren.
2. (Optional) Virtuelle Umgebung erstellen:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```
3. Abhängigkeiten installieren (keine externen Pakete nötig):
   ```bash
   pip install -r requirements.txt
   ```

## Nutzung
### GUI starten
```bash
python main.py --gui
```
Dort finden Sie unter dem Tab **"Erweitert"** die Funktionen für benutzerdefinierte Medikamente und die Toleranzberechnung.

### CLI Beispiele
- **Opioid-Umrechnung:**
  `python main.py --drug hydromorphone --dose 6 --route oral`
- **Mit variablem Abschlag (z.B. 25%):**
  `python main.py --drug oxycodone --dose 20 --discount 25`
- **Methadon (erfordert --previous-ome bei hohen Dosen):**
  `python main.py --drug methadone --dose 10 --previous-ome 150`
- **Äquivalenztabelle anzeigen:**
  `python main.py --list`

## Projektstruktur
- `main.py`: Einstiegspunkt (CLI & GUI).
- `converter.py`: Berechnungslogik und Daten.
- `tests/`: Unit-Tests zur Verifizierung der Logik.

## Lizenz
Dieses Projekt steht unter der MIT-Lizenz.
