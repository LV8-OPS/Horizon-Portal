TRANSLATIONS = {
    "en": {
        "site_name": "Horizon Portal",
        "home": "Home", "creator": "Creator", "download": "Download", "account": "Account", "workshop": "Workshop",
        "support": "Support on Discord", "discord_phrase": "Need help? Join our Discord for support.",
        "theme_title": "Themes explained", "theme_desc": "Preview the upcoming styles of Horizon Portal.",
        "welcome": "Welcome to Horizon Portal", "subtitle": "A Destiny 2 inspired portal in White / Gray / Gold.",
        "settings": "Settings", "language": "Language", "default_language": "English is the default language.",
        "switch_language": "You can switch to French in account settings.", "creator_title": "Creator tools", "download_title": "Downloads"
    },
    "fr": {
        "site_name": "Horizon Portal",
        "home": "Accueil", "creator": "Créateur", "download": "Téléchargement", "account": "Compte", "workshop": "Workshop",
        "support": "Support sur Discord", "discord_phrase": "Besoin d’aide ? Rejoins notre Discord pour le support.",
        "theme_title": "Thèmes expliqués", "theme_desc": "Découvre les futurs styles de Horizon Portal.",
        "welcome": "Bienvenue sur Horizon Portal", "subtitle": "Un portail inspiré de Destiny 2 en Blanc / Gris / Or.",
        "settings": "Paramètres", "language": "Langue", "default_language": "L’anglais est la langue par défaut.",
        "switch_language": "Tu peux passer en français dans les paramètres du compte.", "creator_title": "Outils créateur", "download_title": "Téléchargements"
    }
}

def get_locale(request):
    lang = request.cookies.get("lang", "en")
    return "fr" if str(lang).lower().startswith("fr") else "en"

def t(locale, key):
    return TRANSLATIONS.get(locale, TRANSLATIONS["en"]).get(key, key)
