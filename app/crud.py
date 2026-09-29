from sqlalchemy import or_
from hashlib import sha256

from .models import Creator, Download, Theme, User, RedeemCode
from .security import hash_password, verify_password


def seed(db):
    if not db.query(Creator).first():
        db.add_all([
            Creator(slug="dawn", name="Dawn", description="Dawn creator pack"),
            Creator(slug="sunrise", name="SunRise", description="SunRise creator pack"),
        ])
    if not db.query(Download).first():
        db.add(Download(slug="core-pack", title="Core Pack", description="Main download pack", version="1.0.0"))
    theme_seed = [
        ("destiny2", "Destiny 2", "Default Horizon theme.", "free"),
        ("destiny1", "Destiny 1", "Destiny 1 art direction.", "free"),
        ("hive", "Hive", "Free Horizon theme.", "free"),
        ("cabal", "Cabal", "Free Horizon theme.", "free"),
        ("fallen", "Fallen", "Free Horizon theme.", "free"),
        ("corrupted", "Corrupted", "Free Horizon theme.", "free"),
        ("aria", "Aria", "Free Horizon theme.", "free"),
        ("vex", "Vex", "Creator badge only.", "creator"),
        ("beta", "BETA", "Unlocked with a valid Horizon BETA code.", "beta"),
    ]
    db.query(Theme).filter(Theme.slug == "legacy").delete(synchronize_session=False)
    for slug, title, description, unlock_type in theme_seed:
        if not db.query(Theme).filter(Theme.slug == slug).first():
            db.add(Theme(slug=slug, title=title, description=description, unlock_type=unlock_type))
    import os
    admin_password = os.getenv("HORIZON_ADMIN_PASSWORD", "").strip()
    rotate_admin = os.getenv("HORIZON_ROTATE_ADMIN_PASSWORD", "").strip() == "1"
    admin = db.query(User).filter(User.username == "admin").first()

    if admin_password and not admin:
        db.add(User(
            email="admin@horizon.local",
            username="admin",
            password_hash=hash_password(admin_password),
            role="admin",
        ))
    elif admin_password and rotate_admin and admin:
        # Explicit one-time rotation for a previously deployed admin secret.
        admin.password_hash = hash_password(admin_password)
        admin.auth_version = int(admin.auth_version or 1) + 1

    beta_codes = [
        "fb59c5a169f411ff9d063b3b84365c55218efabe4572f59ac740120c6fd3c614",
        "d887f1db500cb59a85ff099a4f0e9c016749be0306fc48326263efa5dc89e3d1",
        "7d4ffe7fcb02fc77d9edc91fc4355195424c4bb9a25fd851db7a44011f453dac",
        "80317e2ee4df8a9253acf25c618a43e24a8fb96c5e49da9fb044d79594b2defa",
        "f3d93e8adad6cf8e7176663a1679b7a38040df5cee20327913b3fba7afc2ad92",
        "19e48c97fd5a73bc2183d0e1757b1a90bd987ebdece535a5eaa4d76eb06cf880",
    ]
    creator_codes = [
        "68383c6e54677c45cd95bca2ce25d1555a32407fea14dab5b214e3de4baed3a8",
        "e19b7c3f4c7aab389763cb50b84653ed7198d0ca6a2cfa7dc74cb9d6a9d2e3ff",
        "fb37b1ee549c9747366d0bdbf15dff21ef72eb3c4c7c78c66625ad6e3b0090d",
        "708bc16c3555eeb812649251a76bdacc05aef4a39a2d0bea041b3dee3a508f27",
        "9f4ea8403c32a89e025caad1a6ba202434793b88fc587c36fcdc184c01f03437",
        "ccce2a15ed0b454d982f049ce8b5e8b570843477b9d6fd2fa712cd1b13b4c60d",
        "f74decd07af312333d82a32e439e602738695f5f6f02bf247571c0d35b3997ea",
        "b87882902bd80b91d540b1f5401991047d1d6940a31a7080294c0c5bf5e23ffe",
        "7ac6d40ee9b2524bde70c10d8aca02122d8c192129019c6769345926005bb5dc",
        "e9fd838fba481be254232b0ae970bac3ec2a88c8278273b37a34966cc2c8e63e",
        "51da782147f0812466f6c44646a92527fe43fb2f69250a358aba28eb9bc19e74",
        "cc87d202a0d1d2c70c3f2349b323c4c7981d89e34e4ac0af0ebdcaf29bcb55b2",
        "76160465d5cdfd3874f3c544eac109ebbe892ac8b7387c05d0c682277e160c06",
        "2eb3f9fe2904b2a9b0c218de05fc0d08d39b10e0a2c147e7700e9b32a2688f14",
        "999652fbde6107b29b497d9fdb7d5f84070d165daf4eed556194694ff731ad0e",
        "46ba8ff7a52bd452b0eb7650f060988f9fa7f961df4023df70dc58b55dcc92f0",
        "d01d80863a62f5b0fb557548d834c4d3256e6032b46687570d6b24cfc899a62a",
        "818d7bfc29edd4922d54a677eab109e0d1fcb9da122ce7c59ef731378c024027",
        "997a599ff41095eb45a9e5c8656155fb9951515575746c660f0e1f3dea1a14ac",
        "49a0d0fb908b44bf53622635e060c60c74a52e9fc76beef60ec803c9b9d2f99f",
        "0712c4b368ff71a395ea185d63c2af5957f67d6c945f7c72004ca5d993a8196b",
        "04a37655b06ee54014245b31b24a0e58bd1bb6c063a69fb027a7e28e4d2d85d2",
        "48d09125df0baeefd32f2d0dcba98dc3eb25fcbc76747c73472fc637d64f5b81",
        "8bd736de5f86888fb9dbed1af11df11671cf9f3a93e231256e71bee97c3cd0f8",
        "1b2d50e7e141726f395b759bc865b38ff879f04f2f969993611d5f4a02f980e0",
        "417bb86d4ab02c2ee1389fd3c70f03ba239298d5d894872d874fdcd7fafafa39",
        "2db069c9a5ec973be2038bf29a9e6333a30b1d9d9cd6e2e24514ad49235e1fce",
        "79f2257c4a7d781bec1be87cf54f3ae8af31f8f87f79e496980f031034f56baf",
        "cc6c5f53446ed83f462d69506b07adf62dfdc6ea7fd1444bef575c635ac6fa1e",
        "3340540b77468943c6a2c894a28ddeadc639647d91350a9bfa3e7c9cf783e56a",
        "f60db89f73b41458730f2b4f58af61c0cf0c61d05eab1bc8d1739a35dba91eac",
        "1d8ffe86cb87d562a1669306cb256c3e2e9fe600643fc8455a4e09ed5d37b724",
        "76af7384f2db4d77d176d376d6b3756745b3f14eaf1ab22aa6978cc4beff0758",
        "5ecb31e86f2c612e8ca5844ff4b0241b472698d9921cc853577e881ffe346e5f",
        "214e63ee335c11a7adc98ce438bf8fe534d08f52577c720978f9768ace5cddd9",
        "1355ca0aaade655949dc81d130e9654793316a1dcb36de72519e5f08f4f48546",
        "502eb0b8e9f49684830b21af6692010f11f0d7457a15322064e0363dfc90fc7b",
        "76350d3b2fa819339a2b97c9690f711637319de2b44a95d5767e1f55c276173a",
        "b02604bb232d2516dad9293cf6b1e07bdba6a35b5573f752b3d3c5a97b357d29",
        "3696b3a42988eddee7d04bbe49e24236e1505fdad01e0d743f30c9fdf24a2507",
        "a1b329112cc1c171a924d0e381a2709ae7782bb5632aa60d7dd832394bf2077c",
        "0703b199c2f9d5a2874373992c343e8d8fd9bda6b297f2211d5a7564418fab0f",
        "37f5386662431d0b246dda08a186e7eeb464ddeb230da9de9bda3d87cbbd8867",
        "0cc0eed223cf2b4f55650eba55613a99794c5ba4ee56c689de46b89ebf1fd7b7",
        "9a129e821b7f095cbff99bfc1889698140868f3eadf31ef47597d3e72a6f5c8b",
        "114b2406cb4deee5e137c10732c3548abce50de35c91317c748ed29c340f92cc",
        "7c0b49901657cf1d29dc2a09d74f8b373c4fb11737aa857e542b6d783447ce97",
        "9e16c89f407767102f2971f14caec39ca078274a84827c08eeb87551ab5db610",
        "e1e539e66510ce36cf872a054286fc554a9b399238f9149b453faf7f0833669d",
        "8504906979dba4192962180f93ba8c54f87e0f401579bc74787231ad4979e49c",
        "bad2bd4bace4bf4ef5dbe9acb9e73b51defcba5a83eab1d2cccbf201fe8d56b8",
        "6b1b1eae9e49a07fcbf39b9e014fb41272ee9ab2b652dfed1b5f3da07f69c831",
        "c351c41679b9c3d80fa91d9956a085c1c57a921794ea25fefb54aee4957288e0",
        "ddeb8add93bf9821082fb4a53860b9afb1ada3fa10be30c37d6b5ea7741b5295",
        "6323b1850ca21ccd363f56a7e0924222474534705b36a534f13757997dfb0b5f",
        "87224ecbb87faab87ec4ceda8d58b876601e52d6d4d0dce9e3e422a8661cb5fd",
        "6531d449d7fa57ee95e252f2220079b88f794dc3e969bfb1bf352fb3e0baa6c6",
        "2bfe8bcd114099f597f61e804543297949319585ab4dafdf5f706bd6618848cb",
        "4a9e3fb9e8cf34d92011aad0e6404937703917749515089050be4a5f597c4ee2",
        "93a923507fee5d280347beb600ef93a37aee7de50b4ae3f7e46d2bed5a3191e4",
        "fc610ae6de496d210bb93d6dcd233d8604999eb4eb3b400a2e27fb453f923a07",
        "fb95c0aedc9091e9ebbce21f815068a4c053b7aa9ac19d4d5ed148e4dfa5bcf7",
        "0eb045fd37e1b04815ec06613104f7126aa381a819e1a8d4c2e59502052b8c38",
        "84902d72cd6253e776b7a608f4a90abe40dec218b726c864d89485b9ce3e489d",
        "b32a04c4ff00e903615caeea49b8da04df41e5c9455aac701e66dac1bde154d1",
        "f0b1d88b56bbb60cb9ab4b482c71f378b494784643ff1e8e0ed674aeacf25c04",
        "61e413c7c7a4065cb634660caf847dc47b4b5e5b6dbe089ec433470fb67a8e34",
        "a151bf90998df371fd8aeaedbab59c952250ec39b70953afce77e1ff62243431",
        "30a66e25ce89511b0ed873bbdf6b75fb41eb3de7097d56a31bca5f71724b0745",
        "a4fef2e04fe0a5b59206a4335aad031b7b140334c925ea5385f870023cd0ae74",
        "7c677bcf5006f6aaacc805dfa1159bbc330ae00191ec5eb725d232bb3b3b8443",
        "d084f3761a8f8364e9e7aeee2c975dcba040091733d52da11a7a3411c32934d6",
        "04369825a4a99fff59173e161d76a14bfe55119a07dedfbc4386d26e27056b6b",
        "88b01462c331fb6238d0f7bc93c3fc99aba8b3339e5452826aa02469d745452a",
        "89359d8a27b1df2b20944b6b8f13101666a3412c69b5442099a3ca6b16b4a952",
        "8d23d7e0352e3df57b48745988c077856b4f056e144549e0b91d218783af7d27",
        "cc0e240e2799e90f887e3e6817386b3756239d2c066232a83edff4cf2f85b5d1",
        "dc28e3792d8b1a2c2cdfcf47f1aab16fc676a1e1d9e20ad1aab0031a8cdada",
        "56594aa714bb02389aefbefbf472c0894c63bd58e4dc8ea263d1c3fc932cd106",
        "c4f3ee061e4504b17122d54a951f09a9beaff20f79083f38776fbaedc8dd0e60",
        "ac4282dd2a45a9a217a4b9026e04d055df4bfaf83de46f6bb400349b87c7a6b9",
        "f839d8ca0f4aabf19403fb5c45f85ca3ab6ea83ef99da7ba7984c95eb106c611",
        "3f83cc0cc8f57ac3c26ef304fc8317c2157470c5f44627db9b7a75e4aa71da0b",
        "40328b1c3d377a19733fc320dd62db8d2dd6980213e85bfd3b01dcf805ce3313",
        "a3c860d2d8da040094fc60e1d1eb3873e528d9e7931feffdec6a9d1ae98ac021",
        "31f66c6769633f09c76f0bfbd772b27d7c1a69c834a873b961e47dc4012db679",
        "65128da68b0859c623b27a6ca904def07af9c35f9f0806c2cc700ed85b45d449",
        "6091a6bf629a2d21d4ec6578bd1569a04845bfec62e79f25c45e4e9fc1b5acc4",
        "6fa94bb69d1408b94cdc543d03af9753b9fd62e5892340f1ec984fb346012562",
        "05e48644eba45cbc5030f769f1ccf2a74f601c17bd0c268d6e6bb209062fe35d",
        "1555f21dd7e541a796f30602c8ad407fe45238079f768eb7f22cf4451269a4b3",
        "bb1548cea99169ea7419f7f2102907f84515d0a27a00e4e8934282db8a902442",
        "9e42e71319d9b50337ff887471309bf10a60a6b0e0906bc43e760a8e68038863",
        "cce8063e0c943aa92c0beb246e80b9de9ee5655550830bf1a0f9726600608900",
        "d8b041c25976cbd2920c9f8505fea1425134213fbc9fb86aa94c1a7a9b726fdb",
        "b8b6d7ca229d8f0df21d3ebaa99aa3ec44b8390c936bb39b93a98a80e88b723c",
        "71d8a9723eedcad777a3276f898d529705fd999576065a9deae0e1b4e6ad1c6d",
        "b8b2285ada4e392ff797037fe7e209215a1747ac1a6da5c93c6c27b76f7f96ef",
        "997015ec0fea2e4562d1c136c81858d9fe35d7ce534e2e66334f067c649d7273",
        "336ca3d5f3736e21d3d7e3b98da95f63775218dbcafc5b63862b9456f7bbd333",
    ]
    for code_hash in beta_codes:
        if not db.query(RedeemCode).filter(RedeemCode.code_hash == code_hash).first():
            db.add(RedeemCode(code_hash=code_hash, entitlement="beta"))
    for code_hash in creator_codes:
        if not db.query(RedeemCode).filter(RedeemCode.code_hash == code_hash).first():
            db.add(RedeemCode(code_hash=code_hash, entitlement="creator"))

    db.commit()


