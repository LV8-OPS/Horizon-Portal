from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200


def test_public_pages():
    for path in ["/", "/workshop", "/creators", "/download", "/docs", "/roadmap", "/status"]:
        response = client.get(path)
        assert response.status_code == 200


def test_account_is_not_in_home_navigation():
    response = client.get("/")
    assert response.status_code == 200
    assert ">Account<" not in response.text


def test_creator_page_has_no_dawn_sunrise_affiliation():
    response = client.get("/creators")
    assert response.status_code == 200
    assert "Dawn creator pack" not in response.text
    assert "SunRise creator pack" not in response.text


def test_security_headers():
    response = client.get("/")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "Content-Security-Policy" in response.headers
