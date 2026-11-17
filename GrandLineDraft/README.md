# Grand Line Draft · Dual Anime Edition 6.0.3

Ein gemeinsames Draft-Spiel mit zwei auswählbaren Anime-Universen: **One Piece** und **Naruto Shippuden**. Der Name und das Auktions-/Draft-Prinzip bleiben erhalten. Charaktere, Bewertungen, Matchups und Spielstände sind pro Universum getrennt. Naruto endet bei **Naruto Shippuden + The Last: Naruto the Movie**; **Boruto ist ausgeschlossen**.

## Umfang

| Universum | Figuren | Eindeutige Matchups | Ziehungen je Paar | Modellziehungen gesamt |
|---|---:|---:|---:|---:|
| One Piece · Manga bis Kapitel 1198 (08.11.2026) | 140 | 9.730 | 15.000 | 145.950.000 |
| Naruto Shippuden + The Last | 89 | 3.916 | 15.000 | 58.740.000 |
| **Gesamt** | **229** | **13.646** | — | **204.690.000** |

Die Ziehungen sind aggregierte Binomial-Monte-Carlo-Stichproben aus dem Matchup-Modell. Sie sind keine 204,69 Millionen kanonischen Kämpfe und machen eine Fan-Schätzung nicht zu einer offiziellen Rangliste.

## Windows-Start

1. ZIP vollständig entpacken.
2. Python 3.10 oder neuer installieren.
3. `Start_GrandLineDraft.bat` starten.
4. Lokal läuft die App unter `http://127.0.0.1:8501`.

Alternativ manuell im Projektordner:

```bash
python -m pip install -r requirements.txt
streamlit run app.py
```

## Spielprinzip (für beide Anime gleich)

- 20 € Startbudget pro Spieler und fünf Teamplätze.
- Lokal zu zweit, gegen KI oder online über eine Supabase-Lobby.
- Maximal drei Rückgaben je Spieler; jede kostet 1 €. Der ursprüngliche Kaufpreis wird nicht erstattet.
- Klassischer Draft und Fivefold Ranking sind weiterhin getrennte Spielmodi.
- Online-Räume sind an das Anime-Universum des Hosts gebunden. Beim Beitritt wechselt der Gast automatisch zu One Piece oder Naruto, lädt die passende Datenbank und verbindet sich anschließend; manuelle Vorauswahl ist nicht nötig. Die Online-Handoff-Korrektur aus 6.0.1 ist enthalten; die Tierlisten- und Datenbankkorrekturen aus 6.0.2 sind zusätzlich enthalten.
- Die Autosaves liegen getrennt unter `saves/` und `saves/naruto/`.

## Classic-Teamwertung

**One Piece:** Power Level 68 %, bestätigtes Haki 14 %, Fähigkeiten/Nutzwert 14 %, Vielseitigkeit 4 %. Nicht quantifizierbares Haki bleibt unbekannt und wird aus dem Haki-Schnitt ausgeschlossen; falls kein Teammitglied einen belastbaren Wert hat, wird der Haki-Anteil ausgelassen und der Rest proportional normalisiert.

**Naruto:** Power Level 68 %, Chakra 16 %, Fähigkeiten 16 %. Chakra ist ein relativer Fan-Schätzwert aus Reserven/Kontrolle und kein offizieller Databook-Wert. Hamuras Fähigkeitswert bleibt in der Anzeige unbekannt; intern wird zur Berechnung neutral 50 verwendet und nicht als kanonischer Score ausgegeben.

Beide Universen verwenden zusätzlich einen begrenzten Intelligenzbonus und Teamchemie. Kopfgeld wird im Naruto-Universum nicht verwendet.

## Fivefold Ranking

Die gleiche Auktion und die gleiche Kategorie-Zuordnung gelten für beide Welten. Jede der fünf Disziplinen zählt 20 %.

**One Piece:** Teufelsfrucht · Haki · Stärke · Geschwindigkeit · Battle IQ.

