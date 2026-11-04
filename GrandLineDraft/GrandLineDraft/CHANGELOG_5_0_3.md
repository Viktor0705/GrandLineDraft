# Grand Line Draft 5.0.3 – Performance Edition

## Optimierungen

- Große 9.045er-Matchup-Tabelle aus `character_ratings.json` ausgelagert und gzip-komprimiert. Die Matchups werden erst beim Zugriff auf die Team-/Duell-Auswertung geladen. Die vollständigen Paarungen und 15.000 Ergebnisziehungen je Paarung bleiben erhalten.
- Charakterprofile und Fivefold-Profile werden als reine, datenabhängige Funktionen über Streamlit Cache zwischengespeichert.
- Volltext-Suchindex des Charakterpools wird nur einmal erstellt. Suchinteraktionen nutzen anschließend vorgefertigte Zeichenketten.
- Cloud-Porträts der aktuell sichtbaren Team-/Poolkarten werden parallel vorab geladen und in einem Batch-Cache gehalten.
- Charakterkarten verwenden kompakte JPEG-Thumbnails; das Profil behält die größere Version.
- Supabase REST verwendet Keep-Alive-Sessions je Worker-Thread.
- Doppelte Persistenz-/Hash-/Online-Sync-Ausführung pro vollständigem Seitenlauf entfernt.
- Gemeinsame Rad-Startzeit auf 2,5 Sekunden Vorlauf erhöht, damit der zweite Client den Spin vor Start über sein 1-Sekunden-Polling erhalten kann.

## Datenkompatibilität

`character_ratings.json` enthält nur Charakterprofile, Quellen und Bewertungsmethodik. `matchup_results.json.gz` enthält unverändert alle 9.045 eindeutigen Paarungen. Alte Datenstände ohne die GZIP-Datei werden weiterhin unterstützt.

## Sicherheit / Deployment

- `.streamlit/secrets.toml` bleibt ausgeschlossen. Bestehende Streamlit-Cloud-Secrets müssen nicht geändert werden.
- Keine Supabase-Schemaänderung notwendig.
- Bestehende GitHub-Dateien können mit dieser Version überschrieben werden; das Repository bleibt privat.

## Tests

Die Datenintegritäts-, Cloud-Portrait-, Spin- und Performance-Tests prüfen die vorhandenen 135 Charaktere, alle 9.045 Paarungen, 15.000 Durchläufe je Paarung sowie die Trennung der Matchup-Daten vom Start-Payload. Ein Live-Latenztest auf Streamlit Cloud ist umgebungsabhängig und muss nach Deployment mit zwei Geräten erfolgen.
