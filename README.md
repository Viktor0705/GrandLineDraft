# Grand Line Draft 5.1 — Peak Edition

One-Piece-Draft-App auf Python/Streamlit-Basis. Diese vollständige Version baut auf der vom Nutzer bereitgestellten **5.0.4-Vollversion mit 135 Charakteren** auf und erweitert sie auf **140 Charaktere**, ohne bestehende IDs oder die Spielmechanik zu entfernen. Enthalten sind Classic Draft, Fivefold Ranking, Online-Lobby, Supabase-Cloud-Porträts und die vollständige neue Matchup-Matrix.

## Windows-Start

1. ZIP vollständig entpacken.
2. Python 3.10 oder neuer installieren.
3. `Start_GrandLineDraft.bat` starten.
4. Lokal läuft die App standardmäßig unter `http://127.0.0.1:8501`.

## Was in 5.1 neu ist

- **140 Charaktere**: alle 135 Figuren aus deiner 5.0.4-Version bleiben erhalten; IDs 166–170 ergänzen Gecko Moria (Prime), Kyros, Ashura Doji, Vergo und Kawamatsu.
- **Manga-Stichtag Kapitel 1198 (9. November 2026, Deutschland)**: Ruffys neue dunkle, affenartig wirkende Nika-Manifestation ist berücksichtigt. Sie wird nicht als Gear 6 bezeichnet, weil der Manga sie nicht so benennt. Power Level Ruffy: **96**.
- **Ethanbaron V. Nusjuro** erhält einen Gesamt-Haki-Schätzwert von **93**: Observation 91, Armament 93, Conqueror 94.
- **Prime-Gecko-Moria: Power 89**. Seine frühere Konfrontation mit Kaido zählt, aber der Kampf ist nicht vollständig gezeigt und Kaido gewann. Daher bleibt die Konfidenz niedrig; Moria wird nicht einfach mit Kaido gleichgesetzt.
- Katakuris Gesamt-Haki bleibt **89** (Observation 98, Armament 89, Conqueror 80).
- Alle **9.730 eindeutigen Matchups** wurden neu aus den Profilen berechnet; die widersprüchlichen alten Wahrscheinlichkeiten wurden nicht übernommen.

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

- Gleicher 140er-Charakterpool, 20 € Budget je Spieler, gleiche Auktion, maximal drei Rückgaben je Spieler für je 1 €.
- Der Gewinner einer Karte weist diese einer freien Kategorie zu: Teufelsfrucht, Haki, Stärke, Geschwindigkeit oder Battle IQ.
- Jede Kategorie zählt 20 %. Der Durchschnitt ist 0–100 (nicht 500).
- Der Enddurchschnitt und die Gewinnwahrscheinlichkeit werden erst am Ende offengelegt.
- Kein bestätigter Fruchtbesitz bedeutet 0 in der Teufelsfrucht-Kategorie, nicht 0 Kampfstärke.
- **Unbekannte Haki-Meisterschaft wird als `?` angezeigt.** Für die Fivefold-Mittelwertberechnung wird intern ein neutraler Platzhalter 50 verwendet, damit die Kategorien gleich gewichtet sind. Der Wert 50 wird nicht als Kanon-Hakiwert ausgegeben. Im klassischen Modus wird unbekanntes Haki aus dem Haki-Schnitt ausgeschlossen.

## Power Matrix v5.1

Bewertungsstichtag: **Manga-Kapitel 1198 vom 9. November 2026 (deutsche Veröffentlichung)**. Das ist der aktuell veröffentlichte Stand zum Erstellungsdatum dieser Version (16. November 2026). Kapitel 1199 ist für den 22. November 2026 gelistet.

Power Level und Einzelwerte sind Fan-Modellschätzungen, keine offiziellen Oda-Werte. Manga-Feats und belegte Aussagen haben Vorrang vor Wikis, Foren, YouTube-Rankings und Fan-Theorien. Community-Material dient nur als ergänzende Perspektive. Bei widersprüchlichen oder unzureichenden Belegen wird die Konfidenz abgesenkt bzw. Haki-Meisterschaft als unbekannt belassen.

### Wichtige Vergleichsanker

