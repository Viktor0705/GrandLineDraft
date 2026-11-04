# Performance-Update 5.0.3

## Was bremste bisher?

1. `character_ratings.json` enthielt neben 135 Profilen auch 9.045 Matchup-Objekte. Dadurch musste die App beim ersten Zugriff auf Profildaten eine große JSON-Datei lesen und parsen, obwohl die Matchups in vielen Sitzungen gar nicht gebraucht werden.
2. Der Charakterpool baute Suchtexte und Profilansichten bei jeder Streamlit-Ausführung erneut auf.
3. Private Cloud-Bilder konnten auf einer neuen Sitzung nacheinander statt parallel geladen werden.
4. Karten übertrugen größere Portrait-Bytes auch in kleinen Rasterkarten.
5. Die Persistenz-/Hash-/Online-Sync-Schutzroutine wurde zweimal je vollständigem App-Lauf aufgerufen.
6. Eine 1,25-Sekunden-Radvorlaufzeit war bei 1-Sekunden-Online-Polls zu knapp für zuverlässige gemeinsame Animation.

## Was 5.0.3 ändert

- Matchup-Tabelle in `matchup_results.json.gz` separiert und lazy geladen. Unveränderte Daten, keine neue Simulation und kein Verlust von Wahrscheinlichkeiten.
- Caching für statische Charakterprofile, Fivefold-Profile und Suchindex.
- Batch-/Parallel-Downloads für aktuell sichtbare Cloud-Portraits; keine 135 Bilder werden beim Start geladen.
- Thumbnail-Bilder für Listen/Teams, Vollbild im Detail.
- Keep-Alive für Supabase REST-Verbindungen.
- Nur noch eine End-of-run Persistenzroutine je vollständigem Seitenlauf.
- 2,5 Sekunden gemeinsamer Radvorlauf, damit beide Clients den neuen Spin-Zustand vor Animationsbeginn erhalten.

## Was gleich bleibt

- 135 Charaktere und ihre Bewertungen.
- 9.045 Paarungen mit jeweils 15.000 Ergebnisziehungen.
- Classic Draft und Fivefold Ranking.
- Budget, Auktionen und Rückgaberegeln.
- Supabase-Tabellen, Storage-Bucket, Raumcodes und bestehende Streamlit-Secrets.

## Deployment

1. Vor dem Update sicherstellen, dass der GitHub-Branch `main` den bisherigen Stand enthält.
2. Den Inhalt des 5.0.3-Projektordners über GitHub `Add file → Upload files` aktualisieren.
3. `.streamlit/secrets.toml` NICHT hochladen.
4. Streamlit Cloud deployt nach Commit neu. Die bestehenden Secrets bleiben erhalten.
5. Mit zwei Geräten einen neuen Raum erstellen und Classic/Fivefold jeweils eine Runde testen.

## Erwartete Wirkung

Der Start-/Profilpfad liest eine deutlich kleinere JSON-Datei (Matchups werden nicht beim App-Start geparst). Kartenansichten übertragen kleinere Thumbnails. Auf einem frischen Browser kann der erste Cloud-Bildsatz parallel geladen werden. Die reale Ladezeit hängt weiterhin von Streamlit-Ressourcen, Netzwerk und Supabase-Region ab; dies ist kein Versprechen fester Millisekundenwerte.
