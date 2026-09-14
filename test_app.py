import app


def test_app_loads(monkeypatch):
    # Smoke test: app module and Flask app instance import correctly.
    assert app.app is not None
    assert hasattr(app.app, "test_client")


def test_home_returns_404_when_no_restaurant(monkeypatch):
    monkeypatch.setattr(app, "fetch_one", lambda query, params=(): None)

    client = app.app.test_client()
    response = client.get("/")
    assert response.status_code == 404


def test_menu_returns_404_when_restaurant_missing(monkeypatch):
    monkeypatch.setattr(app, "fetch_one", lambda query, params=(): None)

    client = app.app.test_client()
    response = client.get("/menu/dca-demo")
    assert response.status_code == 404


def test_marketplace_has_campaign_and_offer_forms(monkeypatch):
    monkeypatch.setattr(app, "fetch_all", lambda query, params=(): [])
    monkeypatch.setattr(app, "fetch_one", lambda query, params=(): None)

    client = app.app.test_client()
    response = client.get("/marketplace")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert 'action="/marketplace/campaign"' in html
    assert 'action="/marketplace/offer"' in html
    assert 'ROI' in html
    assert 'WhatsApp' in html


def test_build_whatsapp_url_helper_creates_custom_message_link():
    given_text = "Quero fazer um pedido"
    url = app.build_whatsapp_url("5588999999999", given_text)
    assert url == "https://wa.me/5588999999999?text=Quero%20fazer%20um%20pedido"


def test_home_template_has_accessible_navigation(monkeypatch):
    monkeypatch.setattr(app, "fetch_one", lambda query, params=(): {"name": "DCA Demo"})

    client = app.app.test_client()
    response = client.get("/")
    assert response.status_code == 200

    html = response.get_data(as_text=True)
    assert 'class="skip-link"' in html
    assert 'aria-label="Navegação principal"' in html
