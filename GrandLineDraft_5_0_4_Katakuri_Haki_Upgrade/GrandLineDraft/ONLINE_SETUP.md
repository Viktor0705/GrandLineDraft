# Online-Modus einrichten (Supabase)

Grand Line Draft 5.0 enthält einen serverseitigen Online-Lobby-Prototyp für Classic Draft und Fivefold Ranking. Lokales Spiel und KI-Modus funktionieren ohne Online-Dienst. Für echte Verbindungen zwischen zwei Geräten ist eine Supabase-Datenbank erforderlich.

## 1. Supabase-Projekt

1. Ein Supabase-Projekt anlegen: https://supabase.com/
2. Im SQL Editor den vollständigen Inhalt von `online_schema.sql` ausführen.
3. Unter Project Settings → API die Project URL und den `service_role`-Key kopieren.

## 2. Lokal konfigurieren

1. `.streamlit/secrets.toml.example` nach `.streamlit/secrets.toml` kopieren.
2. `url` und `service_role_key` mit den eigenen Werten ersetzen.
3. App neu starten und im Spielmenü `Online · Lobby` wählen.
4. Raum erstellen und den angezeigten achtstelligen Raumcode an den zweiten Spieler schicken.
5. Der zweite Spieler wählt `Online · Lobby` und tritt mit dem Code bei.

Alternativ können die Umgebungsvariablen `SUPABASE_URL` und `SUPABASE_SERVICE_ROLE_KEY` gesetzt werden.

## 3. Öffentlich hosten

Die Streamlit-App kann beispielsweise über Streamlit Community Cloud, Render oder Railway bereitgestellt werden. Die Supabase-Werte müssen beim Hosting-Anbieter als serverseitige Secrets hinterlegt werden. `secrets.toml` und der Service-Role-Key dürfen niemals in ein öffentliches Git-Repository oder in clientseitiges JavaScript gelangen.

Eine eigene Domain ist optional. Die Hosting-Plattform stellt zunächst eine öffentliche Standard-URL bereit.

## Sicherheits- und Funktionsgrenzen

- Das Room-Payload wird serverseitig über die Supabase REST API gelesen und geschrieben. Der Service-Role-Key wird nicht an den Browser übergeben.
- Lobbycodes sind Einladungslinks in Kurzform, aber keine Benutzerkonten. Jeder, der den Code kennt, kann versuchen beizutreten.
- Die App nutzt `revision` für optimistische Schreibkonflikt-Erkennung. Das ist ein kleiner Multiplayer-Prototyp, keine gehärtete Turnierplattform.
- Für einen öffentlichen Wettbewerb sollten zusätzlich Supabase Auth, serverseitige RPC-Funktionen mit atomarer Zugvalidierung, Rate Limits, Moderation, Missbrauchsschutz und ein Ablauf-/Löschprozess implementiert werden.
- Räume laufen nach 24 Stunden ab. Abgelaufene Zeilen können regelmäßig mit `delete from public.gld_online_rooms where expires_at < now();` entfernt werden.
- Ohne konfigurierte Supabase-Verbindung bleibt Online deaktiviert; es wird kein lokaler Mehrspieler als echter Online-Modus ausgegeben.


## 4. Gemeinsame Charakterbilder (Supabase Storage)

1. Im Supabase SQL Editor zusätzlich `cloud_portraits_schema.sql` ausführen. Das Skript erstellt den privaten Storage-Bucket `gld-character-portraits` und die Tabelle `gld_character_portraits`.
2. Der Bucket bleibt **privat**. Die App lädt Bilder serverseitig mit dem Streamlit-Secret; der Service-Role-Key wird nicht an den Browser übergeben.
3. In der veröffentlichten App unter `Eigene Charakterbilder hinzufügen / ersetzen` den Expander `Gemeinsame Cloud-Bilderdatenbank` öffnen.
4. Für vorhandene Bilder vom PC: den Inhalt des lokalen Ordners `portraits` als ZIP packen und über `Lokales portraits-Archiv (.zip)` hochladen. Die Dateinamen müssen dem App-Schema entsprechen, z. B. `manual_character_001.jpg`, `linked_character_001.jpg` oder `character_001_<8-stelliger-hash>.jpg`.
5. Neue Bilder per Link oder Upload werden anschließend automatisch in Supabase Storage übertragen. Ein Cloud-Bild wird auf weiteren Geräten aus dem privaten Bucket geladen und im App-Cache zwischengespeichert.

Die Cloud-Bildertabelle enthält Charakter-ID, Anzeigename, Storage-Pfad, Dateigröße, Quelle und Änderungszeit. Das Importprogramm liest ZIP-Einträge ohne sie auf dem Server zu entpacken und akzeptiert nur passende Bilddateinamen.

## 5. Online-Animation und Performance

- Online-Polling fragt regelmäßig nur kleine Metadaten (Revision, Status, Spielernamen) ab. Der vollständige Spielstand wird nur geladen, wenn sich die Revision geändert hat.
- Classic Draft verwendet jetzt dieselbe browserseitige Rad-Komponente wie Fivefold. Die Ziehung wird als gemeinsame `spinning`-Phase gespeichert, sodass beide Online-Geräte die Animation sehen. Nur der Spieler, der gerade zieht, darf das Ergebnis festschreiben.
- Die Rad-Animation läuft clientseitig und blockiert den Python-Server nicht mit `time.sleep`-Schleifen.


## 6. Update 5.0.2 – Performance, gemeinsames Rad und Cloud-Bilder

- Beim Online-Polling werden nur Raum-Metadaten geladen; der große Spielstand wird erst bei einer neuen Revision abgerufen. Die Metadaten werden alle 0,5 Sekunden abgefragt.
- Beide Browser erhalten dieselbe absolute Startzeit der Rad-Animation. Die nicht ziehende Sitzung übernimmt einen Spin-Status auch dann, wenn ein lokaler Session-Hash leicht abweicht.
- Direkte Bild-URLs und manuelle Uploads werden automatisch hochgeladen, sobald der private Storage-Bucket und die Tabelle eingerichtet sind.
- Für geräteübergreifende Porträts `cloud_portraits_schema.sql` einmal im Supabase SQL Editor ausführen. Danach in der App den Expander `Gemeinsame Cloud-Bilderdatenbank` öffnen und den lokalen `portraits`-Ordner als ZIP importieren.
- Die Bilder sind im privaten Bucket; Zugriff erfolgt serverseitig über Streamlit Secrets. Den Service-Role-Key niemals in GitHub oder clientseitigen Code hochladen.
