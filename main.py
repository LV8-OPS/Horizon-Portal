from pathlib import Path
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent.parent
app = FastAPI(title="Horizon Portal")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
NAV = [("Creator", "/creator"), ("Download", "/download"), ("Account", "/account")]
TEXT = {
    "en": {"site_name":"Horizon Portal","slogan":"Beyond the Horizon","welcome":"Beyond the Horizon","subtitle":"A social launcher connecting players and developers who want to share, discover and enjoy D2 modded content without wasting hours searching.","what_is":"What is Horizon Portal?","what_is_desc":"A clean social hub for players who want to install content easily and for developers who need a better place to showcase their work.","offers":"What Horizon Portal offers","how":"How it works","community":"Community","cta":"Get started","support":"Support on Discord","download_btn":"DOWNLOAD HORIZON PORTAL","discord_btn":"JOIN DISCORD","ticket_btn":"ANSWER THE QUESTIONNAIRE","account_title":"Account","download_title":"Horizon Portal","creator_title":"Creator Program","creator_intro":"Publish your work, get noticed, and help players discover quality D2 modded content.","download_intro":"Download the launcher, install it, and start browsing content without the hassle.","account_intro":"Manage your profile, language, inbox and sign-in options.","post_text":"Creators post through Discord after completing a short questionnaire.","user_text":"Players can install the software and enjoy content without overthinking.","dev_text":"Developers can publish their work and be highlighted through quality.","community_text":"Join Discord to connect, ask questions and share updates.","support_text":"Supporting the project grants the benefits listed below.","inbox":"Inbox","free":"Free Access","donator":"Donator Role — €1+","corrupted":"Corrupted Role — €5+","aria":"Aria Role — €10+","creator_role":"Creator Role","legacy":"Legacy Role","download_box":"Download the .exe","version":"Version","size":"Size","system":"Supported system","tutorial":"Quick tutorial","linux":"Linux soon"},
    "fr": {"site_name":"Horizon Portal","slogan":"Beyond the Horizon","welcome":"Beyond the Horizon","subtitle":"Un launcher social qui relie les joueurs et les développeurs pour partager, découvrir et profiter de contenu D2 modded sans perdre des heures à chercher.","what_is":"Qu'est-ce que Horizon Portal ?","what_is_desc":"Un hub social simple pour les joueurs qui veulent installer du contenu facilement et pour les développeurs qui cherchent un endroit clair pour mettre leur travail en avant.","offers":"Ce que propose Horizon Portal","how":"Comment ça marche","community":"Communauté","cta":"Commencer","support":"Support sur Discord","download_btn":"TÉLÉCHARGER HORIZON PORTAL","discord_btn":"REJOINDRE DISCORD","ticket_btn":"RÉPONDRE AU QUESTIONNAIRE","account_title":"Compte","download_title":"Horizon Portal","creator_title":"Programme Creator","creator_intro":"Publie ton travail, gagne en visibilité et aide les joueurs à découvrir du contenu D2 modded de qualité.","download_intro":"Télécharge le launcher, installe-le et commence à parcourir le contenu sans prise de tête.","account_intro":"Gère ton profil, la langue, l’inbox et les options de connexion.","post_text":"Les créateurs publient via Discord après avoir répondu à un petit questionnaire.","user_text":"Les joueurs peuvent installer le logiciel et profiter du contenu sans se prendre la tête.","dev_text":"Les développeurs peuvent publier leur travail et être mis en avant grâce à la qualité.","community_text":"Rejoins Discord pour discuter, poser des questions et partager les nouveautés.","support_text":"Contribuer au projet donne accès aux avantages listés ci-dessous.","inbox":"In box","free":"Free Access","donator":"Donator Role — €1+","corrupted":"Corrupted Role — €5+","aria":"Aria Role — €10+","creator_role":"Creator Role","legacy":"Legacy Role","download_box":"Download the .exe","version":"Version","size":"Size","system":"Supported system","tutorial":"Quick tutorial","linux":"Linux soon"}
}

def lang(request): return "fr" if request.cookies.get("lang", "en").lower().startswith("fr") else "en"
def t(request, key): return TEXT[lang(request)][key]
def ctx(request, extra=None):
    c = {"request": request, "lang": lang(request), "t": lambda k: t(request, k), "site_name": t(request, "site_name"), "nav": NAV}
    if extra: c.update(extra)
    return c

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    c = ctx(request, {
        "offers": [
            {"title": "For players", "text": t(request, "user_text")},
            {"title": "For developers", "text": t(request, "dev_text")},
            {"title": "Community", "text": t(request, "community_text")},
            {"title": "Support", "text": t(request, "support_text")}
        ],
        "steps": [
            "Download the launcher.",
            "Install and open it.",
            "Browse or submit content.",
            "Use Discord for community and posting."
        ],
        "benefits": [
            (t(request, "free"), ["Everyone can access the core launcher experience."]),
            (t(request, "donator"), ["Discord role.", "Access to extra themes.", "24h early access to updates.", "Early access before public release."]),
            (t(request, "corrupted"), ["Discord role.", "All Donator benefits.", "Exclusive Corrupted theme.", "7 days early access.", "Ad-free website."]),
            (t(request, "aria"), ["Discord role.", "All supporter benefits.", "Exclusive Aria theme.", "7 days early access.", "Ad-free website."]),
            (t(request, "creator_role"), ["Discord role for approved creators.", "Exclusive Vex theme.", "Creator theme panel.", "Publish and manage approved projects."]),
            (t(request, "legacy"), ["Discord role.", "7 days early access.", "Exclusive Legacy panel.", "Ad-free website."])
        ]
    })
    return templates.TemplateResponse(request=request, name="index.html", context=c)

@app.get("/download", response_class=HTMLResponse)
async def download(request: Request):
    return templates.TemplateResponse(request=request, name="download.html", context=ctx(request, {"version":"Soon","size":"Soon","system":"Windows","steps":["Download the .exe.","Run the installer.","Launch Horizon Portal.","Sign in or create your account.","Enjoy the content."],"tutorial":["Open the download page.","Click the launcher button.","Install the software.","Return to Discord if you need help."]}))

@app.get("/creator", response_class=HTMLResponse)
async def creator(request: Request):
    return templates.TemplateResponse(request=request, name="creator.html", context=ctx(request, {"steps":["Join Discord.","Answer the questionnaire.","Submit your project.","Wait for review.","Get approved.","Publish your content."],"types":["Weapons","D1 imports","HUD changes","Raid content","Assault content","Mission content"],"role_benefits":[t(request, "creator_role"), t(request, "support_text")] }))

@app.get("/account", response_class=HTMLResponse)
async def account(request: Request):
    return templates.TemplateResponse(request=request, name="account.html", context=ctx(request, {"is_authenticated": False}))

@app.post("/set-language")
async def set_language(language: str = Form(...)):
    response = RedirectResponse(url="/account", status_code=303)
    response.set_cookie("lang", "fr" if language.lower().startswith("fr") else "en", max_age=31536000)
    return response
