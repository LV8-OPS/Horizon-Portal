from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_docs():
    r = client.get("/docs")
    assert r.status_code == 200


def test_legal_pages_and_footer_links():
    for path, title in [
        ("/terms", "Terms of Service"),
        ("/privacy", "Privacy Policy"),
    ]:
        response = client.get(path)
        assert response.status_code == 200
        assert 'lang="en"' in response.text
        assert title in response.text
        assert 'href="/terms">Terms of Service</a>' in response.text
        assert 'href="/privacy">Privacy Policy</a>' in response.text