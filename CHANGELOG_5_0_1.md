# Grand Line Draft 5.0.1 – Charakterpool-Fehlerbehebung

## Behoben
- Die Charakterpool-Suche verarbeitet optionale Felder mit `null`/`None` jetzt sicher.
- Fehlende Teufelsfruchtnamen und optionale Begründungstexte führen nicht mehr zu einem `TypeError` beim Zusammenführen der Suchbegriffe.
- Verschachtelte Werte wie Listen und Dictionaries werden für die Suche robust in Text umgewandelt.
- Fehlende Haki-Listen werden als leere Liste behandelt.
- Bei der Sortierung nach Haki werden Charaktere mit unbekannter quantitativer Haki-Meisterschaft hinter Figuren mit numerischem Haki-Wert eingeordnet; „unbekannt“ wird nicht als 0 dargestellt.
- Optionale Haki-Detailfelder werden beim Laden des Charakterprofils normalisiert.

## Unverändert
- Charakterdaten, IDs und Bewertungen
- Classic Draft und Fivefold Ranking
- Online-Konfiguration und Supabase-Schema
- Bilder, Bildlinks und Spielstandsformat