**Naruto:** Ninjutsu · Chakra · Taijutsu · Geschwindigkeit · Battle IQ.

Unbekannte Werte bleiben sichtbar als `?`; für die Mittelwertbildung wird ein neutraler Platzhalter verwendet. Das ist keine Behauptung, dass die Figur exakt 50 Punkte besitzt.

## Naruto-Bewertungsanker

Die aktive Naruto-Datenbank enthält 89 Profile. Die vier eigenständigen Bijū Kurama, Son Gokū, Gyūki und Shukaku wurden aus dem Draft-Pool entfernt. Menschliche Jinchūriki wie Naruto, Killer B, Gaara und Yugito bleiben enthalten; ebenso Beschwörungen wie Manda und Gamabunta. Das bereitgestellte, nicht beschriftete Tierlistenbild zeigt 87 sichtbare Portrait-Kacheln; eine vollständige 1:1-Namenszuordnung ist daraus nicht zweifelsfrei möglich. Die Kakashi-/Sakumo-Identitätskorrektur bleibt unverändert. Die folgenden Kernanker wurden nach dessen Vorgabe gesetzt:

| Figur / Peak-Form | Power | Chakra | Fähigkeiten |
|---|---:|---:|---:|
| Kaguya Ōtsutsuki | 100 | 100 | 100 |
| Hagoromo Ōtsutsuki · Jūbi-/Six-Paths-Peak | 100 | 100 | 100 |
| Madara · Jūbi-Jinchūriki | 98 | 100 | 100 |
| Naruto · The Last | 97 | 98 | 97 |
| Sasuke · The Last | 97 | 95 | 98 |
| Hamura Ōtsutsuki | 96 | 99 | unbekannt |
| Obito · Jūbi-Jinchūriki | 95 | 99 | 95 |
| Ashura Ōtsutsuki | 95 | 98 | 98 |
| Indra Ōtsutsuki | 94 | 97 | 96 |
| Toneri Ōtsutsuki | 94 | 98 | 97 |
| Kakashi · DMS | 94 | 96 | 98 |
| Might Guy · Acht Tore | 93 | 84 | 97 |
| Hashirama · Prime | 92 | 97 | 91 |
| Tobirama / Hiruzen · Prime | 91 | 95 / 94 | 97 / 96 |
| Nagato · Prime | 90 | 98 | 100 |
| Minato · KCM/Edo | 90 | 96 | 97 |
| Itachi · Edo Tensei | 90 | 94 | 98 |
| Kabuto · Sennin-Modus | 89 | 94 | 97 |
| Pain · Sechs Pfade | 88 | 96 | 97 |
| Killer B · Gyūki-Jinchūriki | 88 | 98 | 94 |

Alle Kaguya-/Hagoromo-Fivefold-Disziplinen und sichtbaren Kampf-Teilwerte stehen auf 100, wie vom Nutzer gewünscht. Kanon-Kontext: Kaguya wurde von **Hagoromo und Hamura gemeinsam** versiegelt; das wird nicht als Hagoromos Solo-Sieg beschrieben. Hagoromos 100er-Peak ist die vom Nutzer gesetzte spätere Jūbi-/Six-Paths-Deckenbewertung.

Die Eight-Gates-Matchup-Notiz für Might Guy würdigt Night Guy als beinahe tödlichen Treffer gegen Jūbi-Madara. Der zeitlich extrem begrenzte und lebensgefährliche Zustand macht daraus aber keinen automatischen Gesamtsieg; Madara bleibt im Modell knapp favorisiert.

## One-Piece-Stand

