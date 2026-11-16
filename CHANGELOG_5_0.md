# Grand Line Draft 5.0 — Peak Edition

## Inhalt
- Einheitlicher Pool mit 135 eindeutigen Charakteren; 15 Ergänzungen mit stabilen IDs 151–165.
- Peak-/Prime-Bewertungen mit Manga-Cutoff Kapitel 1197 (01.11.2026).
- Haki-Datenregel verschärft: Typbestätigung und numerische Meisterschaft werden getrennt; nicht quantifizierbare Meisterschaft bleibt unbekannt.
- Fivefold zeigt unbekanntes Haki als `?`, nutzt für den gleich gewichteten Enddurchschnitt intern neutral 50 und kennzeichnet das.
- 9.045 Matchups, je 15.000 aggregierte Monte-Carlo-Ergebnisziehungen (135.675.000 insgesamt).
- Matchup-Richtungslogik, enger Vergleich Shanks/Mihawk, Kaido knapp vor Gear-5-Ruffy, Queen knapp vor Doflamingo und abgesenktes Katakuri-Rating.
- Spielumgebungs-Auswahl: lokal, KI oder Online-Lobby.
- Server-seitige Supabase REST-Anbindung als Online-Prototyp, Raumcode, Revision und periodische Synchronisierung.
- Migration älterer aktiver 120er-Spielstände: neue unclaimed Charaktere werden automatisch dem verbleibenden Pool hinzugefügt.

## Neue Charaktere
Charlotte Smoothie, Charlotte Oven, Charlotte Daifuku, Charlotte Snack, Urouge, Edward Weevil, Vista, Jozu, S-Hawk, S-Snake, S-Bear, S-Shark, Limejuice, Shepherd Sommers und Rimoshifu Killingham.

## Grenzen
- Die Simulationen sind keine tatsächlichen KI-gesteuerten Kampfverläufe, sondern vorab berechnete binomiale Monte-Carlo-Ergebnisziehungen auf Basis eines Matchup-Wahrscheinlichkeitsmodells.
- Der Online-Modus erfordert Supabase-Konfiguration; ohne diese bleiben Offline/KI vollständig nutzbar. Der mitgelieferte Online-Modus ist ein Prototyp, kein abgesichertes Ranked-/Turniersystem.
- Streamlit wurde in der Build-Umgebung nicht installiert, daher wurde kein vollständiger Browser-Live-Test durchgeführt.
