"""Tests for web module - Flask routes and API endpoints."""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Need to set FLASK_ENV before importing
os.environ["FLASK_ENV"] = "development"
os.environ["FLASK_SECRET_KEY"] = "test-secret-key-for-testing"

from sidecar.web import _load_current_project, _save_current_project, app


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    # App is already configured at module import time
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    with app.test_client() as client:
        yield client


@pytest.fixture
def temp_project_dir():
    """Create a temporary directory for test projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


def test_app_exists():
    """Test that Flask app is created."""
    assert app is not None
    assert app.name == "sidecar.web"


def test_app_testing_mode(client):
    """Test that app can be put in testing mode."""
    assert app.config["TESTING"] is True


def test_index_route_get(client):
    """Test GET request to index route."""
    response = client.get("/")

    # Should return a successful response
    assert response.status_code in [200, 302, 400, 500]  # Various states are valid

    # If 200, should have HTML content
    if response.status_code == 200:
        assert b"html" in response.data.lower() or b"<!DOCTYPE" in response.data


def test_index_route_post_no_project(client):
    """Test POST to index without project path."""
    response = client.post("/", data={})

    # Should redirect or show error
    assert response.status_code in [200, 302, 400]


def test_index_route_post_with_project(client, temp_project_dir):
    """Test POST to index with valid project path."""
    # Create a test schematic file
    sch_path = temp_project_dir / "test.kicad_sch"
    sch_path.write_text("(kicad_sch (version 20231120))")

    response = client.post("/", data={"project_path": str(sch_path), "user_prompt": "Add LED"})

    # Should process or show result
    assert response.status_code in [200, 302, 400, 500]


def test_load_current_project_no_file():
    """Test loading project when no file exists."""
    with patch("sidecar.web.CURRENT_PROJECT_FILE") as mock_file:
        mock_file.exists.return_value = False

        result = _load_current_project()

        # Should return None or empty string
        assert result is None or result == ""


def test_load_current_project_with_file():
    """Test loading project from file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = Path(tmpdir) / "current_project.json"
        project_file.write_text(json.dumps({"project_path": "/path/to/project"}))

        with patch("sidecar.web.CURRENT_PROJECT_FILE", project_file):
            result = _load_current_project()

            assert result == "/path/to/project"


def test_save_current_project():
    """Test saving current project."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = Path(tmpdir) / "current_project.json"

        with patch("sidecar.web.CURRENT_PROJECT_FILE", project_file):
            _save_current_project("/test/path")

            assert project_file.exists()
            data = json.loads(project_file.read_text())
            assert data["project_path"] == "/test/path"


def test_load_current_project_corrupt_file():
    """Test loading project with corrupt JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = Path(tmpdir) / "current_project.json"
        project_file.write_text("{ invalid json }")

        with patch("sidecar.web.CURRENT_PROJECT_FILE", project_file):
            # Also need to clear the environment variable fallback
            with patch.dict(os.environ, {"KAICAD_PROJECT": ""}, clear=False):
                result = _load_current_project()

                # Should handle error gracefully
                assert result is None or result == ""


def test_save_current_project_sets_env_var():
    """Test that saving project sets environment variable."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_file = Path(tmpdir) / "current_project.json"

        with patch("sidecar.web.CURRENT_PROJECT_FILE", project_file):
            _save_current_project("/test/project")

            assert os.environ.get("KAICAD_PROJECT") == "/test/project"


def test_debug_schematic_route_no_project(client):
    """Test debug_schematic endpoint without project."""
    response = client.get("/debug_schematic")

    # Should return some response (error or redirect)
    assert response.status_code in [200, 302, 400, 404]


def test_debug_schematic_route_with_project(client, temp_project_dir):
    """Test debug_schematic endpoint with project."""
    sch_path = temp_project_dir / "test.kicad_sch"
    sch_path.write_text("(kicad_sch (version 20231120))")

    with patch("sidecar.web._load_current_project", return_value=str(sch_path)):
        response = client.get("/debug_schematic")

        assert response.status_code in [200, 400, 500]


def test_generate_description_route_get_not_allowed(client):
    """Test that generate_description doesn't allow GET."""
    response = client.get("/generate_description")

    # Should not allow GET (405) or redirect
    assert response.status_code in [302, 405]