Die hochgeladene 5.0.4-Datenbank mit 135 Charakteren wurde beibehalten und um fünf Charaktere auf **140** erweitert: **Kyros, Ashura Doji, Gecko Moria (Prime), Vergo und Kanjuro**. Luffy steht bei Power Level 96 mit der neuen, noch nicht offiziell benannten affenartigen Nika-Darstellung aus Kapitel 1198; sie wird nicht als bestätigtes Gear 6 bezeichnet. Nusjuro hat einen Haki-Gesamtwert und alle drei Teilbereiche. Katakuri bleibt bei Gesamt-Haki 89 (Observation 98, Armament 89, Conqueror 80). Gecko Moria Prime steht bei Power 89 mit niedriger Evidenzsicherheit: seine frühere Rivalität mit Kaido ist bekannt, der konkrete Kampf ist nicht vollständig dargestellt und die Bewertung behauptet keine Gleichwertigkeit.

## Matchup-Modell

- Jede Paarung wird genau einmal gespeichert, mit identischer Gegenpaar-Orientierung im UI.
- Die Rating-Basis enthält Power, bestätigtes Haki bzw. Chakra, Fähigkeiten, Vielseitigkeit, Angriff, Defensive, Tempo, Ausdauer und Battle IQ.
- Situative Vorteile (z. B. Chiyo/Sasori, Shikamaru/Hidan oder Naruto/Toneri) werden nur als begrenzte Matchup-Modifikatoren modelliert.
- Die Wahrscheinlichkeitskurve ist steil genug, damit extreme Leistungsunterschiede keine absurden Upsets mit mehreren Prozentpunkten erzeugen. Ein minimaler Rest bleibt, weil Modellwahrscheinlichkeiten keine absolute Kanon-Wahrheit darstellen.
- Konfidenz beschreibt die Quellen- und Feat-Sicherheit, nicht die Zahl der Monte-Carlo-Stichproben.

## Änderungen 6.0.3

- Die vier eigenständigen Bijū Kurama, Son Gokū, Gyūki und Shukaku sind aus dem Naruto-Draft-Pool entfernt. Jinchūriki und Beschwörungen bleiben erhalten.
- Naruto umfasst jetzt 89 Profile und 3.916 Matchups.
- Der Sammelimport kann nach dem automatischen Porträt-Abruf direkt nach Supabase synchronisieren; Vorschaukacheln sind einheitlich 3:4.

## Historische Tierlisten-Korrekturen 6.0.2

- Kakashi ist nur als DMS-Peak vertreten; der unbestätigte zusätzliche Kriegsbogen-Datensatz wurde entfernt. Sakumo Hatake bleibt eine eigenständige Person und nicht eine Kakashi-Variante.
- Kakuzu steht mit Power 84 leicht über Sasori (83). Sasoris Gift und Puppen bleiben ein situativer Matchup-Vorteil.
- Killer B steht auf Power 88; Chakra 98 und Fähigkeiten 94 werden getrennt betrachtet.

## Online-Modus und Secrets

Für den Online-Modus siehe `ONLINE_SETUP.md`. Beim Beitritt übernimmt der Gast automatisch das Anime-Universum des Hosts (einschließlich Wechsel der getrennten Datenbank und Spielstand-Umgebung). `.streamlit/secrets.toml` ist absichtlich nicht Bestandteil des ZIPs. Eigene Supabase-Secrets bleiben lokal bzw. als sichere Hosting-Secrets. Niemals einen `service_role`-Key in GitHub oder in eine clientseitige Datei hochladen.

## Sammelimport von Charakterporträts

Wähle Naruto in der Sidebar und starte **„Alle 89 Bildquellen prüfen & Porträts lokal speichern“**. Die App fragt die exakten `wiki_slug`-Seiten bei Narutopedia ab und lädt vorhandene Seiten-Thumbnails gesammelt herunter; nicht auffindbare Bilder werden am Ende aufgelistet. Wenn Supabase konfiguriert ist und `cloud_portraits_schema.sql` eingerichtet wurde, synchronisiert die App die geladenen Bilder direkt im Anschluss mit Supabase Storage. So ist kein einzelnes Einfügen je Charakter nötig.