| Charakter | Power Level |
|---|---:|
| Imu / Joy Boy | 100 |
| Rocks D. Xebec | 99 |
| Roger / Prime Whitebeard / Prime Garp | 98 |
| Shanks / Mihawk | 97 |
| Kaido / Ruffy | 96 |
| Ethanbaron V. Nusjuro | 93 |
| Gecko Moria (Prime) | 89 |
| Charlotte Katakuri | 89 |

Shanks gegen Mihawk bleibt ein offenes Spitzenduell. Kaido wird in einem langen, gesunden 1-gegen-1 knapp vor Ruffy geführt. Diese Werte entscheiden nicht jedes situative Matchup automatisch.

## Haki-Daten

Ein bestätigter Haki-Typ ist nicht automatisch eine bestätigte quantitative Meisterschaft. Der Gesamt-Haki-Wert wird nur angezeigt, wenn die Daten eine individuelle Meisterschaftsschätzung tragen. Nicht quantifizierbare Werte bleiben `null`/`?`; sie werden nicht künstlich als 0 interpretiert. Nusjuros drei Teilwerte werden jeweils in der Charakterdetailansicht erläutert.

## Matchup-Modell

- 140 Charaktere ergeben **9.730 eindeutige 1-gegen-1-Paarungen**.
- Je Paarung: 15.000 reproduzierbare, vorab berechnete Ergebnisziehungen (**145.950.000 insgesamt**).
- Jede Paarung wurde aus Power, bestätigtem Haki, Fähigkeiten, Vielseitigkeit, Angriff, Defensive, Tempo, Ausdauer und Battle IQ neu bewertet; die alten Wahrscheinlichkeiten wurden nicht als Vorannahme übernommen.
- Kanonische Einschränkungen und ausgewählte konkrete Konter werden als begrenzte, dokumentierte Modifikatoren berücksichtigt.
- Große Stärkeabstände können sehr klare Favoriten ergeben; auch dann bleibt eine kleine modellierte Upset-Chance. Shanks gegen Lysop ist beispielsweise kein ausgeglichenes Duell.
- Diese Ergebnisziehungen sind statistische Stichproben aus einem Wahrscheinlichkeitsmodell, keine panelgetreuen Manga-Kämpfe. Die Anzahl der Samples stabilisiert nur den numerischen Schätzwert; sie erhöht nicht die Kanon-Evidenz.

## Charakterporträts und Bilder

Bereits lokal gespeicherte oder hochgeladene Porträts werden verwendet. Bilder können über den Bildmanager aus einer direkten Bild-URL ergänzt/ersetzt werden. Es sind nicht automatisch alle 140 Rechteinhaber-Bilder im ZIP eingebettet; neue Bilder werden nur auf ausdrückliche Aktion geladen und lokal gecacht. Die bestehende Supabase-Cloud-Bildintegration und das private Bucket-Schema bleiben erhalten.

## Tests

Im Projektordner:

```bash
python -m unittest discover -s tests -v
python -m pytest -q
python -m py_compile app.py
```

Ein erfolgreicher Syntax-/Datentest ersetzt keinen abschließenden Live-Test in deiner eigenen Streamlit-Cloud- und Supabase-Umgebung. Bestehende `.streamlit/secrets.toml`-Zugangsdaten werden nicht mitgeliefert und dürfen nicht in GitHub committet werden.

## Quellen / Methodenhinweise

- Offizielle Kapitelübersicht: https://www.viz.com/shonenjump/chapters/one-piece
- Kapitel 1198: https://www.viz.com/shonenjump/one-piece-chapter-1198/chapter/52163
- OPwiki, aktuelle Kapitel: https://opwiki.org/wiki/Aktuelle_Kapitel
- Nusjuro: https://opwiki.org/wiki/Ethanbaron_V._Nusjuro
- Haki-System-Übersicht: https://onepiece.fandom.com/wiki/Haki
- Gecko Moria: https://onepiece.fandom.com/wiki/Gecko_Moria
- Ashura Doji: https://onepiece.fandom.com/wiki/Ashura_Doji
- Vergo: https://onepiece.fandom.com/wiki/Vergo
- Kawamatsu: https://onepiece.fandom.com/wiki/Kawamatsu

Fanprojekt, nicht mit Eiichiro Oda, Shueisha, VIZ oder anderen Rechteinhabern verbunden.

---

## Versionshistorie

