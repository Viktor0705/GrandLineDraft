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
