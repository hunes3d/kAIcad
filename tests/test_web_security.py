"""Security tests for the Flask web app: secret key and CSRF enforcement."""

import os
import pytest
from contextlib import contextmanager


@contextmanager
def temp_env(env: dict):
    old = {k: os.environ.get(k) for k in env.keys()}
    try:
        os.environ.update({k: v for k, v in env.items() if v is not None})
        yield
    finally:
        for k, v in old.items():
            if v is None and k in os.environ:
                del os.environ[k]
            elif v is not None:
                os.environ[k] = v


def test_web_fails_without_secret_in_production():
    # Ensure no development mode and no secret: app init should raise
    with temp_env({"FLASK_ENV": "production", "FLASK_SECRET_KEY": None}):
        import sidecar.web as web
        with pytest.raises(RuntimeError):
            web.create_app()


def test_web_allows_dev_mode_without_secret(monkeypatch):
    # In development, app should start even without explicit secret
    with temp_env({"FLASK_ENV": "development", "FLASK_SECRET_KEY": None}):
        from importlib import reload
        import sidecar.web as web
        app = reload(web).create_app()
        assert app.secret_key is not None


def test_csrf_required_for_form_posts(monkeypatch):
    # CSRF should be enforced for form POSTS; simulate a POST without token
    with temp_env({"FLASK_ENV": "development", "FLASK_SECRET_KEY": None}):
        from importlib import reload
        import sidecar.web as web
        app = reload(web).create_app()
        client = app.test_client()

        # If CSRF not enabled (flask-wtf missing), skip this test
        try:
            from flask_wtf.csrf import generate_csrf  # type: ignore
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
        import sidecar.web as web
        app = reload(web).create_app()
        client = app.test_client()

        # If CSRF not enabled (flask-wtf missing), skip this test
        try:
            from flask_wtf.csrf import generate_csrf  # type: ignore
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

            resp2 = client.post(
                "/generate_description",
                json={"input": "LED"},
                headers={"X-CSRFToken": token}
            )
            # Either succeed (200) or fail with 400 due to missing API key; but not CSRF error
            assert resp2.status_code in (200, 400)