Die Abschnitte 5.0.2, 5.0.3 und 5.0.4 weiter unten dokumentieren die Änderungen der Vorgängerversionen. Die aktuelle Fassung ist **5.1** und verwendet die oben beschriebene Kapitel-1198-Datenbank mit 140 Charakteren.


## 5.0.2 – Online-Performance und gemeinsame Bilder

- Online-Polling lädt im Normalfall nur Raum-Metadaten; vollständige Payloads werden nur bei einer neuen Revision geladen.
- Classic und Fivefold verwenden eine browserseitige gemeinsame Rad-Animation.
- Lokale Autosaves werden bei unverändertem Spielzustand nicht erneut auf die Festplatte geschrieben.
- Supabase Storage kann über `cloud_portraits_schema.sql` für einen privaten, geräteübergreifenden Charakterbildspeicher eingerichtet werden.
- Eigene Bilder per URL oder Datei werden bei konfigurierter Cloud-Bilderdatenbank automatisch hochgeladen. Bestehende PC-Bilder können per ZIP importiert werden.


## Grand Line Draft 5.0.2 – Online Performance & Cloud Portraits

Diese Version synchronisiert Classic- und Fivefold-Rad-Animationen über einen gemeinsamen Startzeitpunkt, reduziert die Online-Polling-Last auf kompakte Metadaten und nutzt Supabase Storage für gemeinsame Charakterporträts. Vor der ersten Bildsynchronisierung einmal `cloud_portraits_schema.sql` im Supabase SQL Editor ausführen. Danach in der App den Cloud-Bilder-Expander verwenden. Siehe `ONLINE_SETUP.md`.


## Performance Edition 5.0.3

Die Matchup-Tabelle liegt separat in `matchup_results.json.gz` und wird erst beim Teamvergleich geladen. Charakter-/Fivefold-Profile und der Suchindex sind gecacht; sichtbare Cloud-Porträts werden parallel vorgeladen und als kompakte Thumbnails gerendert.


## 5.0.4 – Katakuri Haki-Rekalibrierung

- Katakuris Gesamt-Haki wurde von 84 auf 89 angepasst.
- Observationshaki 98 und Rüstungshaki 89 bleiben bestehen; Königshaki steigt von 65 auf 80 (bestätigte Grundanwendung, keine belegte fortgeschrittene Beschichtung).
- Fivefold-Haki-Wert und Charakterdetail zeigen jetzt 89.
- Die 134 Katakuri-Matchups wurden mit kleinem Haki-Einfluss und 15.000 Ergebnisziehungen je Paar aktualisiert.
- Keine Änderung an Katakuris Power Level (89), Draft-Regeln, Charakter-IDs oder Supabase-Schema.


## 5.1 – Manga-Kapitel 1198 und 140er-Roster

- Basis ist die vom Nutzer bereitgestellte Vollversion 5.0.4 (135 bestehende Charaktere); fünf Figuren ergänzt: Gecko Moria (Prime), Kyros, Ashura Doji, Vergo und Kawamatsu. Bestehende IDs bleiben erhalten, neue IDs sind 166–170.
- Ruffy: Power Level 96. Kapitel 1198 zeigt eine neue dunkle, affenartig wirkende Nika-Manifestation. Sie wird nicht als Gear 6 ausgegeben, da der Manga sie nicht so benennt.
- Nusjuro: Haki 93 (Observation 91, Armament 93, Conqueror 94), weil alle drei Formen individuell belegt sind.
- Gecko Moria: Prime-Power 89. Der frühere Kampf gegen Kaido wird als wichtiger Peak-Nachweis berücksichtigt; Kaido gewann, die genaue Kampfdarstellung bleibt unvollständig.
- Katakuri bleibt bei Gesamt-Haki 89 (Observation 98, Armament 89, Conqueror 80).
- Alle 9.730 Matchups wurden aus den Profilen neu erzeugt. Unplausible Alt-Prioren werden nicht wiederverwendet. Shanks vs. Mihawk bleibt ein offenes Spitzenduell; Kaido ist in einem langen, gesunden 1v1 knapp vor Ruffy.
- Matchup-Wahrscheinlichkeiten dürfen 99,95 % erreichen, fallen aber nie auf garantierte 100 %; der alte 98-%-Deckel wurde entfernt.
- 15.000 aggregierte Binomialziehungen je Paarung, 145.950.000 insgesamt. Werte bleiben Fan-Schätzungen, keine Kanon-Ergebnisse.