THEME_ACCESS = {
    "destiny2": {"kind": "free", "min_donation": 0},
    "destiny1": {"kind": "free", "min_donation": 0},
    "hive": {"kind": "free", "min_donation": 0},
    "cabal": {"kind": "free", "min_donation": 0},
    "fallen": {"kind": "free", "min_donation": 0},
    "corrupted": {"kind": "free", "min_donation": 0},
    "aria": {"kind": "free", "min_donation": 0},
    "vex": {"kind": "creator"},
    "beta": {"kind": "beta"},
}


def theme_entitlements(user: User | None) -> list[str]:
    access = ["destiny2", "destiny1", "hive", "cabal", "fallen", "corrupted", "aria"]
    if user and bool(getattr(user, "creator_badge", 0)):
        access.append("vex")
    if user and bool(getattr(user, "beta_access", 0)):
        access.append("beta")
    return access

def theme_access(user: User | None, slug: str) -> bool:
    return slug in theme_entitlements(user)


def _public_user(user: User) -> dict:
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


def register_user(db, payload: dict):
    email = payload.get("email", "").strip().lower()
    username = payload.get("username", "").strip()
    password = payload.get("password", "")

    if not email or not username or not password:
        return None

    existing = db.query(User).filter(or_(User.email == email, User.username == username)).first()
    if existing:
        return None

    # Public account creation is Discord-only. Keep this helper for legacy/admin
    # tooling, but never expose it as a public account-creation path.
    user = User(
        email=email,
        username=username,
        password_hash=hash_password(password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _public_user(user)


def authenticate_user(db, identifier: str, password: str):
    identifier = identifier.strip()
    user = db.query(User).filter(
        or_(User.email == identifier.lower(), User.username == identifier)
    ).first()
    # Discord-linked users must authenticate through Discord. This prevents a
    # planted or previously known password from bypassing Discord identity/roles.
    if not user or user.role != "admin":
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(db, payload: dict):
    identifier = payload.get("identifier") or payload.get("email") or payload.get("username") or ""
    password = payload.get("password", "")
    user = authenticate_user(db, identifier, password)
    return _public_user(user) if user else None


def get_user(db, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_auth_id(db, auth_id: str):
    return db.query(User).filter(User.auth_id == auth_id).first()


def _creator(item):
    return {"id": item.id, "slug": item.slug, "name": item.name, "description": item.description, "image_url": item.image_url, "download_url": item.download_url}


def _download(item):
    return {"id": item.id, "slug": item.slug, "title": item.title, "description": item.description, "file_url": item.file_url, "version": item.version}


def _theme(item):
    return {"id": item.id, "slug": item.slug, "title": item.title, "description": item.description, "preview_url": item.preview_url, "unlock_type": item.unlock_type}


def _user(item):
    return _public_user(item)


def list_creators(db): return [_creator(x) for x in db.query(Creator).order_by(Creator.id.asc()).all()]
def get_creator_by_slug(db, slug: str):
    item = db.query(Creator).filter(Creator.slug == slug).first()
    return _creator(item) if item else None


def list_downloads(db): return [_download(x) for x in db.query(Download).order_by(Download.id.asc()).all()]
def get_download_by_slug(db, slug: str):
    item = db.query(Download).filter(Download.slug == slug).first()
    return _download(item) if item else None


def list_themes(db): return [_theme(x) for x in db.query(Theme).order_by(Theme.id.asc()).all()]
def get_theme_by_slug(db, slug: str):
    item = db.query(Theme).filter(Theme.slug == slug).first()
    return _theme(item) if item else None


def list_users(db): return [_user(x) for x in db.query(User).order_by(User.id.asc()).all()]


def delete_user(db, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user: return False
    db.delete(user); db.commit(); return True


def delete_download(db, download_id: int):
    item = db.query(Download).filter(Download.id == download_id).first()
    if not item: return False
    db.delete(item); db.commit(); return True


def update_entitlements(db, user_id: int, donation_cents: int | None = None, creator_badge: bool | None = None, beta_access: bool | None = None):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if donation_cents is not None:
        user.donation_cents = max(0, int(donation_cents))
    if creator_badge is not None:
        user.creator_badge = 1 if creator_badge else 0
    if beta_access is not None:
        user.beta_access = 1 if beta_access else 0
    # Entitlement changes invalidate previously issued launcher/web tokens.
    user.auth_version = int(user.auth_version or 1) + 1
    db.commit()
    db.refresh(user)
    return _public_user(user)
