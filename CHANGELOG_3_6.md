# Grand Line Draft 3.6 – Performance, Fivefold UI und Bildlinks

## Fivefold Ranking
- Tatsächliche browserseitige Rad-Animation mit kurzem Spin und anschließender Kartenenthüllung.
- Neu gestaltete Drag-and-drop-Zuordnung: gewonnene Figur auf eine der fünf farbcodierten Disziplin-Karten ziehen; freie Plätze sind als Drop-Ziele markiert.
- Klickbasierte Zuordnung bleibt als barriereärmere Alternative erhalten.
- Durchschnitt und Gewinnprognose sind im laufenden Draft verborgen und werden erst im finalen Ergebnisbereich aufgedeckt.

## Performance
- Die Charakterliste wird über Streamlit-Cache gelesen.
- Normale Porträtanzeige führt keine synchronen Netzwerkabfragen mehr aus. Lokal gespeicherte Bilder und gecachte Ersatzporträts werden direkt verwendet.
- Der Charakter-Explorer wird erst dann gerendert, wenn er ausdrücklich geöffnet wird; so werden nicht bei jedem Spielzug alle Filter- und Kartenwidgets neu erzeugt.
- Bilddownloads finden nur durch explizite Aktionen statt (direkter Bildlink oder Sammelabruf).

## Charakterbilder per URL
- Neuer Manager für direkte Bildlinks (JPG/PNG/WEBP).
- Bilddatei wird beim Speichern geprüft, auf JPEG normalisiert und lokal abgelegt.
- Die URL wird in `portrait_links.json` gespeichert; das Bild ist zusätzlich in `portraits/` vorhanden und wird in portable Backups aufgenommen.
- Linkbild und manueller Upload ersetzen sich gegenseitig, damit klar ist, welche Quelle aktiv ist.

## Datenkorrektur
- Edward Newgate / Whitebeard: Fivefold-Teufelsfruchtwert von 0 auf 100 korrigiert; Begründung nennt ausdrücklich die Gura Gura no Mi.

## Technische Hinweise
- Klassischer Auktionsmodus, Fivefold-Budget (20 €), drei Rückgaben zu je 1 € sowie vorhandene Spielhistorien bleiben erhalten.
- Unterstützte Startstände aus 3.5 bleiben importierbar.
- Python-Syntax und JSON-Strukturen werden vor Auslieferung geprüft.

## Zusätzliche Korrekturen nach Nutzerfeedback
- Im Charakterpool besitzt jede Figur jetzt einen eigenen Button **„Werte ansehen“**. Ein Klick öffnet ein vollständiges Profil, ohne den laufenden Draft zurückzusetzen oder die Figur zu ziehen.
- Das Profil zeigt Power Level, Kopfgeld, Haki inklusive Einzeltypen und Status, Fähigkeiten/Nutzwert, Angriff, Defensive, Tempo, Ausdauer, Konterhinweise sowie die Fivefold-Kategorien und deren Begründungen.
- Der Suchindex umfasst nun auch hinterlegte Fruchtnamen und Fivefold-Begründungen.
- Bestätigte Fruchtnamen werden sichtbar dargestellt. Whitebeards Gura Gura no Mi ist ausdrücklich als **Beben-Beben-Frucht** gelistet und hat Fivefold-Teufelsfrucht **100/100**.
- Warcury, Nusjuro, Mars und Ju Peter haben statt eines irreführenden Fruchtwerts 0 vorsichtige, ausdrücklich unsichere Modellwerte, weil ihre gezeigten Bestienformen zwar mutmaßlich mythische Zoan-Kräfte darstellen, aber keine konkreten Fruchtnamen bestätigt sind.
- Profile werden im Charakter-Explorer nur einmal je Charakter und Seitenlauf berechnet. Externe Google-Fonts werden nicht mehr geladen, damit die Oberfläche ohne zusätzlichen Font-Netzwerkaufruf startet.
- Die Startdatei prüft Abhängigkeiten zuerst und führt `pip install` nur aus, wenn erforderliche Pakete fehlen – nicht bei jedem Start erneut.
