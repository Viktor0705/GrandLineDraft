# Grand Line Draft 5.0.2 – Online Performance & Cloud Portraits

- Classic Draft wheel no longer blocks the Streamlit server with a Python `time.sleep` animation. It uses the browser component shared with Fivefold.
- Online clients receive the same `spinning` state. Only the session belonging to the current spinner commits the card after the synchronized animation window.
- Online polling fetches small room metadata every second and downloads the full payload only when the revision changes.
- PATCH responses return only room metadata fields.
- Local autosave skips disk writes when the canonical game-state hash has not changed.
- Added private Supabase Storage bucket and `gld_character_portraits` metadata table.
- Added one-time ZIP import for existing local portraits.
- New manual uploads and direct image links are automatically uploaded to Supabase Storage when configured.
- Cloud images are cached server-side and shown on all devices.

## Setup

1. Run `cloud_portraits_schema.sql` once in Supabase SQL Editor.
2. Commit the updated app and files to the private GitHub repository.
3. Wait for Streamlit Community Cloud to redeploy.
4. Open the image manager and import a ZIP of the local `portraits/` folder from your PC.
5. Use the Cloud Portraits panel to verify the number of stored images.

Keep the Supabase service-role secret only in Streamlit Secrets. Do not make the app publicly accessible until authentication, server-side action validation and rate limiting have been added.
