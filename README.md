# Der unsichtbare Gegner ⚽🌍

**Reisedistanz & Zeitzonen als heimlicher Mitspieler bei der Fußball-WM 2026**

Datenanalyse und Kartenvisualisierung zur Frage, wie weite Reisewege und
Zeitzonenwechsel die Teams bei der Weltmeisterschaft 2026 (USA · Kanada · Mexiko)
beeinflussen. Datenaufbereitung in Python (pandas), Visualisierung in Tableau.

---

## 🎯 Leitfragen

- Welche Teams legen die größten Reisedistanzen zurück?
- Wie stark belasten Zeitzonenwechsel die einzelnen Mannschaften?
- Wo liegen die Quartiere – gibt es geografische „Hot Spots"?
- Gibt es einen Zusammenhang zwischen Reisebelastung und sportlichem Erfolg?

## 📁 Projektstruktur

```
WM2026_Analyse/
├── notebooks/        Jupyter-Notebooks zur Datenaufbereitung
├── data/             Eingabe- und Ergebnis-CSVs (Input für Visualisierung)
├── app.py            Streamlit-App (interaktive Variante)
├── requirements.txt  Python-Abhängigkeiten
├── .gitignore
└── README.md
```

## 🧮 Methodik

**Reisemodell – Sternmodell:** Jedes Team wohnt während der Gruppenphase in einem
festen **Quartier (Base Camp)** und reist zu jedem Spiel hin und zurück:

```
Total_Distance_KM = Σ über alle Spiele:  2 × Luftlinie(Quartier → Spielort)
```

Zum Vergleich wird zusätzlich die naive **Stadion-zu-Stadion-Kette**
(`Chain_Distance_KM`) berechnet – sie zeigt, wie stark das Quartier die echte
Reisebelastung erhöht.

- **Distanzen:** Luftlinie (Haversine-Formel) – eine Untergrenze, keine realen Flugrouten.
- **Zeitzonen:** Die Stadion-Zeitzonen sind auf die zur WM (Juni/Juli 2026) gültige
  Sommerzeit korrigiert (USA/Kanada mit DST, Mexiko ohne). Die Zeitzone eines
  Quartiers wird aus dem **nächstgelegenen Stadion** abgeleitet.
- **Umfang:** Gruppenphase (48 Teams, 72 Spiele, je 3 Spiele pro Team).

## 📊 Datensätze

### Eingabe (manuell gepflegt)

| Datei | Spalten | Inhalt |
|-------|---------|--------|
| `data/wm2026_stadien_koordinaten_zeitzonen.csv` | `Stadium_Name, City, Country, Latitude, Longitude, Timezone_UTC, Matches_Count` | Die 16 Spielorte mit Geokoordinaten und korrigierter Zeitzone |
| `data/spielplan.csv` | `Date, Stadium, Team_A, Team_B` | Gruppenphasen-Spielplan (Date = `JJJJ-MM-TT`, Stadium exakt wie Stadien-CSV) |
| `data/quartiere.csv` | `Team, BaseCamp_City, Latitude, Longitude` | Mannschaftsquartiere (Längengrad in Nordamerika negativ!) |

### Ergebnis (vom Notebook erzeugt)

| Datei | Inhalt | Tableau-Verwendung |
|-------|--------|--------------------|
| `data/wm2026_team_reiserouten_distanzen.csv` | Eine Zeile pro Team mit allen Kennzahlen | Ranking, KPIs, Streudiagramme |
| `data/wm2026_reiselinien.csv` | Eine Zeile pro Etappe (Quartier → Spielort) mit Start-/Ziel-Koordinaten | Reiselinien auf der Karte (via `MAKELINE`) |

Die Quartiere-Datei (`quartiere.csv`) dient zugleich als Punkt-Layer für die
Team-Standorte und Hot-Spot-Karte.

**Kennzahlen in `wm2026_team_reiserouten_distanzen.csv`:**

| Spalte | Bedeutung |
|--------|-----------|
| `Total_Distance_KM` | Hauptmetrik – Reisedistanz im Sternmodell |
| `Chain_Distance_KM` | Vergleich: naive Stadion→Stadion-Kette ohne Quartier |
| `Longest_Trip_KM` | weiteste einzelne Anreise (Quartier → Spielort) |
| `Timezone_Shift_Total_H` | Summe der Zeitzonendifferenzen ggü. Quartier |
| `Max_Timezone_Diff_H` | größte einzelne Zeitzonendifferenz |
| `Avg_Days_Between_Games` | durchschnittliche Erholungszeit zwischen Spielen |
| `BaseCamp_City`, `Games_Count` | Kontext |

## 🛠️ Verwendung

1. Eingabe-CSVs in `data/` pflegen (`spielplan.csv`, `quartiere.csv`).
2. Notebook [`notebooks/wm2026_team_reiserouten.ipynb`](notebooks/wm2026_team_reiserouten.ipynb)
   öffnen (VS Code oder Jupyter) und von oben nach unten ausführen.
3. Die erzeugten CSVs aus `data/` in Tableau einlesen und visualisieren.

### Voraussetzungen
- Python 3
- `pandas` (`python3 -m pip install pandas`)

## 🗺️ Visualisierung in Tableau

Drei Bausteine, verknüpft über das gemeinsame Feld `Team`:

1. **Ranking / KPIs** – `wm2026_team_reiserouten_distanzen.csv`
   (z. B. sortierter Balken nach `Total_Distance_KM`, Streudiagramm Distanz ↔ Zeitzonen).
2. **Quartiere & Hot Spots** – `quartiere.csv`
   (`Latitude`/`Longitude` auf die Karte, `Team` auf Detail/Label).
   *Hinweis:* Teams mit identischen Koordinaten liegen übereinander – für die
   Hotspot-Sicht nach Stadt aggregieren und Punktgröße = Anzahl Teams setzen.
3. **Reiselinien** – `wm2026_reiselinien.csv`, berechnete Felder:
   ```
   Origin      = MAKEPOINT([Quartier_Lat], [Quartier_Lon])
   Destination = MAKEPOINT([Spielort_Lat], [Spielort_Lon])
   Reiselinie  = MAKELINE([Origin], [Destination])
   ```
   `Reiselinie` auf die Karte, `Team` auf Farbe, `Distanz_KM` auf Größe/Tooltip.

## 🚀 Visualisierung in Streamlit (Variante 2)

Interaktive Alternative zu Tableau – nutzt dieselben CSVs.

```bash
python3 -m pip install -r requirements.txt
streamlit run app.py
```

Die App ([`app.py`](app.py)) bietet drei Tabs – **Reiselinien** (pydeck-Bögen
Quartier → Spielort), **Quartiere & Hotspots** (Punktgröße = Anzahl Teams) und
**Ranking** (Sternmodell vs. naive Kette) – plus Team-Filter in der Sidebar.
Deploybar über die [Streamlit Community Cloud](https://streamlit.io/cloud).

## ⚠️ Einschränkungen

- Distanzen sind **Luftlinie**, keine realen Flug-/Bodenrouten → Untergrenze.
- Nur die **Gruppenphase**; K.-o.-Runden sind (noch) nicht enthalten.
- Das Quartier gilt als über die Gruppenphase **fest**; reale Standortwechsel
  werden nicht abgebildet.