Die Karten-Vorschau verwendet ein einheitliches 3:4-Format und beschneidet Figuren nicht aggressiv. Die Bildbibliothek normalisiert Dateien zu JPG; bereits transparente Quelldateien werden dabei sauber auf den dunklen App-Hintergrund gelegt, aber nicht als echte transparente PNG-Datei gespeichert. Narutopedia/Fandom-Bilddateien sind zudem nicht automatisch zur Weiterveröffentlichung lizenziert; Fandom weist ausdrücklich darauf hin, dass Bilder nicht automatisch dieselbe Lizenz wie Wiki-Text haben. Für öffentliche Verteilung bitte die Lizenz der einzelnen Datei prüfen oder eigene/freigegebene Grafiken verwenden.

## Charakterbilder und Backups

Die Porträts liegen gemeinsam unter `portraits/`; die One-Piece-IDs und Naruto-IDs überschneiden sich nicht. Naruto-IDs mit vier Ziffern werden vom Bildarchiv-Importer unterstützt. Im Menü kann die Sammelprüfung alle Charakterporträts anhand der exakten Wiki-Seiten abrufen; bei konfigurierter Cloud-Bilderdatenbank werden die gefundenen Porträts anschließend gesammelt nach Supabase Storage übertragen. Die Vorschau-Kacheln verwenden ein einheitliches 3:4-Format ohne aggressive Bildbeschneidung. Narutopedia-/Fandom-Bilder sind nicht automatisch für Weiterveröffentlichung lizenziert; die Lizenz jeder Datei muss separat geprüft werden. Portables Backup umfasst beide Anime-Datenbanken und beide getrennten Autosaves. Die Cloud-Bilderbibliothek bleibt privat und erfordert `cloud_portraits_schema.sql`.

## Tests

Im Projektordner:

```bash
python -m py_compile app.py
python -m pytest -q
python -m unittest discover -s tests -v
```

Die Tests prüfen getrennte Roster, vollständige Paarungsmatrizen, die vom Nutzer vorgegebenen Peak-Anker, Kakuzu/Sasori-Reihenfolge, Killer-B-Wert 88, die Kakashi-/Sakumo-Identitätskorrektur, Haki-/Chakra-Labels, keine Boruto-Figuren sowie Online-/Cloud-Sicherheitsfunktionen. Ein browserbasierter Live-Test setzt eine installierte Streamlit-Laufzeit und konfigurierte Secrets voraus.

## Quellen / Bewertungsgrenzen

Naruto: [Offizielle Naruto-Seite – Shippuden](https://naruto-official.com/en/anime/naruto2) · [Origins of Ninshu / Indra und Ashura](https://naruto-official.com/en/anime/naruto2/list?episode=the_origins_of_ninshu_the_two_souls%2C_indra_and_ashura&page=1) · [Six Paths / Finale](https://naruto-official.com/en/news/01_1355) · [Hashirama](https://naruto-official.com/en/news/01_1627) · [Tobirama](https://naruto-official.com/de/news/01_1694) · [Minato](https://naruto-official.com/en/news/01_1517) · [Might Guy](https://naruto-official.com/en/news/01_1673) · [Madara](https://naruto-official.com/en/news/01_1333) · [DMS Kakashi](https://naruto-official.com/en/anime/naruto2/list/01_859) · [The Last](https://naruto.fandom.com/wiki/The_Last:_Naruto_the_Movie).

One Piece: [Offizielle Kapitelübersicht](https://www.viz.com/shonenjump/chapters/one-piece) · [Kapitel 1198](https://www.viz.com/shonenjump/one-piece-chapter-1198/chapter/52017) · [OPwiki – aktuelle Kapitel](https://opwiki.org/wiki/Aktuelle_Kapitel) · [Haki-Übersicht](https://onepiece.fandom.com/wiki/Haki).

Alle Punktwerte und Siegchancen sind eigene Fan-Schätzungen. Offizielle Quellen belegen Handlungen, Fähigkeiten und Feats, nicht die hier verwendete 0–100-Skala. Fanprojekt, keine Verbindung zu den Rechteinhabern.
