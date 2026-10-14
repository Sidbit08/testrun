import os, secrets, sqlite3, time
from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

BASE = Path(__file__).resolve().parent
DB = Path(os.getenv("CTF_DB", str(BASE / "ctf.db")))
DB.parent.mkdir(parents=True, exist_ok=True)

from backend.secrets import CREDENTIALS

app = FastAPI(title="Through The Void")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SESSION_SECRET", "change-this-before-deployment"),
    max_age=60 * 60 * 12,
    same_site="lax",
    https_only=os.getenv("HTTPS_ONLY", "0") == "1",
)
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")

STAGE_INFO = {
    1: ("Linking problem!!", "Easy"),
    2: ("Light it up", "Moderate"),
    3: ("The Light Falls, the Dark illuminates", "Moderate"),
    4: ("A Silent Voice", "Hard"),
    5: ("Seven In The Void", "Hard"),
}

STAGE3_BINARY = "01010100 01101000 01100101 00100000 01001000 01110101 01101110 01110100 01100101 01110010 00100111 01110011 00100000 01010010 01100101 01100100 00100000 01010011 01101000 01101111 01110101 01101100 01100100 01100101 01110010"
STAGE5_BINARY = "01110010 01100111 01110111 00100000 01100001 01110111 01100011 01110111 01100010 00100000 01110110 01110111 01110100 01101001 01100010 01110011 00100000 01110010 01100111 01110111 00100000 01110110 01111001 01101011 01101011 01100001 00100000 01110111 01110100 01110111"


def db():
    con = sqlite3.connect(DB, timeout=15)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA synchronous=NORMAL")
    con.execute("PRAGMA busy_timeout=15000")
    con.execute("""CREATE TABLE IF NOT EXISTS players(
        session_id TEXT PRIMARY KEY,
        callsign TEXT NOT NULL,
        unlocked INTEGER NOT NULL DEFAULT 1,
        started_at INTEGER NOT NULL,
        updated_at INTEGER NOT NULL
    )""")
    return con


def player(request):
    sid = request.session.get("sid")
    if not sid:
        return None
    con = db()
    row = con.execute("SELECT session_id,callsign,unlocked FROM players WHERE session_id=?", (sid,)).fetchone()
    con.close()
    return row


def render(name, **values):
    html = (BASE / "templates" / name).read_text(encoding="utf-8")
    for k, v in values.items():
        html = html.replace("{{" + k + "}}", str(v))
    return HTMLResponse(html)


def advance(request, unlocked):
    p = player(request)
    if not p:
        return
    con = db()
    con.execute("UPDATE players SET unlocked=?,updated_at=? WHERE session_id=? AND unlocked<?", (unlocked, int(time.time()), p[0], unlocked))
    con.commit()
    con.close()


def bad_credentials():
    return RedirectResponse("/error-404", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def home():
    return render("index.html")

@app.post("/start", response_class=HTMLResponse)
async def start(request: Request, callsign: str = Form(...)):
    callsign = callsign.strip()
    if not 2 <= len(callsign) <= 32:
        return render("index.html", error="Enter a callsign between 2 and 32 characters.")
    sid = secrets.token_urlsafe(32)
    now = int(time.time())
    con = db()
    con.execute("INSERT INTO players(session_id,callsign,unlocked,started_at,updated_at) VALUES(?,?,?,?,?)", (sid, callsign, 1, now, now))
    con.commit(); con.close()
    request.session["sid"] = sid
    request.session["callsign"] = callsign
    return RedirectResponse("/stage/1", status_code=303)

@app.get("/stage/{stage}", response_class=HTMLResponse)
async def stage(request: Request, stage: int):
    p = player(request)
    if not p:
        return RedirectResponse("/")
    if stage < 1 or stage > 5:
        return RedirectResponse("/error-404")
    if p[2] < stage:
        return RedirectResponse(f"/stage/{p[2]}")
    return render(f"stage{stage}.html", callsign=p[1], binary=(STAGE3_BINARY if stage == 3 else STAGE5_BINARY))

@app.get("/access/{target}", response_class=HTMLResponse)
async def access(request: Request, target: int):
    p = player(request)
    if not p:
        return RedirectResponse("/")
    # Stage 1 exposes /access/2, stage 2 exposes /access/3, etc.
    if target < 2 or target > 6 or target != p[2] + 1:
        return RedirectResponse(f"/stage/{min(max(p[2],1),5)}")
    title = "The Winter Sky" if target == 6 else STAGE_INFO[target][0]
    return render("access.html", target=target, title=title, error="")

@app.post("/access/{target}", response_class=HTMLResponse)
async def access_submit(request: Request, target: int, username: str = Form(...), password: str = Form(...)):
    p = player(request)
    if not p:
        return RedirectResponse("/")
    if target < 2 or target > 6 or target != p[2] + 1:
        return RedirectResponse(f"/stage/{min(max(p[2],1),5)}")
    expected_user, expected_pass = CREDENTIALS[target]
    if username.strip().casefold() != expected_user.casefold() or password.strip().casefold() != expected_pass.casefold():
        return bad_credentials()
    advance(request, 5 if target == 6 else target)
    return RedirectResponse("/final" if target == 6 else f"/stage/{target}", status_code=303)

@app.get("/final", response_class=HTMLResponse)
async def final(request: Request):
    p = player(request)
    if not p or p[2] < 5:
        return RedirectResponse(f"/stage/{p[2] if p else 1}")
    return render("final.html", callsign=p[1])

@app.get("/error-404", response_class=HTMLResponse)
async def error_404():
    return render("error404.html")

# Challenge-specific "URL tricks". These intentionally do not expose credentials.
@app.get("/clues/stage2.png")
async def stage2_png():
    return FileResponse(BASE / "static/assets/stage2.png", media_type="image/png")

@app.get("/clues/stage4.png")
async def stage4_png():
    return FileResponse(BASE / "static/assets/stage4.png", media_type="image/png")

@app.get("/clues/stage2.gif", response_class=HTMLResponse)
async def stage2_gif_clue(request: Request):
    if not player(request): return RedirectResponse("/")
    return render("stage2gif.html")

@app.get("/clues/stage4.gif", response_class=HTMLResponse)
async def stage4_gif_clue(request: Request):
    if not player(request): return RedirectResponse("/")
    return render("stage4gif.html")

@app.get("/seven-in-the-void", response_class=HTMLResponse)
async def stage5_hidden(request: Request):
    if not player(request): return RedirectResponse("/")
    return render("stage5hidden.html", binary=STAGE5_BINARY)

@app.get("/robots.txt")
async def robots():
    return Response("User-agent: *\nDisallow: /\n", media_type="text/plain")

@app.get("/api/health")
async def health():
    return {"ok": True}
