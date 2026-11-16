# Grand Line Draft 5.1 – vollständige Projektversion

**Manga-Stichtag:** Kapitel 1198 (9. November 2026)  
**Roster:** 125 Figuren  
**Matchups:** 7.750 eindeutige Paarungen, jeweils 15.000 reproduzierbare Modellziehungen

## Inhalt

- `app.py` – vollständiger Streamlit-App-Code
- `characters.json` – Charakterpool mit 125 Einträgen
- `character_ratings.json` – vollständige Profile, Haki-Teilwerte und Matchup-Daten
- `fivefold_component/index.html` – lokale Fivefold-Rad- und Kategorienkomponente
- `requirements.txt` – Python-Abhängigkeiten
- `.streamlit/config.toml` – Streamlit-Konfiguration
- `.streamlit/secrets.toml.example` – Vorlage ohne echte Zugangsdaten
- `tests/` – Daten- und Matchup-Prüfungen

## Gecko Moria – Prime-Korrektur

Gecko Moria wird mit **Power Level 89** bewertet, nicht mehr mit 75. Das Profil bezieht sich ausdrücklich auf seine Prime-Zeit als Kapitän der Gecko-Piraten und seinen Feldzug nach Wano gegen Kaido. In Kapitel 483 wird er rückblickend als jemand beschrieben, der mit Kaido konkurrieren konnte; Kapitel 456 und 969 verankern seine Niederlage und den Verlust seiner Crew. Da der Kampf nicht vollständig gezeigt wird, ist der Wert bewusst eine vorsichtige Fan-Schätzung und keine Behauptung, dass er Kaido auf dessen heutigem Peak gleichkommt. Haki bleibt mangels eindeutiger Einzelbelege unbekannt.

## Lokal starten (Windows)

1. ZIP vollständig entpacken.
2. Python 3.10 oder neuer installieren.
3. Im entpackten Projektordner ein Terminal öffnen.
4. `python -m pip install -r requirements.txt` ausführen.
5. `Start_GrandLineDraft.bat` doppelklicken oder `python -m streamlit run app.py` ausführen.

## Streamlit Community Cloud / GitHub

1. Zuerst dein bestehendes Repository als ZIP sichern oder einen Git-Commit erstellen.
2. Den Inhalt dieses Projektordners ins Repository hochladen und die App-Datei als `app.py` im Repository-Stamm ablegen.
3. `secrets.toml` **nicht** hochladen. Bereits hinterlegte Streamlit-Secrets und die Supabase-Datenbank unverändert lassen.
4. In Streamlit Cloud bei Bedarf einen Reboot auslösen.

## Wichtig zur vorhandenen Live-App

Diese Vollversion wurde aus der in den Projektdateien verfügbaren vollständigen App-Quelle vom **4. November 2026** aufgebaut und für v5.1 angepasst. Eine nachweislich aktuellere originale `app.py` der von dir erwähnten 5.0.4-Livefassung lag hier nicht vor. Daher ist dies eine vollständige lauffähige Projektdatei, aber keine bitgenaue Fortsetzung eines nicht vorliegenden 5.0.4-Quellstands. Vergleiche vor dem Ersetzen deine zuletzt eingesetzte `app.py`, besonders bei später ergänzten Online-/Cloud-Bild-Funktionen.

## Matchup-Methode

Jedes Paar wird aus den internen Duel-Ratings (Power, bestätigtes Haki, Fähigkeiten, Angriff, Defensive, Tempo, Ausdauer und Battle IQ) sowie vorhandenen dokumentierten Matchup-Modifikatoren neu berechnet. Große Stärkeunterschiede erhalten dadurch sehr geringe Außenseiterwahrscheinlichkeiten; nahe Top-Tier-Duelle bleiben offen. 15.000 Ziehungen sind eine Stichprobe des Modells, keine Canon-Kämpfe. Das ist eine systematische Neukalibrierung aller Paare und keine 7.750 separat verfassten Manga-Essays.

## Datenschutz und Secrets

- `.streamlit/secrets.toml` darf nie in GitHub veröffentlicht werden.
- `saves/` und `portraits/` bleiben lokal und werden nicht automatisch in dieses ZIP aufgenommen.
- Die vorhandenen Supabase-Tabellen werden durch die Datenaktualisierung nicht verändert.

Die Zahlen sind Fan-Schätzungen; One Piece besitzt keine offizielle allgemeine 0–100-Power-Skala.