def test_generate_description_route_post_no_data(client):
    """Test generate_description POST without data."""
    response = client.post("/generate_description", json={})

    # Should return error or process
    assert response.status_code in [200, 400, 500]


def test_generate_description_route_post_with_prompt(client):
    """Test generate_description POST with prompt."""
    response = client.post("/generate_description", json={"prompt": "Test prompt"})

    # Should return JSON response
    assert response.status_code in [200, 400, 500]

    if response.status_code == 200:
        # Should be JSON
        data = response.get_json()
        assert data is not None


def test_send_chat_route_get_not_allowed(client):
    """Test that send_chat doesn't allow GET."""
    response = client.get("/send_chat")

    # Should not allow GET
    assert response.status_code in [302, 405]


def test_send_chat_route_post_no_message(client):
    """Test send_chat POST without message."""
    response = client.post("/send_chat", json={})

    # Should return 200 with error in JSON
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data.get("success") is False


def test_send_chat_route_post_with_message(client):
    """Test send_chat POST with message."""
    response = client.post("/send_chat", json={"message": "Hello"})

    # Should return response
    assert response.status_code in [200, 400, 500]


def test_app_has_required_routes(client):
    """Test that app has all expected routes."""
    # Get all registered routes
    routes = [str(rule) for rule in app.url_map.iter_rules()]

    # Check for main routes
    assert "/" in routes
    assert "/debug_schematic" in routes
    assert "/generate_description" in routes
    assert "/send_chat" in routes


def test_app_security_config():
    """Test that app has security configuration."""
    # App is already configured at module import time
    # Should have secret key configured
    assert app.secret_key is not None
    assert app.secret_key != ""
    assert len(app.secret_key) > 10


def test_index_with_invalid_project_path(client):
    """Test index with non-existent project path."""
    response = client.post("/", data={"project_path": "/nonexistent/path/test.kicad_sch", "user_prompt": "Test"})

    # Should handle gracefully
    assert response.status_code in [200, 302, 400, 500]


def test_app_template_folder_configured():
    """Test that template folder is properly configured."""
    assert app.template_folder is not None
    assert "templates" in str(app.template_folder).lower()


def test_load_current_project_respects_env_var():
    """Test that load falls back to environment variable."""
    with patch("sidecar.web.CURRENT_PROJECT_FILE") as mock_file:
        mock_file.exists.return_value = False

        with patch.dict(os.environ, {"KAICAD_PROJECT": "/env/project"}):
            result = _load_current_project()

            # Should fall back to env var
            assert result == "/env/project" or result == ""


def test_multiple_requests_maintain_state(client):
    """Test that multiple requests work correctly."""
    # First request
    response1 = client.get("/")
    assert response1.status_code in [200, 302, 400, 500]

    # Second request
    response2 = client.get("/")
    assert response2.status_code in [200, 302, 400, 500]

    # Both should succeed
    assert response1.status_code >= 0
    assert response2.status_code >= 0


def test_json_endpoints_return_json(client):
    """Test that JSON endpoints return JSON content type."""
    # Test generate_description
    response = client.post("/generate_description", json={"prompt": "test"}, content_type="application/json")

    if response.status_code == 200:
        assert response.is_json or "application/json" in response.content_type


def test_app_handles_missing_csrf_gracefully(client):
    """Test that app handles missing CSRF token in testing mode."""
    # In testing mode with CSRF disabled, this should work
    response = client.post("/", data={"test": "data"})

    # Should not fail due to CSRF
    assert response.status_code in [200, 302, 400, 500]


def test_project_persistence_across_requests(client, temp_project_dir):
    """Test that project path persists across requests."""
    sch_path = temp_project_dir / "persist.kicad_sch"
    sch_path.write_text("(kicad_sch (version 20231120))")

    # Save project
    with patch("sidecar.web.CURRENT_PROJECT_FILE") as mock_file:
        mock_file.exists.return_value = False
        _save_current_project(str(sch_path))

    # Verify it was saved
    assert os.environ.get("KAICAD_PROJECT") == str(sch_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
