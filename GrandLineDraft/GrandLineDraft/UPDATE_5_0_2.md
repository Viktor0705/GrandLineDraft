# Grand Line Draft 5.0.2 – Update, Online-Rad und Cloud-Bilder

## Was ist neu?

- Classic- und Fivefold-Rad nutzen eine gemeinsame, in Supabase gespeicherte Startzeit. Beide Browser starten die clientseitige Animation ungefähr synchron.
- Der Online-Poll lädt einmal pro Sekunde nur kompakte Raum-Metadaten. Der vollständige Spielzustand wird nur bei einer neuen Revision übertragen.
- Die lokale Autosave-Datei wird nur geschrieben, wenn sich der gespeicherte Spielzustand geändert hat.
- Direkte Bildlinks und manuelle Porträt-Uploads werden nach Einrichtung des Cloud-Schemas automatisch in Supabase Storage gespeichert.
- Vorhandene Porträts können als ZIP importiert werden. Auch ein Komplett-Backup-ZIP der alten App kann verwendet werden: Der Importer liest darin nur passende Dateien unter `portraits/`.
- Der Storage-Bucket bleibt privat; alle Storage-Aufrufe laufen serverseitig über Streamlit Secrets.

## Wichtiger Schritt vor dem Update: bestehende Bilder sichern

Wenn in der aktuell laufenden 5.0.1-App bereits eigene Porträts vorhanden sind, öffne zuerst die alte App und nutze in der Seitenleiste `Komplett-Backup erzeugen` und danach `Komplett-Backup herunterladen`. Bewahre diese ZIP-Datei auf. Sie kann nach dem Update direkt über den Cloud-Bilder-Importer hochgeladen werden.

Wenn deine Porträts nur in einem lokalen Windows-Projektordner vorhanden sind, zippe alternativ den Ordner `GrandLineDraft/portraits`.

## A. Supabase Storage einmalig einrichten

1. Supabase Dashboard öffnen und das richtige GrandLineDraft-Projekt wählen.
2. Links `SQL Editor` öffnen, `New Query` wählen.
3. Den Inhalt aus `cloud_portraits_schema.sql` einfügen.
4. `Run` klicken.
5. Unter `Storage` muss der private Bucket `gld-character-portraits` erscheinen; im `Table Editor` die Tabelle `gld_character_portraits`.

Das bestehende `gld_online_rooms`-Schema bleibt unverändert. `cloud_portraits_schema.sql` ist ein zusätzliches Skript und muss nur einmal ausgeführt werden.

## B. GitHub-Webrepository aktualisieren

1. Diese ZIP-Datei herunterladen und lokal entpacken.
2. Den inneren Projektordner `GrandLineDraft` öffnen. Dort liegt direkt `app.py`.
3. Vorher sichern, dass in der bisherigen Streamlit-App keine nicht exportierten Porträts mehr liegen (siehe Backup oben).
4. GitHub im Browser öffnen und das private Repository `GrandLineDraft` aufrufen.
5. `Add file` → `Upload files` wählen.
6. Den Inhalt des inneren Projektordners auswählen und auf die Upload-Fläche ziehen. Vorhandene Dateien werden aktualisiert, neue Dateien wie `cloud_portraits_schema.sql` und Tests hinzugefügt.
7. Prüfen, dass `.streamlit/secrets.toml` NICHT im Upload erscheint. Die echte Datei bleibt ausschließlich in Streamlit Secrets. `secrets.toml.example` darf hochgeladen werden.
8. Commit auf `main` erstellen. Streamlit Community Cloud startet danach automatisch ein neues Deployment.

Wichtig: Die Inhalte des Projektordners hochladen, nicht die ZIP-Datei als einzelne Datei und nicht den übergeordneten Ordner. `app.py` muss im Repository-Hauptverzeichnis liegen.

## C. Vorhandene Porträts in Supabase übertragen

1. Nach erfolgreichem Streamlit-Deployment die App öffnen.
2. In der Seitenleiste `Eigene Charakterbilder hinzufügen / ersetzen` öffnen.
3. Den Expander `Gemeinsame Cloud-Bilderdatenbank · Supabase Storage` öffnen.
4. Prüfen, dass `Cloud-Bildertabelle erreichbar` erscheint.
5. Bei `Lokales portraits-Archiv (.zip)` die zuvor erzeugte Komplett-Backup-ZIP oder das ZIP deines `portraits`-Ordners auswählen.
6. `Bilderarchiv in die Cloud übertragen` klicken.
7. Die Anzeige `Bilder in der Cloud` kontrollieren.

Der Importer liest keine beliebigen Dateien aus dem ZIP aus. Er akzeptiert nur bekannte Porträt-Dateinamen wie `manual_character_001.jpg`, `linked_character_001.jpg` und `character_001_<hash>.jpg` unter einem `portraits/`-Pfad. Bilder werden auf maximal 620 × 800 Pixel optimiert und als JPEG gespeichert.

## D. Künftige Bilder

Nach der Einrichtung werden neue manuelle Bild-Uploads und direkte Bildlinks automatisch in Supabase Storage hochgeladen. Auf anderen Geräten lädt die App dasselbe zentrale Porträt. Der Bucket ist privat, und der geheime Supabase-Schlüssel wird nicht an den Browser weitergegeben.

## E. Multiplayer-Test

1. Zwei Geräte öffnen dieselbe veröffentlichte App.
2. Spieler A erstellt eine Online-Lobby und teilt den 8-stelligen Code.
3. Spieler B tritt bei.
4. In Classic Draft und Fivefold jeweils einmal ziehen. Beide Browser sollten die Rad-Animation mit derselben geplanten Startzeit anzeigen.
5. Anschließend Auktion / Fivefold-Zuordnung testen.

## Grenzen und Sicherheit

- Die App führt Streamlit serverseitig in der Cloud aus; dein Laptop hostet nichts.
- Der GitHub-Code bleibt privat und die App-Freigabe sollte auf bekannte Personen beschränkt bleiben.
- `service_role_key` darf niemals in GitHub committed oder clientseitig verwendet werden.
- Die bestehende Lobby ist weiterhin ein Freundes-Prototyp mit Raumcode, keine gehärtete öffentliche Turnierplattform. Für offene öffentliche Lobbys wären Supabase Auth, serverseitige Zugvalidierung, Rate Limits und Moderation nötig.
- Die erste Anzeige eines noch nicht gecachten Cloud-Bildes benötigt einen Storage-Download. Danach hält Streamlit die optimierten Bildbytes im Cache.
