"""Tests for the enhanced planner_v2 module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from kaicad.config.settings import Settings
from kaicad.core.planner_v2 import _demo_plan, _snap_to_grid, plan_from_prompt, KICAD_GRID_MM
from kaicad.schema.plan import Plan


class TestGridSnapping:
    """Test grid snapping functionality."""

    def test_snap_to_grid_exact(self):
        """Test snapping coordinates that are already on grid."""
        x, y = _snap_to_grid(1.27, 2.54)
        assert x == 1.27
        assert y == 2.54

    def test_snap_to_grid_round_down(self):
        """Test snapping coordinates that round down."""
        x, y = _snap_to_grid(1.0, 2.0, grid=KICAD_GRID_MM)
        assert abs(x - 1.27) < 0.01
        assert abs(y - 2.54) < 0.01

    def test_snap_to_grid_round_up(self):
        """Test snapping coordinates that round up."""
        x, y = _snap_to_grid(1.5, 3.0, grid=KICAD_GRID_MM)
        assert abs(x - 1.27) < 0.01
        assert abs(y - 2.54) < 0.01

    def test_snap_to_grid_custom_grid(self):
        """Test snapping with custom grid size."""
        x, y = _snap_to_grid(5.5, 7.8, grid=2.0)
        assert x == 6.0
        assert y == 8.0


class TestDemoPlan:
    """Test demo plan generation."""

    def test_demo_plan_valid(self):
        """Test that demo plan is valid."""
        plan = _demo_plan()
        assert isinstance(plan, Plan)
        assert plan.plan_version == 1
        assert len(plan.ops) > 0

    def test_demo_plan_has_led_circuit(self):
        """Test that demo plan contains LED circuit components."""
        plan = _demo_plan()
        refs = [op.ref for op in plan.ops if hasattr(op, "ref")]
        assert "R1" in refs
        assert "D1" in refs


class TestPlanFromPromptNoAPIKey:
    """Test plan_from_prompt when no API key is available."""

    def test_no_api_key_returns_demo_plan(self):
        """Test that missing API key returns demo plan with warning."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="",  # No API key
            default_project="",
            dock_right=True
        )

        result = plan_from_prompt("Add LED", settings=settings)

        assert result.plan is not None
        assert len(result.diagnostics) == 1
        assert result.diagnostics[0].severity == "warning"
        assert "No OpenAI API key" in result.diagnostics[0].message

    def test_no_settings_loads_from_config(self):
        """Test that plan_from_prompt loads settings if not provided."""
        # Remove env var so config is used
        old_key = os.environ.pop("OPENAI_API_KEY", None)
        try:
            with patch("kaicad.core.planner_v2.Settings.load") as mock_load:
                mock_settings = Settings(
                    openai_model="gpt-4o-mini",
                    openai_temperature=0.0,
                    openai_api_key="",
                    default_project="",
                    dock_right=True
                )
                mock_load.return_value = mock_settings

                result = plan_from_prompt("Add LED")

                mock_load.assert_called_once()
                assert result.plan is not None
        finally:
            if old_key:
                os.environ["OPENAI_API_KEY"] = old_key


