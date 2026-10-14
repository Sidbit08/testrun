# Through The Void — Web CTF

A five-stage astronomy-themed CTF based on the requested source-code/URL puzzle style.

## Flow

Home → Level 1 → Access Gate 2 → Level 2 → Access Gate 3 → Level 3 → Access Gate 4 → Level 4 → Access Gate 5 → Level 5 → Access Gate 6 → Final.

Each gate is validated on the server. Wrong credentials redirect to the Home-style `ERROR 404: Wrong input provided` page.

## Challenge mechanics

1. **Linking problem!!** — centered image with a clickable white hotspot. Source contains the next route and password clue.
2. **Light it up** — open the image in a new tab, change `.png` to `.gif`, then invert the PNG to identify Rigel. The `.gif` URL is an HTML clue page.
3. **The Light Falls, the Dark illuminates** — the page background contains a black/white 8-bit ASCII pattern. `1 = black`, `0 = white`.
4. **A Silent Voice** — open the PNG, change `.png` to `.gif`, then follow the Morse audio link. The audio decodes to “THE EYE OF THE BULL IN THE SKY”.
5. **Seven In The Void** — image-name URL `/seven-in-the-void` reveals the binary clue. The physical shift-key clue is left for the player.

## Security model

- Challenge answers live only in `backend/secrets.py` on the server.
- No answer-validation API is exposed to the browser.
- Direct stage skipping is blocked by the session's `unlocked` value.
- The frontend contains only intentional puzzle clues/routes.
- The session uses a signed cookie; the database stores the server-side progression.
- SQLite is configured with WAL + busy timeout for concurrent players.

No ordinary website can reliably determine whether a player is using an external AI assistant. This build therefore does not claim to detect every AI tool. If you later want bot/automation defenses, put them at the reverse proxy/WAF layer rather than trying to identify “AI” from the browser.

## Local run

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Cloud run

For ~100 simultaneous users, a small VM/container with 2 Uvicorn workers is enough for this workload. For multiple application replicas, move the player table to PostgreSQL and use a shared session strategy.

Before deployment, set a long random `SESSION_SECRET` and enable HTTPS.

## Replace the temporary images

The placeholder assets are in `static/assets/`:

- `vishwa-placeholder.svg`
- `stage1.svg`
- `stage2.png`
- `stage3-constellation.svg`
- `stage3-binary.png`
- `stage4.png`
- `stage5.svg`
- `final-sky.svg`

The temporary ambient audio is `ambient.wav`; the Morse challenge audio is `morse.wav`.

## Organizer credentials

Stored only in `backend/secrets.py`:

- Gate 2: The Brightest / Sirius
- Gate 3: Orion / Rigel
- Gate 4: Orion / Betelgeuse
- Gate 5: Taurus / Aldebaran
- Gate 6: Taurus / Pleiades
