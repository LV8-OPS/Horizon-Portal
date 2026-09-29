from pathlib import Path
from typing import Any
import os
import uuid

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .database import Base, SessionLocal, engine
from . import models
from .crud import seed, authenticate_user, get_user, get_user_by_auth_id, register_user
from sqlalchemy import text

from .security import SESSION_COOKIE, create_token, decode_token, hash_password, verify_password
from .crud import theme_entitlements
from .routers import admin, auth, creators as creators_api, downloads as downloads_api, themes as themes_api, discord as discord_api, launcher as launcher_api

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="Horizon Portal", version="1.0.0")


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # Block cross-origin state-changing browser requests when Origin is present.
    if request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlsplit
            origin_host = urlsplit(origin).netloc.lower()
            request_host = request.headers.get("host", "").lower()
            tauri_origin = origin_host in {"tauri.localhost", "localhost", "127.0.0.1"}
            if not origin_host or (origin_host != request_host and not tauri_origin):
                from fastapi.responses import JSONResponse
                return JSONResponse({"detail": "Cross-origin request blocked."}, status_code=403)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    return response


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

NAV = [("workshop", "/workshop"), ("creators", "/creators"), ("download", "/download"), ("account", "/account")]

TEXT = {
    "en": {
        "site_name": "Horizon Portal",
        "slogan": "Beyond the Horizon",
        "home": "Home",
        "workshop": "Workshop",
        "creators": "Creators",
        "download": "Download",
        "account": "Account",
        "login": "Sign in",
        "register": "Create account",
        "welcome": "Build beyond limits.",
        "subtitle": "A centralized home for Destiny modded projects, creators and players.",
        "what_is": "What is Horizon Portal?",
        "what_is_desc": "Horizon Portal brings discovery, installation and community support into one clean experience instead of scattering everything across websites and Discord channels.",
        "explore": "Explore the Workshop",
        "creator_program": "Creator Program",
        "download_btn": "Download Horizon Portal",
        "discord_btn": "Join Discord",
        "account_title": "Your account",
        "account_intro": "Manage your profile, language and account access.",
        "creator_title": "Creator Program",
        "creator_intro": "Publish quality Destiny modded projects and give players a clear way to discover your work.",
        "download_title": "Horizon Portal",
        "download_intro": "Install the Windows launcher and use Horizon Portal as your central entry point.",
        "download_box": "Download the .exe",
        "version": "Version",
        "size": "Size",
        "system": "Supported system",
        "tutorial": "Quick install",
        "workshop_title": "Workshop",
        "settings": "Settings",
        "inbox": "Inbox",
        "support": "Need help? Join Discord",
        "linux": "Linux support is planned for a future release.",
        "free": "Free Access",
        "donator": "Donator",
        "corrupted": "Corrupted",
        "aria": "Aria",
        "creator_role": "Creator",
        "legacy": "Legacy",
    },
    "fr": {
        "site_name": "Horizon Portal",
        "slogan": "Beyond the Horizon",
        "home": "Accueil",
        "workshop": "Workshop",
        "creators": "Creators",
        "download": "Téléchargement",
        "account": "Compte",
        "login": "Connexion",
        "register": "Créer un compte",
        "welcome": "Build beyond limits.",
        "subtitle": "Le point central pour les projets Destiny modded, leurs créateurs et leurs joueurs.",
        "what_is": "Qu'est-ce que Horizon Portal ?",
        "what_is_desc": "Horizon Portal rassemble découverte, installation et support communautaire dans une seule expérience claire, au lieu de disperser le contenu entre sites et serveurs Discord.",
        "explore": "Explorer le Workshop",
        "creator_program": "Programme Creator",
        "download_btn": "Télécharger Horizon Portal",
        "discord_btn": "Rejoindre Discord",
        "account_title": "Votre compte",
        "account_intro": "Gérez votre profil, votre langue et vos options de connexion.",
        "creator_title": "Programme Creator",
        "creator_intro": "Publiez des projets Destiny modded de qualité et donnez aux joueurs un moyen clair de découvrir votre travail.",
        "download_title": "Horizon Portal",
        "download_intro": "Installez le launcher Windows et utilisez Horizon Portal comme point d'entrée central.",
        "download_box": "Télécharger le .exe",
        "version": "Version",
        "size": "Taille",
        "system": "Système compatible",
        "tutorial": "Installation rapide",
        "workshop_title": "Workshop",
        "settings": "Paramètres",
        "inbox": "Messages",
        "support": "Besoin d'aide ? Rejoindre Discord",
        "linux": "Le support Linux est prévu pour une future version.",
        "free": "Accès gratuit",
        "donator": "Donator",
        "corrupted": "Corrupted",
        "aria": "Aria",
        "creator_role": "Creator",
        "legacy": "Legacy",
    },
}