class TestPlanFromPromptWithMockAPI:
    """Test plan_from_prompt with mocked OpenAI API."""

    def test_successful_plan_generation_responses_api(self):
        """Test successful plan generation using Responses API."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        mock_plan = {
            "plan_version": 1,
            "ops": [
                {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80, 50], "rot": 0}
            ]
        }

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Mock Responses API
            mock_response = MagicMock()
            mock_response.output_text = json.dumps(mock_plan)
            mock_client.responses.create.return_value = mock_response

            result = plan_from_prompt("Add resistor", settings=settings)

            assert result.plan is not None
            assert len(result.plan.ops) == 1
            assert result.diagnostics[0].severity == "info"
            assert "Responses API" in result.diagnostics[0].message

    def test_successful_plan_generation_chat_api(self):
        """Test successful plan generation using Chat API fallback."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        mock_plan = {
            "plan_version": 1,
            "ops": [
                {"op": "add_component", "ref": "D1", "symbol": "Device:LED", "value": "RED", "at": [100, 50], "rot": 0}
            ]
        }

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Responses API fails, Chat API succeeds
            mock_client.responses.create.side_effect = Exception("Responses API not available")

            mock_choice = MagicMock()
            mock_choice.message.content = json.dumps(mock_plan)
            mock_completion = MagicMock()
            mock_completion.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_completion

            result = plan_from_prompt("Add LED", settings=settings)

            assert result.plan is not None
            assert len(result.plan.ops) == 1
            assert result.diagnostics[0].severity == "info"
            assert "Chat API" in result.diagnostics[0].message

    def test_invalid_model_returns_demo_plan(self):
        """Test that invalid model returns demo plan with error."""
        settings = Settings(
            openai_model="gpt-999-nonexistent",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        result = plan_from_prompt("Add LED", settings=settings)

        assert result.plan is not None
        assert any(d.severity == "error" and "Invalid model" in d.message for d in result.diagnostics)

    def test_json_decode_error_returns_demo_plan(self):
        """Test that invalid JSON response returns demo plan with error."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Both APIs fail, return invalid JSON
            mock_client.responses.create.side_effect = Exception("Responses API not available")

            mock_choice = MagicMock()
            mock_choice.message.content = "This is not JSON"
            mock_completion = MagicMock()
            mock_completion.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_completion

            result = plan_from_prompt("Add LED", settings=settings)

            assert result.plan is not None
            assert any(d.severity == "error" and "Invalid JSON" in d.message for d in result.diagnostics)

    def test_openai_api_error_returns_demo_plan(self):
        """Test that OpenAI API error returns demo plan with warning."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # All APIs fail
            mock_client.responses.create.side_effect = Exception("Responses API failed")
            mock_client.chat.completions.create.side_effect = Exception("Rate limit exceeded")

            result = plan_from_prompt("Add LED", settings=settings)

            assert result.plan is not None
            assert any(d.severity == "warning" and "OpenAI API error" in d.message for d in result.diagnostics)

    def test_openai_import_error_returns_demo_plan(self):
        """Test that missing OpenAI package returns demo plan with error."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        # Patch the import itself to simulate missing package
        import builtins
        original_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "openai":
                raise ImportError("No module named 'openai'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            result = plan_from_prompt("Add LED", settings=settings)

            assert result.plan is not None
            assert any(d.severity == "error" and "not installed" in d.message for d in result.diagnostics)

    def test_model_override_parameter(self):
        """Test that model_override parameter works."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.0,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        mock_plan = {
            "plan_version": 1,
            "ops": [
                {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80, 50], "rot": 0}
            ]
        }

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            mock_response = MagicMock()
            mock_response.output_text = json.dumps(mock_plan)
            mock_client.responses.create.return_value = mock_response

            result = plan_from_prompt("Add resistor", settings=settings, model_override="gpt-4o")

            # Verify the override model was used
            call_args = mock_client.responses.create.call_args
            assert call_args[1]["model"] == "gpt-4o"

    def test_temperature_setting_used(self):
        """Test that temperature from settings is used."""
        settings = Settings(
            openai_model="gpt-4o-mini",
            openai_temperature=0.7,
            openai_api_key="sk-test-key",
            default_project="",
            dock_right=True
        )

        mock_plan = {
            "plan_version": 1,
            "ops": [
                {"op": "add_component", "ref": "R1", "symbol": "Device:R", "value": "1k", "at": [80, 50], "rot": 0}
            ]
        }

        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client

            # Responses API fails, Chat API succeeds
            mock_client.responses.create.side_effect = Exception("Not available")

            mock_choice = MagicMock()
            mock_choice.message.content = json.dumps(mock_plan)
            mock_completion = MagicMock()
            mock_completion.choices = [mock_choice]
            mock_client.chat.completions.create.return_value = mock_completion

            result = plan_from_prompt("Add resistor", settings=settings)

            # Verify temperature was passed
            call_args = mock_client.chat.completions.create.call_args
            assert call_args[1]["temperature"] == 0.7
