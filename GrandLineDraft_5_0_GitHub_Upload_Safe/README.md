# Grand Line Draft 5.0 — Peak Edition

One-Piece-Draft-App auf Python/Streamlit-Basis. Sie enthält den klassischen Auktions-Draft und den separaten Fivefold-Ranking-Modus. Beide nutzen denselben Pool aus **135 eindeutigen Charakter-IDs** und eine gemeinsame Power-/Matchup-Matrix. Spielumgebung und Draft-Spielmodus sind getrennt wählbar.

## Windows-Start

1. ZIP vollständig entpacken.
2. Python 3.10 oder neuer installieren.
3. `Start_GrandLineDraft.bat` starten.
4. Lokal läuft die App standardmäßig unter `http://127.0.0.1:8501`.

## Spielumgebung

- **Lokal · 2 Spieler:** beide Spieler verwenden denselben Browser/dieselbe Sitzung.
- **Gegen KI:** regelbasierte KI auf Spieler-B-Seite.
- **Online · Lobby:** Raum erstellen oder per achtstelligem Code beitreten. Erfordert einmalige Supabase-Konfiguration; siehe `ONLINE_SETUP.md`.

## Draft-Spielmodus 1: Classic Grand Line Draft

- 20 € Budget je Spieler, fünf Charaktere je Team.
- Bestehende Ziehungs- und Auktionsregeln bleiben erhalten.
- Maximal drei Rückgaben je Spieler, je Rückgabe 1 € Strafkosten; Kaufpreis wird nicht erstattet.
- Teamvergleich und Ergebnisprognose basieren auf Charakterprofilen und den hinterlegten Matchup-Wahrscheinlichkeiten.

## Draft-Spielmodus 2: Fivefold Ranking

- Gleicher 135er-Charakterpool, 20 € Budget je Spieler, gleiche Auktion, maximal drei Rückgaben je Spieler für je 1 €.
- Der Gewinner einer Karte weist diese einer freien Kategorie zu: Teufelsfrucht, Haki, Stärke, Geschwindigkeit oder Battle IQ.
- Jede Kategorie zählt 20 %. Der Durchschnitt ist 0–100 (nicht 500).
- Der Enddurchschnitt und die Gewinnwahrscheinlichkeit werden erst am Ende offengelegt.
- Kein bestätigter Fruchtbesitz bedeutet 0 in der Teufelsfrucht-Kategorie, nicht 0 Kampfstärke.
- **Unbekannte Haki-Meisterschaft wird als `?` angezeigt.** Für die Fivefold-Mittelwertberechnung wird intern ein neutraler Platzhalter 50 verwendet, damit die Kategorien gleich gewichtet sind. Der Wert 50 wird nicht als Kanon-Hakiwert ausgegeben. Im klassischen Modus wird unbekanntes Haki aus dem Haki-Schnitt ausgeschlossen.

## Power Matrix v5.0

Bewertungsstichtag: **Manga-Kapitel 1197, veröffentlicht am 1. November 2026**. Kapitel 1198 ist am 4. November 2026 noch nicht veröffentlicht.

Die Power-Level sind Fan-Modellschätzungen, keine offiziellen Oda-Werte. Manga-Feats und belegte Aussagen haben Vorrang vor Wikis, Foren, YouTube-Rankings und Fan-Theorien. Community-Material dient nur als ergänzende Perspektive. Bei widersprüchlichen oder unzureichenden Belegen wird die Konfidenz abgesenkt bzw. Haki-Meisterschaft als unbekannt belassen.

### Vom Nutzer gesetzte Peak-Anker

| Charakter | Power Level |
|---|---:|
| Imu / Joy Boy | 100 |
| Rocks D. Xebec | 99 |
| Roger / Prime Whitebeard / Prime Garp | 98 |
| Shanks / Mihawk | 97 |
| Kaido | 96 |
| Gear-5-Ruffy | 95 |
| Katakuri | 89 |
| Queen | 85 |
| Doflamingo | 83 |

Mihawk und Shanks erhalten dieselbe Gesamtstufe; Mihawk führt bei reiner Schwertkunst, Shanks bei den klar gezeigten Haki-Spitzenleistungen. Kaido wird in einem unbelasteten, gesunden 1-gegen-1 knapp vor Gear-5-Ruffy geführt. Diese Werte entscheiden nicht jedes situative Matchup automatisch.

## Haki-Daten

Ein bestätigter Haki-Typ ist nicht automatisch eine bestätigte quantitative Meisterschaft. Der Gesamt-Haki-Wert wird nur angezeigt, wenn die Daten eine individuelle Meisterschaftsschätzung tragen. Nicht quantifizierbare Werte bleiben `null`/`?`; sie werden nicht künstlich als 0 interpretiert. Benn Beckmans in SBS Band 8 gepriesene Intelligenz wird separat als Intelligenz-/Taktikhinweis geführt und nicht als Haki-Beleg.

## Matchup-Modell

- 135 Charaktere ergeben 9.045 eindeutige 1-gegen-1-Paarungen.
- Je Paarung: 15.000 vorab berechnete Monte-Carlo-Ergebnisziehungen (135.675.000 insgesamt).
- Die Datenbank speichert die Paarungen; beim Öffnen eines Matchups wird nicht live simuliert.
- Diese Ergebnisziehungen sind statistische Stichproben aus einem Wahrscheinlichkeitsmodell, keine 135 Millionen unabhängig simulierten, panelgetreuen Manga-Kämpfe.
- Die Anzahl der Samples stabilisiert nur den numerischen Schätzwert; sie erhöht nicht die Kanon-Evidenz. Konfidenz beschreibt die Quellenqualität.

## Charakterporträts und Bilder

Bereits lokal gespeicherte oder hochgeladene Porträts werden verwendet. Bilder können über den Bildmanager aus einer direkten Bild-URL ergänzt/ersetzt werden. Es sind nicht automatisch alle 135 Rechteinhaber-Bilder im ZIP eingebettet; neue Bilder werden nur auf ausdrückliche Aktion geladen und lokal gecacht.

## Tests

Im Projektordner:

```bash
python -m unittest discover -s tests -v
python -m py_compile app.py
```

Die Oberfläche wurde im Build-Kontext syntaktisch geprüft. Da in der Erstellungsumgebung Streamlit nicht installiert ist, ist ein vollständiger Browser-Live-Test nicht Bestandteil der bereitgestellten Prüfung.

## Quellen / Methodenhinweise

- Offizielle Kapitelübersicht: https://www.viz.com/shonenjump/chapters/one-piece
- Kapitel 1197: https://www.viz.com/shonenjump/one-piece-chapter-1197/chapter/52017
- One Piece Official Character Profiles: https://one-piece.com/character/
- SBS Band 8 – Beckmans Intelligenz (historisch begrenzte Formulierung): https://onepiece.fandom.com/wiki/SBS_Volume_8
- Haki-System-Übersicht: https://onepiece.fandom.com/wiki/Haki
- One Piece Wiki, OPwiki, Foren und Community-Videoanalysen werden nur als sekundäre Interpretationen verwendet.

Fanprojekt, nicht mit Eiichiro Oda, Shueisha, VIZ oder anderen Rechteinhabern verbunden.