@app.on_event("startup")
async def startup() -> None:
    Base.metadata.create_all(bind=engine)

    # Lightweight schema migration that works for both SQLite and PostgreSQL.
    from sqlalchemy import inspect
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    additions = {
        "donation_cents": "INTEGER NOT NULL DEFAULT 0",
        "creator_badge": "INTEGER NOT NULL DEFAULT 0",
        "beta_access": "INTEGER NOT NULL DEFAULT 0",
        "discord_id": "VARCHAR(32)",
        "discord_username": "VARCHAR(255) NOT NULL DEFAULT ''",
        "auth_id": "VARCHAR(36)",
        "auth_version": "INTEGER NOT NULL DEFAULT 1",
    }
    for name, definition in additions.items():
        if name not in columns:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {name} {definition}"))

    redeem_columns = {column["name"] for column in inspect(engine).get_columns("redeem_codes")}
    if "redeemed_by_device_id" not in redeem_columns:
        with engine.begin() as conn:
            conn.execute(text("ALTER TABLE redeem_codes ADD COLUMN redeemed_by_device_id VARCHAR(64)"))

    db = SessionLocal()
    try:
        # Backfill immutable auth identities and repair any legacy duplicate
        # Discord identities before enforcing uniqueness.
        users = db.query(models.User).order_by(models.User.id.asc()).all()
        seen_discord = set()
        for user in users:
            if not user.auth_id:
                user.auth_id = str(uuid.uuid4())
            if not user.auth_version:
                user.auth_version = 1
            if user.discord_id:
                discord_id = str(user.discord_id)
                if discord_id in seen_discord:
                    user.discord_id = None
                    user.discord_username = ""
                else:
                    seen_discord.add(discord_id)
        db.commit()

        with engine.begin() as conn:
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_auth_id ON users (auth_id)"
            ))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_users_discord_id ON users (discord_id)"
            ))

        seed(db)
    finally:
        db.close()


