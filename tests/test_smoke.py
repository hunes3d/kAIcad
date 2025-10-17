"""Smoke tests for kAIcad sidecar"""
import os
import pytest
from pathlib import Path
from sidecar.schema import Plan, AddComponent, Label, Wire
from sidecar.settings import Settings


def test_schema_validation():
    """Test Plan schema accepts valid operations"""
    plan_dict = {
        "ops": [
            {
                "op": "add_component",
                "ref": "R1",
                "symbol": "Device:R",
                "value": "1k",
                "at": [100, 100],
                "rot": 0
            },
            {
                "op": "label",
                "net": "VCC",
                "at": [120, 100]
            },
            {
                "op": "wire",
                "from": "R1:1",
                "to": "R2:2"
            }
        ]
    }
    plan = Plan.model_validate(plan_dict)
    assert len(plan.ops) == 3
    assert isinstance(plan.ops[0], AddComponent)
    assert isinstance(plan.ops[1], Label)
    assert isinstance(plan.ops[2], Wire)


def test_schema_serialization_uses_aliases():
    """Test that serialization produces 'from' not 'from_'"""
    plan = Plan(ops=[
        Wire(op="wire", from_="R1:1", to="R2:2")
    ])
    dumped = plan.model_dump(by_alias=True)
    assert "from" in dumped["ops"][0]
    assert "from_" not in dumped["ops"][0]


def test_settings_persistence(tmp_path):
    """Test settings can be saved and loaded"""
    config_dir = tmp_path / ".kAIcad"
    config_path = config_dir / "config.json"
    
    # Monkey-patch the config path
    import sidecar.settings as settings_module
    original_dir = settings_module.CONFIG_DIR
    original_path = settings_module.CONFIG_PATH
    
    try:
        settings_module.CONFIG_DIR = config_dir
        settings_module.CONFIG_PATH = config_path
        
        # Create and save settings
        s = Settings(
            openai_model="gpt-4o",
            openai_temperature=0.5,
            openai_api_key="test-key",
            default_project="/test/path"
        )
        s.save()
        
        # Load and verify - clear env vars that might override
        old_temp = os.environ.get("OPENAI_TEMPERATURE")
        try:
            os.environ.pop("OPENAI_TEMPERATURE", None)
            s2 = Settings.load()
            assert s2.openai_model == "gpt-4o"
            assert s2.openai_temperature == 0.5
            assert s2.openai_api_key == "test-key"
        finally:
            if old_temp is not None:
                os.environ["OPENAI_TEMPERATURE"] = old_temp
        
    finally:
        settings_module.CONFIG_DIR = original_dir
        settings_module.CONFIG_PATH = original_path


def test_imports():
    """Test all main modules import without errors"""
    from sidecar.main import main
    from sidecar.web import create_app
    from sidecar.desk import SidecarApp
    from sidecar.planner import plan_from_prompt
    from sidecar.writer_skip import apply_plan
    
    assert callable(main)
    assert callable(create_app)
    assert callable(plan_from_prompt)
    assert callable(apply_plan)
