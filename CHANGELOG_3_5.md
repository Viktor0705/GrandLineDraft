# Grand Line Draft 3.5 – Änderungen

## Neue Spielvariante: Fivefold Ranking
- Separater Modus neben dem klassischen Grand Line Draft.
- Gleicher Pool aus 120 Charakteren; 20 € Budget, Auktionslogik, maximal drei Rückgaben und 1 € Strafe pro Rückgabe.
- Der Gewinner jeder Auktion wählt eine freie Kategorie: Teufelsfrucht, Haki, Stärke, Geschwindigkeit oder Battle IQ.
- Fünf gleich gewichtete Kategorie-Scores ergeben am Ende den Mittelwert von 0 bis 100.
- Vorläufige und finale modellierte Gewinnwahrscheinlichkeit auf derselben logistischen 10-Punkte-Skala wie beim klassischen Matchup-Modell.
- Eigenständiger Spielzustand und eigene Historie; der klassische Draft wird beim Moduswechsel nicht zurückgesetzt.

## Charakterbewertungen
- Die 120 Power Levels wurden erneut auf einer gemeinsamen Skala kalibriert: Imu/Joy Boy 100, Rocks 99, Roger/Prime-Whitebeard/Prime-Garp 98, Shanks/Mihawk 97, Kaido/Gear-5-Ruffy 96, Katakuri 91, Hancock 84.
- Ergänzte und überarbeitete Kategorie-Werte für Teufelsfrucht, Haki, Stärke, Geschwindigkeit und Battle IQ; jede Zahl hat Evidenzhinweis und kurze Begründung.
- Haki-Detailwerte für Observation, Armament und Königshaki; bei nicht bestätigten Typen wird „Nicht bestätigt“ gezeigt und kein fälschlicher Nullwert behauptet.
- Spezialisierte Vergleichswerte für Schwertkunst und Haki-Spitzenwert werden in Charakterdetails dargestellt, ändern aber nicht eigenständig die klassische Teamformel.

## Bedienung & Speicherung
- Modus-Auswahl auf der Startseite.
- Charakter-Explorer für beide Modi mit Suche, Crew-/Rollenfilter, Power-Level-Bereich, Haki-/Fruchtfilter und mehreren Sortierungen.
- Spieleridentitäten können im Freund-Modus getauscht werden; Teams und laufende Auktionszuordnungen bleiben bei der jeweiligen Person.
- Ergebniswahl (Spieler A, Spieler B oder Unentschieden), persistente Spielhistorie und automatische Regel für den nächsten Startspieler: Verlierer startet; bei Unentschieden bleibt der bisherige Startspieler.
- Die Historie kann nur nach expliziter Bestätigung gelöscht werden.
- Export/Import sowie vollständiges Backup mit gespeicherten Porträts bleiben verfügbar.

## Teststatus
- Python-Syntaxprüfung erfolgreich.
- Datenprüfung: 120 eindeutige IDs, alle 120 Charaktere mit fünf Kategorie-Werten, Evidenz und Begründungen; Haki-Teilwerte im zulässigen Bereich.
- Isolierte Logiktests für Kategorie-Durchschnitt, Gewinnwahrscheinlichkeit, Ergebnis-/Startspieler-Regel und Spielerwechsel erfolgreich.
- Ein vollständiger Streamlit-Browserlauf konnte in der Build-Umgebung nicht durchgeführt werden, weil Streamlit nicht installiert war und Paketinstallation am fehlenden Netzwerk-DNS scheiterte. Der Windows-Launcher installiert die Abhängigkeiten beim ersten Start.