app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(discord_api.router, prefix="/api/auth", tags=["discord"])
app.include_router(launcher_api.router, prefix="/api/launcher")
app.include_router(creators_api.router, prefix="/api/creators", tags=["creators"])
app.include_router(downloads_api.router, prefix="/api/downloads", tags=["downloads"])
app.include_router(themes_api.router, prefix="/api/themes", tags=["themes"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


def get_lang(request: Request) -> str:
    return "fr" if request.cookies.get("lang", "en").lower().startswith("fr") else "en"


def tr(request: Request, key: str) -> str:
    language = get_lang(request)
    return TEXT[language].get(key, TEXT["en"].get(key, key))


def current_user(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    payload = decode_token(token)
    if not payload:
        return None
    db = SessionLocal()
    try:
        user = get_user_by_auth_id(db, payload["auth_id"])
        if not user:
            return None
        if int(user.auth_version or 1) != int(payload["auth_version"]):
            return None
        return {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "role": user.role,
            "donation_cents": int(getattr(user, "donation_cents", 0) or 0),
            "creator_badge": bool(getattr(user, "creator_badge", 0)),
            "beta_access": bool(getattr(user, "beta_access", 0)),
            "theme_entitlements": theme_entitlements(user),
        }
    finally:
        db.close()


def context(request: Request, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    data: dict[str, Any] = {
        "request": request,
        "lang": get_lang(request),
        "t": lambda key: tr(request, key),
        "site_name": "Horizon Portal",
        "nav": NAV,
        "user": current_user(request),
    }
    if extra:
        data.update(extra)
    return data


def auth_redirect(request: Request):
    return RedirectResponse(url=f"/login?next={request.url.path}", status_code=303)


def page(request: Request, name: str, extra: dict[str, Any] | None = None) -> HTMLResponse:
    return templates.TemplateResponse(request=request, name=name, context=context(request, extra))


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/me")
async def api_me(request: Request):
    user = current_user(request)
    if not user:
        return {"authenticated": False, "theme_entitlements": ["destiny2", "destiny1", "hive", "cabal", "fallen", "corrupted", "aria"]}
    return {"authenticated": True, **user}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return page(request, "index.html")


@app.get("/workshop", response_class=HTMLResponse)
async def workshop(request: Request):
    return page(request, "workshop.html", {
        "features": ["Discover projects", "Check compatibility", "Follow updates", "Install with confidence"],
        "categories": ["Weapons", "Missions", "D1 Imports", "HUD", "Sandbox", "Utilities"],
    })


@app.get("/creators", response_class=HTMLResponse)
async def creators(request: Request):
    return page(request, "creators.html", {
        "creators": [
            {"name": "Dawn", "slug": "dawn", "description": "Dawn creator pack."},
            {"name": "SunRise", "slug": "sunrise", "description": "SunRise creator pack."},
        ]
    })


@app.get("/creator", response_class=HTMLResponse)
async def creator(request: Request):
    return page(request, "creator.html", {
        "steps": ["Join Discord", "Answer the questionnaire", "Submit your project", "Project review", "Publication"],
        "types": ["Weapons", "D1 imports", "HUD changes", "Raid content", "Mission content", "Utilities"],
    })


@app.get("/download", response_class=HTMLResponse)
async def download(request: Request):
    return page(request, "download.html", {
        "version": "0.2.1 BETA",
        "size": "12.4 MB",
        "system": "Windows 10 / 11",
        "launcher_download_url": "/static/downloads/Horizon%20Manager_0.2.1_x64-setup.exe",
        "steps": ["Download the installer", "Run the .exe", "Install Horizon Manager", "Open the launcher"],
    })


@app.get("/downloads", response_class=HTMLResponse)
async def downloads(request: Request):
    return page(request, "downloads.html")


@app.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    user = current_user(request)
    if not user:
        return auth_redirect(request)
    return page(request, "account.html")


@app.get("/settings", response_class=HTMLResponse)
async def settings(request: Request):
    user = current_user(request)
    if not user:
        return auth_redirect(request)
    message = None
    if request.query_params.get("password_changed") == "1":
        message = "Mot de passe mis à jour avec succès."
    return page(request, "settings.html", {"password_message": message})


@app.post("/account/password")
async def change_password(
    request: Request,
    current_password: str = Form(...),
    new_password: str = Form(...),
    new_password_confirm: str = Form(...),
):
    user_data = current_user(request)
    if not user_data:
        return auth_redirect(request)

    if len(new_password) < 8:
        return page(request, "settings.html", {"password_message": "Le nouveau mot de passe doit contenir au moins 8 caractères."})
    if new_password != new_password_confirm:
        return page(request, "settings.html", {"password_message": "Les nouveaux mots de passe ne correspondent pas."})

    db = SessionLocal()
    try:
        user = get_user(db, user_data["id"])
        if not user or not verify_password(current_password, user.password_hash):
            return page(request, "settings.html", {"password_message": "Le mot de passe actuel est incorrect."})
        user.password_hash = hash_password(new_password)
        # Changing the password revokes every previously copied token.
        user.auth_version = int(user.auth_version or 1) + 1
        db.commit()
    finally:
        db.close()

    return RedirectResponse(url="/settings?password_changed=1", status_code=303)


@app.get("/themes", response_class=HTMLResponse)
async def themes(request: Request):
    user_data = current_user(request)
    theme_catalog = [
        {"slug": "destiny2", "title": "Destiny 2", "requirement": ""},
        {"slug": "destiny1", "title": "Destiny 1", "requirement": ""},
        {"slug": "hive", "title": "Hive", "requirement": ""},
        {"slug": "cabal", "title": "Cabal", "requirement": ""},
        {"slug": "fallen", "title": "Fallen", "requirement": ""},
        {"slug": "corrupted", "title": "Corrupted", "requirement": ""},
        {"slug": "aria", "title": "Aria", "requirement": ""},
        {"slug": "vex", "title": "Vex", "requirement": "Creator only"},
        {"slug": "beta", "title": "BETA", "requirement": "Beta players only"},
    ]
    allowed = set(user_data["theme_entitlements"]) if user_data else {
        "destiny2", "destiny1", "hive", "cabal", "fallen", "corrupted", "aria"
    }
    for theme in theme_catalog:
        theme["unlocked"] = theme["slug"] in allowed
    return page(request, "themes.html", {"themes": theme_catalog, "theme_entitlements": list(allowed)})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if current_user(request):
        return RedirectResponse(url="/account", status_code=303)
    return page(request, "login.html", {"next": request.query_params.get("next", "/account"), "error": request.query_params.get("error")})


@app.post("/login")
async def login_submit(request: Request, identifier: str = Form(...), password: str = Form(...), next: str = Form("/account")):
    db = SessionLocal()
    try:
        user = authenticate_user(db, identifier, password)
        if not user:
            return page(request, "login.html", {"next": next, "error": "Identifiants incorrects."})
        token = create_token(user.auth_id, user.auth_version)
    finally:
        db.close()
    target = next if next.startswith("/") and not next.startswith("//") else "/account"
    response = RedirectResponse(url=target, status_code=303)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=7 * 24 * 3600,
        httponly=True,
        samesite="lax",
        secure=bool(os.getenv("VERCEL") or os.getenv("HORIZON_ENV", "").lower() == "production"),
        path="/",
    )
    return response


@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    if current_user(request):
        return RedirectResponse(url="/account", status_code=303)
    return page(request, "register.html", {"error": request.query_params.get("error")})


@app.post("/register")
async def register_submit(request: Request):
    return RedirectResponse(
        url="/api/auth/discord/start?mode=web",
        status_code=303,
    )


@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie(SESSION_COOKIE, path="/")
    return response


@app.post("/set-language")
async def set_language(language: str = Form(...)):
    response = RedirectResponse(url="/account", status_code=303)
    response.set_cookie("lang", "fr" if language.lower().startswith("fr") else "en", max_age=31536000, samesite="lax")
    return response


# HORIZON_AUTH_FINAL_V2

def _horizon_remove_route(path, method):
    for route in list(app.router.routes):
        if getattr(route, 'path', None) == path:
            methods = getattr(route, 'methods', set()) or set()
            if method in methods:
                app.router.routes.remove(route)

_horizon_remove_route('/login', 'GET')
_horizon_remove_route('/register', 'GET')
_horizon_remove_route('/logout', 'POST')

@app.get('/login', response_class=HTMLResponse)
async def horizon_login_page(request: Request):
    next_url = request.query_params.get('next', '/account')
    return templates.TemplateResponse(
        request=request,
        name='login.html',
        context=ctx(request, {'next': next_url})
    )

@app.get('/register', response_class=HTMLResponse)
async def horizon_register_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name='register.html',
        context=ctx(request)
    )

@app.post('/logout')
async def horizon_logout(request: Request):
    response = RedirectResponse('/login', status_code=303)
    response.delete_cookie(key=SESSION_COOKIE, path='/ ')
    return response

# === HORIZON AUTH FINAL PATCH ===

def _horizon_lang(request):
    value = request.cookies.get("lang", "en").lower()
    return "fr" if value.startswith("fr") else "en"


def _horizon_t(request, key):
    translations = {
        "en": {
            "site_name": "Horizon Portal",
            "login": "Login",
            "register": "Register",
        },
        "fr": {
            "site_name": "Horizon Portal",
            "login": "Connexion",
            "register": "Inscription",
        },
    }

    try:
        return TEXT[_horizon_lang(request)][key]
    except Exception:
        return translations[_horizon_lang(request)].get(key, key)


def _horizon_context(request, extra=None):
    context = {
        "request": request,
        "lang": _horizon_lang(request),
        "t": lambda key: _horizon_t(request, key),
        "site_name": _horizon_t(request, "site_name"),
        "nav": [],
        "is_authenticated": False,
    }

    if extra:
        context.update(extra)

    return context


def _horizon_remove_routes(path, methods):
    for route in list(app.router.routes):
        if getattr(route, "path", None) == path:
            route_methods = getattr(route, "methods", set()) or set()

            if route_methods.intersection(methods):
                try:
                    app.router.routes.remove(route)
                except ValueError:
                    pass


_horizon_remove_routes("/login", {"GET"})
_horizon_remove_routes("/register", {"GET"})
_horizon_remove_routes("/logout", {"POST"})


@app.get("/login", response_class=HTMLResponse)
async def horizon_login_page(request: Request):
    next_url = request.query_params.get("next", "/account")

    if not next_url.startswith("/"):
        next_url = "/account"

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context=_horizon_context(
            request,
            {"next": next_url}
        )
    )


@app.get("/register", response_class=HTMLResponse)
async def horizon_register_page(request: Request):
    return RedirectResponse(
        url="/api/auth/discord/start?mode=web",
        status_code=303,
    )


@app.post("/logout")
async def horizon_logout(request: Request):
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        payload = decode_token(token)
        if payload:
            db = SessionLocal()
            try:
                user = get_user_by_auth_id(db, payload["auth_id"])
                if user and int(user.auth_version or 1) == int(payload["auth_version"]):
                    # Version bump revokes every copied web/launcher token for this account.
                    user.auth_version = int(user.auth_version or 1) + 1
                    db.commit()
            finally:
                db.close()

    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return response
