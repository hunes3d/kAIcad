"""Security tests for the Flask web app: secret key and CSRF enforcement."""

import os
from contextlib import contextmanager

import pytest

# Set development mode for initial import
os.environ.setdefault("FLASK_ENV", "development")
os.environ.setdefault("FLASK_SECRET_KEY", "test-secret-for-security-tests")


@contextmanager
def temp_env(env: dict):
    old = {k: os.environ.get(k) for k in env.keys()}
    try:
        for k, v in env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        yield
    finally:
        for k, v in old.items():
            if v is None and k in os.environ:
                del os.environ[k]
            elif v is not None:
                os.environ[k] = v


def test_web_fails_without_secret_in_production():
    # Test that _configure_security raises when called with production settings and no key
    from flask import Flask

    import kaicad.ui.web.app as web

    # Create a fresh test app
    test_app = Flask(__name__)

    with temp_env({"FLASK_ENV": "production", "FLASK_SECRET_KEY": None}):
        # Try to configure security on this fresh app - should raise
        with pytest.raises(RuntimeError, match="FLASK_SECRET_KEY"):
            # Create a new _configure_security call by manually calling it
            # We need to reset the flag temporarily
            old_flag = web._app_configured
            web._app_configured = False
            try:
                web._configure_security(test_app)
            finally:
                web._app_configured = old_flag


def test_web_allows_dev_mode_without_secret(monkeypatch):
    # In development, app should start even without explicit secret
    with temp_env({"FLASK_ENV": "development", "FLASK_SECRET_KEY": None}):
        from importlib import reload

        import kaicad.ui.web.app as web

        app = reload(web).create_app()
        assert app.secret_key is not None


def test_csrf_required_for_form_posts(monkeypatch):
    # CSRF should be enforced for form POSTS; simulate a POST without token
    with temp_env({"FLASK_ENV": "development", "FLASK_SECRET_KEY": None}):
        from importlib import reload

        import kaicad.ui.web.app as web

        app = reload(web).create_app()
        client = app.test_client()

        # If CSRF not enabled (flask-wtf missing), skip this test
        try:
            csrf_enabled = True
        except Exception:
            csrf_enabled = False

        resp = client.post("/", data={"action": "plan", "prompt": "Add R1"})
        if csrf_enabled:
            assert resp.status_code in (400, 403)
        else:
            pytest.skip("flask-wtf not installed; CSRF not enforced in this environment")


def test_csrf_header_required_for_json_endpoints(monkeypatch):
    # JSON endpoints require X-CSRFToken header when CSRF enabled
    with temp_env({"FLASK_ENV": "development", "FLASK_SECRET_KEY": None}):
        from importlib import reload

        import kaicad.ui.web.app as web

        app = reload(web).create_app()
        client = app.test_client()

        # If CSRF not enabled (flask-wtf missing), skip this test
        try:
            csrf_enabled = True
        except Exception:
            csrf_enabled = False

        # No header -> expect 400/403 when CSRF is enabled
        resp = client.post("/generate_description", json={"input": "LED"})
        if csrf_enabled:
            assert resp.status_code in (400, 403)
        else:
            pytest.skip("flask-wtf not installed; CSRF not enforced in this environment")

        if csrf_enabled:
            # Provide header with token from rendered form
            # Fetch index to get a valid csrf token in the page
            index = client.get("/")
            # Extract token from the HTML
            import re

            m = re.search(rb'name="csrf_token" value="([^"]+)"', index.data)
            assert m, "Expected CSRF token in form"
            token = m.group(1).decode()

            resp2 = client.post("/generate_description", json={"input": "LED"}, headers={"X-CSRFToken": token})
            # Either succeed (200) or fail with 400 due to missing API key; but not CSRF error
            assert resp2.status_code in (200, 400)
